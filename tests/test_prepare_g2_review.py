"""The G2 work packet must preserve source decisions without approving proposals."""

import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_g2_review", ROOT / "scripts/prepare_g2_review.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rows(content):
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


class G2ReviewTests(unittest.TestCase):
    def test_frozen_provenance_and_no_fabricated_approvals(self):
        outputs, summary = module.construct()
        self.assertEqual((summary["synsets"], summary["senses"], summary["relations"], summary["is_a_proposals"]), (66, 82, 29, 18))
        self.assertEqual(summary["new_approved_records"], 0)
        manifest = json.loads(outputs["manifest.json"])
        for name, checksum in manifest["source_sha256"].items():
            self.assertEqual(module.digest((ROOT / name).read_bytes()), checksum)
            self.assertEqual(outputs["references/" + name], (ROOT / name).read_bytes())
        for name in ["synset-review.csv", "relation-review.csv", "is-a-pilot-review.csv"]:
            for row in rows(outputs[name]):
                self.assertEqual(row["state"], "pending")
                for key in module.REVIEW_FIELDS:
                    self.assertEqual(row[key], "")

    def test_relation_join_preserves_reject_and_does_not_choose_target(self):
        outputs, _ = module.construct()
        original = {r["candidate_id"]: r for r in rows(outputs["references/" + module.CANDIDATES])}
        pending = rows(outputs["relation-review.csv"])
        self.assertEqual(len(pending), 29)
        for row in pending:
            source = original[row["source_candidate_id"]]
            for key in ["decision", "relation", "reviewer", "reviewed_at", "example_id", "example_text", "notes"]:
                self.assertEqual(row["source_" + key], source[key])
            self.assertEqual(row["resolved_object_synset_id"], "")
            self.assertEqual(row["final_predicate"], "")
            if row["source_predicate"] == "antonym_of":
                self.assertEqual(row["source_decision"], "reject")
                self.assertIn("reject_synonym_does_not_approve_antonym", row["review_focus"])
        self.assertEqual(sum(r["target_status"] == "no_existing_synset" for r in pending), 28)

    def test_pilot_uses_distinct_existing_sense_groups_and_keeps_alternatives(self):
        outputs, _ = module.construct()
        synsets = {r["synset_id"]: r for r in module.read_jsonl(outputs["references/" + module.SNAPSHOT + "/synsets.jsonl"])}
        pilot = rows(outputs["is-a-pilot-review.csv"])
        pairs = set()
        for row in pilot:
            child, parent = row["subject_synset_id"], row["object_synset_id"]
            self.assertNotEqual(child, parent)
            self.assertEqual(row["subject_definition"], synsets[child]["definition"])
            self.assertEqual(row["object_definition"], synsets[parent]["definition"])
            self.assertIn("no_relation", row["alternatives"])
            self.assertEqual(row["final_predicate"], "")
            pairs.add((child, parent))
        self.assertEqual(len(pairs), 18)
        self.assertTrue(any(row["case_type"] == "boundary_case" for row in pilot))

    def test_existing_review_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / module.DEFAULT_OUTPUT
            target.mkdir(parents=True)
            sentinel = target / "synset-review.csv"
            sentinel.write_bytes(b"human changes")
            with self.assertRaises(FileExistsError):
                module.build(root)
            self.assertEqual(sentinel.read_bytes(), b"human changes")

    def test_untraceable_source_stops_before_output_creation(self):
        outputs, _ = module.construct()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in outputs.items():
                if name.startswith("references/"):
                    target = root / name.removeprefix("references/")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
            path = root / module.CANDIDATES
            source = rows(path.read_bytes())
            path.write_bytes(module.csv_bytes([r for r in source if r["relation"] != "antonym"]))
            with self.assertRaisesRegex(ValueError, "uniquely trace"):
                module.build(root)
            self.assertFalse((root / module.DEFAULT_OUTPUT).exists())


if __name__ == "__main__":
    unittest.main()
