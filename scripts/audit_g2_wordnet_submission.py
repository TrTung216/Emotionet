"""Archive the submitted WordNet profile/relation review and audit implementation gaps.

This records submitted decisions; it never promotes them or modifies snapshots.
"""

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/local/g2-wordnet-review-v1"


def sha(content):
    return hashlib.sha256(content).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def csv_rows(content):
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def build():
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite receipt: {OUTPUT}")
    names = [
        "docs/g2/wordnet-profile-spec.md", "src/emotionet/core.py",
        "data/local/g2-review-v1/relation-review.csv",
        "data/local/g2-review-submitted-v1/relation-review.csv",
        "data/local/g2-review-reconciled-v1/relation-review.csv",
        "data/local/g2-review-reconciled-v1/manifest.json",
        "data/local/g2-review-reconciled-v1/received-decisions.jsonl",
    ] + ["data/local/seed-synsets-v2/" + name for name in
         ["manifest.json", "entries.jsonl", "senses.jsonl", "synsets.jsonl", "relations.jsonl", "evidence.jsonl"]]
    inputs = {name: (ROOT / name).read_bytes() for name in names}
    path = "data/local/g2-review-reconciled-v1/relation-review.csv"
    rows = csv_rows(inputs[path])
    original = {r["review_id"]: r for r in csv_rows(inputs["data/local/g2-review-v1/relation-review.csv"])}
    if len(rows) != len(original) or set(original) != {r["review_id"] for r in rows}:
        raise ValueError("Submitted IDs do not match the original 29 proposals")
    if inputs[path] != inputs["data/local/g2-review-submitted-v1/relation-review.csv"]:
        raise ValueError("The two submitted relation files differ")
    editable = {"resolved_object_synset_id", "proposed_object_definition", "final_predicate",
                "relation_evidence_locators", "decision", "reviewer", "reviewed_at", "resolution_notes"}
    changes = [{"review_id": r["review_id"], "field": key} for r in rows for key in original[r["review_id"]]
               if key not in editable and r.get(key) != original[r["review_id"]][key]]
    load = lambda name: [json.loads(line) for line in inputs["data/local/seed-synsets-v2/" + name + ".jsonl"].decode("utf-8").splitlines()]
    synsets, senses, entries = load("synsets"), load("senses"), load("entries")
    syn_index = {r["synset_id"]: r for r in synsets}
    receipt_manifest = json.loads(inputs["data/local/g2-review-reconciled-v1/manifest.json"])
    stale = [name for name, expected in receipt_manifest["output_sha256"].items()
             if not (ROOT / "data/local/g2-review-reconciled-v1" / name).is_file()
             or sha((ROOT / "data/local/g2-review-reconciled-v1" / name).read_bytes()) != expected]
    missing_ids = sorted({r["resolved_object_synset_id"] for r in rows
                          if r["resolved_object_synset_id"] and r["resolved_object_synset_id"] not in syn_index})
    groups = defaultdict(list)
    for row in rows:
        groups[(row["object_term"], row["proposed_object_definition"])].append(row)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["object_term", "proposed_definition", "source_review_ids",
                                               "declared_target_ids", "requires_sense_and_pos_review"], lineterminator="\n")
    writer.writeheader()
    for (term, definition), group in sorted(groups.items()):
        writer.writerow({"object_term": term, "proposed_definition": definition,
                         "source_review_ids": ";".join(r["review_id"] for r in group),
                         "declared_target_ids": ";".join(sorted({r["resolved_object_synset_id"] for r in group if r["resolved_object_synset_id"]})),
                         "requires_sense_and_pos_review": "true"})
    summary = {
        "relation_rows": len(rows), "decisions": dict(Counter(r["decision"] for r in rows)),
        "final_predicates": dict(Counter(r["final_predicate"] for r in rows)),
        "missing_target_id_rows": sum(not r["resolved_object_synset_id"] for r in rows),
        "declared_but_missing_target_ids": missing_ids,
        "distinct_target_forms": len({r["object_term"] for r in rows}),
        "target_form_definition_groups": len(groups),
        "distinct_forms_without_declared_id": len({r["object_term"] for r in rows if not r["resolved_object_synset_id"]}),
        "missing_relation_evidence_locator_rows": sum(not r["relation_evidence_locators"] for r in rows),
        "readonly_field_changes": changes,
        "snapshot_synsets": len(synsets), "snapshot_senses": len(senses),
        "snapshot_entries_with_missing_pos": sum(not r.get("pos") for r in entries),
        "previous_receipt_stale_output_hashes": stale,
        "decision_receipt_only": True, "graph_edges_created": 0,
    }
    events = [{"review_id": r["review_id"], "decision": r["decision"],
               "final_predicate": r["final_predicate"], "reviewer_as_submitted": r["reviewer"],
               "reviewed_at_as_submitted": r["reviewed_at"],
               "resolution_notes": r["resolution_notes"],
               "source_locator": "inputs/" + path + "#" + r["review_id"],
               "status": "received_not_applied_to_graph"} for r in rows]
    outputs = {"inputs/" + name: content for name, content in inputs.items()}
    outputs["target-definition-groups.csv"] = stream.getvalue().encode("utf-8-sig")
    outputs["audit.json"] = json_bytes(summary)
    outputs["received-relation-decisions.jsonl"] = ("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)).encode("utf-8")
    outputs["manifest.json"] = json_bytes({"schema": "emotionet_wordnet_review_receipt_v1", "received_on": "2026-11-24",
        "status": "review_received_profile_and_migration_incomplete", "summary": summary,
        "source_sha256": {name: sha(content) for name, content in inputs.items()},
        "output_sha256": {name: sha(content) for name, content in outputs.items()},
        "note": "Previous manifest mismatches are recorded, not rewritten. Target groups are drafting aids, not newly approved concepts."})
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, content in outputs.items():
        target = OUTPUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
