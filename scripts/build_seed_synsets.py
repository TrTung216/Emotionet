"""Build versioned singleton seed synsets from selected, reviewed meanings.

Cross-lemma equivalence is proposed separately, never inferred from emotion labels.
This research schema is separate from the original generic G0 candidate fixtures.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def private_output(output):
    output, private = output.resolve(), (ROOT / "data/local").resolve()
    if output == private or not output.is_relative_to(private):
        raise ValueError("Use a new directory under data/local")
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing dataset")
    return output


def construct(seeds, splits):
    seed_index = {r["seed_id"]: r for r in seeds}
    if not seeds or len(seed_index) != len(seeds):
        raise ValueError("Empty seeds or duplicate seed ID")
    split_index, split_ids = {}, set()
    for row in splits:
        parent = seed_index[row["seed_id"]]
        if row["sense_id"] in split_ids or row["term"] != parent["term"]:
            raise ValueError("Invalid or duplicate split sense")
        if row["semantic_status"] != "accepted_as_submitted" or not row["emotion_labels"] or not set(row["emotion_labels"]) <= set(parent["emotion_labels"]):
            raise ValueError("Split sense lacks acceptance or has unsupported labels")
        split_ids.add(row["sense_id"])
        split_index.setdefault(row["seed_id"], []).append(row)
    entries, senses, synsets, evidence = [], [], [], []
    for seed in seeds:
        if seed["semantic_status"] != "accepted":
            raise ValueError("Seed is not accepted")
        entry_id = "entry_" + seed["seed_id"]
        rows = split_index.get(seed["seed_id"], [{
            "sense_id": seed["seed_id"] + "_sense", "seed_id": seed["seed_id"],
            "term": seed["term"], "sense_gloss": seed["sense_gloss"],
            "emotion_labels": seed["emotion_labels"], "reviewer": seed["reviewer"],
            "reviewed_at": seed["reviewed_at"], "review_notes": seed["review_notes"],
        }])
        entries.append({"entry_id": entry_id, "seed_id": seed["seed_id"], "lemma": seed["term"],
                        "normalized_form": seed["normalized_form"], "lang": "vi", "pos": None,
                        "sense_ids": [row["sense_id"] for row in rows]})
        for row in rows:
            sid = row["sense_id"]
            synid = "syn_" + hashlib.sha256(sid.encode("utf-8")).hexdigest()[:16]
            eid = "ev_review_" + sid
            evidence.append({"evidence_id": eid, "method": "submitted_semantic_review",
                             "source_kind": "split_sense_review" if seed["seed_id"] in split_index else "seed_review",
                             "source_record_id": sid if seed["seed_id"] in split_index else seed["seed_id"],
                             "reviewer": row["reviewer"], "reviewed_at": row["reviewed_at"],
                             "notes": row["review_notes"], "independent_review_verified": False})
            senses.append({"sense_id": sid, "entry_id": entry_id, "seed_id": seed["seed_id"],
                           "lemma": row["term"], "synset_id": synid, "gloss": row["sense_gloss"],
                           "emotion_labels": row["emotion_labels"],
                           "examples": [row["context_example"]] if row.get("context_example") else [],
                           "example_kind": "illustrative_not_corpus_citation",
                           "semantic_status": "accepted_as_submitted", "evidence_ids": [eid],
                           "intensity": None, "confidence": None, "publication_status": "not_cleared"})
            synsets.append({"synset_id": synid, "preferred_lemma": row["term"], "definition": row["sense_gloss"],
                            "member_sense_ids": [sid], "lemmas": [row["term"]],
                            "emotion_labels": row["emotion_labels"], "evidence_ids": [eid],
                            "construction": "singleton_from_reviewed_meaning", "membership_status": "singleton",
                            "semantic_status": "inherited_from_reviewed_member", "publication_status": "not_cleared"})
    return entries, senses, synsets, evidence


def build(selection_path, output):
    output = private_output(output)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    paths = {"seed_source": ROOT / selection["selected_seed_path"],
             "split_source": ROOT / selection["selected_split_senses_path"],
             "context_source": ROOT / selection["context_resolution_path"]}
    entries, senses, synsets, evidence = construct(read_jsonl(paths["seed_source"]), read_jsonl(paths["split_source"]))
    sense_index = {r["sense_id"]: r for r in senses}
    for context in read_jsonl(paths["context_source"]):
        if context["final_decision"] != "matches_sense" or not context["sense_id"]:
            continue
        sense = sense_index[context["sense_id"]]
        if sense["seed_id"] != context["seed_id"]:
            raise ValueError("Context resolution points to a different seed")
        eid = "ev_context_" + hashlib.sha256((context["sense_id"] + ":" + context["dataset_id"]).encode()).hexdigest()[:16]
        evidence.append({"evidence_id": eid, "method": "submitted_context_assignment", "source_kind": "context_resolution",
                         "source_record_id": context["dataset_id"], "sense_id": context["sense_id"],
                         "split": "train", "text": context["text"], "reviewer": context["reviewer"],
                         "reviewed_at": context["reviewed_at"], "context_flags": context["context_flags"],
                         "sentence_emotion_labels": context["sentence_emotion_labels"],
                         "sentence_labels_are_not_sense_annotations": True})
        sense["evidence_ids"].append(eid)
    for synset in synsets:
        synset["evidence_ids"] = list(sense_index[synset["member_sense_ids"][0]]["evidence_ids"])
    # Explicit hypotheses, not approved synonym groups.
    proposed_pairs = [("yêu", "love", "thương", "love"),
                      ("nhẹ nhõm", "relief", "nhẹ lòng", "relief"),
                      ("đồng tình", "approval", "tán thành", "approval"),
                      ("nhận ra", "realization", "vỡ lẽ", "realization"),
                      ("lo", "nervousness", "lo lắng", "nervousness")]
    proposals = []
    for a, label_a, b, label_b in proposed_pairs:
        left = next(r for r in senses if r["lemma"] == a and r["emotion_labels"] == [label_a])
        right = next(r for r in senses if r["lemma"] == b and r["emotion_labels"] == [label_b])
        proposals.append({"sense_a": left["sense_id"], "sense_b": right["sense_id"],
                          "lemma_a": a, "lemma_b": b, "gloss_a": left["gloss"], "gloss_b": right["gloss"],
                          "proposal_method": "assistant_gloss_comparison_not_reviewed_equivalence",
                          "status": "needs_review", "decision": "", "reviewer": "", "reviewed_at": "", "notes": ""})
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in [("entries", entries), ("senses", senses), ("synsets", synsets), ("evidence", evidence)]:
        write_jsonl(output / (name + ".jsonl"), rows)
    with (output / "merge-proposals.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(proposals[0])); writer.writeheader(); writer.writerows(proposals)
    for name, path in paths.items():
        (output / (name + ".jsonl")).write_bytes(path.read_bytes())
    (output / "selection-source.json").write_bytes(selection_path.read_bytes())
    manifest = {"schema": "emotionet_research_seed_synsets_v1", "data_version": "seed-synsets-v1",
                "entries": len(entries), "senses": len(senses), "synsets": len(synsets),
                "cross_lemma_merges_applied": 0, "merge_proposals": len(proposals),
                "emotion_label_count": len({label for s in senses for label in s["emotion_labels"]}),
                "publication_status": "not_cleared", "pos_policy": "unknown; no invented POS labels",
                "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in paths.items()},
                "output_sha256": {path.name: sha256(path) for path in output.iterdir()}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=ROOT / "configs/seed-selection.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/local/seed-synsets-v1")
    args = parser.parse_args()
    result = build(args.selection, args.output)
    print(json.dumps({k: result[k] for k in ["entries", "senses", "synsets", "merge_proposals", "emotion_label_count"]}))
