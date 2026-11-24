import pandas as pd

df = pd.read_csv('data/local/g2-review-reconciled-v1/relation-review.csv')
print(f"Total relations: {len(df)}")
for idx, r in df.iterrows():
    print(f"{idx+1}. {r['review_id']} | Subj: {r['subject_lemmas']} ({r['subject_synset_id']}) --[{r['source_predicate']}]--> Obj: '{r['object_term']}'")
    print(f"   Source notes: {r['source_notes']}")
    print(f"   Target status: {r['target_status']}")
