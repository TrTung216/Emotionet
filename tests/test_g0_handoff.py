"""The G0 handoff must not hide conflicting meanings or use non-train context."""

import csv
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_g0_handoff", ROOT / "scripts/prepare_g0_handoff.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class G0HandoffTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.config = json.loads((ROOT / "configs/g0-handoff.json").read_text(encoding="utf-8"))
        paths = ["configs/g0-handoff.json"] + [self.config[k] for k in [
            "seed_source", "sense_source", "context_source", "split_source", "taxonomy_source",
            "sharing_authorization", "seed_selection",
        ]]
        for name in paths:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_conflicting_sense_cannot_reuse_seed_approval(self):
        _, samples, _ = module.construct(self.root)
        path = self.root / self.config["sense_source"]
        rows = module.read_jsonl(path)
        row = next(r for r in rows if r["sense_id"] == samples[0]["sense_id"])
        row["gloss"] = "A different unreviewed meaning"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from approved seed"):
            module.construct(self.root)

    def test_positive_validation_context_is_not_accepted_as_train_evidence(self):
        path = self.root / self.config["context_source"]
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row["split"] = "validation"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "No eligible"):
            module.construct(self.root)


if __name__ == "__main__":
    unittest.main()
