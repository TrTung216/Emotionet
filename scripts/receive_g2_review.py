"""Receive G2 decisions and a confirmed correction without modifying the submission."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/local/g2-review-v1"
SUBMITTED = ROOT / "data/local/g2-review-submitted-v1"
CONFIRMATION = ROOT / "configs/g2-review-confirmation-v1.json"
EDITABLE = {
    "synset-review.csv": {"membership_decision", "proposed_definition", "proposed_member_sense_ids", "additional_evidence_locators"},
    "is-a-pilot-review.csv": {"forward_entailment", "reverse_entailment", "differentia", "counterexample", "final_predicate", "relation_evidence_locators"},
    "relation-review.csv": {"resolved_object_synset_id", "proposed_object_definition", "final_predicate", "relation_evidence_locators"},
}
COMMON = {"decision", "reviewer", "reviewed_at", "resolution_notes"}


def digest(content):
    return hashlib.sha256(content).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def csv_rows(content):
    with io.StringIO(content.decode("utf-8-sig"), newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        result = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in result):
        raise ValueError("Malformed CSV row")
    if len({r["review_id"] for r in result}) != len(result):
        raise ValueError("Duplicate review IDs")
    return fields, result


def receive(summary_path, output):
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / "data/local").resolve()):
        raise ValueError("Receipt must stay within data/local")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite receipt: {output}")
    initial = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in initial["initial_output_sha256"].items():
        if digest((BASE / name).read_bytes()) != expected:
            raise ValueError(f"Original packet changed: {name}")
    source = {}
    for path in sorted(SUBMITTED.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlink not allowed: {path}")
        if path.is_file():
            source[path.relative_to(SUBMITTED).as_posix()] = path.read_bytes()
    rows_by_file = {}
    for name, expected in initial["initial_output_sha256"].items():
        if name not in source:
            raise ValueError(f"Missing submitted file: {name}")
        if name not in EDITABLE:
            if digest(source[name]) != expected:
                raise ValueError(f"Reference file changed: {name}")
            continue
        old_fields, old_rows = csv_rows((BASE / name).read_bytes())
        fields, rows = csv_rows(source[name])
        old = {r["review_id"]: r for r in old_rows}
        if fields != old_fields or set(old) != {r["review_id"] for r in rows}:
            raise ValueError(f"Columns/IDs changed: {name}")
        for row in rows:
            for field in set(fields) - EDITABLE[name] - COMMON:
                if row[field] != old[row["review_id"]][field]:
                    raise ValueError(f"Source field changed: {name}/{row['review_id']}/{field}")
        rows_by_file[name] = (fields, rows)

    confirmation = json.loads(CONFIRMATION.read_bytes())
    fields, pilot = rows_by_file["is-a-pilot-review.csv"]
    row = next(r for r in pilot if r["review_id"] == confirmation["review_id"])
    for key in ("subject_synset_id", "object_synset_id"):
        if row[key] != confirmation[key]:
            raise ValueError("Confirmation endpoints differ from submitted row")
    if any(row[key] for key in COMMON | EDITABLE["is-a-pilot-review.csv"]):
        raise ValueError("Correction expects the unfilled row; do not replace a later review")
    for key in ("decision", "final_predicate", "reviewer", "resolution_notes"):
        row[key] = confirmation[key]
    # The user confirmed a decision, not an exact review time or entailment tests.
    row["relation_evidence_locators"] = "user-confirmation.json#" + row["review_id"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(pilot)
    outputs = {name: content for name, content in source.items() if name != "manifest.json"}
    outputs["is-a-pilot-review.csv"] = stream.getvalue().encode("utf-8-sig")
    outputs.update({"source-submission/" + name: content for name, content in source.items()})
    outputs["user-confirmation.json"] = CONFIRMATION.read_bytes()
    outputs["submission-summary.txt"] = Path(summary_path).read_bytes()

    decisions = []
    for name, (_, rows) in rows_by_file.items():
        for record in rows:
            if not record["decision"]:
                continue
            corrected = name == "is-a-pilot-review.csv" and record["review_id"] == confirmation["review_id"]
            decisions.append({
                "review_id": record["review_id"], "review_file": name,
                "decision": record["decision"], "membership_decision": record.get("membership_decision"),
                "final_predicate": record.get("final_predicate"), "reviewer_as_submitted": record["reviewer"],
                "reviewed_at_as_submitted": record["reviewed_at"] or None,
                "confirmed_on": confirmation["confirmed_on"] if corrected else None,
                "provenance_locator": ("user-confirmation.json" if corrected else "source-submission/" + name) + "#" + record["review_id"],
                "receipt_status": "recorded_not_applied_to_snapshot", "resolution_notes": record["resolution_notes"],
            })
    outputs["received-decisions.jsonl"] = ("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in decisions)).encode("utf-8")
    synsets = rows_by_file["synset-review.csv"][1]
    relations = rows_by_file["relation-review.csv"][1]
    summary = {"synset_definition_decisions": dict(Counter(r["decision"] for r in synsets)),
               "synset_membership_decisions": dict(Counter(r["membership_decision"] for r in synsets)),
               "is_a_pilot_decisions": dict(Counter(r["decision"] for r in pilot)),
               "legacy_relation_review_remaining": sum(not r["decision"] for r in relations),
               "recorded_decisions": len(decisions), "new_approved_graph_edges": 0}
    manifest = {"schema": "emotionet_g2_review_receipt_v1", "received_on": "2026-11-24",
                "status": "review_received_wordnet_preparation_pending", "summary": summary,
                "original_submission": SUBMITTED.relative_to(ROOT).as_posix(),
                "source_sha256": {name: digest(content) for name, content in source.items()},
                "output_sha256": {name: digest(content) for name, content in outputs.items()},
                "notes": ["Original submission and its initial-template manifest retained verbatim under source-submission/.",
                          "Only the owner-confirmed blank pilot row was reconciled; exact time and entailment fields were not invented.",
                          "Review receipt does not create synsets or graph edges, or replace POS/schema review."]}
    outputs["manifest.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in outputs.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(content)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/g2-review-reconciled-v1")
    args = parser.parse_args()
    print(json.dumps(receive(args.summary, args.output), ensure_ascii=False, indent=2))
