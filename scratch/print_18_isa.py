import pandas as pd

isa_df = pd.read_csv('data/local/g2-review-v1/is-a-pilot-review.csv')
for idx, r in isa_df.iterrows():
    print(f"Index {idx+1}: {r['review_id']}")
    print(f"  Child (Subj): [{r['subject_lemmas']}] ({r['subject_synset_id']})")
    print(f"    Def: {r['subject_definition']}")
    print(f"  Parent (Obj): [{r['object_lemmas']}] ({r['object_synset_id']})")
    print(f"    Def: {r['object_definition']}")
    print(f"  Case Type: {r['case_type']}")
    print(f"  Question: {r['review_question']}")
    print(f"  Alternatives: {r['alternatives']}")
    print()
