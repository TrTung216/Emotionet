"""Emotionet: Vietnamese lexical-semantic emotion network and feature extraction library."""

from emotionet.features import (
    EMOTION_27_LABELS,
    EMOTION_27_TO_IDX,
    FeatureExtractor,
    FeatureManifest,
)
from emotionet.integration import (
    EmotionetClassifierHead,
    ViGoEmotionsDataset,
    compute_multilabel_metrics,
)
from emotionet.matcher import MatchResult, PhraseMatcher
from emotionet.models import (
    EmotionAnnotation,
    EmotionetLexicon,
    Entry,
    MatchSpan,
    Relation,
    Sense,
    Synset,
)

__all__ = [
    "EmotionAnnotation",
    "Sense",
    "Entry",
    "Synset",
    "Relation",
    "MatchSpan",
    "EmotionetLexicon",
    "PhraseMatcher",
    "MatchResult",
    "FeatureExtractor",
    "FeatureManifest",
    "EMOTION_27_LABELS",
    "EMOTION_27_TO_IDX",
    "EmotionetClassifierHead",
    "ViGoEmotionsDataset",
    "compute_multilabel_metrics",
    "load_snapshot_v2",
]


def load_snapshot_v2(snapshot_dir: str = "data/local/seed-synsets-v2") -> EmotionetLexicon:
    """Convenience function to load the v2 synsets snapshot."""
    return EmotionetLexicon.from_snapshot(snapshot_dir)
