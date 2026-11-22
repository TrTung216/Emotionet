"""Feature extraction and grouping (F1-F8) for Emotionet ViGoEmotions GA-xLSTM."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from emotionet.matcher import MatchResult, PhraseMatcher
from emotionet.models import EmotionetLexicon

# 27 active emotion labels (excluding neutral which is at index 27)
EMOTION_27_LABELS = [
    "amusement", "excitement", "joy", "love", "desire", "optimism",
    "caring", "pride", "admiration", "gratitude", "relief", "approval",
    "realization", "surprise", "curiosity", "confusion", "fear", "nervousness",
    "remorse", "embarrassment", "disappointment", "sadness", "grief", "disgust",
    "anger", "annoyance", "disapproval",
]

EMOTION_27_TO_IDX = {label: i for i, label in enumerate(EMOTION_27_LABELS)}


@dataclass
class FeatureManifest:
    """Detailed metadata and column breakdown for the F1-F8 feature schema."""
    version: str = "vigoemotions-f1-f8-v1"
    total_dim: int = 171
    num_groups: int = 8
    group_names: List[str] = field(default_factory=lambda: [
        "F1_normalized_counts",
        "F2_binary_presence",
        "F3_multiword_matches",
        "F4_emoji_emoticon_matches",
        "F5_negated_matches",
        "F6_intensity_interactions",
        "F7_discourse_punctuation",
        "F8_coverage_meta",
    ])
    group_ranges: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        "F1": (0, 27),
        "F2": (27, 54),
        "F3": (54, 81),
        "F4": (81, 109),
        "F5": (109, 136),
        "F6": (136, 164),
        "F7": (164, 167),
        "F8": (167, 171),
    })

    def get_column_mask(self, group_mask: Sequence[Union[int, bool]]) -> np.ndarray:
        """Expand an 8-bit chromosome into a boolean column mask of length 171."""
        if len(group_mask) != 8:
            raise ValueError(f"group_mask must have 8 elements, got {len(group_mask)}")

        col_mask = np.zeros(self.total_dim, dtype=bool)
        for i, is_active in enumerate(group_mask):
            if is_active:
                group_key = f"F{i+1}"
                start, end = self.group_ranges[group_key]
                col_mask[start:end] = True
        return col_mask


class FeatureExtractor:
    """Extracts 171-dimensional F1-F8 feature vector from text matching results."""

    def __init__(
        self,
        matcher: PhraseMatcher,
        manifest: Optional[FeatureManifest] = None,
    ) -> None:
        self.matcher = matcher
        self.manifest = manifest or FeatureManifest()
        self.emotion_labels = EMOTION_27_LABELS
        self.emotion_to_idx = EMOTION_27_TO_IDX

    def extract_from_result(self, result: MatchResult) -> np.ndarray:
        """Compute the full 171-d float32 feature vector from a MatchResult."""
        vector = np.zeros(self.manifest.total_dim, dtype=np.float32)

        words = result.text.split()
        num_words = max(1, len(words))
        char_len = max(1, len(result.text))

        # F1: Normalized counts per 27 emotions (0..26)
        f1_counts = np.zeros(27, dtype=np.float32)
        for span in result.spans:
            for emo in span.emotion_labels:
                if emo in self.emotion_to_idx:
                    f1_counts[self.emotion_to_idx[emo]] += 1.0
        vector[0:27] = f1_counts / num_words

        # F2: Binary presence flags per 27 emotions (27..53)
        vector[27:54] = (f1_counts > 0).astype(np.float32)

        # F3: Multi-word phrase matches per 27 emotions (54..80)
        f3_counts = np.zeros(27, dtype=np.float32)
        for span in result.spans:
            if span.is_multiword:
                for emo in span.emotion_labels:
                    if emo in self.emotion_to_idx:
                        f3_counts[self.emotion_to_idx[emo]] += 1.0
        vector[54:81] = f3_counts

        # F4: Emoji/emoticon matches (81..108 = 27 emotions + 1 unmapped)
        f4_emojis = np.zeros(28, dtype=np.float32)
        for _, emo in result.emoji_matches:
            if emo in self.emotion_to_idx:
                f4_emojis[self.emotion_to_idx[emo]] += 1.0
        f4_emojis[27] = float(result.unmapped_emoji_count)
        vector[81:109] = f4_emojis

        # F5: Negation-scoped matches per 27 emotions (109..135)
        f5_neg = np.zeros(27, dtype=np.float32)
        for span in result.negated_spans:
            for emo in span.emotion_labels:
                if emo in self.emotion_to_idx:
                    f5_neg[self.emotion_to_idx[emo]] += 1.0
        vector[109:136] = f5_neg

        # F6: Intensity interactions (136..163 = 27 emotions + 1 total intensity count)
        f6_int = np.zeros(28, dtype=np.float32)
        total_intensity_mods = 0
        for span in result.intensified_spans:
            weight = 1.5 if span.intensity_modifier == "high" else 0.5
            total_intensity_mods += 1
            for emo in span.emotion_labels:
                if emo in self.emotion_to_idx:
                    f6_int[self.emotion_to_idx[emo]] += weight
        f6_int[27] = float(total_intensity_mods)
        vector[136:164] = f6_int

        # F7: Discourse / syntactic markers (164..166 = 3 dims)
        # [contrastive_count, repeated_punct_count, elongated_char_count]
        vector[164] = float(result.contrastive_count)
        vector[165] = float(result.repeated_punct_count)
        vector[166] = float(result.elongated_char_count)

        # F8: Coverage & ambiguity meta-stats (167..170 = 4 dims)
        # [coverage_ratio, ambiguous_matches, total_matches, zero_matches_flag]
        matched_chars = sum(s.end_char - s.start_char for s in result.spans)
        coverage_ratio = min(1.0, matched_chars / char_len)
        ambiguous_matches = sum(1 for s in result.spans if len(s.emotion_labels) > 1)
        total_matches = len(result.spans) + len(result.emoji_matches)
        zero_matches_flag = 1.0 if total_matches == 0 else 0.0

        vector[167] = float(coverage_ratio)
        vector[168] = float(ambiguous_matches)
        vector[169] = float(total_matches)
        vector[170] = float(zero_matches_flag)

        return vector

    def extract(self, text: str) -> np.ndarray:
        """Match text and return 171-d feature vector."""
        res = self.matcher.match(text)
        return self.extract_from_result(res)

    def extract_batch(self, texts: Sequence[str]) -> np.ndarray:
        """Extract feature matrix of shape [N, 171]."""
        batch_vecs = [self.extract(t) for t in texts]
        if batch_vecs:
            return np.stack(batch_vecs, axis=0)
        return np.zeros((0, self.manifest.total_dim), dtype=np.float32)
