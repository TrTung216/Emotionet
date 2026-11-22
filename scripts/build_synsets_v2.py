# -*- coding: utf-8 -*-
"""Build seed-synsets-v2 incorporating reviewed merges and embedding candidates."""

import csv
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())

def main():
    v1_dir = ROOT / "data/local/seed-synsets-v1"
    v2_dir = ROOT / "data/local/seed-synsets-v2"
    exp_dir = ROOT / "data/local/embedding-expansion-v1"
    
    if v2_dir.exists():
        import shutil
        shutil.rmtree(v2_dir)
    v2_dir.mkdir(parents=True, exist_ok=True)
    
    entries = read_jsonl(v1_dir / "entries.jsonl")
    senses = read_jsonl(v1_dir / "senses.jsonl")
    synsets = read_jsonl(v1_dir / "synsets.jsonl")
    evidence = read_jsonl(v1_dir / "evidence.jsonl")
    
    entry_index = {e["entry_id"]: e for e in entries}
    sense_index = {s["sense_id"]: s for s in senses}
    synset_index = {s["synset_id"]: s for s in synsets}
    
    # 1. Apply 5 accepted merge proposals
    with open(v1_dir / "merge-proposals.csv", encoding="utf-8-sig") as f:
        merges = [r for r in csv.DictReader(f) if r["decision"] == "accept"]
    
    merges_applied = []
    for m in merges:
        sa_id = m["sense_a"]
        sb_id = m["sense_b"]
        sense_a = sense_index[sa_id]
        sense_b = sense_index[sb_id]
        
        syn_a = synset_index[sense_a["synset_id"]]
        syn_b = synset_index[sense_b["synset_id"]]
        
        # Merge syn_b into syn_a
        target_syn_id = syn_a["synset_id"]
        ev_id = f"ev_merge_{sa_id}_{sb_id}"[:32]
        
        evidence.append({
            "evidence_id": ev_id,
            "method": "reviewed_cross_lemma_merge",
            "source_kind": "merge_proposals_v1",
            "source_record_id": f"{sa_id}+{sb_id}",
            "reviewer": m["reviewer"],
            "reviewed_at": m["reviewed_at"],
            "notes": m["notes"]
        })
        
        sense_b["synset_id"] = target_syn_id
        if ev_id not in sense_a["evidence_ids"]:
            sense_a["evidence_ids"].append(ev_id)
        if ev_id not in sense_b["evidence_ids"]:
            sense_b["evidence_ids"].append(ev_id)
            
        if sb_id not in syn_a["member_sense_ids"]:
            syn_a["member_sense_ids"].append(sb_id)
        if m["lemma_b"] not in syn_a["lemmas"]:
            syn_a["lemmas"].append(m["lemma_b"])
        syn_a["membership_status"] = "synonym_group"
        syn_a["construction"] = "reviewed_cross_lemma_merge"
        if ev_id not in syn_a["evidence_ids"]:
            syn_a["evidence_ids"].append(ev_id)
            
        # Delete syn_b from index
        if syn_b["synset_id"] in synset_index and syn_b["synset_id"] != target_syn_id:
            del synset_index[syn_b["synset_id"]]
            
        merges_applied.append({
            "target_synset_id": target_syn_id,
            "merged_lemmas": [m["lemma_a"], m["lemma_b"]],
            "merged_senses": [sa_id, sb_id],
            "notes": m["notes"]
        })
    
    # Rebuild synsets list after merges
    synsets = list(synset_index.values())
    
    # 2. Apply reviewed candidate expansion
    with open(exp_dir / "candidate-review.csv", encoding="utf-8-sig") as f:
        cands = list(csv.DictReader(f))
        
    relations = []
    candidates_applied = []
    
    for c in cands:
        dec = c["decision"]
        rel = c["relation"]
        cand_form = c["candidate_form"]
        target_syn_id = c["target_synset_id"]
        
        if target_syn_id not in synset_index:
            # Synset might have been merged into another synset
            for s in synsets:
                if c["target_lemmas"] in s["lemmas"]:
                    target_syn_id = s["synset_id"]
                    break
        
        if dec == "accept" and rel == "synonym":
            target_syn = synset_index[target_syn_id]
            norm_cand = normalize(cand_form)
            cand_entry_id = "entry_cand_" + hashlib.sha256(norm_cand.encode()).hexdigest()[:12]
            cand_sense_id = "sense_cand_" + hashlib.sha256((norm_cand + ":" + target_syn_id).encode()).hexdigest()[:12]
            ev_id = "ev_cand_" + hashlib.sha256((cand_form + ":" + target_syn_id).encode()).hexdigest()[:12]
            
            evidence.append({
                "evidence_id": ev_id,
                "method": "embedding_expansion_reviewed_synonym",
                "source_kind": "candidate_review_v1",
                "source_record_id": c["candidate_id"],
                "reviewer": c["reviewer"],
                "reviewed_at": c["reviewed_at"],
                "notes": c["notes"]
            })
            
            # Check or create entry
            if cand_entry_id not in entry_index:
                cand_entry = {
                    "entry_id": cand_entry_id,
                    "seed_id": None,
                    "lemma": cand_form,
                    "normalized_form": norm_cand,
                    "lang": "vi",
                    "pos": None,
                    "sense_ids": [cand_sense_id]
                }
                entry_index[cand_entry_id] = cand_entry
                entries.append(cand_entry)
            else:
                if cand_sense_id not in entry_index[cand_entry_id]["sense_ids"]:
                    entry_index[cand_entry_id]["sense_ids"].append(cand_sense_id)
            
            # Create sense
            if cand_sense_id not in sense_index:
                cand_sense = {
                    "sense_id": cand_sense_id,
                    "entry_id": cand_entry_id,
                    "seed_id": None,
                    "lemma": cand_form,
                    "synset_id": target_syn_id,
                    "gloss": c["candidate_gloss"],
                    "emotion_labels": c["reviewed_emotions"].split(";"),
                    "examples": [c["example_text"]] if c["example_text"] else [],
                    "example_kind": "train_corpus_citation",
                    "semantic_status": "accepted_as_submitted",
                    "evidence_ids": [ev_id],
                    "intensity": None,
                    "confidence": None,
                    "publication_status": "not_cleared"
                }
                sense_index[cand_sense_id] = cand_sense
                senses.append(cand_sense)
                
            # Add to synset
            if cand_sense_id not in target_syn["member_sense_ids"]:
                target_syn["member_sense_ids"].append(cand_sense_id)
            if cand_form not in target_syn["lemmas"]:
                target_syn["lemmas"].append(cand_form)
            target_syn["membership_status"] = "synonym_group"
            if ev_id not in target_syn["evidence_ids"]:
                target_syn["evidence_ids"].append(ev_id)
                
            candidates_applied.append({
                "type": "synonym",
                "candidate": cand_form,
                "target_synset_id": target_syn_id,
                "target_lemmas": target_syn["lemmas"]
            })
            
        elif dec == "accept" and rel == "related":
            # Add relation
            rel_id = "rel_" + hashlib.sha256((target_syn_id + ":related_to:" + cand_form).encode()).hexdigest()[:12]
            relations.append({
                "rel_id": rel_id,
                "subject_synset_id": target_syn_id,
                "predicate": "related_to",
                "object_term": cand_form,
                "object_emotions": c["reviewed_emotions"].split(";"),
                "notes": c["notes"]
            })
        elif dec == "reject" and rel == "antonym":
            # Add antonym relation
            rel_id = "rel_" + hashlib.sha256((target_syn_id + ":antonym_of:" + cand_form).encode()).hexdigest()[:12]
            relations.append({
                "rel_id": rel_id,
                "subject_synset_id": target_syn_id,
                "predicate": "antonym_of",
                "object_term": cand_form,
                "notes": c["notes"]
            })
            
    # Write all files
    write_jsonl(v2_dir / "entries.jsonl", entries)
    write_jsonl(v2_dir / "senses.jsonl", senses)
    write_jsonl(v2_dir / "synsets.jsonl", synsets)
    write_jsonl(v2_dir / "relations.jsonl", relations)
    write_jsonl(v2_dir / "evidence.jsonl", evidence)
    
    (v2_dir / "applied_merges.json").write_text(json.dumps(merges_applied, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (v2_dir / "applied_expansions.json").write_text(json.dumps(candidates_applied, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    
    manifest = {
        "schema": "emotionet_research_seed_synsets_v2",
        "data_version": "seed-synsets-v2",
        "entries": len(entries),
        "senses": len(senses),
        "synsets": len(synsets),
        "relations": len(relations),
        "cross_lemma_merges_applied": len(merges_applied),
        "embedding_synonyms_added": len(candidates_applied),
        "emotion_label_count": len({label for s in senses for label in s["emotion_labels"]}),
        "publication_status": "not_cleared",
        "source_snapshot": "seed-synsets-v1",
        "output_sha256": {p.name: sha256(p) for p in sorted(v2_dir.iterdir())}
    }
    (v2_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshot v2 created at {v2_dir}:")
    print(f"  Entries: {len(entries)}")
    print(f"  Senses: {len(senses)}")
    print(f"  Synsets: {len(synsets)}")
    print(f"  Relations: {len(relations)}")
    print(f"  Merges applied: {len(merges_applied)}")
    print(f"  Synonym candidates added: {len(candidates_applied)}")

if __name__ == "__main__":
    main()
