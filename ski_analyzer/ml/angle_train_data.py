"""Общая загрузка разметки и resampled-углов для скриптов обучения."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from ski_analyzer.config.settings import ANGLES, N_RESAMPLE_POINTS


def load_train_angle_baseline_module(repo_root: Path):
    """Загружает scripts/train_angle_baseline.py как модуль (доступ к _read_labels, _resolve_sample_to_resampled)."""
    path = repo_root / "scripts" / "train_angle_baseline.py"
    spec = importlib.util.spec_from_file_location("train_angle_baseline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось загрузить {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resampled_df_to_tensor(df: pd.DataFrame, target_len: int = N_RESAMPLE_POINTS) -> np.ndarray:
    """DataFrame resampled углов -> массив (n_angles, T) float32; при другой длине — линейная интерполяция по времени."""
    cols = [c for c in ANGLES if c in df.columns]
    if not cols:
        raise ValueError("В resampled нет ни одной колонки из ANGLES")
    series = []
    for col in ANGLES:
        if col not in df.columns:
            series.append(np.zeros(len(df), dtype=np.float64))
        else:
            s = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .astype(float)
                .values
            )
            series.append(s.astype(np.float64))
    x = np.stack(series, axis=0)  # (C, T_raw)
    _, t_raw = x.shape
    if t_raw == target_len:
        return x.astype(np.float32)
    t_old = np.linspace(0.0, 1.0, t_raw)
    t_new = np.linspace(0.0, 1.0, target_len)
    out = np.zeros((len(ANGLES), target_len), dtype=np.float32)
    for c in range(len(ANGLES)):
        out[c] = np.interp(t_new, t_old, x[c]).astype(np.float32)
    return out


def load_xy_tensors(
    labels_path: Path,
    repo_root: Path,
    results_root: Path,
) -> Tuple[np.ndarray, np.ndarray, List[str], List[Tuple[str, str]]]:
    """
    Возвращает:
      X: (N, C, T), y: (N,) int 0..K-1, class_names по порядку id,
      bad_samples: [(sample, err), ...]
    """
    mod = load_train_angle_baseline_module(repo_root)
    df_labels = mod._read_labels(labels_path)
    if len(df_labels) < 6:
        raise ValueError("Нужно хотя бы 6 размеченных примеров.")

    raw_labels: List[str] = []
    tensors: List[np.ndarray] = []
    bad_samples: List[Tuple[str, str]] = []

    for _, r in df_labels.iterrows():
        sample = r["sample"]
        label = str(r["label"]).strip()
        try:
            resampled = mod._resolve_sample_to_resampled(sample, repo_root, results_root)
            t = resampled_df_to_tensor(resampled)
            tensors.append(t)
            raw_labels.append(label)
        except Exception as e:
            bad_samples.append((sample, str(e)))

    if len(tensors) < 6:
        raise ValueError(
            f"Слишком мало валидных примеров: {len(tensors)}. Первые ошибки: {bad_samples[:5]}"
        )

    classes = sorted(set(raw_labels))
    label_to_id = {c: i for i, c in enumerate(classes)}
    y = np.array([label_to_id[L] for L in raw_labels], dtype=np.int64)
    X = np.stack(tensors, axis=0)
    return X, y, classes, bad_samples
