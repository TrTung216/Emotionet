import pandas as pd
import json

df = pd.read_csv('data/local/g2-review-reconciled-v1/relation-review.csv')
for idx, r in df.iterrows():
    print(f"[{r['review_id']}] ({r['rel_id']}): Subj: [{r['subject_lemmas']}] ({r['subject_synset_id']}) -> Obj: '{r['object_term']}'")
    print(f"   Pred: {r['source_predicate']} | Target status: {r['target_status']}")
    print(f"   Subj def: {r['subject_definition']}")
    print(f"   Source notes: {r['source_notes']}")
    print(f"   Candidate details: {r['candidate_object_details_json']}")
    print(f"   Focus: {r['review_focus']}")
    print("-" * 60)
