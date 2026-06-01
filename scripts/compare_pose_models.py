#!/usr/bin/env python3
"""
Сравнение моделей извлечения скелета (Ultralytics YOLO-pose) на одних и тех же видео.

Метрики (без ручной разметки GT):
  - detection_rate: доля кадров, где найден хотя бы один человек с keypoints
  - mean_confidence: средняя уверенность по 17 точкам (первый человек с max mean conf при нескольких)
  - hip_stability_px: среднее смещение центра бёдер между соседними кадрами (ниже при стабильной позе/трекинге)
  - sec_per_frame, total_sec

Пример:
  python scripts/compare_pose_models.py --video Ski.Videos/some.mp4
  python scripts/compare_pose_models.py --video a.mp4 --video b.mp4 --models yolov8n-pose yolov8s-pose yolo11n-pose
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# корень репозитория
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# COCO: левое бедро 11, правое 12
LEFT_HIP, RIGHT_HIP = 11, 12


DEFAULT_MODELS = [
    "yolov8n-pose.pt",
    "yolov8s-pose.pt",
    "yolov8m-pose.pt",
    "yolov8l-pose.pt",
    "yolov8x-pose.pt",
    "yolo11n-pose.pt",
    "yolo11s-pose.pt",
]


def _pick_person_keypoints(keypoints_xyconf: np.ndarray) -> Optional[np.ndarray]:
    """
    keypoints_xyconf: (N_people, 17, 3) x,y,conf
    Возвращает (17, 3) для человека с максимальной средней conf.
    """
    if keypoints_xyconf is None or keypoints_xyconf.size == 0:
        return None
    if keypoints_xyconf.ndim == 2:
        return keypoints_xyconf
    scores = keypoints_xyconf[:, :, 2].mean(axis=1)
    best = int(np.argmax(scores))
    return keypoints_xyconf[best]


def run_pose_metrics(
    model_name: str,
    video_path: Path,
    max_frames: Optional[int] = None,
    imgsz: int = 640,
) -> Dict[str, float]:
    from ultralytics import YOLO

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Не удалось открыть видео: {video_path}")

    model = YOLO(model_name)

    frames_total = 0
    frames_with = 0
    conf_sum = 0.0
    conf_count = 0
    hip_mid_prev: Optional[np.ndarray] = None
    hip_disp_sum = 0.0
    hip_disp_n = 0

    t0 = time.perf_counter()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if max_frames is not None and frames_total >= max_frames:
            break

        frames_total += 1
        results = model(frame, verbose=False, imgsz=imgsz)
        r0 = results[0]
        if r0.keypoints is None or r0.keypoints.data is None:
            hip_mid_prev = None
            continue

        kpts = r0.keypoints.data.cpu().numpy()
        person = _pick_person_keypoints(kpts)
        if person is None:
            hip_mid_prev = None
            continue

        frames_with += 1
        confs = person[:, 2]
        conf_sum += float(confs.sum())
        conf_count += 17

        lh = person[LEFT_HIP, :2]
        rh = person[RIGHT_HIP, :2]
        mid = (lh + rh) / 2.0
        if hip_mid_prev is not None:
            d = float(np.linalg.norm(mid - hip_mid_prev))
            hip_disp_sum += d
            hip_disp_n += 1
        hip_mid_prev = mid.copy()

    cap.release()
    elapsed = time.perf_counter() - t0

    det_rate = frames_with / frames_total if frames_total else 0.0
    mean_conf = conf_sum / conf_count if conf_count else 0.0
    hip_stab = hip_disp_sum / hip_disp_n if hip_disp_n else float("nan")
    spf = elapsed / frames_total if frames_total else float("nan")

    return {
        "frames_total": float(frames_total),
        "frames_with_pose": float(frames_with),
        "detection_rate": det_rate,
        "mean_confidence": mean_conf,
        "hip_stability_mean_px": hip_stab,
        "total_sec": elapsed,
        "sec_per_frame": spf,
    }


def resolve_model_path(name: str) -> str:
    """Имя веса или путь: если файл в корне репо — используем абсолютный путь."""
    p = Path(name)
    if p.is_file():
        return str(p.resolve())
    root_candidate = REPO_ROOT / name
    if root_candidate.is_file():
        return str(root_candidate)
    return name


def main() -> None:
    parser = argparse.ArgumentParser(description="Сравнение YOLO-pose моделей на видео")
    parser.add_argument(
        "--video",
        action="append",
        dest="videos",
        required=True,
        help="Путь к видео (можно указать несколько раз)",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Имена весов Ultralytics (скачиваются автоматически), по умолчанию набор DEFAULT_MODELS",
    )
    parser.add_argument("--max-frames", type=int, default=None, help="Ограничить число кадров (быстрый тест)")
    parser.add_argument("--imgsz", type=int, default=640, help="Размер инференса YOLO")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "results" / "pose_model_comparison.csv",
        help="CSV с результатами",
    )
    args = parser.parse_args()

    models = args.models if args.models else DEFAULT_MODELS
    models = [resolve_model_path(m) for m in models]

    videos = [Path(v) for v in args.videos]
    for v in videos:
        if not v.is_file():
            print(f"Пропуск (нет файла): {v}", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows: List[dict] = []

    for video_path in videos:
        if not video_path.is_file():
            continue
        rel = str(video_path)
        for m in models:
            print(f"\n=== {m}  |  {rel} ===", flush=True)
            try:
                metrics = run_pose_metrics(m, video_path, max_frames=args.max_frames, imgsz=args.imgsz)
            except Exception as e:
                print(f"Ошибка: {e}", flush=True)
                rows.append(
                    {
                        "video": rel,
                        "model": m,
                        "error": str(e),
                    }
                )
                continue
            row = {"video": rel, "model": m, **{k: metrics[k] for k in metrics}}
            rows.append(row)
            print(
                f"  detection_rate={metrics['detection_rate']:.3f}  "
                f"mean_conf={metrics['mean_confidence']:.3f}  "
                f"hip_disp_px={metrics['hip_stability_mean_px']:.2f}  "
                f"sec/frame={metrics['sec_per_frame']:.4f}",
                flush=True,
            )

    if not rows:
        print("Нет результатов.", file=sys.stderr)
        sys.exit(1)

    fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nСохранено: {args.out}")


if __name__ == "__main__":
    main()
