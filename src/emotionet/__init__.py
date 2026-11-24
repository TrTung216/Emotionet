"""Emotionet: Vietnamese lexical-semantic emotion network and feature extraction library."""

from importlib import import_module

from emotionet.core import Emotionet, PublicationError, SnapshotError
from emotionet.normalization import normalize_text
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
    "Emotionet",
    "PublicationError",
    "SnapshotError",
    "normalize_text",
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

__version__ = "0.1.0.dev0"

_OPTIONAL_EXPORTS = {
    **dict.fromkeys(["EMOTION_27_LABELS", "EMOTION_27_TO_IDX", "FeatureExtractor", "FeatureManifest"], "features"),
    **dict.fromkeys(["EmotionetClassifierHead", "ViGoEmotionsDataset", "compute_multilabel_metrics"], "integration"),
}


def __getattr__(name):
    module = _OPTIONAL_EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"emotionet.{module}"), name)
    globals()[name] = value
    return value


def load_snapshot_v2(snapshot_dir: str = "data/local/seed-synsets-v2") -> EmotionetLexicon:
    """Convenience function to load the v2 synsets snapshot."""
    return EmotionetLexicon.from_snapshot(snapshot_dir)
