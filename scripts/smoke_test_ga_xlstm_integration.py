"""Smoke test and integration verification for Emotionet + GA-xLSTM on ViGoEmotions."""

import json
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

from emotionet import (
    EmotionetClassifierHead,
    EmotionetLexicon,
    FeatureExtractor,
    FeatureManifest,
    PhraseMatcher,
    ViGoEmotionsDataset,
    compute_multilabel_metrics,
    load_snapshot_v2,
)


def run_smoke_test():
    print("=" * 60)
    print("EMOTIONET + GA-xLSTM INTEGRATION SMOKE TEST")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 1. Load Snapshot v2
    snapshot_dir = Path("data/local/seed-synsets-v2")
    lexicon = load_snapshot_v2(str(snapshot_dir))
    print(f"Loaded Snapshot v2: {len(lexicon.entries)} entries, {len(lexicon.synsets)} synsets, {len(lexicon.relations)} relations.")

    # 2. Build Matcher and Feature Extractor
    matcher = PhraseMatcher(lexicon)
    extractor = FeatureExtractor(matcher)
    manifest = FeatureManifest()
    print(f"Feature Extractor ready: {manifest.total_dim} dimensions, {manifest.num_groups} feature groups (F1-F8).")

    # 3. Load sample from ViGoEmotions
    vigo_val_path = Path("D:/NCKH_GA+LSTM_Emotion_Recognition/data_external/ViGoEmotions/val.csv")
    if not vigo_val_path.exists():
        print(f"Warning: {vigo_val_path} not found, using dummy data.")
        return

    dataset = ViGoEmotionsDataset(
        csv_path=vigo_val_path,
        num_labels=28,
        feature_extractor=extractor,
    )
    print(f"Loaded ViGoEmotions validation split: {len(dataset)} samples.")

    # Select a small batch for smoke test
    batch_size = 16
    batch_features = torch.from_numpy(dataset.features[:batch_size]).to(device)
    batch_targets = torch.stack([dataset[i]["target"] for i in range(batch_size)]).to(device)

    # Simulated xLSTM pooled embeddings [B, 64]
    hidden_dim = 64
    torch.manual_seed(42)
    mock_pooled_h = torch.randn(batch_size, hidden_dim, device=device, requires_grad=True)

    # 4. Instantiate EmotionetClassifierHead
    head = EmotionetClassifierHead(
        hidden_dim=hidden_dim,
        feature_dim=manifest.total_dim,
        num_labels=28,
        projection_dim=32,
        mlp_dim=64,
        dropout=0.1,
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()

    # 5. Test different GA chromosome configurations
    test_chromosomes = [
        ("Baseline (All 0s)", [0, 0, 0, 0, 0, 0, 0, 0]),
        ("Full Lexicon (All 1s)", [1, 1, 1, 1, 1, 1, 1, 1]),
        ("F1+F2+F5 (Counts, Presence, Negation)", [1, 1, 0, 0, 1, 0, 0, 0]),
        ("F1+F6+F7 (Counts, Intensity, Discourse)", [1, 0, 0, 0, 0, 1, 1, 0]),
    ]

    print("\nEvaluating GA chromosomes (Forward + Backward pass):")
    for name, chrom in test_chromosomes:
        col_mask = torch.from_numpy(manifest.get_column_mask(chrom)).to(device)
        active_dims = col_mask.sum().item()

        head.zero_grad()
        if mock_pooled_h.grad is not None:
            mock_pooled_h.grad.zero_()

        # Forward
        logits = head(mock_pooled_h, batch_features, column_mask=col_mask)
        loss = criterion(logits, batch_targets)

        # Backward
        loss.backward(retain_graph=True)

        # Metrics
        metrics = compute_multilabel_metrics(logits, batch_targets, threshold=0.5)

        print(f"  - [{name}]")
        print(f"    Active dims: {active_dims}/171 | Loss: {loss.item():.4f}")
        print(f"    Macro-F1 (28): {metrics['macro_f1_28']:.4f} | Macro-F1 (27 emo): {metrics['macro_f1_27_emotions']:.4f} | Micro-F1: {metrics['micro_f1']:.4f}")
        print(f"    Empty preds: {metrics['empty_prediction_count']}/{batch_size} ({metrics['empty_prediction_rate']*100:.1f}%)")

    print("\nSmoke test passed successfully!")


if __name__ == "__main__":
    run_smoke_test()
