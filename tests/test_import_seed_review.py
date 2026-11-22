"""Review import boundaries, using synthetic records only."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("import_seed_review", Path(__file__).resolve().parents[1] / "scripts/import_seed_review.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ReviewImportTests(unittest.TestCase):
    def setUp(self):
        self.template, self.reviewed, self.evidence = [], [], []
        for index, decision in enumerate(IMPORTER.DECISIONS):
            row = dict.fromkeys(IMPORTER.FIELDS, "")
            row.update(review_id=f"seed_{index}", term=f"term-{index}", normalized_form=f"term-{index}",
                       proposed_vigoemotions="joy", source_count="0", source_row_count="0", status="candidate")
            self.template.append(row)
            self.reviewed.append({**row, "decision": decision, "reviewed_emotions": "sadness",
                                  "sense_gloss": "Test sense", "reviewer": "test-reviewer",
                                  "reviewed_at": "2026-11-20T09:10:00+07:00", "notes": "Review reason"})
            self.evidence.append({"review_id": row["review_id"], "observations": []})
        self.taxonomy = {"taxonomy_id": "test", "version": "1", "label2id": {"joy": 0, "sadness": 1, "neutral": 2}}

    def validate(self, reviewed=None, evidence=None):
        return IMPORTER.validate(self.template, reviewed if reviewed is not None else self.reviewed,
                                 evidence if evidence is not None else self.evidence, self.taxonomy["label2id"])

    def test_duplicate_missing_and_unknown_ids_fail(self):
        for rows in (self.reviewed[:-1], self.reviewed + [self.reviewed[0]],
                     [{**self.reviewed[0], "review_id": "unknown"}, *self.reviewed[1:]]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.validate(rows)

    def test_immutable_fields_and_invalid_reviews_fail(self):
        for field, value in [("term", "modified"), ("source_count", "2"), ("status", "approved"),
                             ("decision", ""), ("reviewer", ""), ("sense_gloss", ""),
                             ("reviewed_at", "2026-11-20"), ("reviewed_emotions", "joy;joy"),
                             ("reviewed_emotions", "neutral"), ("reviewed_emotions", "unknown")]:
            rows = copy.deepcopy(self.reviewed)
            rows[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.validate(rows)

    def test_mismatched_evidence_fails(self):
        evidence = copy.deepcopy(self.evidence)
        evidence[0]["observations"] = [{"source_id": "test", "normalized_form": "wrong"}]
        with self.assertRaises(ValueError):
            self.validate(evidence=evidence)

    def test_snapshot_uses_only_accept_and_reviewed_labels_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / name for name in ("review.csv", "template.csv", "evidence.jsonl", "taxonomy.json", "sources.json")]
            IMPORTER.write_csv(paths[0], self.reviewed)
            IMPORTER.write_csv(paths[1], self.template)
            IMPORTER.write_jsonl(paths[2], self.evidence)
            paths[3].write_text(json.dumps(self.taxonomy), encoding="utf-8")
            paths[4].write_text('{"source_files": {}}', encoding="utf-8")
            before = {p: p.read_bytes() for p in paths}
            output = root / "data/local/accepted-v1"
            with patch.object(IMPORTER, "ROOT", root):
                summary = IMPORTER.import_review(*paths, output)
                with self.assertRaises(FileExistsError):
                    IMPORTER.import_review(*paths, output)
                with self.assertRaises(ValueError):
                    IMPORTER.import_review(*paths, root / "public")
            seeds = [json.loads(line) for line in (output / "accepted-seeds.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(seeds), 1)
            self.assertEqual(seeds[0]["emotion_labels"], ["sadness"])
            self.assertEqual(seeds[0]["emotion_ids"], [1])
            self.assertEqual(seeds[0]["publication_status"], "not_cleared")
            self.assertIsNone(seeds[0]["synset_id"])
            self.assertEqual(len(IMPORTER.read_csv(output / "pending-review.csv")), 2)
            self.assertEqual(len(IMPORTER.read_csv(output / "rejected-review.csv")), 1)
            self.assertEqual(summary["decisions"], dict.fromkeys(IMPORTER.DECISIONS, 1))
            for path, content in before.items():
                self.assertEqual(path.read_bytes(), content)
            self.assertEqual((output / "submitted-review.csv").read_bytes(), before[paths[0]])
            for name, digest in summary["output_sha256"].items():
                self.assertEqual(IMPORTER.sha256(output / name), digest)


if __name__ == "__main__":
    unittest.main()
