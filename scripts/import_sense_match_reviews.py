"""Snapshot sense decisions and sample reviews, checking text against train.

Review decisions are preserved as submitted. Ingestion does not adjudicate
semantics, infer sample reviewers or turn this convenience sample into gold data.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_seed_coverage import audit

ROOT = Path(__file__).resolve().parents[1]
MATCH_DECISIONS = {"matches_sense", "wrong_sense", "uncertain"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or any(None in r or None in r.values() for r in rows):
        raise ValueError("Empty or malformed CSV")
    return rows


def validate_senses(rows, seeds):
    index = {s["seed_id"]: s for s in seeds}
    ids = set()
    for row in rows:
        key = row["draft_sense_id"]
        if key in ids or not re.fullmatch(re.escape(row["seed_id"]) + r"_s[1-9][0-9]*", key):
            raise ValueError("Duplicate or invalid sense ID")
        ids.add(key)
        parent = index[row["seed_id"]]
        labels = row["proposed_emotions"].split(";")
        if row["term"] != parent["term"] or len(set(labels)) != len(labels) or not set(labels) <= set(parent["emotion_labels"]):
            raise ValueError("Sense term/labels do not match the selected seed version")
        if row["decision"] != "accept" or not row["reviewer"].strip() or not row["sense_gloss"].strip():
            raise ValueError("Expected explicit accepted sense with reviewer and gloss")


def validate_samples(rows, expected):
    original = {(r["seed_id"], r["dataset_id"]): r for r in expected}
    keys = [(r["seed_id"], r["dataset_id"]) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(original):
        raise ValueError("Reviewed sample pairs differ from regenerated train samples")
    for row in rows:
        reference = original[(row["seed_id"], row["dataset_id"])]
        if row.keys() != reference.keys():
            raise ValueError("Sample columns differ")
        for field in reference.keys() - {"sense_match_decision", "notes"}:
            if row[field] != reference[field]:
                raise ValueError(f"Original sample field modified: {field}")
        if row["sense_match_decision"] not in MATCH_DECISIONS or not row["notes"].strip():
            raise ValueError("Missing sample decision or reason")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def run(sense_path, sample_path, seed_path, train_path, submission_path, output):
    output = output.resolve()
    private = (ROOT / "data/local").resolve()
    if output == private or not output.is_relative_to(private):
        raise ValueError("Output must be a new directory under data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite a review snapshot")
    if train_path.name != "train.csv":
        raise ValueError("Use train.csv only")
    seeds = [json.loads(s) for s in seed_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    senses, samples = read_csv(sense_path), read_csv(sample_path)
    validate_senses(senses, seeds)
    with train_path.open(encoding="utf-8-sig", newline="") as handle:
        _, _, expected = audit(seeds, csv.DictReader(handle))
    validate_samples(samples, expected)
    imported_at = datetime.now(timezone.utc).isoformat()
    sense_hash = sha256(sense_path)
    accepted = [{"sense_id": r["draft_sense_id"], "seed_id": r["seed_id"], "term": r["term"],
                 "emotion_labels": r["proposed_emotions"].split(";"), "sense_gloss": r["sense_gloss"],
                 "context_example": r["context_example"], "example_kind": "illustrative_text_not_full_corpus_citation",
                 "semantic_status": "accepted_as_submitted", "reviewer": r["reviewer"], "reviewed_at": None,
                 "review_notes": r["notes"], "imported_at": imported_at, "source_sha256": sense_hash,
                 "synset_id": None, "publication_status": "not_cleared"} for r in senses]
    counts = Counter(r["sense_match_decision"] for r in samples)
    summary = {"schema_version": 1, "imported_at": imported_at, "accepted_split_senses": len(accepted),
               "split_terms": len({r["seed_id"] for r in senses}), "sample_pairs": len(samples),
               "distinct_train_sentences": len({r["dataset_id"] for r in samples}),
               "submitted_sample_decisions": dict(counts),
               "submitted_match_fraction": counts["matches_sense"] / len(samples),
               "source_identity_validation": "all sample pairs, texts and metadata match regenerated train samples",
               "semantic_validation": "not_adjudicated; review notes and decisions may require correction",
               "review_metadata": "Sense reviewer retained; sense review dates and sample reviewer/date unspecified, not inferred.",
               "limitations": ["155 sampled seed-sentence pairs are not necessarily 155 distinct sentences.",
                               "First-three-per-seed samples do not establish overall precision or accuracy.",
                               "Separate lexical meaning from negation, intensity scope, speaker attribution and mentions.",
                               "Splitting senses does not perform contextual word sense disambiguation."]}
    paths = {"sense_review": sense_path, "match_review": sample_path, "seeds": seed_path,
             "train": train_path, "user_submission": submission_path}
    summary["inputs"] = {name: {"path": str(path), "sha256": sha256(path)} for name, path in paths.items()}
    output.mkdir(parents=True, exist_ok=False)
    for name, path in paths.items():
        if name != "train":
            (output / (name + path.suffix)).write_bytes(path.read_bytes())
    jsonl(output / "accepted-split-senses.jsonl", accepted)
    jsonl(output / "sense-review-events.jsonl", [{"submitted_row": r, "imported_at": imported_at,
          "source_sha256": sense_hash} for r in senses])
    jsonl(output / "match-review-events.jsonl", [{"submitted_row": r, "reviewer": None, "reviewed_at": None,
          "imported_at": imported_at, "source_sha256": sha256(sample_path), "status": "submitted_not_adjudicated"} for r in samples])
    summary["output_sha256"] = {path.name: sha256(path) for path in output.iterdir()}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--senses", type=Path, default=ROOT / "data/local/seed-analysis-v2/sense-split-review.csv")
    parser.add_argument("--samples", type=Path, default=ROOT / "data/local/seed-coverage-v2/match-review-samples.csv")
    parser.add_argument("--seeds", type=Path, default=ROOT / "data/local/reviewed-seeds-v2/accepted-seeds.jsonl")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/sense-match-review-v1")
    args = parser.parse_args()
    result = run(args.senses, args.samples, args.seeds, args.train, args.submission, args.output)
    print(json.dumps({k: result[k] for k in ["accepted_split_senses", "sample_pairs", "distinct_train_sentences", "submitted_sample_decisions"]}))


if __name__ == "__main__":
    main()
