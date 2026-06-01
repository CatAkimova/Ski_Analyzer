#!/usr/bin/env python3
"""
Создает шаблон labels CSV для baseline-обучения по углам.

По умолчанию сканирует Ski.Videos/*.mp4 и пишет:
  data/angle_labels_template.csv

Поля:
  sample,label,notes

Где:
  - sample: путь к видео/landmarks/angles (можно оставить видео)
  - label: заполняется вручную (например, 0=bad, 1=good)
  - notes: опционально
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

_VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate angle labels CSV template")
    parser.add_argument(
        "--videos-dir",
        type=Path,
        default=Path("Ski.Videos"),
        help="Папка с видео",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/angle_labels_template.csv"),
        help="Выходной CSV",
    )
    args = parser.parse_args()

    videos_dir = args.videos_dir
    out_path = args.out

    if not videos_dir.is_dir():
        raise SystemExit(f"Нет каталога: {videos_dir}")
    files = sorted(
        p for p in videos_dir.iterdir()
        if p.is_file() and p.suffix.lower() in _VIDEO_SUFFIXES
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sample", "label", "notes"])
        w.writeheader()
        for fp in files:
            w.writerow(
                {
                    "sample": str(fp),
                    "label": "",
                    "notes": "",
                }
            )

    print(f"✓ Шаблон сохранен: {out_path}")
    print(f"  Файлов: {len(files)}")
    print("  Заполни колонку label (например: 0=bad, 1=good).")


if __name__ == "__main__":
    main()

