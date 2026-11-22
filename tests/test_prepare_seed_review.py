"""Import invariants tested without redistributing either lexicon."""

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("prepare_seed_review", Path(__file__).resolve().parents[1] / "scripts/prepare_seed_review.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class SeedImportTests(unittest.TestCase):
    def test_missing_flag_stays_unknown(self):
        self.assertIsNone(IMPORTER.binary(""))
        self.assertEqual(IMPORTER.binary("0"), 0)
        self.assertEqual(IMPORTER.binary("1"), 1)
        for value in ("0.6", "true", "2", "N/A"):
            with self.assertRaises(ValueError):
                IMPORTER.binary(value)

    def test_nrc_translation_collisions_keep_separate_observations(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "nrc.zip"
            header = ["English Word", *IMPORTER.CATEGORIES, "Vietnamese Word"]
            flags = ["0"] * len(IMPORTER.CATEGORIES)
            joy = flags.copy()
            joy[IMPORTER.CATEGORIES.index("joy")] = "1"
            content = "\n".join("\t".join(row) for row in [header, ["term-a", *flags, "Vui"], ["term-b", *joy, " vui "]])
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("NRC/OneFilePerLanguage/Vietnamese-NRC-EmoLex.txt", content)
            rows = IMPORTER.read_nrc(archive)
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]["source_locator"], rows[1]["source_locator"])
            self.assertEqual(rows[0]["normalized_form"], rows[1]["normalized_form"])
            self.assertEqual(rows[0]["associations"]["joy"], 0)
            self.assertEqual(rows[1]["associations"]["joy"], 1)
            self.assertEqual(IMPORTER.summarize(rows)["forms_with_differing_association_vectors"], 1)
            self.assertTrue(all(row["status"] == "candidate" for row in rows))

    def test_workbook_keeps_sparse_columns_and_missing_flag(self):
        namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        headers = {"B": "Vietnamese", "C": "Positive", "D": "Negative", "E": "Anger", "F": "Anticipation",
                   "G": "Disgust", "H": "Fear", "I": "Joy", "J": "Sadness", "K": "Surprise", "L": "Trust"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.xlsx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("xl/workbook.xml", f'<workbook xmlns="{namespace}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" r:id="rId1"/></sheets></workbook>')
                archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                head = ''.join(f'<c r="{column}1" t="inlineStr"><is><t>{value}</t></is></c>' for column, value in headers.items())
                # Column E is absent, rather than empty; I stays Joy, not shifted.
                values = ''.join(f'<c r="{column}2"><v>{1 if column == "I" else 0}</v></c>' for column in "CDFGHIJKL")
                row = '<c r="B2" t="inlineStr"><is><t>vui</t></is></c>' + values + '<c r="M2"><f>SUM(C2:L2)</f><v>1</v></c>'
                archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{namespace}"><sheetData><row r="1">{head}</row><row r="2">{row}</row></sheetData></worksheet>')
            rows = IMPORTER.read_vn(path)
            self.assertIsNone(rows[0]["associations"]["anger"])
            self.assertEqual(rows[0]["associations"]["joy"], 1)
            self.assertEqual(rows[0]["missing_categories"], ["anger"])

    def test_output_cannot_escape_private_directory(self):
        with self.assertRaises(ValueError):
            IMPORTER.prepare(Path("missing"), Path("missing"), Path("missing"), IMPORTER.ROOT / "data/seeds/public")


if __name__ == "__main__":
    unittest.main()
