import json
from pathlib import Path

entries = [json.loads(l) for l in Path('data/local/seed-synsets-v2/entries.jsonl').read_text(encoding='utf-8').splitlines()]
senses = {s['sense_id']: s for s in [json.loads(l) for l in Path('data/local/seed-synsets-v2/senses.jsonl').read_text(encoding='utf-8').splitlines()]}
synsets = {s['synset_id']: s for s in [json.loads(l) for l in Path('data/local/seed-synsets-v2/synsets.jsonl').read_text(encoding='utf-8').splitlines()]}

for e in sorted(entries, key=lambda x: x['lemma']):
    sense_objs = [senses[sid] for sid in e['sense_ids'] if sid in senses]
    syn_objs = [synsets[s['synset_id']] for s in sense_objs if s['synset_id'] in synsets]
    labels = list(set([lbl for s in sense_objs for lbl in s.get('emotion_labels', [])]))
    print(f"{e['entry_id']} | {e['lemma']} | {labels} | senses={len(e['sense_ids'])}")
