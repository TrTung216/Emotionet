"""Core acceptance tests: real snapshot fidelity and adversarial imports."""

import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from emotionet import Emotionet, PublicationError, SnapshotError, normalize_text


class CoreTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db_path = self.root / "core.sqlite"
        self.net = Emotionet.open(self.db_path, mode="research")
        self.addCleanup(self.net.close)

    def snapshot(self, source="data/local/seed-synsets-v2"):
        path = self.root / "input"
        shutil.copytree(ROOT / source, path)
        return path

    def alter(self, path, filename, change):
        rows = [json.loads(line) for line in (path / filename).read_text(encoding="utf-8").splitlines() if line]
        change(rows)
        (path / filename).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        # Deliberately make a new unsigned test snapshot, not a stale signed one.
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        manifest.pop("output_sha256", None)
        (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def assert_empty(self):
        self.assertTrue(all(count == 0 for count in self.net.stats().values()))
        self.assertEqual(self.net.manifest, {})

    def test_real_v2_roundtrip_preserves_every_byte_and_reopens(self):
        source = ROOT / "data/local/seed-synsets-v2"
        counts = self.net.import_jsonl(source)
        self.assertEqual(counts, dict(entries=77, forms=0, senses=82, concepts=66, relations=29, evidence=90))
        target = self.net.export_jsonl(self.root / "export")
        self.assertEqual({p.name: p.read_bytes() for p in source.iterdir()},
                         {p.name: p.read_bytes() for p in target.iterdir()})
        with Emotionet.open(self.db_path, mode="research") as reopened:
            self.assertEqual(reopened.lookup("khó chịu"), self.net.lookup("khó chịu"))
        with Emotionet.open(self.root / "second.sqlite", mode="research") as second:
            self.assertEqual(second.import_jsonl(target), counts)
            self.assertEqual(second.lookup("ghét"), self.net.lookup("ghét"))

    def test_vietnamese_normalization_polysemy_and_multilabel(self):
        self.net.import_jsonl(ROOT / "data/local/seed-synsets-v2")
        result = self.net.lookup("  KHÓ\t CHỊU \n")
        self.assertEqual(result, self.net.lookup(unicodedata.normalize("NFD", "khó chịu")))
        self.assertEqual(result[0]["senses"][0]["sense"]["emotion_labels"], ["annoyance"])
        self.assertEqual(self.net.lookup("kho chiu"), [])
        self.assertEqual(self.net.lookup("unknown term"), [])
        for term in ["thương", "lo", "tiếc", "ghét"]:
            self.assertGreaterEqual(sum(len(e["senses"]) for e in self.net.lookup(term)), 2, term)
        labels = self.net.lookup("yêu thương")[0]["senses"][0]["sense"]["emotion_labels"]
        self.assertEqual(set(labels), {"love", "caring"})

    def test_legacy_aliases_and_incoming_edges(self):
        self.net.import_jsonl(ROOT / "data/seeds/g0")
        forms = [json.loads(line) for line in (ROOT / "data/seeds/g0/forms.jsonl").read_text(encoding="utf-8").splitlines()]
        alias = next(f for f in forms if f["form_type"] != "canonical")
        hit = self.net.lookup(alias["surface"])
        self.assertEqual(hit[0]["entry"]["entry_id"], alias["entry_id"])
        edge = json.loads((ROOT / "data/seeds/g0/relations.jsonl").read_text(encoding="utf-8").splitlines()[0])
        incoming = self.net.relations(edge["object_id"], direction="in", predicate=edge["predicate"])
        self.assertIn(edge, [r["relation"] for r in incoming])
        self.assertIsNotNone(self.net.get_concept(edge["subject_id"]))
        self.assertIsNone(self.net.get_concept("missing"))

    def test_unresolved_relations_stay_proposals(self):
        self.net.import_jsonl(ROOT / "data/local/seed-synsets-v2")
        row = json.loads((ROOT / "data/local/seed-synsets-v2/relations.jsonl").read_text(encoding="utf-8").splitlines()[0])
        result = self.net.relations(row["subject_synset_id"])
        self.assertTrue(result)
        self.assertTrue(all(r["state"] == "needs_review" and not r["resolved"] for r in result))
        self.assertEqual(self.net.relations(row["object_term"], direction="in"), [])

    def test_default_mode_does_not_promote_reviewed_research(self):
        self.net.import_jsonl(ROOT / "data/local/seed-synsets-v2")
        with Emotionet.open(self.db_path) as approved:
            self.assertEqual(approved.lookup("khó chịu"), [])
            self.assertIsNone(approved.get_concept(self.net.lookup("khó chịu")[0]["senses"][0]["sense"]["synset_id"]))
            with self.assertRaises(PublicationError):
                approved.export_jsonl(self.root / "release")
        self.assertFalse((self.root / "release").exists())

    def test_stale_checksums_rejected_before_writes(self):
        path = self.snapshot()
        with (path / "entries.jsonl").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(SnapshotError, "checksum"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_missing_reference_rolls_back_and_allows_retry(self):
        path = self.snapshot()
        self.alter(path, "relations.jsonl", lambda rows: rows[-1].update(subject_synset_id="absent"))
        with self.assertRaisesRegex(SnapshotError, "integrity"):
            self.net.import_jsonl(path)
        self.assert_empty()
        self.net.import_jsonl(ROOT / "data/local/seed-synsets-v2")
        self.assertEqual(self.net.stats()["senses"], 82)

    def test_duplicate_id_rejected(self):
        path = self.snapshot()
        self.alter(path, "entries.jsonl", lambda rows: rows.append(rows[0]))
        with self.assertRaisesRegex(SnapshotError, "integrity"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_dangling_evidence_rejected(self):
        path = self.snapshot()
        self.alter(path, "senses.jsonl", lambda rows: rows[0].update(evidence_ids=["absent"]))
        with self.assertRaisesRegex(SnapshotError, "integrity"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_membership_mismatch_rejected(self):
        path = self.snapshot()
        self.alter(path, "synsets.jsonl", lambda rows: rows[0].update(member_sense_ids=[]))
        with self.assertRaisesRegex(SnapshotError, "member_sense_ids"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_hierarchy_cycle_rejected(self):
        path = self.snapshot("data/seeds/g0")
        def cycle(rows):
            edge = rows[0]
            rows.append(dict(edge, rel_id="rel_cycle", subject_id=edge["object_id"], object_id=edge["subject_id"]))
        self.alter(path, "relations.jsonl", cycle)
        with self.assertRaisesRegex(SnapshotError, "Cycle"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_normalized_key_must_match_surface(self):
        path = self.snapshot()
        self.alter(path, "entries.jsonl", lambda rows: rows[0].update(normalized_form="incorrect"))
        with self.assertRaisesRegex(SnapshotError, "normalized_form"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_no_overwriting_import_or_export(self):
        self.net.import_jsonl(ROOT / "data/local/seed-synsets-v2")
        before = self.net.lookup("ghét")
        with self.assertRaisesRegex(SnapshotError, "already contains"):
            self.net.import_jsonl(ROOT / "data/seeds/g0")
        self.assertEqual(self.net.lookup("ghét"), before)
        target = self.net.export_jsonl(self.root / "output")
        with self.assertRaises(FileExistsError):
            self.net.export_jsonl(target)

    def test_sqlite_foreign_keys_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.net._db.execute("INSERT INTO senses VALUES ('bad','missing','missing')")
        self.net._db.rollback()

    def test_core_import_does_not_import_optional_ml(self):
        code = "import sys; sys.path.insert(0,sys.argv[1]); from emotionet import Emotionet; assert 'torch' not in sys.modules; assert 'numpy' not in sys.modules; Emotionet.open().close()"
        subprocess.run([sys.executable, "-S", "-c", code, str(ROOT / "src")], check=True, capture_output=True)

    def test_invalid_inputs_and_non_emotionet_database(self):
        with self.assertRaises(ValueError):
            Emotionet.open(mode="guess")
        with self.assertRaises(TypeError):
            normalize_text(None)
        with self.assertRaises(ValueError):
            self.net.relations("x", direction="sideways")
        with self.assertRaises(SnapshotError):
            self.net.export_jsonl(self.root / "empty")
        other = self.root / "other.sqlite"
        with sqlite3.connect(other) as db:
            db.execute("CREATE TABLE other(value TEXT)")
        db.close()
        with self.assertRaises(SnapshotError):
            Emotionet.open(other)

    def test_manifest_counts_cannot_silently_drift(self):
        path = self.snapshot()
        self.alter(path, "relations.jsonl", lambda rows: rows.pop())
        with self.assertRaisesRegex(SnapshotError, "count mismatch"):
            self.net.import_jsonl(path)
        self.assert_empty()
        (path / "relations.jsonl").unlink()
        with self.assertRaisesRegex(SnapshotError, "count mismatch"):
            self.net.import_jsonl(path)
        self.assert_empty()

    def test_approved_path_and_unreviewed_alias_filter(self):
        # Synthetic approvals exercise policy logic, not approvals of real data.
        path = self.root / "approved-fixture"
        path.mkdir()
        approval = dict(status="approved", reviewer="test-reviewer", reviewed_at="2026-01-01", evidence_ids=["ev1"])
        records = {
            "concepts": [dict(approval, concept_id="c1", preferred_label="mừng", definition="test meaning")],
            "entries": [dict(approval, entry_id="e1", lemma="mừng", normalized_form="mừng", lang="vi", pos=None)],
            "senses": [dict(approval, sense_id="s1", entry_id="e1", concept_id="c1", gloss="test meaning")],
            "evidence": [dict(evidence_id="ev1", status="approved", reviewer="test-reviewer", reviewed_at="2026-01-01")],
            "forms": [dict(form_id="f1", entry_id="e1", surface="alias", normalized_form="alias", form_type="abbreviation", status="candidate")],
        }
        for name, rows in records.items():
            (path / (name + ".jsonl")).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        (path / "manifest.json").write_text(json.dumps(dict(schema_version=1, publication_status="cleared")), encoding="utf-8")
        self.net.import_jsonl(path)
        self.assertTrue(self.net.lookup("alias"))
        with Emotionet.open(self.db_path) as approved:
            self.assertTrue(approved.lookup("mừng"))
            self.assertEqual(approved.lookup("alias"), [])
            self.assertIsNotNone(approved.get_concept("c1"))
            with self.assertRaises(PublicationError):
                approved.export_jsonl(self.root / "blocked")
        (path / "forms.jsonl").write_text("", encoding="utf-8")
        with Emotionet.open(self.root / "approved.sqlite") as approved:
            approved.import_jsonl(path)
            self.assertEqual(approved.publication_issues(), [])
            approved.export_jsonl(self.root / "approved-export")

    def test_record_rights_cannot_be_overridden_by_manifest(self):
        path = self.snapshot()
        self.alter(path, "entries.jsonl", lambda rows: None)
        manifest_path = path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["publication_status"] = "cleared"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.net.import_jsonl(path)
        self.assertTrue(any("publication restrictions" in issue for issue in self.net.publication_issues()))

    def test_duplicate_json_keys_rejected(self):
        path = self.snapshot()
        (path / "manifest.json").write_text('{"schema_version":1,"schema_version":2}', encoding="utf-8")
        with self.assertRaisesRegex(SnapshotError, "duplicate JSON key"):
            self.net.import_jsonl(path)
        self.assert_empty()


if __name__ == "__main__":
    unittest.main()
