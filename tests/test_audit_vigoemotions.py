"""Synthetic cases for structural audit; no private dataset needed."""

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "audit_vigoemotions", Path(__file__).resolve().parents[1] / "scripts" / "audit_vigoemotions.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AuditTests(unittest.TestCase):
    def test_multilabel_neutral_duplicates_and_unicode(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.csv"
            rows = [
                {"id": "1", "text": "Tôi vui", "labels": "[2, 27, 2]"},
                {"id": "2", "text": "  TO\u0302I   vui ", "labels": "[2, 27]"},
                {"id": "2", "text": "Tôi vui", "labels": "[2]"},
                {"id": "4", "text": "sample", "labels": "[true]"},
                {"id": "5", "text": "sample2", "labels": "[28]"},
                {"id": "6", "text": "sample3", "labels": "[2.0]"},
                {"id": "7", "text": "sample4", "labels": "[]"},
                {"id": "8", "text": "sample5", "labels": "broken"},
                {"id": "", "text": " ", "labels": "[2]"},
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "text", "labels"])
                writer.writeheader()
                writer.writerows(rows)
            before = path.read_bytes()
            report, _, _ = AUDIT.audit_split(path, dict(enumerate(str(i) for i in range(28))))
            self.assertEqual(report["rows"], 9)
            self.assertEqual(report["issues"]["neutral_with_emotion_rows"], 2)
            self.assertEqual(report["issues"]["repeated_label_ids_rows"], 1)
            self.assertEqual(report["issues"]["invalid_label_values_rows"], 4)
            self.assertEqual(report["issues"]["invalid_labels_json_rows"], 1)
            self.assertEqual(report["issues"]["empty_id_rows"], 1)
            self.assertEqual(report["issues"]["empty_text_rows"], 1)
            self.assertEqual(report["duplicate_id_rows_beyond_first"], 1)
            self.assertEqual(report["normalized_duplicate_text_rows_beyond_first"], 2)
            self.assertEqual(report["normalized_text_groups_with_different_label_sets"], 1)
            self.assertEqual(report["label_support"]["2"], 4)
            self.assertEqual(report["multi_label_rows"], 2)
            self.assertNotIn("Tôi vui", json.dumps(report, ensure_ascii=False))
            self.assertEqual(path.read_bytes(), before)

    def test_wrong_columns_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.csv"
            path.write_text("id,text,label\n1,sample,2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                AUDIT.audit_split(path, {2: "joy"})


if __name__ == "__main__":
    unittest.main()
