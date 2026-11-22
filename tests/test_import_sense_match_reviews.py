import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_sense_match_reviews import validate_samples, validate_senses


class SenseMatchReviewTests(unittest.TestCase):
    def test_sample_identity_checks_pair_and_text_not_just_sentence(self):
        a = dict(seed_id="a", dataset_id="1", term="test", text="test text", split="train",
                 sense_match_decision="", notes="", sample_method="first_3_matching_rows_not_random")
        b = {**a, "seed_id": "b"}
        accepted = [{**r, "sense_match_decision": "matches_sense", "notes": "Reviewed"} for r in [a, b]]
        validate_samples(accepted, [a, b])
        for bad in [[accepted[0], accepted[0]], [{**accepted[0], "text": "changed"}, accepted[1]], accepted[:1]]:
            with self.assertRaises(ValueError):
                validate_samples(bad, [a, b])

    def test_accepted_sense_must_belong_to_selected_seed(self):
        seed = dict(seed_id="seed_a", term="test", emotion_labels=["love", "caring"])
        sense = dict(seed_id="seed_a", term="test", draft_sense_id="seed_a_s1", proposed_emotions="love",
                     decision="accept", reviewer="submitted reviewer", sense_gloss="Reviewed sense")
        validate_senses([sense], [seed])
        for change in [dict(proposed_emotions="anger"), dict(reviewer=""), dict(decision=""), dict(term="other")]:
            with self.assertRaises(ValueError):
                validate_senses([{**sense, **change}], [seed])
        with self.assertRaises(ValueError):
            validate_senses([sense, sense], [seed])


if __name__ == "__main__":
    unittest.main()
