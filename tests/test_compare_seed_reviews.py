import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("compare_seed_reviews", Path(__file__).resolve().parents[1] / "scripts/compare_seed_reviews.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(**updates):
    result = dict(review_id="s1", term="test", decision="accept", reviewed_emotions="joy;amusement",
                  sense_gloss="Example sense", reviewer="Reviewer", reviewed_at="", notes="",
                  association_vectors_differ="True")
    result.update(updates)
    return result


class ComparisonTests(unittest.TestCase):
    def test_label_order_does_not_create_conflict_and_glosses_not_equated(self):
        summary, rows = MODULE.compare([row()], [row(reviewed_emotions="amusement;joy", sense_gloss="Other wording")], [row()])
        self.assertEqual(rows[0]["comparison_status"], "aligned_accept")
        self.assertEqual(summary["gloss_text_identical_count"], 0)
        self.assertEqual(rows[0]["final_decision"], "")

    def test_shared_pending_and_joint_label_change_need_adjudication(self):
        for a, b, expected in [(row(decision="needs_evidence"), row(decision="needs_evidence"), "needs_adjudication"),
                                (row(), row(decision="revise"), "needs_adjudication"),
                                (row(reviewed_emotions="joy"), row(reviewed_emotions="joy"), "joint_label_change")]:
            _, rows = MODULE.compare([a], [b], [row()])
            self.assertEqual(rows[0]["comparison_status"], expected)

    def test_formatting_and_missing_dates_preserved_but_content_changes_rejected(self):
        submitted = row(association_vectors_differ="TRUE")
        self.assertEqual(MODULE.validate([submitted], [row()], {"joy", "amusement"}), ["s1"])
        self.assertEqual(submitted["reviewed_at"], "")
        with self.assertRaises(ValueError):
            MODULE.validate([row(term="different")], [row()], {"joy", "amusement"})
        with self.assertRaises(ValueError):
            MODULE.validate([row(reviewed_emotions="joy;joy")], [row()], {"joy", "amusement"})
        with self.assertRaises(ValueError):
            MODULE.compare([row(), row()], [row()], [row()])


if __name__ == "__main__":
    unittest.main()
