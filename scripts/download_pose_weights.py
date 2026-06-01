#!/usr/bin/env python3
"""
Скачивает веса YOLO-pose в корень репозитория (рядом с yolov8n-pose.pt в settings).

Запуск:
  python scripts/download_pose_weights.py
  python scripts/download_pose_weights.py --only yolov8n-pose.pt yolov8s-pose.pt
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Те же имена, что в compare_pose_models.py / compare_pose_backends.py
DEFAULT_WEIGHTS = [
    "yolov8n-pose.pt",
    "yolov8s-pose.pt",
    "yolov8m-pose.pt",
    "yolov8l-pose.pt",
    "yolov8x-pose.pt",
    "yolo11n-pose.pt",
    "yolo11s-pose.pt",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Скачать только перечисленные файлы (имена как в Ultralytics)",
    )
    args = parser.parse_args()
    weights = args.only if args.only else DEFAULT_WEIGHTS

    os.chdir(REPO_ROOT)
    print(f"Каталог загрузки: {REPO_ROOT}\n")

    from ultralytics import YOLO

    for name in weights:
        print(f"Загрузка/проверка: {name} ...", flush=True)
        try:
            model = YOLO(name)
            # Лёгкий прогон — кэш и файлы подтянутся
            _ = model.task
        except Exception as e:
            print(f"  ОШИБКА {name}: {e}", flush=True)
            continue
        # Ultralytics кладёт .pt в cwd при первом скачивании
        local = REPO_ROOT / name
        if local.is_file():
            print(f"  OK: {local} ({local.stat().st_size // 1024} KB)\n", flush=True)
        else:
            print(f"  OK: модель загружена (файл может быть в кэше Ultralytics): {name}\n", flush=True)

    print("Готово. Проверь наличие *.pt в корне проекта или в ~/.cache/ultralytics.")


if __name__ == "__main__":
    main()
