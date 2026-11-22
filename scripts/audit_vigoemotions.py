"""Read local ViGoEmotions files and emit aggregate diagnostics, never row text.

No model imports, training, prediction, source edits, or lexicon extraction.
Test is read only for structural and duplicate checks, not semantic examples.
"""

import argparse
import csv
import hashlib
import itertools
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def match_key(text):
    return " ".join(unicodedata.normalize("NFC", text).lower().split())


def read_taxonomy(readme):
    labels = {}
    for line in readme.read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"\s*\|\s*(\d+)\s*\|\s*([a-z]+)\s*\|\s*", line)
        if match:
            identifier, label = int(match[1]), match[2]
            if identifier in labels:
                raise ValueError("Duplicate ID in README label mapping")
            labels[identifier] = label
    if set(labels) != set(range(28)) or len(set(labels.values())) != 28 or labels[27] != "neutral":
        raise ValueError("Expected 28 distinct labels and neutral at ID 27")
    return labels


def audit_split(path, label_names):
    ids, text_keys, label_sets = Counter(), Counter(), defaultdict(set)
    support, cardinalities, issues = Counter(), Counter(), Counter()
    rows = 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if not {"id", "text", "labels"}.issubset(columns):
            raise ValueError(f"{path.name}: expected id, text, labels columns")
        for row in reader:
            rows += 1
            identifier, text, raw = row["id"], row["text"], row["labels"]
            if identifier is None or not identifier.strip():
                issues["empty_id_rows"] += 1
            else:
                ids[identifier] += 1
            key = match_key(text or "")
            if not key:
                issues["empty_text_rows"] += 1
            else:
                text_keys[key] += 1
            try:
                labels = json.loads(raw)
            except (TypeError, ValueError):
                issues["invalid_labels_json_rows"] += 1
                continue
            if not isinstance(labels, list) or not labels or any(type(x) is not int or x not in label_names for x in labels):
                issues["invalid_label_values_rows"] += 1
                continue
            unique = frozenset(labels)
            if len(labels) != len(unique):
                issues["repeated_label_ids_rows"] += 1
            if 27 in unique and len(unique) > 1:
                issues["neutral_with_emotion_rows"] += 1
            support.update(unique)
            cardinalities[len(unique)] += 1
            if key:
                label_sets[key].add(tuple(sorted(unique)))
    report = {
        "rows": rows,
        "columns": columns,
        "sha256": sha256(path),
        "duplicate_id_rows_beyond_first": sum(n - 1 for n in ids.values()),
        "normalized_duplicate_text_rows_beyond_first": sum(n - 1 for n in text_keys.values()),
        "normalized_text_groups_with_different_label_sets": sum(len(values) > 1 for values in label_sets.values()),
        "unique_label_cardinality_counts": dict(sorted(cardinalities.items())),
        "multi_label_rows": sum(n for cardinality, n in cardinalities.items() if cardinality > 1),
        "label_support": {name: support[index] for index, name in label_names.items()},
        "issues": dict(sorted(issues.items())),
    }
    return report, set(text_keys), set(ids)


def audit(data_dir):
    label_names = read_taxonomy(data_dir / "README.md")
    manifest = json.loads((data_dir / "source_manifest.json").read_text(encoding="utf-8"))
    checks = {}
    for name in ("README.md", "train.csv", "val.csv", "test.csv"):
        path = data_dir / name
        expected = manifest["files"][name]
        checks[name] = {
            "sha256_matches_manifest": sha256(path) == expected["sha256"],
            "size_matches_manifest": path.stat().st_size == expected["bytes"],
        }
    reports, texts, ids = {}, {}, {}
    for split in ("train", "val", "test"):
        reports[split], texts[split], ids[split] = audit_split(data_dir / f"{split}.csv", label_names)
    overlaps = {}
    for first, second in itertools.combinations(reports, 2):
        overlaps[f"{first}__{second}"] = {
            "normalized_exact_text_groups": len(texts[first] & texts[second]),
            "shared_id_values": len(ids[first] & ids[second]),
        }
    return {
        "audit_schema_version": 1,
        "source_repository": manifest["repository"],
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256(data_dir / "source_manifest.json"),
        "readme_sha256": sha256(data_dir / "README.md"),
        "source_integrity": checks,
        "label2id": {name: index for index, name in label_names.items()},
        "splits": reports,
        "cross_split_overlap": overlaps,
        "limits": [
            "Only aggregate structural checks; no semantic label review or near-duplicate detection.",
            "Support counts use each distinct label once per row; raw duplicate IDs are reported, not edited.",
            "Different label sets on equal text are review candidates, not automatically annotation errors.",
            "No original comments, row IDs, predictions or per-row hashes are exported.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.data_dir)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        destination = args.output.resolve()
        if destination.is_relative_to(args.data_dir.resolve()):
            raise ValueError("Write audit outputs outside the source dataset directory")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
    else:
        print(output)
    integrity_ok = all(all(check.values()) for check in report["source_integrity"].values())
    if args.output:
        print(json.dumps({"source_integrity_ok": integrity_ok,
                          "rows": {name: split["rows"] for name, split in report["splits"].items()},
                          "issues": {name: split["issues"] for name, split in report["splits"].items()},
                          "cross_split_overlap": report["cross_split_overlap"]}, ensure_ascii=True))
    return 0 if integrity_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
