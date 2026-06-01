#!/usr/bin/env python3
"""
Строит data/angle_labels.csv из двух каталогов: хорошие / плохие ролики.

Пути к видео записываются относительно текущей директории запуска (как в train_angle_baseline).

Пример:
  python scripts/build_angle_labels_from_folders.py
  python scripts/build_angle_labels_from_folders.py --out data/angle_labels.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

# pathlib.glob("*.mp4") не находит Bad8.MP4 на регистрозависимых ФС — сравниваем суффикс в нижнем регистре
_VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})


def _collect_videos(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    files: list[Path] = []
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in _VIDEO_SUFFIXES:
            files.append(p)
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Собрать angle_labels.csv из Ski.Videos (good) и Bad.Videos (bad)"
    )
    parser.add_argument(
        "--good-dir",
        type=Path,
        default=Path("Ski.Videos"),
        help="Каталог с корректной техникой",
    )
    parser.add_argument(
        "--bad-dir",
        type=Path,
        default=Path("Bad.Videos"),
        help="Каталог с ошибками техники",
    )
    parser.add_argument(
        "--good-label",
        default="1.0",
        help="Метка для good-dir (как в train_angle_baseline)",
    )
    parser.add_argument(
        "--bad-label",
        default="0.0",
        help="Метка для bad-dir",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/angle_labels.csv"),
        help="Итоговый CSV",
    )
    args = parser.parse_args()

    good_files = _collect_videos(args.good_dir)
    bad_files = _collect_videos(args.bad_dir)

    if not good_files and not bad_files:
        raise SystemExit(
            f"Нет видео в {args.good_dir} и {args.bad_dir}. Проверь пути и форматы файлов."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sample", "label", "notes"])
        w.writeheader()
        for fp in good_files:
            w.writerow(
                {
                    "sample": str(fp),
                    "label": args.good_label,
                    "notes": "",
                }
            )
        for fp in bad_files:
            w.writerow(
                {
                    "sample": str(fp),
                    "label": args.bad_label,
                    "notes": "",
                }
            )

    print(f"✓ Записано: {args.out}")
    print(f"  {args.good_dir}: {len(good_files)} файлов -> label={args.good_label}")
    print(f"  {args.bad_dir}: {len(bad_files)} файлов -> label={args.bad_label}")
    print(f"  Всего строк: {len(good_files) + len(bad_files)}")


if __name__ == "__main__":
    main()
