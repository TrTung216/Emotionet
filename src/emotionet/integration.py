"""PyTorch integration module for Emotionet with GA-xLSTM on ViGoEmotions."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset

from emotionet.features import FeatureExtractor, FeatureManifest


class EmotionetClassifierHead(nn.Module):
    """Classifier head fusing xLSTM pooled representation with Emotionet feature vector."""

    def __init__(
        self,
        hidden_dim: int,
        feature_dim: int = 171,
        num_labels: int = 28,
        projection_dim: int = 64,
        mlp_dim: int = 128,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.feature_dim = feature_dim
        self.num_labels = num_labels
        self.projection_dim = projection_dim

        # Emotionet feature projection branch
        self.feature_proj = nn.Sequential(
            nn.Linear(feature_dim, projection_dim),
            nn.LayerNorm(projection_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Joint classification head: [h; g_proj] -> num_labels logits
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim + projection_dim, mlp_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, num_labels),
        )

    def forward(
        self,
        h: torch.Tensor,
        g: Optional[torch.Tensor] = None,
        column_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            h: Pooled hidden state from xLSTM [B, hidden_dim].
            g: Emotionet features [B, feature_dim]. If None, a zero vector is used.
            column_mask: Boolean/int tensor of shape [feature_dim] or [B, feature_dim].
        
        Returns:
            Logits of shape [B, num_labels].
        """
        batch_size = h.size(0)

        # 1. Determine feature branch activity at chromosome/configuration level
        # This condition is purely a configuration check, NEVER depending on batch contents!
        features_active = True
        if g is None:
            features_active = False
        elif column_mask is not None:
            # Check if any gene in column_mask is active
            if (column_mask > 0).sum() == 0:
                features_active = False

        if not features_active:
            g_proj = torch.zeros(
                (batch_size, self.projection_dim),
                dtype=h.dtype,
                device=h.device,
            )
        else:
            if column_mask is not None:
                g_masked = g * column_mask.to(dtype=g.dtype, device=g.device)
            else:
                g_masked = g

            # Sample-level indicator: strictly per-row [B, 1], independent across batch samples!
            # If a sample has no active features (all 0), its projection is strictly 0.
            sample_active = (g_masked.abs().sum(dim=-1, keepdim=True) > 0).to(dtype=h.dtype)
            g_proj = self.feature_proj(g_masked) * sample_active

        fused = torch.cat([h, g_proj], dim=-1)
        logits = self.classifier(fused)
        return logits


def truncate_text_to_visible_window(
    text: str,
    max_length: int,
    tokenizer: Optional[Any] = None,
    tokenizer_fn: Optional[Callable[[str], List[int]]] = None,
    tokenizer_decode_fn: Optional[Callable[[List[int]], str]] = None,
) -> str:
    """Truncate text strictly to the token window visible to the encoder,
    preventing dictionary features from reading truncated words.
    """
    if max_length <= 0:
        return ""

    if tokenizer is not None and hasattr(tokenizer, "encode") and hasattr(tokenizer, "decode"):
        tokens = tokenizer.encode(text)
        if len(tokens) > max_length:
            return tokenizer.decode(tokens[:max_length])
        return text
    elif tokenizer_fn is not None and tokenizer_decode_fn is not None:
        tokens = tokenizer_fn(text)
        if len(tokens) > max_length:
            return tokenizer_decode_fn(tokens[:max_length])
        return text
    elif tokenizer_fn is not None:
        tokens = tokenizer_fn(text)
        if len(tokens) <= max_length:
            return text

        # Preserve the original prefix, including whitespace. A length check alone
        # is insufficient: re-tokenizing a prefix may change subword IDs, and token
        # counts need not be monotonic. Search conservatively without binary search.
        # Supplying a decoder avoids this potentially expensive fallback.
        visible_tokens = list(tokens[:max_length])
        for end in range(len(text) - 1, 0, -1):
            candidate = text[:end]
            candidate_tokens = list(tokenizer_fn(candidate))
            if (0 < len(candidate_tokens) <= max_length
                    and candidate_tokens == visible_tokens[:len(candidate_tokens)]):
                return candidate
        # No nonempty prefix could be verified against the encoder's tokens.
        return ""
    else:
        # Explicit word-level fallback when no encoder tokenizer was supplied.
        # Use source offsets so leading/repeated whitespace remains unchanged.
        words = list(re.finditer(r"\S+", text))
        if len(words) > max_length:
            return text[:words[max_length - 1].end()]
        return text


def validate_precomputed_features_cache(
    precomputed: Union[np.ndarray, Dict[str, Any]],
    visible_texts: List[str],
    max_length: int,
    feature_extractor: Optional[FeatureExtractor] = None,
    ids: Optional[List[str]] = None,
) -> np.ndarray:
    """Validate every cached column against the current visible-text extractor.

    Without an extractor, row count and max_length cannot establish cache validity.
    Raw arrays remain supported when an extractor is provided.
    """
    if isinstance(precomputed, dict):
        cached_max_len = precomputed.get("max_length")
        if cached_max_len is not None and cached_max_len != max_length:
            raise ValueError(
                f"precomputed_features cache max_length mismatch: cache was created with max_length={cached_max_len}, "
                f"but dataset requested max_length={max_length}."
            )
        cached_ids = precomputed.get("ids")
        if cached_ids is not None and ids is not None and list(cached_ids) != list(ids):
            raise ValueError("precomputed_features cache sample IDs/order mismatch")
        feats = precomputed["features"]
    else:
        feats = precomputed

    if feature_extractor is None:
        raise ValueError("precomputed_features requires feature_extractor to validate the token window")
    feats = np.asarray(feats, dtype=np.float32)
    expected_shape = (len(visible_texts), feature_extractor.manifest.total_dim)
    if feats.shape != expected_shape:
        raise ValueError(f"precomputed_features shape mismatch: {feats.shape}, expected {expected_shape}")
    if not np.isfinite(feats).all():
        raise ValueError("precomputed_features must contain only finite values")

    for i, vis_text in enumerate(visible_texts):
        expected_feat = feature_extractor.extract(vis_text)
        if not np.allclose(feats[i], expected_feat, atol=1e-6, rtol=0.0):
            sample_id = ids[i] if ids else str(i)
            raise ValueError(
                f"precomputed_features cache validation failed at sample {i} (id={sample_id}): "
                "cached features differ from extraction on the current visible text. "
                "Rebuild the cache with the current token window, sample order, lexicon and extractor."
            )

    return feats


class ViGoEmotionsDataset(Dataset):
    """PyTorch Dataset loading ViGoEmotions CSV with multi-hot 28-class targets."""

    def __init__(
        self,
        csv_path: Union[str, Path],
        num_labels: int = 28,
        feature_extractor: Optional[FeatureExtractor] = None,
        precomputed_features: Optional[Union[np.ndarray, Dict[str, Any]]] = None,
        tokenizer: Optional[Any] = None,
        tokenizer_fn: Optional[Callable[[str], List[int]]] = None,
        tokenizer_decode_fn: Optional[Callable[[List[int]], str]] = None,
        max_length: int = 128,
        pad_id: int = 0,
        truncate_dictionary_text: bool = True,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.num_labels = num_labels
        self.feature_extractor = feature_extractor
        self.tokenizer = tokenizer
        self.tokenizer_fn = tokenizer_fn
        self.tokenizer_decode_fn = tokenizer_decode_fn
        self.max_length = max_length
        self.pad_id = pad_id
        self.truncate_dictionary_text = truncate_dictionary_text

        self.ids: List[str] = []
        self.texts: List[str] = []
        self.targets: List[np.ndarray] = []

        self._load_data()

        # Build visible text window to ensure dictionary feature extractor does NOT
        # read text truncated by the tokenizer/encoder.
        if self.truncate_dictionary_text:
            self.visible_texts = [
                truncate_text_to_visible_window(
                    t,
                    self.max_length,
                    tokenizer=self.tokenizer,
                    tokenizer_fn=self.tokenizer_fn,
                    tokenizer_decode_fn=self.tokenizer_decode_fn,
                )
                for t in self.texts
            ]
        else:
            self.visible_texts = list(self.texts)

        if precomputed_features is not None:
            self.features = validate_precomputed_features_cache(
                precomputed_features,
                visible_texts=self.visible_texts,
                max_length=self.max_length,
                feature_extractor=self.feature_extractor,
                ids=self.ids,
            )
        elif feature_extractor is not None:
            self.features = feature_extractor.extract_batch(self.visible_texts)
        else:
            self.features = np.zeros((len(self.texts), 171), dtype=np.float32)

    def _load_data(self) -> None:
        with open(self.csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_id = row["id"]
                text = row["text"]
                raw_labels = row["labels"]

                # Parse JSON labels: list of integer IDs (0..27)
                label_ids = json.loads(raw_labels)

                # Construct idempotent 28-d multi-hot vector
                target_vec = np.zeros(self.num_labels, dtype=np.float32)
                for lid in label_ids:
                    if 0 <= lid < self.num_labels:
                        target_vec[lid] = 1.0

                self.ids.append(item_id)
                self.texts.append(text)
                self.targets.append(target_vec)

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        raw_text = self.texts[idx]
        vis_text = self.visible_texts[idx]
        item: Dict[str, Any] = {
            "id": self.ids[idx],
            "raw_text": raw_text,
            "text": vis_text,
            "target": torch.from_numpy(self.targets[idx]),
            "feature": torch.from_numpy(self.features[idx]),
        }

        if self.tokenizer is not None and hasattr(self.tokenizer, "encode"):
            tokens = self.tokenizer.encode(raw_text)
            if len(tokens) > self.max_length:
                tokens = tokens[:self.max_length]
            mask = [1] * len(tokens)
            if len(tokens) < self.max_length:
                pad_len = self.max_length - len(tokens)
                tokens.extend([self.pad_id] * pad_len)
                mask.extend([0] * pad_len)
            item["input_ids"] = torch.tensor(tokens, dtype=torch.long)
            item["attention_mask"] = torch.tensor(mask, dtype=torch.float32)

        elif self.tokenizer_fn is not None:
            token_ids = self.tokenizer_fn(raw_text)
            # Truncate and pad
            if len(token_ids) > self.max_length:
                token_ids = token_ids[:self.max_length]
            mask = [1] * len(token_ids)
            if len(token_ids) < self.max_length:
                pad_len = self.max_length - len(token_ids)
                token_ids.extend([self.pad_id] * pad_len)
                mask.extend([0] * pad_len)

            item["input_ids"] = torch.tensor(token_ids, dtype=torch.long)
            item["attention_mask"] = torch.tensor(mask, dtype=torch.float32)

            item["input_ids"] = torch.tensor(token_ids, dtype=torch.long)
            item["attention_mask"] = torch.tensor(mask, dtype=torch.float32)

        return item


def compute_multilabel_metrics(
    logits: Union[torch.Tensor, np.ndarray],
    targets: Union[torch.Tensor, np.ndarray],
    threshold: float = 0.5,
    neutral_idx: int = 27,
) -> Dict[str, Any]:
    """Compute Macro-F1, Micro-F1, per-class metrics, and empty-prediction rate."""
    if isinstance(logits, torch.Tensor):
        probs = torch.sigmoid(logits).detach().cpu().numpy()
    else:
        probs = 1.0 / (1.0 + np.exp(-logits))

    if isinstance(targets, torch.Tensor):
        targets_np = targets.detach().cpu().numpy()
    else:
        targets_np = targets

    preds = (probs >= threshold).astype(np.int32)
    targets_int = targets_np.astype(np.int32)

    num_classes = targets_np.shape[1]
    per_class_f1 = np.zeros(num_classes, dtype=np.float32)
    per_class_precision = np.zeros(num_classes, dtype=np.float32)
    per_class_recall = np.zeros(num_classes, dtype=np.float32)
    support = np.sum(targets_int, axis=0)

    tp_total = 0
    fp_total = 0
    fn_total = 0

    for c in range(num_classes):
        tp = int(np.sum((preds[:, c] == 1) & (targets_int[:, c] == 1)))
        fp = int(np.sum((preds[:, c] == 1) & (targets_int[:, c] == 0)))
        fn = int(np.sum((preds[:, c] == 0) & (targets_int[:, c] == 1)))

        tp_total += tp
        fp_total += fp
        fn_total += fn

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        per_class_precision[c] = p
        per_class_recall[c] = r
        per_class_f1[c] = f1

    # Macro-F1 over all 28 classes
    macro_f1_all = float(np.mean(per_class_f1))

    # Macro-F1 over 27 emotion classes (excluding neutral)
    emotion_indices = [c for c in range(num_classes) if c != neutral_idx]
    macro_f1_emotions = float(np.mean(per_class_f1[emotion_indices]))

    # Micro-F1
    micro_p = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
    micro_r = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
    micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    # Empty prediction rate (samples where no label was predicted)
    empty_samples = int(np.sum(np.sum(preds, axis=1) == 0))
    empty_rate = float(empty_samples / preds.shape[0]) if preds.shape[0] > 0 else 0.0

    return {
        "macro_f1_28": macro_f1_all,
        "macro_f1_27_emotions": macro_f1_emotions,
        "micro_f1": micro_f1,
        "per_class_f1": per_class_f1.tolist(),
        "per_class_precision": per_class_precision.tolist(),
        "per_class_recall": per_class_recall.tolist(),
        "support": support.tolist(),
        "empty_prediction_count": empty_samples,
        "empty_prediction_rate": empty_rate,
        "total_samples": int(preds.shape[0]),
    }
