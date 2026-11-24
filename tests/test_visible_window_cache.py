"""Regression tests for cache validation and source-preserving token windows."""

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from emotionet import FeatureExtractor, PhraseMatcher, load_snapshot_v2
from emotionet.integration import (
    ViGoEmotionsDataset,
    truncate_text_to_visible_window,
    validate_precomputed_features_cache,
)


class VisibleWindowCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot = Path(__file__).resolve().parents[1] / "data/local/seed-synsets-v2"
        cls.extractor = FeatureExtractor(PhraseMatcher(load_snapshot_v2(str(snapshot))))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def dataset(self, text, **kwargs):
        path = Path(self.temp.name) / "sample.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["id", "text", "labels"])
            writer.writerow(["sample", text, "[2]"])
        return ViGoEmotionsDataset(path, feature_extractor=self.extractor, **kwargs)

    def test_character_window_preserves_leading_and_internal_whitespace(self):
        for text, limit in [("  vui buồn", 3), ("a\t\n  vui buồn", 6), ("buồn vui", 1)]:
            with self.subTest(text=text):
                ds = self.dataset(text, tokenizer_fn=lambda s: list(map(ord, s)), max_length=limit)
                item = ds[0]
                self.assertEqual(item["text"], text[:limit])
                self.assertEqual(item["input_ids"].tolist(), list(map(ord, text[:limit])))
                self.assertEqual(float(item["feature"][2]), 0.0)
                self.assertEqual(float(item["feature"][21]), 0.0)

    def test_word_fallback_preserves_source_offsets(self):
        self.assertEqual(
            truncate_text_to_visible_window(" \t hôm\n  nay vui", 2),
            " \t hôm\n  nay",
        )
        self.assertEqual(truncate_text_to_visible_window("  vui", 0), "")

    def test_equal_token_count_does_not_prove_prefix_identity(self):
        # A prefix gets a different token after re-tokenization. Returning it
        # solely because it fits would introduce a word absent from the encoder.
        def encode(text):
            return {"vui buồn": [10, 20], "vui": [99]}.get(text, [98])

        self.assertEqual(
            truncate_text_to_visible_window("vui buồn", 1, tokenizer_fn=encode), ""
        )

    def test_fallback_does_not_assume_monotonic_token_counts(self):
        def encode(text):
            return {"abcd": [1, 2, 3], "abc": [1], "ab": [7, 8], "a": [1]}[text]

        self.assertEqual(truncate_text_to_visible_window("abcd", 1, tokenizer_fn=encode), "abc")

    def test_cache_rejects_hidden_emotion_when_visible_emotion_remains(self):
        text = "vui buồn"
        encode = lambda s: [{"vui": 1, "buồn": 2}[w] for w in s.split()]
        decode = lambda ids: " ".join({1: "vui", 2: "buồn"}[i] for i in ids)
        dirty = {"features": self.extractor.extract_batch([text]), "max_length": 1}
        with self.assertRaisesRegex(ValueError, "cache validation failed"):
            self.dataset(text, tokenizer_fn=encode, tokenizer_decode_fn=decode,
                         max_length=1, precomputed_features=dirty)
        clean = {"features": self.extractor.extract_batch(["vui"]), "max_length": 1,
                 "ids": ["sample"]}
        ds = self.dataset(text, tokenizer_fn=encode, tokenizer_decode_fn=decode,
                          max_length=1, precomputed_features=clean)
        self.assertEqual(ds[0]["text"], "vui")
        self.assertGreater(float(ds[0]["feature"][2]), 0.0)
        self.assertEqual(float(ds[0]["feature"][21]), 0.0)

    def test_cache_checks_columns_in_every_feature_group(self):
        clean = self.extractor.extract_batch(["vui"])
        for column in [0, 27, 54, 81, 109, 136, 164, 167, 170]:
            with self.subTest(column=column):
                dirty = clean.copy()
                dirty[0, column] += 1.0
                with self.assertRaisesRegex(ValueError, "cache validation failed"):
                    validate_precomputed_features_cache(dirty, ["vui"], 1, self.extractor)

    def test_cache_rejects_wrong_shape_nonfinite_and_metadata(self):
        clean = self.extractor.extract_batch(["vui"])
        for dirty in [clean[:, :54], np.full((1, 171), np.nan), np.full((1, 171), np.inf)]:
            with self.subTest(shape=dirty.shape):
                with self.assertRaises(ValueError):
                    validate_precomputed_features_cache(dirty, ["vui"], 1, self.extractor)
        for cache in [
            {"features": clean, "max_length": 2},
            {"features": clean, "ids": ["different_sample"]},
        ]:
            with self.assertRaises(ValueError):
                validate_precomputed_features_cache(cache, ["vui"], 1, self.extractor, ["sample"])

    def test_cache_cannot_be_certified_without_extractor(self):
        with self.assertRaisesRegex(ValueError, "requires feature_extractor"):
            validate_precomputed_features_cache(np.zeros((1, 171)), ["vui"], 1)


if __name__ == "__main__":
    unittest.main()
