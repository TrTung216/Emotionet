"""Measure seed surface matches on train only; this is not emotion prediction.

Reports both all phrase matches and leftmost-longest non-overlapping matches.
Examples are inspection candidates, never automatically verified sense evidence.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def match(text, patterns):
    text = normalize(text)
    hits = sorted((found.start(), found.end(), key)
                  for key, pattern in patterns.items() for found in pattern.finditer(text))
    selected, end = [], 0
    for hit in sorted(hits, key=lambda h: (h[0], -(h[1] - h[0]), h[2])):
        if hit[0] >= end:
            selected.append(hit)
            end = hit[1]
    return hits, selected


def audit(seeds, rows):
    index = {seed["seed_id"]: seed for seed in seeds}
    if not seeds or len(index) != len(seeds):
        raise ValueError("Empty seed set or duplicate seed ID")
    forms = [normalize(seed["normalized_form"]) for seed in seeds]
    if any(not form for form in forms) or len(set(forms)) != len(forms):
        raise ValueError("Expected unique nonempty seed forms")
    if any(seed["semantic_status"] != "accepted" for seed in seeds):
        raise ValueError("Only accepted lexical seeds may enter this audit")
    patterns = {seed["seed_id"]: re.compile(r"(?<!\w)" + re.escape(form) + r"(?!\w)")
                for seed, form in zip(seeds, forms)}
    raw_occ, chosen_occ, raw_rows, chosen_rows = Counter(), Counter(), Counter(), Counter()
    samples, sample_counts = [], Counter()
    count, matched = 0, 0
    ids = set()
    for row in rows:
        if not row.get("id") or row["id"] in ids or not isinstance(row.get("text"), str):
            raise ValueError("Missing/duplicate train ID or missing text")
        ids.add(row["id"])
        count += 1
        raw, chosen = match(row["text"], patterns)
        matched += bool(raw)
        raw_occ.update(key for _, _, key in raw)
        chosen_occ.update(key for _, _, key in chosen)
        raw_rows.update({key for _, _, key in raw})
        chosen_rows.update({key for _, _, key in chosen})
        for key in sorted({key for _, _, key in chosen}):
            if sample_counts[key] < 3:
                samples.append({"seed_id": key, "term": index[key]["term"], "dataset_id": row["id"],
                                "split": "train", "text": row["text"], "sense_match_decision": "",
                                "notes": "", "sample_method": "first_3_matching_rows_not_random"})
                sample_counts[key] += 1
    per_seed = [{"seed_id": key, "term": seed["term"],
                 "reviewed_emotions": ";".join(seed["emotion_labels"]),
                 "raw_matching_rows": raw_rows[key], "raw_occurrences": raw_occ[key],
                 "longest_matching_rows": chosen_rows[key], "longest_occurrences": chosen_occ[key]}
                for key, seed in index.items()]
    return {"train_rows": count, "rows_with_any_seed": matched,
            "surface_coverage_fraction": matched / count if count else None,
            "seed_count": len(seeds), "seeds_seen_in_train": sum(raw_rows[key] > 0 for key in index),
            "seeds_not_seen_in_train": [seed["term"] for key, seed in index.items() if not raw_rows[key]],
            "raw_occurrences": sum(raw_occ.values()), "longest_occurrences": sum(chosen_occ.values()),
            "interpretation": "Surface coverage only, not precision, recall, sense verification or emotion prediction.",
            "normalization": "NFC, casefold, collapse whitespace; Unicode word boundaries; no accent removal",
            "selection": "leftmost-longest, non-overlapping; raw counts also retained",
            "limitations": ["No word sense disambiguation, negation, sarcasm or intensity handling.",
                            "Multi-label lexical entries do not imply all labels for every occurrence.",
                            "No match does not imply neutral.",
                            "Samples are first 3 selected rows per seed, not an unbiased evaluation set."]}, per_seed, samples


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(seed_path, train_path, output):
    output = output.resolve()
    private = (ROOT / "data/local").resolve()
    if output == private or not output.is_relative_to(private):
        raise ValueError("Output must be a new directory under data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing audit")
    if train_path.name != "train.csv":
        raise ValueError("This seed development audit accepts train.csv only")
    seeds = [json.loads(line) for line in seed_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    with train_path.open(encoding="utf-8-sig", newline="") as handle:
        summary, per_seed, samples = audit(seeds, csv.DictReader(handle))
    summary["inputs"] = {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                         for name, path in [("seeds", seed_path), ("train", train_path)]}
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "coverage-by-seed.csv", per_seed, list(per_seed[0]))
    write_csv(output / "match-review-samples.csv", samples,
              ["seed_id", "term", "dataset_id", "split", "text", "sense_match_decision", "notes", "sample_method"])
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=ROOT / "data/local/reviewed-seeds-v2/accepted-seeds.jsonl")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/seed-coverage-v2")
    args = parser.parse_args()
    print(json.dumps(run(args.seeds, args.train, args.output), ensure_ascii=True))


if __name__ == "__main__":
    main()
