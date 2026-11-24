import pandas as pd
import json

print("=== 18 IS_A PROPOSALS ===")
isa_df = pd.read_csv('data/local/g2-review-v1/is-a-pilot-review.csv')
for idx, r in isa_df.iterrows():
    print(f"[{r['review_id']}] {r['case_type']}: [{r['subject_lemmas']}] ({r['subject_synset_id']}) -> [{r['object_lemmas']}] ({r['object_synset_id']})")
    print(f"   Subj Def: {r['subject_definition']}")
    print(f"   Obj  Def: {r['object_definition']}")
    print(f"   Question: {r['review_question']}")
    print(f"   Alternatives: {r['alternatives']}")

print("\n=== 10 FOCUS SYNSETS IN SYNSET-REVIEW.CSV ===")
syn_df = pd.read_csv('data/local/g2-review-v1/synset-review.csv')
sense_ref = pd.read_csv('data/local/g2-review-v1/sense-reference.csv')

focus_syn = syn_df[syn_df['review_focus'].str.contains('check_all_member_glosses')]
for idx, r in focus_syn.iterrows():
    sid = r['synset_id']
    print(f"Synset: {sid} | Lemmas: {r['lemmas']} | Focus: {r['review_focus']}")
    print(f"  Synset Def: {r['definition']}")
    print(f"  Emotions: {r['emotion_labels']}")
    members = str(r['member_sense_ids']).split(';')
    print(f"  Members ({len(members)}):")
    for mid in members:
        s_row = sense_ref[sense_ref['sense_id'] == mid]
        if not s_row.empty:
            s = s_row.iloc[0]
            print(f"    - {s['sense_id']} [{s['lemma']}]: gloss='{s['gloss']}' | emo={s['emotion_labels']} | ex={s['examples_json']}")
    print()
