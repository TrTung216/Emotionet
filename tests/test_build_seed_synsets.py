import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_seed_synsets import construct


def seed(key, term, labels):
    return dict(seed_id=key, term=term, normalized_form=term, sense_gloss="Reviewed " + term,
                emotion_labels=labels, semantic_status="accepted", reviewer="reviewer", reviewed_at=None, review_notes="")


class SynsetBuildTests(unittest.TestCase):
    def test_split_replaces_unsplit_sense_and_same_label_does_not_merge(self):
        seeds = [seed("a", "one", ["love", "caring"]), seed("b", "two", ["love"])]
        splits = [dict(sense_id="a_s1", seed_id="a", term="one", sense_gloss="Sense one", emotion_labels=["love"],
                       semantic_status="accepted_as_submitted", reviewer="r", reviewed_at=None, review_notes=""),
                  dict(sense_id="a_s2", seed_id="a", term="one", sense_gloss="Sense two", emotion_labels=["caring"],
                       semantic_status="accepted_as_submitted", reviewer="r", reviewed_at=None, review_notes="")]
        entries, senses, synsets, evidence = construct(seeds, splits)
        self.assertEqual((len(entries), len(senses), len(synsets)), (2, 3, 3))
        self.assertNotIn("a_sense", {s["sense_id"] for s in senses})
        self.assertEqual(len({s["synset_id"] for s in senses}), 3)
        self.assertTrue(all(len(s["member_sense_ids"]) == 1 for s in synsets))
        self.assertTrue(all(s["publication_status"] == "not_cleared" for s in senses))
        self.assertEqual({s["synset_id"] for s in construct(list(reversed(seeds)), splits)[1]},
                         {s["synset_id"] for s in senses})

    def test_rejects_unaccepted_seeds_and_unsupported_split_labels(self):
        base = seed("a", "one", ["love"])
        with self.assertRaises(ValueError):
            construct([{**base, "semantic_status": "candidate"}], [])
        with self.assertRaises(ValueError):
            construct([base], [dict(seed_id="a", sense_id="a_s1", term="one", semantic_status="accepted_as_submitted",
                                    emotion_labels=["anger"])])


if __name__ == "__main__":
    unittest.main()
