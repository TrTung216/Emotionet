# -*- coding: utf-8 -*-
"""Audit seed-synsets-v3 against G2 WordNet audit criteria."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3_DIR = ROOT / "data/local/seed-synsets-v3"

def main():
    manifest = json.loads((V3_DIR / "manifest.json").read_text(encoding="utf-8"))
    
    # 1. Verify checksums
    print("1. Verifying manifest sha256 checksums...")
    for filename, expected_hash in manifest["output_sha256"].items():
        file_path = V3_DIR / filename
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {filename}"
    print("   All manifest checksums matched.")
    
    # 2. Load records
    entries = [json.loads(l) for l in (V3_DIR / "entries.jsonl").read_text(encoding="utf-8").splitlines()]
    senses = [json.loads(l) for l in (V3_DIR / "senses.jsonl").read_text(encoding="utf-8").splitlines()]
    synsets = [json.loads(l) for l in (V3_DIR / "synsets.jsonl").read_text(encoding="utf-8").splitlines()]
    relations = [json.loads(l) for l in (V3_DIR / "relations.jsonl").read_text(encoding="utf-8").splitlines()]
    evidence = [json.loads(l) for l in (V3_DIR / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
    
    synset_map = {s["synset_id"]: s for s in synsets}
    entry_map = {e["entry_id"]: e for e in entries}
    sense_map = {s["sense_id"]: s for s in senses}
    evidence_ids = {ev["evidence_id"] for ev in evidence}
    
    # 3. Audit POS
    print("2. Auditing POS assignment...")
    null_pos = [e for e in entries if not e.get("pos")]
    assert len(null_pos) == 0, f"Found {len(null_pos)} entries with missing POS!"
    invalid_pos = [e for e in entries if e["pos"] not in {"a", "v", "n", "r"}]
    assert len(invalid_pos) == 0, f"Found invalid POS: {invalid_pos}"
    print(f"   100% entries have valid POS in {{a, v, n, r}}: {len(entries)} total.")
    
    # 4. Audit Synset POS homogeneity
    print("3. Auditing Synset POS homogeneity...")
    for s in synsets:
        m_senses = [sense_map[sid] for sid in s["member_sense_ids"]]
        m_entries = [entry_map[s_obj["entry_id"]] for s_obj in m_senses]
        pos_set = {e["pos"] for e in m_entries}
        assert len(pos_set) == 1, f"Synset {s['synset_id']} has mixed POS: {pos_set}"
    print("   All synsets have 100% homogeneous POS across all member senses.")
    
    # 5. Audit Relations
    print("4. Auditing relations...")
    for r in relations:
        assert r["subject_synset_id"] in synset_map, f"Subject {r['subject_synset_id']} not in synsets"
        assert r["object_synset_id"] in synset_map, f"Object {r['object_synset_id']} not in synsets"
        assert r["predicate"] in {"is_a", "related_to"}, f"Unsupported predicate: {r['predicate']}"
        for eid in r.get("evidence_ids", []):
            assert eid in evidence_ids, f"Evidence {eid} missing from evidence.jsonl"
            
        # If is_a, check same-POS
        if r["predicate"] == "is_a":
            sub_entry = entry_map[sense_map[synset_map[r["subject_synset_id"]]["member_sense_ids"][0]]["entry_id"]]
            obj_entry = entry_map[sense_map[synset_map[r["object_synset_id"]]["member_sense_ids"][0]]["entry_id"]]
            assert sub_entry["pos"] == obj_entry["pos"], f"is_a cross-POS: {sub_entry['pos']} -> {obj_entry['pos']}"
    print(f"   All {len(relations)} relations valid, referentially intact, same-POS for is_a.")
    
    # 6. Audit Membership Revisions
    print("5. Auditing Membership Revisions...")
    # Tủi thân
    syn_buon = synset_map["syn_bfcacfd3e7930678"]
    assert "tủi thân" not in syn_buon["lemmas"], "tủi thân still in syn_buon!"
    assert "syn_tui_than" in synset_map, "syn_tui_than not in synsets!"
    # Nể
    entry_ne = entry_map["entry_cand_5b53f6a9f5f2"]
    assert len(entry_ne["sense_ids"]) == 2, f"entry_ne does not have 2 senses: {entry_ne['sense_ids']}"
    assert "syn_kieng_ne" in synset_map, "syn_kieng_ne not in synsets!"
    print("   Both membership revisions verified.")
    
    print("\nALL AUDIT CHECKS PASSED FOR seed-synsets-v3!")

if __name__ == "__main__":
    main()
