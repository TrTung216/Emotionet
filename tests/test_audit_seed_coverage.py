import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("audit_seed_coverage", Path(__file__).resolve().parents[1] / "scripts/audit_seed_coverage.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def seed(key, term):
    return {"seed_id": key, "term": term, "normalized_form": term,
            "semantic_status": "accepted", "emotion_labels": ["joy"]}


class CoverageTests(unittest.TestCase):
    def test_longest_phrase_does_not_double_count_nested_seed(self):
        summary, per_seed, _ = MODULE.audit([seed("short", "lo"), seed("long", "lo lắng cho")],
                                          [{"id": "1", "text": "Lo lắng cho con, rồi lại lo."}])
        counts = {row["seed_id"]: row for row in per_seed}
        self.assertEqual(counts["short"]["raw_occurrences"], 2)
        self.assertEqual(counts["short"]["longest_occurrences"], 1)
        self.assertEqual(counts["long"]["longest_occurrences"], 1)
        self.assertEqual(summary["rows_with_any_seed"], 1)

    def test_unicode_boundaries_normalization_and_zero_matches(self):
        summary, per_seed, samples = MODULE.audit([seed("v", "vui"), seed("b", "buồn")],
            [{"id": "1", "text": "vuila"}, {"id": "2", "text": "BUO\u0302\u0300N!"},
             {"id": "3", "text": "vuivui"}])
        self.assertEqual(summary["rows_with_any_seed"], 1)
        self.assertEqual(summary["seeds_not_seen_in_train"], ["vui"])
        self.assertEqual(samples[0]["sense_match_decision"], "")

    def test_samples_are_bounded_and_rows_not_occurrences(self):
        summary, per_seed, samples = MODULE.audit([seed("v", "vui")],
            [{"id": str(i), "text": "vui vui vui"} for i in range(5)])
        self.assertEqual(len(samples), 3)
        self.assertEqual(per_seed[0]["raw_matching_rows"], 5)
        self.assertEqual(per_seed[0]["raw_occurrences"], 15)
        with self.assertRaises(ValueError):
            MODULE.audit([seed("v", "vui")], [{"id": "1", "text": "vui"}] * 2)


if __name__ == "__main__":
    unittest.main()
