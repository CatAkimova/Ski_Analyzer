#!/usr/bin/env python3
"""
Baseline-обучение классификатора по углам (RandomForest).

Вход:
  labels CSV (по умолчанию data/angle_labels.csv) с колонками:
    sample,label
  sample может быть:
    - путь к видео (.mp4/.mov) -> landmarks в --results-dir (по умолчанию results/), в т.ч. results/Ski.Videos/<stem>_landmarks.csv
    - путь к *_landmarks.csv
    - путь к *_angles_resampled.csv
    - просто stem (например Ski1) -> ищет results/Ski1_landmarks.csv

Выход:
  - models/angle_baseline_rf.joblib
  - results/angle_baseline_report.txt
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from ski_analyzer.core.angle_calculator import AngleCalculator
from ski_analyzer.core.data_processor import DataProcessor
from ski_analyzer.config.settings import ANGLES


def _read_labels(labels_path: Path) -> pd.DataFrame:
    df = pd.read_csv(labels_path)
    if "sample" not in df.columns or "label" not in df.columns:
        raise ValueError("labels CSV должен содержать колонки: sample,label")
    df = df.dropna(subset=["sample", "label"]).copy()
    df["sample"] = df["sample"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip()
    df = df[(df["sample"] != "") & (df["label"] != "")]
    return df


def _resolve_sample_to_resampled(
    sample: str, repo_root: Path, results_root: Path
) -> pd.DataFrame:
    sample_path = Path(sample)
    if not sample_path.is_absolute():
        sample_path = repo_root / sample_path

    angle_calc = AngleCalculator()
    data_proc = DataProcessor()

    # 1) already resampled angles
    if sample_path.exists() and sample_path.name.endswith("_angles_resampled.csv"):
        return pd.read_csv(sample_path, sep=";")

    # 2) landmarks CSV
    if sample_path.exists() and sample_path.name.endswith("_landmarks.csv"):
        angles_df = angle_calc.process_file(str(sample_path), output_path=None)
        return data_proc.process_angles(angles_df)

    # 3) video path -> find landmarks under results_root (run_pose_batch кладёт results/Ski.Videos/<stem>_landmarks.csv)
    candidates: List[Path] = []
    stem = sample_path.stem if sample_path.suffix else sample_path.name
    try:
        rel_parent = sample_path.relative_to(repo_root).parent
    except ValueError:
        rel_parent = Path()

    candidates.append(results_root / f"{stem}_angles_resampled.csv")
    candidates.append(results_root / f"{stem}_landmarks.csv")
    if rel_parent != Path():
        candidates.append(results_root / rel_parent / f"{stem}_angles_resampled.csv")
        candidates.append(results_root / rel_parent / f"{stem}_landmarks.csv")

    for c in candidates:
        if c.exists():
            if c.name.endswith("_angles_resampled.csv"):
                return pd.read_csv(c, sep=";")
            angles_df = angle_calc.process_file(str(c), output_path=None)
            return data_proc.process_angles(angles_df)

    raise FileNotFoundError(
        f"Не удалось разрешить sample='{sample}'. "
        f"Ожидается путь к video/landmarks/angles или файлы под {results_root}/ "
        f"(в т.ч. {results_root}/<папка видео>/{stem}_landmarks.csv)."
    )


def _extract_features(resampled_df: pd.DataFrame) -> Dict[str, float]:
    feats: Dict[str, float] = {}
    for col in ANGLES:
        if col not in resampled_df.columns:
            continue
        s = (
            resampled_df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
            .values
        )
        if len(s) == 0:
            continue
        feats[f"{col}_mean"] = float(np.mean(s))
        feats[f"{col}_std"] = float(np.std(s))
        feats[f"{col}_min"] = float(np.min(s))
        feats[f"{col}_max"] = float(np.max(s))
        feats[f"{col}_range"] = float(np.max(s) - np.min(s))
        feats[f"{col}_q25"] = float(np.quantile(s, 0.25))
        feats[f"{col}_q75"] = float(np.quantile(s, 0.75))
        feats[f"{col}_first"] = float(s[0])
        feats[f"{col}_last"] = float(s[-1])
        feats[f"{col}_delta"] = float(s[-1] - s[0])
    return feats


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline RF by angle features")
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("data/angle_labels.csv"),
        help="CSV с колонками sample,label",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Доля теста",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Где лежат *_landmarks.csv от run_pose_batch (для сравнения разных YOLO — разные каталоги)",
    )
    parser.add_argument(
        "--model-out",
        type=Path,
        default=Path("models/angle_baseline_rf.joblib"),
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("results/angle_baseline_report.txt"),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    labels_path = args.labels if args.labels.is_absolute() else repo_root / args.labels
    model_out = args.model_out if args.model_out.is_absolute() else repo_root / args.model_out
    report_out = args.report_out if args.report_out.is_absolute() else repo_root / args.report_out
    results_root = (
        args.results_dir if args.results_dir.is_absolute() else repo_root / args.results_dir
    )

    df_labels = _read_labels(labels_path)
    if len(df_labels) < 6:
        raise ValueError("Нужно хотя бы 6 размеченных примеров для baseline.")

    rows = []
    y = []
    bad_samples = []
    for _, r in df_labels.iterrows():
        sample = r["sample"]
        label = r["label"]
        try:
            resampled = _resolve_sample_to_resampled(sample, repo_root, results_root)
            feats = _extract_features(resampled)
            if not feats:
                bad_samples.append((sample, "empty_features"))
                continue
            rows.append(feats)
            y.append(label)
        except Exception as e:
            bad_samples.append((sample, str(e)))

    if len(rows) < 6:
        raise ValueError(
            f"Слишком мало валидных примеров: {len(rows)}. Проблемные sample: {bad_samples[:5]}"
        )

    X = pd.DataFrame(rows).fillna(0.0)
    y_arr = np.array(y)

    # stratify только если в каждом классе >= 2 примеров
    _, counts = np.unique(y_arr, return_counts=True)
    stratify = y_arr if np.all(counts >= 2) else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_arr,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=stratify,
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=args.seed,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=4)

    model_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "feature_columns": list(X.columns)}, model_out)

    with report_out.open("w", encoding="utf-8") as f:
        f.write(f"Landmarks dir: {results_root}\n")
        f.write(f"Train samples: {len(X_train)}\n")
        f.write(f"Test samples: {len(X_test)}\n")
        f.write(f"Features: {X.shape[1]}\n")
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write("Confusion matrix:\n")
        f.write(str(cm))
        f.write("\n\nClassification report:\n")
        f.write(report)
        if bad_samples:
            f.write("\n\nSkipped samples:\n")
            for s, err in bad_samples:
                f.write(f"- {s}: {err}\n")

    print(f"✓ Model saved: {model_out}")
    print(f"✓ Report saved: {report_out}")
    print(f"Accuracy: {acc:.4f}")
    print(f"Used samples: {len(rows)} (skipped {len(bad_samples)})")


if __name__ == "__main__":
    main()

