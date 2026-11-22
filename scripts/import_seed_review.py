"""Validate and snapshot submitted seed decisions without changing the review CSV.

Only accept decisions enter the semantic seed set. Revision/evidence requests
remain pending; source associations never override reviewed emotion labels.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_FIELDS = ("decision", "reviewed_emotions", "sense_gloss", "reviewer", "reviewed_at", "notes")
FIELDS = ("review_id", "term", "normalized_form", "proposed_vigoemotions", "proposal_method",
          "source_count", "source_row_count", "source_emotions_summary",
          "association_vectors_differ", "source_has_missing_flags", "status", *REVIEW_FIELDS)
DECISIONS = ("accept", "revise", "reject", "needs_evidence")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError(f"Unexpected CSV columns: {path.name}")
        rows = list(reader)
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f"Empty or malformed CSV: {path.name}")
    return rows


def index_rows(rows):
    result = {}
    for row in rows:
        key = row["review_id"]
        if not key or key in result:
            raise ValueError(f"Missing or duplicate review_id: {key}")
        result[key] = row
    return result


def validate(template, reviewed, evidence, label2id):
    original = index_rows(template)
    submitted = index_rows(reviewed)
    evidence_index = index_rows(evidence)
    if set(original) != set(submitted) or set(original) != set(evidence_index):
        raise ValueError("Review/template/evidence ID sets differ")
    for key, row in submitted.items():
        for field in FIELDS:
            if field not in REVIEW_FIELDS and row[field] != original[key][field]:
                raise ValueError(f"{key}: original column modified: {field}")
        decision = row["decision"]
        if decision not in DECISIONS:
            raise ValueError(f"{key}: unknown or missing decision")
        for field in ("reviewer", "reviewed_at"):
            if not row[field].strip():
                raise ValueError(f"{key}: missing {field}")
        stamp = datetime.fromisoformat(row["reviewed_at"])
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError(f"{key}: reviewed_at must include timezone")
        labels = row["reviewed_emotions"].split(";") if row["reviewed_emotions"] else []
        if len(labels) != len(set(labels)) or any(label not in label2id or label == "neutral" for label in labels):
            raise ValueError(f"{key}: invalid or duplicate seed emotion")
        if decision in {"accept", "revise"} and (not labels or not row["sense_gloss"].strip()):
            raise ValueError(f"{key}: {decision} needs emotion labels and sense_gloss")
        if decision != "accept" and not row["notes"].strip():
            raise ValueError(f"{key}: non-accept decision needs a reason in notes")
        observations = evidence_index[key]["observations"]
        if len(observations) != int(row["source_row_count"]):
            raise ValueError(f"{key}: evidence row count differs")
        if len({item["source_id"] for item in observations}) != int(row["source_count"]):
            raise ValueError(f"{key}: evidence source count differs")
        if any(item["normalized_form"] != row["normalized_form"] for item in observations):
            raise ValueError(f"{key}: evidence term differs")
    return original, evidence_index


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def import_review(review_path, template_path, evidence_path, taxonomy_path, source_summary_path, output):
    output = output.resolve()
    private_root = (ROOT / "data/local").resolve()
    if not output.is_relative_to(private_root) or output == private_root:
        raise ValueError("Use a new output directory inside Emotionet/data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing review snapshot")
    reviewed = read_csv(review_path)
    template = read_csv(template_path)
    evidence = [json.loads(line) for line in evidence_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    source_summary = json.loads(source_summary_path.read_text(encoding="utf-8"))
    original, evidence_index = validate(template, reviewed, evidence, taxonomy["label2id"])
    imported_at = datetime.now(timezone.utc).isoformat()
    review_hash = sha256(review_path)
    events, seeds = [], []
    for row in reviewed:
        key = row["review_id"]
        event_id = f"{key}:{review_hash[:16]}"
        events.append({"event_id": event_id, "review_id": key, "imported_at": imported_at,
                       "original_row": original[key], "submitted_row": row,
                       "review_file_sha256": review_hash})
        if row["decision"] == "accept":
            labels = row["reviewed_emotions"].split(";")
            seeds.append({
                "seed_id": key, "term": row["term"], "normalized_form": row["normalized_form"],
                "sense_gloss": row["sense_gloss"], "emotion_labels": labels,
                "emotion_ids": [taxonomy["label2id"][label] for label in labels],
                "taxonomy_id": taxonomy["taxonomy_id"], "taxonomy_version": taxonomy["version"],
                "semantic_status": "accepted", "publication_status": "not_cleared",
                "synset_id": None, "intensity": None, "confidence": None,
                "review_event_id": event_id, "reviewer": row["reviewer"], "reviewed_at": row["reviewed_at"],
                "review_notes": row["notes"],
                "source_evidence": evidence_index[key]["observations"],
            })
    counts = Counter(row["decision"] for row in reviewed)
    coverage = Counter(label for seed in seeds for label in seed["emotion_labels"])
    summary = {
        "schema_version": 1, "imported_at": imported_at,
        "reviewed_rows": len(reviewed), "decisions": {key: counts[key] for key in DECISIONS},
        "accepted_seed_count": len(seeds), "accepted_label_counts": dict(sorted(coverage.items())),
        "labels_without_accepted_seeds": sorted(set(taxonomy["label2id"]) - {"neutral"} - set(coverage)),
        "publication_status": "not_cleared", "synsets_created": 0,
        "inputs": {name: {"filename": path.name, "sha256": sha256(path)} for name, path in
                   [("review", review_path), ("template", template_path), ("evidence", evidence_path),
                    ("taxonomy", taxonomy_path), ("source_summary", source_summary_path)]},
        "original_source_files": source_summary["source_files"],
    }
    output.mkdir(parents=True, exist_ok=False)
    write_jsonl(output / "accepted-seeds.jsonl", seeds)
    write_jsonl(output / "review-events.jsonl", events)
    write_csv(output / "pending-review.csv", [row for row in reviewed if row["decision"] in {"revise", "needs_evidence"}])
    write_csv(output / "rejected-review.csv", [row for row in reviewed if row["decision"] == "reject"])
    # Copy bytes to preserve the exact reviewed artifact and its provenance.
    for source, filename in [(review_path, "submitted-review.csv"), (template_path, "original-template.csv"),
                             (evidence_path, "review-evidence.jsonl"), (taxonomy_path, "taxonomy.json"),
                             (source_summary_path, "source-summary.json")]:
        (output / filename).write_bytes(source.read_bytes())
    summary["output_sha256"] = {path.name: sha256(path) for path in sorted(output.iterdir())}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_source = ROOT / "data/local/seed-review-v1"
    parser.add_argument("--review", type=Path, default=default_source / "seed-review-completed.csv")
    parser.add_argument("--template", type=Path, default=default_source / "seed-review.csv")
    parser.add_argument("--evidence", type=Path, default=default_source / "review-evidence.jsonl")
    parser.add_argument("--taxonomy", type=Path, default=ROOT / "configs/vigoemotions-labels.json")
    parser.add_argument("--source-summary", type=Path, default=default_source / "summary.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/reviewed-seeds-v1")
    args = parser.parse_args()
    result = import_review(args.review, args.template, args.evidence, args.taxonomy, args.source_summary, args.output)
    print(json.dumps({key: result[key] for key in ("reviewed_rows", "decisions", "accepted_seed_count", "labels_without_accepted_seeds")}, ensure_ascii=True))


if __name__ == "__main__":
    main()
