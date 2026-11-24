import json
from pathlib import Path

# Let's inspect each of the 66 synsets in v2 and see their member lemmas
entries = {e['entry_id']: e for e in [json.loads(l) for l in Path('data/local/seed-synsets-v2/entries.jsonl').read_text(encoding='utf-8').splitlines()]}
senses = {s['sense_id']: s for s in [json.loads(l) for l in Path('data/local/seed-synsets-v2/senses.jsonl').read_text(encoding='utf-8').splitlines()]}
synsets = [json.loads(l) for l in Path('data/local/seed-synsets-v2/synsets.jsonl').read_text(encoding='utf-8').splitlines()]

print("Multi-member synsets:")
for syn in synsets:
    if len(syn['member_sense_ids']) > 1:
        m_lemmas = [entries[senses[sid]['entry_id']]['lemma'] for sid in syn['member_sense_ids']]
        print(f"{syn['synset_id']} | {syn['preferred_lemma']} | lemmas: {m_lemmas}")
