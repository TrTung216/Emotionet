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

    def test_contrastive_negation_scoping_khong_buon_nhung_vui(self):
        """Issue 3 fix: verify negation scope does not leak past contrastive markers."""
        # 1. "không buồn nhưng vui"
        text1 = "không buồn nhưng vui"
        res1 = self.matcher.match(text1)
        spans1 = {s.lemma: s for s in res1.spans}
        self.assertIn("buồn", spans1)
        self.assertIn("vui", spans1)
        self.assertTrue(spans1["buồn"].in_negation_scope)
        self.assertFalse(spans1["vui"].in_negation_scope)

        # 2. "Tôi không vui nhưng rất biết ơn bạn."
        text2 = "Tôi không vui nhưng rất biết ơn bạn."
        res2 = self.matcher.match(text2)
        spans2 = {s.lemma: s for s in res2.spans}
        self.assertIn("vui", spans2)
        self.assertIn("biết ơn", spans2)
        self.assertTrue(spans2["vui"].in_negation_scope)
        self.assertFalse(spans2["biết ơn"].in_negation_scope)

        # 3. "Không buồn, nhưng cũng chẳng vui"
        text3 = "Không buồn, nhưng cũng chẳng vui"
        res3 = self.matcher.match(text3)
        spans3 = {s.lemma: s for s in res3.spans}
        self.assertTrue(spans3["buồn"].in_negation_scope)
        self.assertTrue(spans3["vui"].in_negation_scope)

    def test_sample_prediction_batch_invariance(self):
        """Issue 2 fix: verify sample prediction never changes depending on what other samples are in batch."""
        head = EmotionetClassifierHead(
            hidden_dim=64,
            feature_dim=171,
            num_labels=28,
            projection_dim=32,
            mlp_dim=64,
            dropout=0.0,
        )
        head.eval()

        torch.manual_seed(123)
        h_A = torch.randn(1, 64)
        g_A = torch.zeros(1, 171)  # Sample A has no dictionary features

        h_B = torch.randn(1, 64)
        g_B = torch.randn(1, 171) * 2.0  # Sample B has non-zero features

        with torch.no_grad():
            # Sample A evaluated alone (batch size 1)
            pred_A_alone = head(h_A, g_A)

            # Sample A evaluated together with Sample B (batch size 2)
            h_batch = torch.cat([h_A, h_B], dim=0)
            g_batch = torch.cat([g_A, g_B], dim=0)
            pred_batch = head(h_batch, g_batch)

        # Prediction for sample A must be equivalent within numerical tolerance to presence of sample B in batch
        self.assertTrue(
            torch.allclose(pred_A_alone, pred_batch[0:1], atol=1e-6, rtol=0.0),
            f"Batch invariance failed: diff={torch.max(torch.abs(pred_A_alone - pred_batch[0:1])).item()}",
        )

    def test_dictionary_truncation_no_leakage(self):
        """Issue 1 fix: verify dictionary feature extractor does not read text truncated by tokenizer."""
        # Suppose encoder max_length is 5 tokens/words.
        # Text has filler words first, and emotion word 'hạnh phúc' at word 10.
        text = "hôm nay đi làm về nhà ăn cơm rồi rất hạnh phúc"
        # Word limit = 5 words: "hôm nay đi làm về" (hạnh phúc is cut off)

        from emotionet.integration import truncate_text_to_visible_window

        visible_5 = truncate_text_to_visible_window(text, max_length=5)
        self.assertEqual(visible_5, "hôm nay đi làm về")

        feat_truncated = self.extractor.extract(visible_5)
        feat_full = self.extractor.extract(text)

        # Joy (hạnh phúc) index is 2
        joy_idx = 2
        self.assertEqual(feat_truncated[joy_idx], 0.0)
        self.assertGreater(feat_full[joy_idx], 0.0)

    def test_punctuation_boundary_no_space_buon_khong_vui(self):
        """Issue 3 fix: verify clause punctuation boundary end position correctly excludes punctuation."""
        # Case 1: no space after comma "buồn,không vui"
        text1 = "buồn,không vui"
        res1 = self.matcher.match(text1)
        spans1 = {s.lemma: s for s in res1.spans}
        self.assertIn("buồn", spans1)
        self.assertIn("vui", spans1)
        self.assertFalse(spans1["buồn"].in_negation_scope)
        self.assertTrue(spans1["vui"].in_negation_scope)

        # Case 2: with space after comma "buồn, không vui"
        text2 = "buồn, không vui"
        res2 = self.matcher.match(text2)
        spans2 = {s.lemma: s for s in res2.spans}
        self.assertIn("buồn", spans2)
        self.assertIn("vui", spans2)
        self.assertFalse(spans2["buồn"].in_negation_scope)
        self.assertTrue(spans2["vui"].in_negation_scope)

    def test_khong_ai_ma_vui_vs_khong_buon_ma_vui(self):
        """Issue 3 fix: structural handling of 'mà' (linking vs adversative replacement)."""
        # 1. "không ai mà vui" -> 'vui' must be negated by 'không ai'
        text1 = "không ai mà vui"
        res1 = self.matcher.match(text1)
        spans1 = {s.lemma: s for s in res1.spans}
        self.assertIn("vui", spans1)
        self.assertTrue(spans1["vui"].in_negation_scope)

        # 2. "không buồn mà vui" -> 'buồn' negated, but 'vui' after 'mà' is NOT negated
        text2 = "không buồn mà vui"
        res2 = self.matcher.match(text2)
        spans2 = {s.lemma: s for s in res2.spans}
        self.assertIn("buồn", spans2)
        self.assertIn("vui", spans2)
        self.assertTrue(spans2["buồn"].in_negation_scope)
        self.assertFalse(spans2["vui"].in_negation_scope)

    def test_character_tokenizer_truncation_no_leakage(self):
        """Issue 1 fix: verify fallback does not leak with char tokenizer, max_length=1 on 'buồn vui'."""
        from emotionet.integration import truncate_text_to_visible_window

        text = "buồn vui"
        char_tokenizer_fn = lambda s: list(s)

        # Encoder max_length=1: only sees 'b'
        vis_1 = truncate_text_to_visible_window(text, max_length=1, tokenizer_fn=char_tokenizer_fn)
        self.assertEqual(vis_1, "b")

        feat = self.extractor.extract(vis_1)
        # Sadness (buồn) index is 21
        sadness_idx = 21
        self.assertEqual(feat[sadness_idx], 0.0)

    def test_precomputed_cache_validation_rejects_leak(self):
        """Issue 1 fix: verify ViGoEmotionsDataset rejects cache containing untruncated leakage."""
        import tempfile
        import csv
        from emotionet.integration import ViGoEmotionsDataset

        # Create temporary CSV with 1 sample
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", delete=False, suffix=".csv") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "text", "labels"])
            writer.writerow(["sample_1", "buồn vui", "[21]"])
            tmp_csv = f.name

        try:
            char_tokenizer_fn = lambda s: list(s)
            # Create a dirty cache where sample_1 has sadness=1.0 (from full text)
            dirty_cache = np.zeros((1, 171), dtype=np.float32)
            dirty_cache[0, 21] = 1.0  # sadness

            # Initializing dataset with max_length=1 means visible_text is 'b', which has NO sadness
            # Passing dirty_cache must be detected and rejected with ValueError!
            with self.assertRaises(ValueError) as ctx:
                ViGoEmotionsDataset(
                    csv_path=tmp_csv,
                    max_length=1,
                    tokenizer_fn=char_tokenizer_fn,
                    feature_extractor=self.extractor,
                    precomputed_features=dirty_cache,
                )
            self.assertIn("cache validation failed", str(ctx.exception))
        finally:
            Path(tmp_csv).unlink(missing_ok=True)

    def test_sentencepiece_truncation_end_to_end(self):
        """Issue 1 fix: verify end-to-end dataset truncation with real SentencePiece model."""
        import sys
        import tempfile
        import csv
        from emotionet.integration import ViGoEmotionsDataset

        sp_deps_path = "D:/NCKH_GA+LSTM_Emotion_Recognition/.experiment_deps"
        sp_model_path = "D:/NCKH_GA+LSTM_Emotion_Recognition/results/ga_lstm_xlstm_comparison/tokenizer.model"

        if not Path(sp_model_path).exists():
            self.skipTest("SentencePiece model not found at specified path")

        if sp_deps_path not in sys.path:
            sys.path.insert(0, sp_deps_path)

        try:
            import sentencepiece as spm
            sp = spm.SentencePieceProcessor()
            sp.load(sp_model_path)
        except ImportError:
            self.skipTest("sentencepiece module not available")

        # Create temporary CSV
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", delete=False, suffix=".csv") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "text", "labels"])
            # Sample 1: joy word 'hạnh phúc' at the very beginning
            writer.writerow(["s1", "hạnh phúc ngập tràn", "[2]"])
            # Sample 2: emotion word 'buồn' at the very end after many filler words
            writer.writerow(["s2", "hôm nay tôi đi làm cả ngày rồi sau đó rất buồn", "[21]"])
            tmp_csv = f.name

        try:
            # max_length=4 tokens:
            # s1: "hạnh phúc" fits in 4 tokens -> joy feature present
            # s2: only first 4 tokens visible, "rất buồn" is cut off -> sadness feature must be 0
            dataset = ViGoEmotionsDataset(
                csv_path=tmp_csv,
                tokenizer=sp,
                max_length=4,
                feature_extractor=self.extractor,
            )

            # Check sample 1: joy is idx 2
            feat_s1 = dataset[0]["feature"].numpy()
            self.assertGreater(feat_s1[2], 0.0)

            # Check sample 2: sadness is idx 21
            feat_s2 = dataset[1]["feature"].numpy()
            self.assertEqual(feat_s2[21], 0.0)
            self.assertNotIn("buồn", dataset[1]["text"])
        finally:
            Path(tmp_csv).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
