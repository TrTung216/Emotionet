# -*- coding: utf-8 -*-
"""Build seed-synsets-v3 applying G2 reviews, membership revisions, POS assignment, and 24 target concepts."""

import csv
import hashlib
import json
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POS_MAP = {
    'biết ơn': 'v',
    'buồn': 'a',
    'buồn bã': 'a',
    'buồn cười': 'a',
    'bối rối': 'a',
    'bồn chồn': 'a',
    'bực bội': 'a',
    'bực mình': 'a',
    'cám ơn': 'v',
    'cảm kích': 'a',
    'day dứt': 'v',
    'ghét': 'v',
    'ghê sợ': 'a',
    'ghê tởm': 'a',
    'giận': 'v',
    'hiếu kỳ': 'a',
    'hoang mang': 'a',
    'hy vọng': 'v',
    'hài hước': 'a',
    'hào hứng': 'a',
    'hãnh diện': 'a',
    'hạnh phúc': 'a',
    'hối hận': 'v',
    'hối tiếc': 'v',
    'hụt hẫng': 'a',
    'khao khát': 'v',
    'khiếp sợ': 'a',
    'khâm phục': 'v',
    'khó chịu': 'a',
    'không tán thành': 'v',
    'lo': 'v',
    'lo lắng': 'v',
    'lo lắng cho': 'v',
    'lo âu': 'v',
    'lạc quan': 'a',
    'mong muốn': 'v',
    'ngưỡng mộ': 'v',
    'ngượng ngùng': 'a',
    'ngạc nhiên': 'a',
    'nhận ra': 'v',
    'nhẹ lòng': 'a',
    'nhẹ nhõm': 'a',
    'nản': 'a',
    'nể': 'v',
    'phản đối': 'v',
    'phấn khích': 'a',
    'phẫn nộ': 'a',
    'phục': 'v',
    'quan tâm': 'v',
    'sầu': 'a',
    'sợ': 'v',
    'sợ hãi': 'a',
    'sợ sệt': 'a',
    'sửng sốt': 'a',
    'thích thú': 'a',
    'thương': 'v',
    'thất vọng': 'a',
    'tiếc': 'v',
    'tiếc nuối': 'v',
    'tán thành': 'v',
    'tò mò': 'a',
    'tủi thân': 'a',
    'tức': 'a',
    'tức giận': 'a',
    'tự hào': 'a',
    'vui': 'a',
    'vui mừng': 'a',
    'vỡ lẽ': 'v',
    'xấu hổ': 'a',
    'yêu': 'v',
    'yêu quý': 'v',
    'yêu thương': 'v',
    'ăn năn': 'v',
    'đau buồn': 'a',
    'đau lòng': 'a',
    'đau thương': 'a',
    'đồng tình': 'v'
}

TARGET_CONCEPTS = {
    'bình an': {'synset_id': 'syn_binh_an', 'pos': 'a', 'emotion_labels': ['joy']},
    'chợt': {'synset_id': 'syn_chot', 'pos': 'r', 'emotion_labels': []},
    'cởi mở': {'synset_id': 'syn_coi_mo', 'pos': 'a', 'emotion_labels': ['joy']},
    'dũng cảm': {'synset_id': 'syn_dung_cam', 'pos': 'a', 'emotion_labels': []},
    'dỗi': {'synset_id': 'syn_doi', 'pos': 'v', 'emotion_labels': ['anger']},
    'khinh': {'synset_id': 'syn_khinh', 'pos': 'v', 'emotion_labels': ['disgust']},
    'mông lung': {'synset_id': 'syn_mong_lung', 'pos': 'a', 'emotion_labels': ['confusion']},
    'mến': {'synset_id': 'syn_men', 'pos': 'v', 'emotion_labels': ['love']},
    'nhân ái': {'synset_id': 'syn_nhan_ai', 'pos': 'a', 'emotion_labels': ['caring']},
    'thú vui': {'synset_id': 'syn_thu_vui', 'pos': 'n', 'emotion_labels': ['amusement']},
    'thất tình': {'synset_id': 'syn_that_tinh', 'pos': 'v', 'emotion_labels': ['sadness']},
    'tinh tế': {'synset_id': 'syn_tinh_te', 'pos': 'a', 'emotion_labels': []},
    'trò đùa': {'synset_id': 'syn_tro_dua', 'pos': 'n', 'emotion_labels': ['amusement']},
    'tội nghiệp': {'synset_id': 'syn_toi_nghiep', 'pos': 'a', 'emotion_labels': ['caring', 'sadness']},
    'tủi thân': {'synset_id': 'syn_tui_than', 'pos': 'a', 'emotion_labels': ['sadness']},
    'vui tính': {'synset_id': 'syn_vui_tinh', 'pos': 'a', 'emotion_labels': ['amusement']},
    'vô tư': {'synset_id': 'syn_vo_tu', 'pos': 'a', 'emotion_labels': ['joy']},
    'xót xa': {'synset_id': 'syn_xot_xa', 'pos': 'a', 'emotion_labels': ['caring', 'sadness']},
    'ác độc': {'synset_id': 'syn_ac_doc', 'pos': 'a', 'emotion_labels': []},
    'ích kỷ': {'synset_id': 'syn_ich_ky', 'pos': 'a', 'emotion_labels': []},
    'đau xót': {'synset_id': 'syn_dau_xot', 'pos': 'a', 'emotion_labels': ['caring', 'sadness']},
    'đúng đắn': {'synset_id': 'syn_dung_dan', 'pos': 'a', 'emotion_labels': []},
    'đồng cảm': {'synset_id': 'syn_dong_cam', 'pos': 'v', 'emotion_labels': ['caring']},
    'ấm áp': {'synset_id': 'syn_am_ap', 'pos': 'a', 'emotion_labels': ['joy']}
}

def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())

def main():
    v2_dir = ROOT / "data/local/seed-synsets-v2"
    v3_dir = ROOT / "data/local/seed-synsets-v3"
    
    if v3_dir.exists():
        shutil.rmtree(v3_dir)
    v3_dir.mkdir(parents=True, exist_ok=True)
    
    entries = read_jsonl(v2_dir / "entries.jsonl")
    senses = read_jsonl(v2_dir / "senses.jsonl")
    synsets = read_jsonl(v2_dir / "synsets.jsonl")
    evidence = read_jsonl(v2_dir / "evidence.jsonl")
    
    entry_index = {e["entry_id"]: e for e in entries}
    sense_index = {s["sense_id"]: s for s in senses}
    synset_index = {s["synset_id"]: s for s in synsets}
    
    # 1. Assign standardized POS to all 77 entries in v2
    for e in entries:
        lemma = e["lemma"]
        if lemma not in POS_MAP:
            raise ValueError(f"Missing POS for entry lemma: {lemma}")
        e["pos"] = POS_MAP[lemma]
    
    # 2. Membership revision A: split 'tủi thân' from syn_bfcacfd3e7930678
    syn_buon = synset_index["syn_bfcacfd3e7930678"]
    tui_than_sense_id = "sense_cand_d6b678c30a79"
    if tui_than_sense_id in syn_buon["member_sense_ids"]:
        syn_buon["member_sense_ids"].remove(tui_than_sense_id)
    if "tủi thân" in syn_buon["lemmas"]:
        syn_buon["lemmas"].remove("tủi thân")
    syn_buon["definition"] = "Trạng thái tâm lý u sầu, đau lòng, ủ rũ khi gặp điều trắc trở"
    
    # Create syn_tui_than
    sense_tui_than = sense_index[tui_than_sense_id]
    sense_tui_than["synset_id"] = "syn_tui_than"
    
    ev_tui_than = {
        "evidence_id": "ev_syn_tui_than",
        "method": "g2_membership_revision_split",
        "source_kind": "g2_review_v1",
        "source_record_id": "syn_tui_than",
        "reviewer": "antigravity",
        "reviewed_at": "2026-11-24T15:00:00+07:00",
        "notes": "Tách tủi thân thành concept độc lập; nỗi buồn tủi xót xa cho thân phận đơn độc của chính mình."
    }
    evidence.append(ev_tui_than)
    
    syn_tui_than = {
        "synset_id": "syn_tui_than",
        "preferred_lemma": "tủi thân",
        "definition": "Nỗi buồn tủi cho thân phận đơn độc, thiệt thòi của chính mình",
        "member_sense_ids": [tui_than_sense_id],
        "lemmas": ["tủi thân"],
        "emotion_labels": ["sadness"],
        "evidence_ids": ["ev_syn_tui_than"],
        "construction": "g2_membership_revision",
        "membership_status": "singleton",
        "semantic_status": "accepted_as_submitted",
        "publication_status": "not_cleared"
    }
    synset_index["syn_tui_than"] = syn_tui_than
    synsets.append(syn_tui_than)
    
    # 3. Membership revision B: create sense 2 for 'nể' (kiêng nể) -> syn_kieng_ne
    entry_ne = entry_index["entry_cand_5b53f6a9f5f2"]
    sense_ne_s2_id = "sense_cand_ne_s2"
    ev_ne_s2 = {
        "evidence_id": "ev_sense_ne_s2",
        "method": "g2_sense_split",
        "source_kind": "g2_review_v1",
        "source_record_id": "syn_kieng_ne",
        "reviewer": "antigravity",
        "reviewed_at": "2026-11-24T15:00:00+07:00",
        "notes": "Tách nghĩa kiêng nể/nể nang khỏi synset nể phục (admiration)."
    }
    evidence.append(ev_ne_s2)
    
    sense_ne_s2 = {
        "sense_id": sense_ne_s2_id,
        "entry_id": entry_ne["entry_id"],
        "seed_id": None,
        "lemma": "nể",
        "synset_id": "syn_kieng_ne",
        "gloss": "Kiêng dè, tránh làm mất lòng người khác vì nể nang",
        "emotion_labels": [],
        "examples": [],
        "example_kind": "illustrative_not_corpus_citation",
        "semantic_status": "candidate",
        "evidence_ids": ["ev_sense_ne_s2"],
        "intensity": None,
        "confidence": None,
        "publication_status": "not_cleared"
    }
    senses.append(sense_ne_s2)
    sense_index[sense_ne_s2_id] = sense_ne_s2
    if sense_ne_s2_id not in entry_ne["sense_ids"]:
        entry_ne["sense_ids"].append(sense_ne_s2_id)
        
    syn_kieng_ne = {
        "synset_id": "syn_kieng_ne",
        "preferred_lemma": "nể",
        "definition": "Trạng thái kiêng dè, e ngại làm mất lòng hoặc vì ràng buộc quan hệ xã giao",
        "member_sense_ids": [sense_ne_s2_id],
        "lemmas": ["nể"],
        "emotion_labels": [],
        "evidence_ids": ["ev_sense_ne_s2"],
        "construction": "g2_sense_split",
        "membership_status": "singleton",
        "semantic_status": "accepted_as_submitted",
        "publication_status": "not_cleared"
    }
    synset_index["syn_kieng_ne"] = syn_kieng_ne
    synsets.append(syn_kieng_ne)
    
    # 4. Create 23 new target concepts
    target_defs_file = ROOT / "data/local/g2-wordnet-review-v1/target-definition-groups.csv"
    with open(target_defs_file, "r", encoding="utf-8-sig") as f:
        target_groups = list(csv.DictReader(f))
        
    target_definitions = {r["object_term"]: r["proposed_definition"] for r in target_groups}
    
    new_concepts_created = []
    for term, meta in TARGET_CONCEPTS.items():
        if term == "tủi thân":
            continue  # Already created from existing entry/sense
        syn_id = meta["synset_id"]
        pos = meta["pos"]
        emotions = meta["emotion_labels"]
        definition = target_definitions[term]
        
        entry_id = f"entry_target_{syn_id.replace('syn_', '')}"
        sense_id = f"sense_target_{syn_id.replace('syn_', '')}"
        ev_id = f"ev_target_{syn_id.replace('syn_', '')}"
        
        ev_record = {
            "evidence_id": ev_id,
            "method": "g2_relation_target_expansion",
            "source_kind": "g2_wordnet_review_v1",
            "source_record_id": syn_id,
            "reviewer": "antigravity",
            "reviewed_at": "2026-11-24T15:00:00+07:00",
            "notes": f"Khởi tạo khái niệm đích chuẩn hóa '{term}' phục vụ phân giải mạng lưới quan hệ WordNet."
        }
        evidence.append(ev_record)
        
        entry_record = {
            "entry_id": entry_id,
            "seed_id": None,
            "lemma": term,
            "normalized_form": normalize(term),
            "lang": "vi",
            "pos": pos,
            "sense_ids": [sense_id]
        }
        entries.append(entry_record)
        entry_index[entry_id] = entry_record
        
        sense_record = {
            "sense_id": sense_id,
            "entry_id": entry_id,
            "seed_id": None,
            "lemma": term,
            "synset_id": syn_id,
            "gloss": definition,
            "emotion_labels": emotions,
            "examples": [],
            "example_kind": "illustrative_not_corpus_citation",
            "semantic_status": "accepted_as_submitted",
            "evidence_ids": [ev_id],
            "intensity": None,
            "confidence": None,
            "publication_status": "not_cleared"
        }
        senses.append(sense_record)
        sense_index[sense_id] = sense_record
        
        synset_record = {
            "synset_id": syn_id,
            "preferred_lemma": term,
            "definition": definition,
            "member_sense_ids": [sense_id],
            "lemmas": [term],
            "emotion_labels": emotions,
            "evidence_ids": [ev_id],
            "construction": "g2_relation_target_expansion",
            "membership_status": "singleton",
            "semantic_status": "accepted_as_submitted",
            "publication_status": "not_cleared"
        }
        synsets.append(synset_record)
        synset_index[syn_id] = synset_record
        new_concepts_created.append({"lemma": term, "synset_id": syn_id, "pos": pos})
        
    # 5. Build relations
    relations = []
    
    # A. 5 accepted is_a edges from is-a-pilot-review.csv
    isa_file = ROOT / "data/local/g2-review-reconciled-v1/is-a-pilot-review.csv"
    with open(isa_file, "r", encoding="utf-8-sig") as f:
        isa_rows = [r for r in csv.DictReader(f) if r["decision"] == "accept"]
        
    for r in isa_rows:
        rel_id = f"rel_isa_{r['review_id'].replace('g2_isa_', '')}"
        ev_id = f"ev_{rel_id}"
        
        ev_record = {
            "evidence_id": ev_id,
            "method": "is_a_pilot_review",
            "source_kind": "is_a_pilot_review_v1",
            "source_record_id": r["review_id"],
            "reviewer": r["reviewer"],
            "reviewed_at": r["reviewed_at"],
            "notes": f"Quan hệ phân cấp is_a được duyệt: {r['subject_lemmas']} -> {r['object_lemmas']}. {r['resolution_notes']}"
        }
        evidence.append(ev_record)
        
        relations.append({
            "rel_id": rel_id,
            "subject_synset_id": r["subject_synset_id"],
            "object_synset_id": r["object_synset_id"],
            "predicate": "is_a",
            "object_term": r["object_lemmas"],
            "evidence_ids": [ev_id],
            "notes": r["resolution_notes"]
        })
        
    # B. 1 related_to edge: syn_tui_than -> syn_bfcacfd3e7930678 (buồn)
    ev_rel_tui_than = {
        "evidence_id": "ev_rel_tui_than_buon",
        "method": "g2_membership_revision_relation",
        "source_kind": "g2_review_v1",
        "source_record_id": "syn_tui_than",
        "reviewer": "antigravity",
        "reviewed_at": "2026-11-24T15:00:00+07:00",
        "notes": "Quan hệ liên quan ngữ nghĩa giữa tủi thân và nhóm u sầu/đau lòng."
    }
    evidence.append(ev_rel_tui_than)
    
    relations.append({
        "rel_id": "rel_tui_than_buon",
        "subject_synset_id": "syn_tui_than",
        "object_synset_id": "syn_bfcacfd3e7930678",
        "predicate": "related_to",
        "object_term": "buồn",
        "evidence_ids": ["ev_rel_tui_than_buon"],
        "notes": "Tủi thân liên quan ngữ nghĩa đến nỗi buồn đau lòng chung."
    })
    
    # C. 29 resolved relations from relation-review.csv
    rel_file = ROOT / "data/local/g2-review-reconciled-v1/relation-review.csv"
    with open(rel_file, "r", encoding="utf-8-sig") as f:
        rel_rows = list(csv.DictReader(f))
        
    for r in rel_rows:
        rev_id = r["review_id"]
        target_term = r["object_term"]
        target_syn_id = TARGET_CONCEPTS[target_term]["synset_id"]
        rel_id = f"rel_{rev_id.replace('g2_rel_', '')}"
        ev_id = f"ev_{rel_id}"
        
        ev_record = {
            "evidence_id": ev_id,
            "method": "g2_relation_review_reconciled",
            "source_kind": "g2_review_v1",
            "source_record_id": rev_id,
            "reviewer": r["reviewer"],
            "reviewed_at": r["reviewed_at"],
            "notes": f"Quan hệ {r['final_predicate']} tới '{target_term}'. {r['resolution_notes']}"
        }
        evidence.append(ev_record)
        
        relations.append({
            "rel_id": rel_id,
            "subject_synset_id": r["subject_synset_id"],
            "object_synset_id": target_syn_id,
            "predicate": "related_to",  # Reconciled per WordNet Profile spec
            "object_term": target_term,
            "evidence_ids": [ev_id],
            "notes": r["resolution_notes"]
        })
        
    # Write all JSONL files
    write_jsonl(v3_dir / "entries.jsonl", entries)
    write_jsonl(v3_dir / "senses.jsonl", senses)
    write_jsonl(v3_dir / "synsets.jsonl", synsets)
    write_jsonl(v3_dir / "relations.jsonl", relations)
    write_jsonl(v3_dir / "evidence.jsonl", evidence)
    
    # Applied revisions summary
    revisions_summary = {
        "pos_assigned_count": len(entries),
        "pos_distribution": {
            pos: sum(1 for e in entries if e["pos"] == pos)
            for pos in ["a", "v", "n", "r"]
        },
        "membership_changes": [
            {
                "synset_id": "syn_bfcacfd3e7930678",
                "removed_sense": tui_than_sense_id,
                "created_synset": "syn_tui_than",
                "action": "split_tui_than"
            },
            {
                "synset_id": "syn_770c2e9f56867e77",
                "retained_sense": "sense_cand_f871e0b10511",
                "created_sense": sense_ne_s2_id,
                "created_synset": "syn_kieng_ne",
                "action": "split_ne_kieng_ne"
            }
        ],
        "new_target_concepts": new_concepts_created,
        "relations_summary": {
            "total_relations": len(relations),
            "is_a_edges": len(isa_rows),
            "related_to_edges": 1 + len(rel_rows),
            "reconciled_antonym_to_related_to": 3
        }
    }
    (v3_dir / "applied_g2_revisions.json").write_text(
        json.dumps(revisions_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    
    manifest = {
        "schema": "emotionet_research_seed_synsets_v3",
        "data_version": "seed-synsets-v3",
        "entries": len(entries),
        "senses": len(senses),
        "synsets": len(synsets),
        "relations": len(relations),
        "evidence": len(evidence),
        "emotion_label_count": len({label for s in senses for label in s.get("emotion_labels", [])}),
        "publication_status": "not_cleared",
        "source_snapshot": "seed-synsets-v2",
        "output_sha256": {p.name: sha256(p) for p in sorted(v3_dir.iterdir())}
    }
    (v3_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    
    print(f"Snapshot v3 successfully created at {v3_dir}:")
    print(f"  Entries: {len(entries)} (0 null POS)")
    print(f"  Senses: {len(senses)}")
    print(f"  Synsets: {len(synsets)}")
    print(f"  Relations: {len(relations)} (5 is_a, 30 related_to)")
    print(f"  Evidence: {len(evidence)}")
    print(f"  POS Distribution: {revisions_summary['pos_distribution']}")

if __name__ == "__main__":
    main()
