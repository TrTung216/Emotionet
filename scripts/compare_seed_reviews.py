"""Compare two submitted reviews without merging decisions or inventing dates."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITABLE = {"decision", "reviewed_emotions", "sense_gloss", "reviewer", "reviewed_at", "notes"}
BOOL_FIELDS = {"association_vectors_differ", "source_has_missing_flags"}
DECISIONS = {"accept", "revise", "reject", "needs_evidence"}


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])):
            raise ValueError("Duplicate CSV column")
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("Empty or malformed review CSV")
    return rows


def index(rows):
    result = {r["review_id"]: r for r in rows}
    if len(result) != len(rows) or "" in result:
        raise ValueError("Duplicate or empty review ID")
    return result


def labels(row):
    return frozenset(x.strip() for x in row["reviewed_emotions"].split(";") if x.strip())


def validate(rows, template, allowed_labels):
    original, submitted = index(template), index(rows)
    if set(original) != set(submitted):
        raise ValueError("Review ID set differs from template")
    missing_dates = []
    for key, row in submitted.items():
        if row.keys() != original[key].keys():
            raise ValueError(f"{key}: columns differ from template")
        for field in row.keys() - EDITABLE:
            left, right = row[field], original[key][field]
            if field in BOOL_FIELDS:
                left, right = left.casefold(), right.casefold()
            elif field == "source_emotions_summary":
                left, right = json.loads(left), json.loads(right)
            if left != right:
                raise ValueError(f"{key}: original column changed: {field}")
        if row["decision"] not in DECISIONS or not row["reviewer"].strip():
            raise ValueError(f"{key}: missing/invalid decision or reviewer")
        tokens = [x.strip() for x in row["reviewed_emotions"].split(";")] if row["reviewed_emotions"] else []
        if len(tokens) != len(set(tokens)) or not set(tokens).issubset(allowed_labels):
            raise ValueError(f"{key}: invalid/duplicate labels")
        if row["decision"] in {"accept", "revise"} and (not tokens or not row["sense_gloss"].strip()):
            raise ValueError(f"{key}: decision needs labels and sense")
        if not row["reviewed_at"].strip():
            missing_dates.append(key)
        else:
            stamp = datetime.fromisoformat(row["reviewed_at"])
            if stamp.tzinfo is None:
                raise ValueError(f"{key}: review date needs timezone")
    return missing_dates


def compare(first, second, baseline):
    a, b, old = index(first), index(second), index(baseline)
    if not set(a) == set(b) == set(old):
        raise ValueError("Review/baseline IDs differ")
    comparison = []
    for key, left in a.items():
        right, previous = b[key], old[key]
        same_decision = left["decision"] == right["decision"]
        same_labels = labels(left) == labels(right)
        both_accept = left["decision"] == right["decision"] == "accept"
        same_baseline = labels(left) == labels(previous)
        status = ("aligned_accept" if same_baseline else "joint_label_change") if both_accept and same_labels else "needs_adjudication"
        row = {"review_id": key, "term": left["term"], "comparison_status": status,
               "decision_agreement": same_decision, "label_set_agreement": same_labels,
               "gloss_text_identical": left["sense_gloss"].strip() == right["sense_gloss"].strip(),
               "baseline_emotions": previous["reviewed_emotions"], "baseline_gloss": previous["sense_gloss"]}
        for prefix, source in [("review_a", left), ("review_b", right)]:
            for field in sorted(EDITABLE):
                row[f"{prefix}_{field}"] = source[field]
        row.update(final_decision="", final_emotions="", final_gloss="", adjudicator="", adjudicated_at="", resolution_notes="")
        comparison.append(row)
    summary = {"rows": len(comparison), "comparison_status_counts": dict(Counter(r["comparison_status"] for r in comparison)),
               "decision_agreement_count": sum(r["decision_agreement"] for r in comparison),
               "label_set_agreement_count": sum(r["label_set_agreement"] for r in comparison),
               "decision_and_label_agreement_count": sum(r["decision_agreement"] and r["label_set_agreement"] for r in comparison),
               "gloss_text_identical_count": sum(r["gloss_text_identical"] for r in comparison),
               "interpretation": ["Agreement compares decision strings and unordered label sets, not semantic equivalence of glosses.",
                                  "Reviewer independence is not established; baseline is a prior version, not a third independent vote.",
                                  "No majority vote, label union, source changes or automatic acceptance is performed."]}
    return summary, comparison


def run(first_path, second_path, baseline_path, template_path, taxonomy_path, output):
    private, output = (ROOT / "data/local").resolve(), output.resolve()
    if output == private or not output.is_relative_to(private):
        raise ValueError("Use a new directory under data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite a comparison")
    first, second, baseline, template = map(read, [first_path, second_path, baseline_path, template_path])
    allowed = set(json.loads(taxonomy_path.read_text(encoding="utf-8"))["label2id"]) - {"neutral"}
    metadata = {}
    for name, rows in [("review_a", first), ("review_b", second)]:
        missing = validate(rows, template, allowed)
        metadata[name] = {"reviewers": sorted({r["reviewer"] for r in rows}),
                          "decisions": dict(Counter(r["decision"] for r in rows)),
                          "missing_reviewed_at_count": len(missing)}
    summary, comparison = compare(first, second, baseline)
    summary["review_metadata"] = metadata
    paths = {"review_a": first_path, "review_b": second_path, "baseline": baseline_path,
             "template": template_path, "taxonomy": taxonomy_path}
    summary["inputs"] = {key: {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for key, p in paths.items()}
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in [("comparison.csv", comparison), ("adjudication-queue.csv", [r for r in comparison if r["comparison_status"] != "aligned_accept"])]:
        with (output / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(comparison[0]))
            writer.writeheader()
            writer.writerows(rows)
    for key, path in paths.items():
        (output / (key + path.suffix)).write_bytes(path.read_bytes())
    summary["output_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-a", type=Path, required=True)
    parser.add_argument("--review-b", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=ROOT / "data/local/reviewed-seeds-v2/submitted-review.csv")
    parser.add_argument("--template", type=Path, default=ROOT / "data/local/seed-review-v1/seed-review.csv")
    parser.add_argument("--taxonomy", type=Path, default=ROOT / "configs/vigoemotions-labels.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/team-seed-review-v1")
    args = parser.parse_args()
    print(json.dumps(run(args.review_a, args.review_b, args.baseline, args.template, args.taxonomy, args.output), ensure_ascii=True))


if __name__ == "__main__":
    main()
