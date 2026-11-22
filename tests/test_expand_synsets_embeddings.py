import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from expand_synsets_embeddings import eligible_candidate, fuse_seed_phrases, read_train, stable_hash


class ExpansionTests(unittest.TestCase):
    def test_seed_phrase_fusion_keeps_boundary_and_longest_order(self):
        patterns = {"lo_lắng": [(("lo_lắng", "cho"), "lo_lắng_cho"), (("lo_lắng",), "lo_lắng")]}
        self.assertEqual(fuse_seed_phrases(["lo_lắng", "cho", "con"], patterns), ["lo_lắng_cho", "con"])
        self.assertEqual(fuse_seed_phrases(["lo_lắng", ",", "cho", "con"], patterns), ["lo_lắng", ",", "cho", "con"])

    def test_candidate_filter_excludes_seeds_rare_terms_and_nonwords(self):
        config = {"min_candidate_count": 5, "stop_tokens": ["và"]}
        self.assertTrue(eligible_candidate("vui_vẻ", 7, {"vui"}, config))
        for token, count in [("vui", 20), ("hiếm", 1), ("và", 100), ("123", 50), ("!", 7)]:
            self.assertFalse(eligible_candidate(token, count, {"vui"}, config))
        self.assertEqual(stable_hash("vui"), stable_hash("vui"))

    def test_inner_train_ids_and_no_label_access(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "text", "labels"])
                writer.writeheader()
                writer.writerows([{"id": "1", "text": "first", "labels": "deliberately invalid"},
                                  {"id": "2", "text": "second", "labels": "not used"}])
            ids = Path(directory) / "ids.json"
            ids.write_text(json.dumps(["2"]), encoding="utf-8")
            self.assertEqual(read_train(path, ids), [{"id": "2", "text": "second"}])
            ids.write_text(json.dumps(["outside_train"]), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_train(path, ids)
            with self.assertRaises(ValueError):
                read_train(Path(directory) / "test.csv")


if __name__ == "__main__":
    unittest.main()
