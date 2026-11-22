"""Unit tests for Emotionet core library models, matcher, features, and integration."""

import unittest
from pathlib import Path

import numpy as np
import torch

from emotionet import (
    EmotionetClassifierHead,
    EmotionetLexicon,
    FeatureExtractor,
    FeatureManifest,
    PhraseMatcher,
    compute_multilabel_metrics,
    load_snapshot_v2,
)


class TestEmotionetLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.snapshot_dir = Path("data/local/seed-synsets-v2")
        cls.lexicon = load_snapshot_v2(str(cls.snapshot_dir))
        cls.matcher = PhraseMatcher(cls.lexicon)
        cls.extractor = FeatureExtractor(cls.matcher)

    def test_snapshot_v2_counts(self):
        """Verify snapshot v2 data integrity."""
        self.assertEqual(len(self.lexicon.entries), 77)
        self.assertEqual(len(self.lexicon.senses), 82)
        self.assertEqual(len(self.lexicon.synsets), 66)
        self.assertEqual(len(self.lexicon.relations), 29)

    def test_phrase_matching_longest(self):
        """Verify longest phrase matching takes precedence."""
        text = "Mẹ luôn lo lắng cho con khi đi học xa nhà."
        res = self.matcher.match(text)
        matched_lemmas = [s.lemma for s in res.spans]
        self.assertIn("lo lắng cho", matched_lemmas)
        # Verify it didn't match the substring 'lo' as a separate span overlapping 'lo lắng cho'
        self.assertEqual(len(res.spans), 1)

    def test_negation_scope(self):
        """Verify negation particles flag in_negation_scope."""
        text = "Câu chuyện này không buồn cười chút nào."
        res = self.matcher.match(text)
        self.assertEqual(len(res.spans), 1)
        span = res.spans[0]
        self.assertEqual(span.lemma, "buồn cười")
        self.assertTrue(span.in_negation_scope)
        self.assertEqual(len(res.negated_spans), 1)

    def test_intensity_modifiers(self):
        """Verify intensity modifiers are detected."""
        text = "Tôi rất vui khi gặp lại bạn bè, vui lắm."
        res = self.matcher.match(text)
        # Should detect "rất vui" and "vui lắm"
        self.assertGreaterEqual(len(res.intensified_spans), 1)
        self.assertEqual(res.spans[0].intensity_modifier, "high")

    def test_emoji_and_discourse(self):
        """Verify emoji matching and punctuation markers."""
        text = "Hôm nay vui quáaa :)) 😂 nhưng mai lại thi rồi ???"
        res = self.matcher.match(text)
        self.assertGreaterEqual(len(res.emoji_matches), 2)
        self.assertGreaterEqual(res.repeated_punct_count, 1)  # ???
        self.assertGreaterEqual(res.elongated_char_count, 1)  # quáaa
        self.assertGreaterEqual(res.contrastive_count, 1)     # nhưng

    def test_feature_manifest_and_extraction(self):
        """Verify 171-d vector structure and 8-bit group masking."""
        manifest = FeatureManifest()
        self.assertEqual(manifest.total_dim, 171)

        # Test group mask expansion
        col_mask = manifest.get_column_mask([1, 0, 0, 0, 0, 0, 0, 0])  # Only F1
        self.assertEqual(col_mask.sum(), 27)
        self.assertTrue(np.all(col_mask[0:27]))
        self.assertFalse(np.any(col_mask[27:]))

        # Test feature extraction vector
        text = "Tôi rất yêu thương gia đình và thấy hạnh phúc :))"
        feat = self.extractor.extract(text)
        self.assertEqual(feat.shape, (171,))
        self.assertEqual(feat.dtype, np.float32)

        # F1/F2 should have non-zero for love (idx 3) and joy (idx 2)
        love_idx = 3
        joy_idx = 2
        self.assertGreater(feat[love_idx], 0.0)
        self.assertEqual(feat[27 + love_idx], 1.0)
        self.assertEqual(feat[27 + joy_idx], 1.0)

    def test_pytorch_classifier_head_forward(self):
        """Verify EmotionetClassifierHead forward pass with and without features."""
        head = EmotionetClassifierHead(
            hidden_dim=64,
            feature_dim=171,
            num_labels=28,
            projection_dim=32,
            mlp_dim=64,
        )

        batch_size = 4
        h = torch.randn(batch_size, 64)
        g = torch.randn(batch_size, 171)

        # 1. Forward with both h and g
        out1 = head(h, g)
        self.assertEqual(out1.shape, (batch_size, 28))

        # 2. Forward without g (baseline equivalent)
        out2 = head(h, None)
        self.assertEqual(out2.shape, (batch_size, 28))

        # 3. Forward with 8-bit group mask
        manifest = FeatureManifest()
        col_mask = torch.from_numpy(manifest.get_column_mask([1, 1, 0, 0, 0, 0, 0, 0]))
        out3 = head(h, g, column_mask=col_mask)
        self.assertEqual(out3.shape, (batch_size, 28))

    def test_multilabel_metrics(self):
        """Verify metric evaluation over 28 classes."""
        # 2 samples, 28 classes
        logits = torch.zeros(2, 28)
        # Sample 0 predicts class 0 and 1
        logits[0, 0] = 3.0
        logits[0, 1] = 3.0
        # Sample 1 predicts nothing (all negative)
        logits[1, :] = -5.0

        targets = torch.zeros(2, 28)
        targets[0, 0] = 1.0
        targets[1, 1] = 1.0

        metrics = compute_multilabel_metrics(logits, targets, threshold=0.5)
        self.assertIn("macro_f1_28", metrics)
        self.assertIn("macro_f1_27_emotions", metrics)
        self.assertIn("micro_f1", metrics)
        self.assertEqual(metrics["total_samples"], 2)
        self.assertEqual(metrics["empty_prediction_count"], 1)
        self.assertEqual(metrics["empty_prediction_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
