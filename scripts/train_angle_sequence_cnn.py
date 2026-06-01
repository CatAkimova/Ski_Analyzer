#!/usr/bin/env python3
"""
Второй подход ML: классификация по временной последовательности углов (1D CNN).

Те же метки и тот же каталог landmarks, что и у train_angle_baseline.py (--results-dir).
Нормализация (mean/std) считается только по обучающей выборке, затем применяется к test.

Выход: models/angle_sequence_cnn.pt + отчёт (accuracy, confusion matrix, classification_report).

Запуск из корня репозитория:
  PYTHONPATH=. python3 scripts/train_angle_sequence_cnn.py \\
    --results-dir results_yolov8m \\
    --report-out results_yolov8m/angle_sequence_cnn_report.txt \\
    --model-out models/angle_sequence_cnn_yolov8m.pt \\
    --seed 42
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

from ski_analyzer.config.settings import ANGLES, N_RESAMPLE_POINTS
from ski_analyzer.ml.angle_train_data import load_xy_tensors


class AngleSeqCNN(nn.Module):
    """Лёгкая 1D CNN: вход (batch, n_angles, T)."""

    def __init__(self, n_angles: int, seq_len: int, num_classes: int):
        super().__init__()
        self.n_angles = n_angles
        self.seq_len = seq_len
        self.body = nn.Sequential(
            nn.Conv1d(n_angles, 32, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv1d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool1d(1),
        )
        self.head = nn.Linear(64, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.body(x).squeeze(-1)
        return self.head(h)


def _train_val_split_tensors(
    X: np.ndarray,
    y: np.ndarray,
    val_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Отделяет часть train в validation для early stopping (без использования test)."""
    if val_fraction <= 0 or val_fraction >= 0.5:
        n_val = max(1, int(len(X) * 0.15))
    else:
        n_val = max(1, int(len(X) * val_fraction))
    rng = np.random.default_rng(seed)
    idx = np.arange(len(X))
    rng.shuffle(idx)
    val_idx = idx[:n_val]
    train_idx = idx[n_val:]
    return (
        X[train_idx],
        y[train_idx],
        X[val_idx],
        y[val_idx],
        train_idx,
        val_idx,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train 1D CNN on angle sequences")
    parser.add_argument("--labels", type=Path, default=Path("data/angle_labels.csv"))
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--model-out", type=Path, default=Path("models/angle_sequence_cnn.pt"))
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("results/angle_sequence_cnn_report.txt"),
    )
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--val-fraction", type=float, default=0.15, help="Доля train для валидации")
    parser.add_argument("--patience", type=int, default=25, help="Early stopping по val loss")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    labels_path = args.labels if args.labels.is_absolute() else repo_root / args.labels
    model_out = args.model_out if args.model_out.is_absolute() else repo_root / args.model_out
    report_out = args.report_out if args.report_out.is_absolute() else repo_root / args.report_out
    results_root = (
        args.results_dir if args.results_dir.is_absolute() else repo_root / args.results_dir
    )

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    X, y, class_names, bad_samples = load_xy_tensors(labels_path, repo_root, results_root)
    n_angles, T = X.shape[1], X.shape[2]
    assert n_angles == len(ANGLES)
    assert T == N_RESAMPLE_POINTS

    _, counts = np.unique(y, return_counts=True)
    stratify = y if np.all(counts >= 2) else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=stratify,
    )

    X_tr, y_tr, X_val, y_val, _, _ = _train_val_split_tensors(
        X_train, y_train, args.val_fraction, args.seed + 1
    )

    mean = X_tr.mean(axis=0, keepdims=True)
    std = X_tr.std(axis=0, keepdims=True) + 1e-6
    X_tr_n = (X_tr - mean) / std
    X_val_n = (X_val - mean) / std
    X_test_n = (X_test - mean) / std

    num_classes = int(y.max()) + 1
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ds_tr = TensorDataset(
        torch.from_numpy(X_tr_n).float(),
        torch.from_numpy(y_tr).long(),
    )
    ds_val = TensorDataset(
        torch.from_numpy(X_val_n).float(),
        torch.from_numpy(y_val).long(),
    )
    dl_tr = DataLoader(ds_tr, batch_size=min(args.batch_size, len(ds_tr)), shuffle=True)
    dl_val = DataLoader(ds_val, batch_size=min(args.batch_size, len(ds_val)), shuffle=False)

    model = AngleSeqCNN(n_angles=n_angles, seq_len=T, num_classes=num_classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    crit = nn.CrossEntropyLoss()

    best_state = None
    best_val = float("inf")
    bad_epochs = 0

    for epoch in range(args.epochs):
        model.train()
        loss_tr = 0.0
        for xb, yb in dl_tr:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()
            loss_tr += loss.item() * xb.size(0)
        loss_tr /= len(ds_tr)

        model.eval()
        loss_val = 0.0
        with torch.no_grad():
            for xb, yb in dl_val:
                xb, yb = xb.to(device), yb.to(device)
                logits = model(xb)
                loss_val += crit(logits, yb).item() * xb.size(0)
        loss_val /= max(1, len(ds_val))

        if loss_val < best_val - 1e-5:
            best_val = loss_val
            bad_epochs = 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    X_test_t = torch.from_numpy(X_test_n).float().to(device)
    with torch.no_grad():
        logits = model(X_test_t)
        y_pred = logits.argmax(dim=1).cpu().numpy()

    y_test_str = np.array([class_names[i] for i in y_test])
    y_pred_str = np.array([class_names[i] for i in y_pred])

    acc = accuracy_score(y_test_str, y_pred_str)
    cm = confusion_matrix(y_test_str, y_pred_str, labels=class_names)
    report = classification_report(y_test_str, y_pred_str, labels=class_names, digits=4)

    model_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)

    torch.save(
        {
            "state_dict": model.state_dict(),
            "mean": mean,
            "std": std,
            "class_names": class_names,
            "n_angles": n_angles,
            "seq_len": T,
            "angles_order": list(ANGLES),
        },
        model_out,
    )

    with report_out.open("w", encoding="utf-8") as f:
        f.write(f"Method: 1D CNN on angle sequences (channels={n_angles}, T={T})\n")
        f.write(f"Landmarks dir: {results_root}\n")
        f.write(f"Train (fit) samples: {len(X_train)}\n")
        f.write(f"Test samples: {len(X_test)}\n")
        f.write(f"Classes: {class_names}\n")
        f.write(f"Device: {device}\n")
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write("Confusion matrix:\n")
        f.write(str(cm))
        f.write("\n\nClassification report:\n")
        f.write(report)
        if bad_samples:
            f.write("\n\nSkipped samples (load):\n")
            for s, err in bad_samples:
                f.write(f"- {s}: {err}\n")

    print(f"✓ Model saved: {model_out}")
    print(f"✓ Report saved: {report_out}")
    print(f"Accuracy: {acc:.4f}")
    print(f"Used samples: {len(X)} (skipped {len(bad_samples)})")


if __name__ == "__main__":
    main()
