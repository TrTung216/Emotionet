"""Check G0 draft structure; does not certify meaning, licensing, or reviews."""

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "concepts": ("concept_id", "con", {"preferred_label", "definition", "domain"}),
    "entries": ("entry_id", "lex", {"lemma", "lang", "pos", "normalized_form"}),
    "forms": ("form_id", "frm", {"entry_id", "surface", "normalized_form", "form_type"}),
    "senses": ("sense_id", "sen", {"entry_id", "concept_id", "gloss", "examples"}),
    "relations": ("rel_id", "rel", {"subject_id", "predicate", "object_id"}),
    "evidence": ("evidence_id", "evd", {"source_id", "locator", "excerpt", "method"}),
    "emotions": ("annotation_id", "emo", {"target_type", "target_id", "emotion", "score", "context_scope", "context"}),
}
STATUSES = {"candidate", "needs_review", "approved", "rejected"}
PREDICATES = {"is_a", "part_of", "subfield_of", "related_to", "antonym_of", "same_as"}
SYMMETRIC = {"related_to", "antonym_of", "same_as"}


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", unicodedata.normalize("NFC", text).casefold()).split())


def read_jsonl(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path.name}:{number}: blank JSONL line")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}:{number}: expected object")
        rows.append(row)
    return rows


def validate(root=ROOT):
    directory = root / "data" / "seeds" / "g0"
    records = {name: read_jsonl(directory / f"{name}.jsonl") for name in TABLES}
    reviews = read_jsonl(directory / "reviews.jsonl")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    with (root / "data" / "licenses" / "sources.csv").open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    sources = {row["source_id"]: row for row in source_rows}
    check(len(sources) == len(source_rows), "Duplicate source_id")
    for source in source_rows:
        check(source["rights_status"] in {"pending", "cleared", "denied"}, "Invalid rights_status")
    indexes = {}
    common = {"status", "created_at", "updated_at", "reviewer", "reviewed_at"}
    for name, (id_field, prefix, fields) in TABLES.items():
        indexes[name] = {}
        for row in records[name]:
            required = common | fields | {id_field} | ({"evidence_ids"} if name != "evidence" else set())
            missing = required - row.keys()
            check(not missing, f"{name}: missing fields {sorted(missing)}")
            if missing:
                continue
            identifier = row[id_field]
            check(isinstance(identifier, str) and re.fullmatch(rf"{prefix}_[0-9]{{6}}", identifier), f"{name}: invalid ID {identifier}")
            check(identifier not in indexes[name], f"{name}: duplicate ID {identifier}")
            indexes[name][identifier] = row
            check(row["status"] in STATUSES, f"{identifier}: invalid status")
            for field in ("created_at", "updated_at"):
                try:
                    parsed = datetime.fromisoformat(row[field])
                    check(parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0,
                          f"{identifier}: {field} must be UTC")
                except (TypeError, ValueError):
                    check(False, f"{identifier}: invalid {field}")
            if row["status"] == "approved":
                check(bool(row["reviewer"]) and bool(row["reviewed_at"]), f"{identifier}: approved without reviewer/time")
            for field, value in row.items():
                if isinstance(value, str):
                    check(unicodedata.is_normalized("NFC", value), f"{identifier}: {field} is not NFC")
    # Stop before relational checks if malformed records make them unsafe.
    if errors:
        return errors, records

    def reference(row, field, table):
        check(row[field] in indexes[table], f"{row}: unknown {field}")

    for name, rows in records.items():
        for row in rows:
            identifier = row[TABLES[name][0]]
            if name == "evidence":
                source = sources.get(row["source_id"])
                check(source is not None, f"{identifier}: source does not exist")
                check(bool(row["locator"]) and bool(row["method"]), f"{identifier}: missing provenance")
                if row["status"] == "approved" and source:
                    check(source["rights_status"] == "cleared" and source["license"] not in {"", "undetermined"},
                          f"{identifier}: source rights not cleared")
                continue
            evidence_ids = row["evidence_ids"]
            check(isinstance(evidence_ids, list) and bool(evidence_ids), f"{identifier}: evidence_ids must be a nonempty list")
            if not isinstance(evidence_ids, list):
                continue
            for evidence_id in evidence_ids:
                evidence = indexes["evidence"].get(evidence_id)
                check(evidence is not None, f"{identifier}: unknown evidence {evidence_id}")
                if row["status"] == "approved" and evidence:
                    check(evidence["status"] == "approved", f"{identifier}: evidence not approved")

    entry_keys = set()
    for entry in records["entries"]:
        key = (entry["lang"], entry["normalized_form"], entry["pos"])
        check(key not in entry_keys, f"Duplicate entry identity: {key}")
        entry_keys.add(key)
        check(entry["lang"] == "vi", f"{entry['entry_id']}: expected Vietnamese")
        check(entry["pos"] in {"NOUN", "VERB", "ADJ", "ADV", "PROPN", "X"}, f"{entry['entry_id']}: invalid POS")
        check(entry["normalized_form"] == normalized(entry["lemma"]), f"{entry['entry_id']}: normalization mismatch")
        canonical = [form for form in records["forms"] if form["entry_id"] == entry["entry_id"] and form["form_type"] == "canonical"]
        check(len(canonical) == 1 and canonical[0]["surface"] == entry["lemma"], f"{entry['entry_id']}: invalid canonical form")
        check(any(sense["entry_id"] == entry["entry_id"] for sense in records["senses"]), f"{entry['entry_id']}: no senses")
    for form in records["forms"]:
        reference(form, "entry_id", "entries")
        check(form["form_type"] in {"canonical", "abbreviation", "spelling_variant"}, f"{form['form_id']}: invalid form_type")
        check(form["normalized_form"] == normalized(form["surface"]), f"{form['form_id']}: normalization mismatch")
    for sense in records["senses"]:
        reference(sense, "entry_id", "entries")
        reference(sense, "concept_id", "concepts")
        check(isinstance(sense["gloss"], str) and bool(sense["gloss"].strip()), f"{sense['sense_id']}: empty gloss")
        check(isinstance(sense["examples"], list) and all(isinstance(value, str) and value.strip() for value in sense["examples"]),
              f"{sense['sense_id']}: invalid examples")
    for concept in records["concepts"]:
        check(bool(concept["preferred_label"].strip()) and bool(concept["definition"].strip()), f"{concept['concept_id']}: empty label/definition")
        check(any(sense["concept_id"] == concept["concept_id"] for sense in records["senses"]), f"{concept['concept_id']}: no senses")

    relation_keys = set()
    graphs = {predicate: {} for predicate in ("is_a", "part_of", "subfield_of")}
    for relation in records["relations"]:
        reference(relation, "subject_id", "concepts")
        reference(relation, "object_id", "concepts")
        subject, predicate, target = (relation[field] for field in ("subject_id", "predicate", "object_id"))
        check(predicate in PREDICATES, f"{relation['rel_id']}: invalid predicate")
        check(subject != target, f"{relation['rel_id']}: self-reference")
        key = (subject, predicate, target)
        check(key not in relation_keys, f"Duplicate relation {key}")
        relation_keys.add(key)
        if predicate in SYMMETRIC:
            check(subject < target, f"{relation['rel_id']}: symmetric edge must use sorted IDs")
        if predicate in graphs and relation["status"] != "rejected":
            graphs[predicate].setdefault(subject, []).append(target)
    for predicate, graph in graphs.items():
        visited, active = set(), set()

        def visit(node):
            if node in active:
                check(False, f"Cycle in {predicate} at {node}")
                return
            if node in visited:
                return
            active.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            active.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    # G0 intentionally has no emotion labels or reviews yet. A later curation
    # implementation must validate those schemas before these guards are removed.
    check(not records["emotions"], "G0 validator expects no emotion annotations; implement their validator at G4")
    check(not reviews, "Review events require the curation validator planned for G1")
    check(all(row["status"] == "candidate" for rows in records.values() for row in rows),
          "This validator covers the initial candidate-only G0 snapshot")
    counts = {name: len(rows) for name, rows in records.items()} | {"reviews": len(reviews)}
    check(manifest["counts"] == counts, "Manifest counts do not match JSONL")
    check(manifest["schema_version"] == 1 and manifest["status"] == "draft", "Invalid draft manifest")
    check(len(records["concepts"]) == 30, "G0 snapshot must contain 30 concepts")
    approved = sum(row["status"] == "approved" for row in records["concepts"])
    check(manifest["approved_concepts"] == approved, "Incorrect approved count")
    for lemma in ("đường", "mạng", "đá"):
        entry_ids = {row["entry_id"] for row in records["entries"] if row["lemma"] == lemma}
        concepts = {row["concept_id"] for row in records["senses"] if row["entry_id"] in entry_ids}
        check(len(concepts) == 2, f"{lemma}: expected two distinct concepts")
    return errors, records


def main():
    try:
        errors, records = validate()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: G0 draft structure, references, normalization, polysemy and relation cycles")
    for name, rows in records.items():
        print(f"  {name}: {len(rows)} ({dict(Counter(row['status'] for row in rows))})")
    print("Semantic review and distribution rights remain pending; this is not publication approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
