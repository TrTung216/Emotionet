"""Prepare private, traceable seed review candidates from local NRC/VnEmoLex.

Uses only the Python standard library. Reads the supplied ZIP/XLSX without
extracting archives, evaluating spreadsheet formulas, or modifying the sources.
All imported records remain candidates. Outputs must stay under data/local.
"""

import argparse
import csv
import hashlib
import io
import json
import posixpath
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EMOTIONS = ("anger", "anticipation", "disgust", "fear", "joy", "sadness", "surprise", "trust")
CATEGORIES = (*EMOTIONS, "positive", "negative")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalize(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary(value):
    # Missing data is unknown, never silently converted to a negative label.
    value = str(value).strip()
    if value == "":
        return None
    if value not in {"0", "1"}:
        raise ValueError(f"Unexpected association flag: {value!r}")
    return int(value)


def record(source, locator, surface, english, values):
    if not surface or not surface.strip():
        raise ValueError(f"Empty Vietnamese term: {source}:{locator}")
    flags = {name: binary(values[name]) for name in CATEGORIES}
    return {
        "source_id": source, "source_locator": locator,
        "surface": surface, "normalized_form": normalize(surface),
        "source_english": english, "associations": flags,
        "missing_categories": [name for name, value in flags.items() if value is None],
        "status": "candidate", "reviewer": None,
        "score_semantics": "binary_association_not_intensity_or_probability",
    }


def read_nrc(path):
    with zipfile.ZipFile(path) as archive:
        matches = [name for name in archive.namelist() if name.endswith("/Vietnamese-NRC-EmoLex.txt") and "__MACOSX" not in name]
        if len(matches) != 1:
            raise ValueError("Expected exactly one Vietnamese NRC member")
        member = matches[0]
        reader = csv.DictReader(io.StringIO(archive.read(member).decode("utf-8-sig")), delimiter="\t")
        if not {*CATEGORIES, "English Word", "Vietnamese Word"}.issubset(reader.fieldnames or []):
            raise ValueError("Unexpected NRC header")
        rows = []
        for number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed NRC row {number}")
            rows.append(record("src_nrc_emolex_vi_2022", f"{member}:line={number}",
                               row["Vietnamese Word"], row["English Word"], row))
        return rows


def xlsx_rows(path):
    """Read the single-sheet layout of the supplied workbook, keeping cell columns."""
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = workbook.findall("s:sheets/s:sheet", NS)
        if len(sheets) != 1:
            raise ValueError("Expected one VnEmoLex sheet; review the layout before importing")
        sheet = sheets[0]
        relation_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = [item.get("Target") for item in relationships if item.get("Id") == relation_id and item.get("TargetMode") != "External"]
        if len(targets) != 1 or not targets[0]:
            raise ValueError("Invalid worksheet relationship")
        target = targets[0]
        member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        if not member.startswith("xl/") or ".." in member.split("/"):
            raise ValueError("Invalid worksheet member")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(node.text or "" for node in item.findall(".//s:t", NS))
                       for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        root = ET.fromstring(archive.read(member))
        result = []
        for row in root.findall("s:sheetData/s:row", NS):
            values = {}
            for cell in row.findall("s:c", NS):
                column = re.sub(r"\d", "", cell.attrib["r"])
                if column not in set("ABCDEFGHIJKL"):
                    continue  # Ignore the workbook's unlabelled summary/formula column M.
                if cell.find("s:f", NS) is not None:
                    raise ValueError("Formula in term/association columns; review before importing")
                value = cell.findtext("s:v", default="", namespaces=NS)
                kind = cell.get("t")
                if kind == "s":
                    value = strings[int(value)]
                elif kind == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//s:t", NS))
                elif kind == "e":
                    raise ValueError("Spreadsheet error in source data")
                values[column] = value
            if any(values.values()):
                result.append((int(row.attrib["r"]), values))
        return sheet.attrib["name"], result


def read_vn(path):
    sheet, rows = xlsx_rows(path)
    expected = {"B": "vietnamese", "C": "positive", "D": "negative", "E": "anger",
                "F": "anticipation", "G": "disgust", "H": "fear", "I": "joy",
                "J": "sadness", "K": "surprise", "L": "trust"}
    header = rows[0][1]
    for column, name in expected.items():
        actual = normalize(header.get(column, "")).split("/")[0].strip()
        if actual != name:
            raise ValueError(f"Unexpected VnEmoLex header {column}: {actual!r}")
    result = []
    for number, values in rows[1:]:
        flags = {name: values.get(column, "") for column, name in expected.items() if column != "B"}
        result.append(record("src_vnemolex_local", f"{sheet}!row={number}", values.get("B", ""), values.get("A", ""), flags))
    return result


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["normalized_form"]].append(row)
    differing = sum(len({tuple(row["associations"][label] for label in CATEGORIES) for row in group}) > 1 for group in groups.values())
    return {
        "rows": len(rows), "unique_normalized_forms": len(groups),
        "duplicate_form_rows_beyond_first": len(rows) - len(groups),
        "forms_with_differing_association_vectors": differing,
        "rows_with_missing_flags": sum(bool(row["missing_categories"]) for row in rows),
        "missing_flag_cells": sum(len(row["missing_categories"]) for row in rows),
        "rows_with_any_emotion": sum(any(row["associations"][label] == 1 for label in EMOTIONS) for row in rows),
        "association_counts": {label: sum(row["associations"][label] == 1 for row in rows) for label in CATEGORIES},
    }


def prepare(nrc_path, vn_path, targets_path, output):
    output = output.resolve()
    private_root = (ROOT / "data/local").resolve()
    if not output.is_relative_to(private_root) or output == private_root:
        raise ValueError("Use a new output directory inside Emotionet/data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing imports or human review work")
    sources = {"nrc": read_nrc(nrc_path), "vnemolex": read_vn(vn_path)}
    config = json.loads(targets_path.read_text(encoding="utf-8"))
    taxonomy = json.loads((ROOT / "configs/vigoemotions-labels.json").read_text(encoding="utf-8"))["label2id"]
    targets = defaultdict(set)
    display = {}
    for label, words in config["targets_by_emotion"].items():
        if label not in taxonomy or label == "neutral":
            raise ValueError(f"Invalid proposed emotion label {label}")
        for word in words:
            key = normalize(word)
            targets[key].add(label)
            display[key] = word
    index = defaultdict(list)
    for rows in sources.values():
        for row in rows:
            index[row["normalized_form"]].append(row)
    review = []
    evidence = []
    for key, labels in targets.items():
        matching = index.get(key, [])
        source_ids = sorted({row["source_id"] for row in matching})
        vectors = {tuple(row["associations"][label] for label in CATEGORIES) for row in matching}
        observations = {source: sorted({emotion for row in matching if row["source_id"] == source
                                        for emotion in EMOTIONS if row["associations"][emotion] == 1}) for source in source_ids}
        review_id = "seed_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        review.append({
            "review_id": review_id, "term": display[key], "normalized_form": key,
            "proposed_vigoemotions": ";".join(sorted(labels)),
            "proposal_method": "ai_assisted_draft_not_source_label_mapping",
            "source_count": len(source_ids), "source_row_count": len(matching),
            "source_emotions_summary": json.dumps(observations, ensure_ascii=False, sort_keys=True),
            "association_vectors_differ": len(vectors) > 1,
            "source_has_missing_flags": any(row["missing_categories"] for row in matching),
            "status": "candidate", "decision": "", "reviewed_emotions": "", "sense_gloss": "",
            "reviewer": "", "reviewed_at": "", "notes": "" if matching else "Chưa tìm thấy chuỗi khớp trong hai nguồn; cần bổ sung bằng chứng",
        })
        evidence.append({"review_id": review_id, "observations": matching})
    all_nrc = {row["normalized_form"] for row in sources["nrc"]}
    all_vn = {row["normalized_form"] for row in sources["vnemolex"]}
    summary = {
        "schema_version": 1, "status": "candidate_only",
        "source_files": {name: {"filename": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
                         for name, path in [("nrc", nrc_path), ("vnemolex", vn_path)]},
        "sources": {name: summarize(rows) for name, rows in sources.items()},
        "shared_normalized_forms": len(all_nrc & all_vn),
        "review": {"targets": len(review), "found_in_any_source": sum(row["source_count"] > 0 for row in review),
                   "found_in_both_sources": sum(row["source_count"] == 2 for row in review),
                   "not_found": sum(row["source_count"] == 0 for row in review),
                   "proposed_labels": len(config["targets_by_emotion"]), "approved": 0},
        "target_config_sha256": sha256(targets_path),
        "interpretation": [
            "NRC and VnEmoLex are not independent evidence sources; no confidence boost for agreement.",
            "Same spelling is grouped for inspection only, never merged into a sense or synset.",
            "Source 0/1 flags mean association, not intensity; missing flags remain null.",
            "Proposed ViGoEmotions labels are AI-assisted review suggestions, not imported annotations.",
            "No automatic mapping from anticipation/trust to fine-grained ViGoEmotions labels.",
            "All outputs are local review artifacts, not licensed publication-ready lexicons.",
        ],
    }
    output.mkdir(parents=True)
    for name, rows in sources.items():
        (output / f"{name}-observations.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (output / "review-evidence.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in evidence), encoding="utf-8")
    with (output / "seed-review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review[0]))
        writer.writeheader()
        writer.writerows(review)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nrc-zip", type=Path, required=True)
    parser.add_argument("--vnemolex", type=Path, required=True)
    parser.add_argument("--targets", type=Path, default=ROOT / "configs/seed-review-targets.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/seed-review-v1")
    args = parser.parse_args()
    summary = prepare(args.nrc_zip, args.vnemolex, args.targets, args.output)
    print(json.dumps({"sources": summary["sources"], "review": summary["review"],
                      "shared_normalized_forms": summary["shared_normalized_forms"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
