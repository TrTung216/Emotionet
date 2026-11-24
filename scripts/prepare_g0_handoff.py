"""Package existing accepted meanings for G0 without inventing new reviews.

Run once to a new directory; --check compares the package with its source reviews.
This verifies provenance and consistency, not independent semantic correctness.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/g0-handoff.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def construct(root=ROOT):
    config = json.loads((root / "configs/g0-handoff.json").read_text(encoding="utf-8"))
    seeds = read_jsonl(root / config["seed_source"])
    senses = {row["seed_id"]: row for row in read_jsonl(root / config["sense_source"])}
    split_ids = {row["seed_id"] for row in read_jsonl(root / config["split_source"])}
    taxonomy = json.loads((root / config["taxonomy_source"]).read_text(encoding="utf-8"))
    with (root / config["context_source"]).open(encoding="utf-8-sig", newline="") as handle:
        contexts = list(csv.DictReader(handle))
    positive = {}
    for row in contexts:
        if row["split"] == "train" and row["sense_match_decision"] == "matches_sense":
            positive.setdefault(row["seed_id"], row)
    eligible = [s for s in seeds if s["seed_id"] not in split_ids
                and s["semantic_status"] == "accepted" and s["reviewer"] and s["reviewed_at"]
                and s["seed_id"] in positive]
    labels = [name for name in taxonomy["label2id"] if name != "neutral"]
    selected = []
    for label in labels:
        matches = [s for s in eligible if s["emotion_labels"] == [label]]
        if not matches:
            raise ValueError(f"No eligible single-label reviewed example for {label}")
        selected.append(matches[0])
    for term in config["extra_terms"]:
        matches = [s for s in eligible if s["term"] == term]
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous extra term: {term}")
        selected.append(matches[0])
    if len(selected) != config["sample_count"] or len({s["seed_id"] for s in selected}) != len(selected):
        raise ValueError("Invalid sample count or duplicate selection")
    samples = []
    for seed in selected:
        sense = senses[seed["seed_id"]]
        if sense["gloss"] != seed["sense_gloss"] or sense["emotion_labels"] != seed["emotion_labels"]:
            raise ValueError(f"Sense differs from approved seed: {seed['seed_id']}")
        context = positive[seed["seed_id"]]
        samples.append({
            "sample_id": "g0_" + sense["sense_id"],
            "entry_id": sense["entry_id"], "sense_id": sense["sense_id"],
            "seed_synset_id": sense["synset_id"], "lemma": seed["term"],
            "normalized_form": seed["normalized_form"], "pos": None,
            "gloss": seed["sense_gloss"], "emotion_labels": seed["emotion_labels"],
            "taxonomy_id": seed["taxonomy_id"], "taxonomy_version": seed["taxonomy_version"],
            "semantic_status": "accepted_from_existing_review",
            "review": {key: seed[key] for key in ["review_event_id", "reviewer", "reviewed_at", "review_notes"]},
            "context_review": dict(context),
            "context_review_identity": "not_recorded_in_submitted_samples",
            "source_evidence": seed["source_evidence"],
            "provenance": {"seed_source": config["seed_source"], "seed_id": seed["seed_id"],
                           "sense_source": config["sense_source"], "context_source": config["context_source"]},
            "independent_review_verified": False,
            "sharing_authorization": config["sharing_authorization"],
            "historical_publication_status": seed["publication_status"],
            "intensity": None, "confidence": None,
        })
    input_paths = [config[k] for k in ["seed_source", "sense_source", "context_source", "split_source",
                                      "taxonomy_source", "sharing_authorization", "seed_selection"]]
    manifest = {
        "schema": "emotionet_g0_reviewed_examples_v1", "prepared_on": config["prepared_on"],
        "sample_count": len(samples), "reviewed_meanings": len(samples),
        "emotion_labels": labels, "label_count": len(labels),
        "context_split": "train", "context_sampling": "existing_exploratory_positive_reviews_not_gold",
        "independent_semantic_review_verified": False,
        "input_sha256": {path: digest(root / path) for path in input_paths},
    }
    return config, samples, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config, samples, manifest = construct()
    target = ROOT / config["sample_directory"]
    if args.check:
        actual = read_jsonl(target / "samples.jsonl")
        saved = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        if actual != samples:
            raise ValueError("Sample package differs from existing review decisions")
        expected = dict(manifest, output_sha256={"samples.jsonl": digest(target / "samples.jsonl")})
        if saved != expected:
            raise ValueError("Manifest count/provenance/hash mismatch")
    else:
        # Never overwrite either a reviewed source or an existing handoff.
        target.mkdir(parents=True, exist_ok=False)
        (target / "samples.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in samples), encoding="utf-8")
        manifest["output_sha256"] = {"samples.jsonl": digest(target / "samples.jsonl")}
        (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(samples)} existing reviewed meanings; {manifest['label_count']} labels; train examples only")
    print("This checks the design handoff; it does not certify a gold set or a new license grant.")


if __name__ == "__main__":
    main()
