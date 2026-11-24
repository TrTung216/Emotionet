import json
from pathlib import Path

pos_map = {
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

entries = {e['entry_id']: e for e in [json.loads(l) for l in Path('data/local/seed-synsets-v2/entries.jsonl').read_text(encoding='utf-8').splitlines()]}
senses = {s['sense_id']: s for s in [json.loads(l) for l in Path('data/local/seed-synsets-v2/senses.jsonl').read_text(encoding='utf-8').splitlines()]}
synsets = [json.loads(l) for l in Path('data/local/seed-synsets-v2/synsets.jsonl').read_text(encoding='utf-8').splitlines()]

conflicts = 0
for syn in synsets:
    syn_id = syn['synset_id']
    m_senses = [senses[sid] for sid in syn['member_sense_ids']]
    m_entries = [entries[s['entry_id']] for s in m_senses]
    m_pos = set(pos_map[e['lemma']] for e in m_entries)
    if len(m_pos) > 1:
        conflicts += 1
        print(f"CONFLICT in synset {syn_id} ({syn['preferred_lemma']}): {[(e['lemma'], pos_map[e['lemma']]) for e in m_entries]}")

if conflicts == 0:
    print("ALL 66 SYNSETS ARE 100% HOMOGENEOUS IN POS!")

counts = {}
for p in pos_map.values():
    counts[p] = counts.get(p, 0) + 1
print(f"POS distribution across 77 entries: {counts}")
