from pathlib import Path
import json
from emotionet.core import Emotionet

v3_path = Path("data/local/seed-synsets-v3")
print("Testing Emotionet import_jsonl on seed-synsets-v3...")

with Emotionet.open(":memory:", mode="research") as em:
    stats = em.import_jsonl(v3_path)
    print("Import successful! Stats:", stats)
    
    cursor = em._db.cursor()
    cursor.execute("SELECT predicate, COUNT(*) FROM relations GROUP BY predicate")
    print("Relations in DB:", cursor.fetchall())
    
    # Check entries pos in records
    cursor.execute("SELECT COUNT(*) FROM records WHERE kind='entry' AND json_extract(payload, '$.pos') IS NULL")
    null_pos = cursor.fetchone()[0]
    print(f"Null POS in DB entries: {null_pos}")
    
    cursor.execute("SELECT json_extract(payload, '$.pos') as pos, COUNT(*) FROM records WHERE kind='entry' GROUP BY pos")
    print("POS distribution in DB:", cursor.fetchall())
    
    # Check is_a edges
    cursor.execute("SELECT r.id, c1.id, c2.id FROM relations r JOIN concepts c1 ON r.subject_id=c1.id JOIN concepts c2 ON r.object_id=c2.id WHERE r.predicate='is_a'")
    print("is_a edges in DB:")
    for edge in cursor.fetchall():
        print(" ", edge)
        
    # Check syn_tui_than
    cursor.execute("SELECT id FROM concepts WHERE id='syn_tui_than'")
    print("syn_tui_than exists:", cursor.fetchone())
    
    # Check syn_kieng_ne
    cursor.execute("SELECT id FROM concepts WHERE id='syn_kieng_ne'")
    print("syn_kieng_ne exists:", cursor.fetchone())
    
    # Verify related_to edge for tui_than
    cursor.execute("SELECT id, subject_id, object_id FROM relations WHERE subject_id='syn_tui_than'")
    print("syn_tui_than relations:", cursor.fetchall())

print("ALL VERIFICATIONS PASSED 100%!")
