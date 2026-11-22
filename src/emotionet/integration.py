"""PyTorch integration module for Emotionet with GA-xLSTM on ViGoEmotions."""

from __future__ import annotations

import csv
import json
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
            column_mask: Boolean tensor of shape [feature_dim] or [B, feature_dim].
        
        Returns:
            Logits of shape [B, num_labels].
        """
        batch_size = h.size(0)

        if g is None:
            g = torch.zeros(
                (batch_size, self.feature_dim),
                dtype=h.dtype,
                device=h.device,
            )
            g_proj = torch.zeros(
                (batch_size, self.projection_dim),
                dtype=h.dtype,
                device=h.device,
            )
        else:
            if column_mask is not None:
                # Mask out inactive features
                g = g * column_mask.to(dtype=g.dtype, device=g.device)

            # Check if feature vector is completely inactive (e.g. all-zero mask)
            if g.abs().sum() == 0:
                g_proj = torch.zeros(
                    (batch_size, self.projection_dim),
                    dtype=h.dtype,
                    device=h.device,
                )
            else:
                g_proj = self.feature_proj(g)

        fused = torch.cat([h, g_proj], dim=-1)
        logits = self.classifier(fused)
        return logits


class ViGoEmotionsDataset(Dataset):
    """PyTorch Dataset loading ViGoEmotions CSV with multi-hot 28-class targets."""

    def __init__(
        self,
        csv_path: Union[str, Path],
        num_labels: int = 28,
        feature_extractor: Optional[FeatureExtractor] = None,
        precomputed_features: Optional[np.ndarray] = None,
        tokenizer_fn: Optional[Callable[[str], List[int]]] = None,
        max_length: int = 128,
        pad_id: int = 0,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.num_labels = num_labels
        self.feature_extractor = feature_extractor
        self.tokenizer_fn = tokenizer_fn
        self.max_length = max_length
        self.pad_id = pad_id

        self.ids: List[str] = []
        self.texts: List[str] = []
        self.targets: List[np.ndarray] = []

        self._load_data()

        if precomputed_features is not None:
            if len(precomputed_features) != len(self.texts):
                raise ValueError(
                    f"Precomputed features length {len(precomputed_features)} does not match dataset length {len(self.texts)}"
                )
            self.features = precomputed_features
        elif feature_extractor is not None:
            self.features = feature_extractor.extract_batch(self.texts)
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
        item: Dict[str, Any] = {
            "id": self.ids[idx],
            "text": self.texts[idx],
            "target": torch.from_numpy(self.targets[idx]),
            "feature": torch.from_numpy(self.features[idx]),
        }

        if self.tokenizer_fn is not None:
            token_ids = self.tokenizer_fn(self.texts[idx])
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
