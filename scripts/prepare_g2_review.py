"""Build a review packet without modifying snapshots or inventing approvals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from emotionet import Emotionet, normalize_text

SNAPSHOT = "data/local/seed-synsets-v2"
PROPOSALS = "configs/g2-is-a-pilot.json"
CANDIDATES = "data/local/embedding-expansion-v1/candidate-review.csv"
OLD_SENSES = "data/local/seed-synsets-v1/senses.jsonl"
DEFAULT_OUTPUT = "data/local/g2-review-v1"
REVIEW_FIELDS = ["decision", "reviewer", "reviewed_at", "resolution_notes"]


def digest(content):
    return hashlib.sha256(content).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_jsonl(content):
    return [json.loads(line) for line in content.decode("utf-8-sig").splitlines() if line.strip()]


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    # BOM lets Excel open Vietnamese directly without changing lexical text.
    return stream.getvalue().encode("utf-8-sig")


def pending(row, extra=()):
    return dict(row, **{key: "" for key in [*extra, *REVIEW_FIELDS]})


def construct(root=ROOT):
    root = Path(root)
    with Emotionet.open(mode="research") as net:
        counts = net.import_jsonl(root / SNAPSHOT)
    if (counts["concepts"], counts["senses"], counts["relations"]) != (66, 82, 29):
        raise ValueError("This pilot requires the reviewed v2 baseline (66/82/29)")
    names = [p.relative_to(root).as_posix() for p in sorted((root / SNAPSHOT).iterdir())]
    names += [PROPOSALS, CANDIDATES, OLD_SENSES, "configs/data-sharing.json", "configs/g0-handoff.json"]
    inputs = {name: (root / name).read_bytes() for name in names}
    load = lambda name: read_jsonl(inputs[f"{SNAPSHOT}/{name}.jsonl"])
    synsets, senses, evidence, relations = map(load, ["synsets", "senses", "evidence", "relations"])
    syn_index = {r["synset_id"]: r for r in synsets}
    sense_index = {r["sense_id"]: r for r in senses}
    ev_index = {r["evidence_id"]: r for r in evidence}
    config = json.loads(inputs[PROPOSALS])
    if config["status"] != "proposal_only":
        raise ValueError("Pilot configuration must remain proposal_only")
    candidate_rows = list(csv.DictReader(io.StringIO(inputs[CANDIDATES].decode("utf-8-sig"))))
    if len({r["candidate_id"] for r in candidate_rows}) != len(candidate_rows):
        raise ValueError("Duplicate source candidate IDs")
    old_to_new = {}
    for row in read_jsonl(inputs[OLD_SENSES]):
        if row["sense_id"] in sense_index:
            old_to_new.setdefault(row["synset_id"], set()).add(sense_index[row["sense_id"]]["synset_id"])
    lexical_targets = {}
    for sense in senses:
        lexical_targets.setdefault(normalize_text(sense["lemma"]), set()).add(sense["synset_id"])

    inventories, sense_reference = [], []
    for syn in synsets:
        members = [sense_index[sid] for sid in syn["member_sense_ids"]]
        ev_ids = sorted(set(syn["evidence_ids"]) | {eid for m in members for eid in m["evidence_ids"]})
        missing_reviewers = [eid for eid in ev_ids if not ev_index[eid].get("reviewer")]
        missing_dates = [eid for eid in ev_ids if not ev_index[eid].get("reviewed_at")]
        expanded = [m["sense_id"] for m in members if m["sense_id"].startswith("sense_cand_")]
        flags = []
        if len(members) > 1:
            flags.append("check_all_member_glosses_for_equivalence")
        if missing_reviewers or missing_dates:
            flags.append("incomplete_review_metadata")
        if expanded:
            flags.append("embedding_added_members_check_context")
        if not any(m.get("example_kind") == "train_corpus_citation" or m.get("context_evidence") for m in members):
            flags.append("consult_source_context_review")
        inventories.append(pending({
            "review_id": "g2_" + syn["synset_id"], "synset_id": syn["synset_id"],
            "lemmas": ";".join(syn["lemmas"]), "definition": syn["definition"],
            "emotion_labels": ";".join(syn["emotion_labels"]),
            "source_semantic_status": syn.get("semantic_status", ""),
            "source_membership_status": syn.get("membership_status", ""),
            "source_publication_status": syn.get("publication_status", ""),
            "member_sense_ids": ";".join(syn["member_sense_ids"]),
            "source_evidence_ids": ";".join(ev_ids),
            "missing_reviewer_evidence_ids": ";".join(missing_reviewers),
            "missing_date_evidence_ids": ";".join(missing_dates),
            "embedding_member_ids": ";".join(expanded), "review_focus": ";".join(flags),
            "state": "pending", "source_locator": f"references/{SNAPSHOT}/synsets.jsonl#{syn['synset_id']}",
        }, ["membership_decision", "proposed_definition", "proposed_member_sense_ids", "additional_evidence_locators"]))
        for member in members:
            sense_reference.append({
                "synset_id": syn["synset_id"], "sense_id": member["sense_id"], "lemma": member["lemma"],
                "gloss": member["gloss"], "emotion_labels": ";".join(member["emotion_labels"]),
                "examples_json": dump(member.get("examples", [])), "example_kind": member.get("example_kind", ""),
                "context_evidence_json": dump(member.get("context_evidence")),
                "source_evidence_json": dump([ev_index[eid] for eid in member["evidence_ids"]]),
                "source_locator": f"references/{SNAPSHOT}/senses.jsonl#{member['sense_id']}",
            })

    relation_reviews = []
    for rel in relations:
        source_relation = {"related_to": "related", "antonym_of": "antonym"}[rel["predicate"]]
        matches = [r for r in candidate_rows if r["relation"] == source_relation
                   and normalize_text(r["candidate_form"]) == normalize_text(rel["object_term"])
                   and old_to_new.get(r["target_synset_id"], {r["target_synset_id"]}) == {rel["subject_synset_id"]}]
        if len(matches) != 1:
            raise ValueError(f"Cannot uniquely trace relation {rel['rel_id']} to original review")
        source = matches[0]
        candidates = sorted(lexical_targets.get(normalize_text(rel["object_term"]), set()))
        subject = syn_index[rel["subject_synset_id"]]
        target_detail = [{"synset_id": sid, "definition": syn_index[sid]["definition"],
                          "lemmas": syn_index[sid]["lemmas"]} for sid in candidates]
        relation_reviews.append(pending({
            "review_id": "g2_" + rel["rel_id"], "rel_id": rel["rel_id"],
            "subject_synset_id": rel["subject_synset_id"], "subject_lemmas": ";".join(subject["lemmas"]),
            "subject_definition": subject["definition"], "source_predicate": rel["predicate"],
            "object_term": rel["object_term"], "candidate_object_synset_ids": ";".join(candidates),
            "candidate_object_details_json": dump(target_detail),
            "target_status": "no_existing_synset" if not candidates else "lexical_candidates_require_sense_review",
            "source_candidate_id": source["candidate_id"], "source_decision": source["decision"],
            "source_relation": source["relation"], "source_reviewer": source["reviewer"],
            "source_reviewed_at": source["reviewed_at"], "source_notes": source["notes"],
            "source_example_id": source["example_id"], "source_example_text": source["example_text"],
            "source_example_status": "copied_from_train_expansion_review_not_revalidated_here",
            "source_review_locator": f"references/{CANDIDATES}#{source['candidate_id']}",
            "source_relation_locator": f"references/{SNAPSHOT}/relations.jsonl#{rel['rel_id']}",
            "review_focus": "resolve_sense_and_record_relation_evidence" + (";reject_synonym_does_not_approve_antonym" if rel["predicate"] == "antonym_of" else ""),
            "state": "pending",
        }, ["resolved_object_synset_id", "proposed_object_definition", "final_predicate", "relation_evidence_locators"]))

    pilot = []
    seen = set()
    for pair in config["pairs"]:
        child, parent = pair["child"], pair["parent"]
        if child == parent or (child, parent) in seen:
            raise ValueError("Self/duplicate is_a proposal")
        seen.add((child, parent))
        sub, sup = syn_index[child], syn_index[parent]
        pilot.append(pending({
            "review_id": "g2_isa_" + digest(f"{child}:{parent}".encode())[:12],
            "subject_synset_id": child, "subject_lemmas": ";".join(sub["lemmas"]),
            "subject_definition": sub["definition"], "object_synset_id": parent,
            "object_lemmas": ";".join(sup["lemmas"]), "object_definition": sup["definition"],
            "proposed_predicate": "is_a", "case_type": pair["case_type"],
            "review_question": pair["question"], "alternatives": pair["alternatives"],
            "source_evidence_ids": ";".join(sorted(set(sub["evidence_ids"] + sup["evidence_ids"]))),
            "subject_locator": f"references/{SNAPSHOT}/synsets.jsonl#{child}",
            "object_locator": f"references/{SNAPSHOT}/synsets.jsonl#{parent}",
            "proposal_method": config["method"], "state": "pending",
        }, ["forward_entailment", "reverse_entailment", "differentia", "counterexample", "final_predicate", "relation_evidence_locators"]))
    outputs = {name: csv_bytes(rows) for name, rows in {
        "synset-review.csv": inventories, "sense-reference.csv": sense_reference,
        "relation-review.csv": relation_reviews, "is-a-pilot-review.csv": pilot,
    }.items()}
    outputs.update({"references/" + name: content for name, content in inputs.items()})
    summary = {"synsets": len(inventories), "senses": len(sense_reference), "relations": len(relation_reviews),
               "antonym_proposals": sum(r["source_predicate"] == "antonym_of" for r in relation_reviews),
               "relations_without_existing_target": sum(r["target_status"] == "no_existing_synset" for r in relation_reviews),
               "is_a_proposals": len(pilot), "new_approved_records": 0}
    manifest = {"schema": "emotionet_g2_review_packet_v1", "prepared_on": config["prepared_on"],
                "status": "awaiting_human_review", "summary": summary,
                "source_sha256": {name: digest(content) for name, content in inputs.items()},
                "initial_output_sha256": {name: digest(content) for name, content in outputs.items()},
                "note": "Initial hashes describe the blank packet. Submitted reviews must be saved as a new version; never rewrite historical hashes."}
    outputs["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return outputs, summary


def build(root=ROOT, output=DEFAULT_OUTPUT):
    root = Path(root).resolve()
    target = (root / output).resolve()
    if not target.is_relative_to(root / "data/local"):
        raise ValueError("Review output must remain inside data/local")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite review packet: {target}")
    outputs, summary = construct(root)
    target.mkdir(parents=True, exist_ok=False)
    for name, content in outputs.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(output=args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
