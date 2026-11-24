# -*- coding: utf-8 -*-
"""Test seed-synsets-v3 snapshot fidelity, WordNet invariants, and Core API integration."""

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))

from emotionet import Emotionet

class SynsetsV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "test_v3.sqlite"
        self.net = Emotionet.open(self.db_path, mode="research")
        self.addCleanup(self.net.close)
        self.v3_path = ROOT / "data/local/seed-synsets-v3"

    def test_v3_import_and_fidelity(self):
        counts = self.net.import_jsonl(self.v3_path)
        self.assertEqual(counts["entries"], 100)
        self.assertEqual(counts["senses"], 106)
        self.assertEqual(counts["concepts"], 91)
        self.assertEqual(counts["relations"], 35)
        self.assertEqual(counts["evidence"], 150)
        
        # Verify POS on all entries in records
        cursor = self.net._db.cursor()
        cursor.execute("SELECT COUNT(*) FROM records WHERE kind='entry' AND json_extract(payload, '$.pos') IS NULL")
        self.assertEqual(cursor.fetchone()[0], 0)
        
        # Verify 5 is_a relations
        cursor.execute("SELECT COUNT(*) FROM relations WHERE predicate='is_a'")
        self.assertEqual(cursor.fetchone()[0], 5)
        
        # Verify 30 related_to relations
        cursor.execute("SELECT COUNT(*) FROM relations WHERE predicate='related_to'")
        self.assertEqual(cursor.fetchone()[0], 30)
        
        # Verify syn_tui_than separation
        cursor.execute("SELECT id FROM concepts WHERE id='syn_tui_than'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Verify syn_kieng_ne separation
        cursor.execute("SELECT id FROM concepts WHERE id='syn_kieng_ne'")
        self.assertIsNotNone(cursor.fetchone())

if __name__ == "__main__":
    unittest.main()
