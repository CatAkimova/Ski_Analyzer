#!/usr/bin/env python3
"""
Сравнение экстракторов скелета: несколько весов YOLO-pose + (опционально) MediaPipe Pose.

Метрики те же, что в compare_pose_models.py (без GT): detection_rate, mean_confidence,
hip_stability_mean_px, sec_per_frame.

Установка альтернативы YOLO:
  pip install mediapipe

Пример:
  python scripts/compare_pose_backends.py --video /path/to/clip1.mp4 /path/to/clip2.mp4
  python scripts/compare_pose_backends.py --video clip.mp4 --no-mediapipe
  python scripts/compare_pose_backends.py --video clip.mp4 --max-frames 500
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

# MediaPipe Tasks: .task модели (скачиваются один раз в models/)
# Индексы бёдер совпадают с Blaze Pose 33 (как в legacy PoseLandmark).
MEDIAPIPE_POSE_TASK_URLS = {
    0: (
        "pose_landmarker_lite.task",
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    ),
    1: (
        "pose_landmarker_full.task",
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
    ),
    2: (
        "pose_landmarker_heavy.task",
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
    ),
}
LEFT_HIP_MP, RIGHT_HIP_MP = 23, 24
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LEFT_HIP, RIGHT_HIP = 11, 12

DEFAULT_YOLO_MODELS = [
    "yolov8n-pose.pt",
    "yolov8s-pose.pt",
    "yolov8m-pose.pt",
    "yolov8l-pose.pt",
    "yolov8x-pose.pt",
    "yolo11n-pose.pt",
    "yolo11s-pose.pt",
]


def _pick_person_keypoints(keypoints_xyconf: np.ndarray) -> Optional[np.ndarray]:
    if keypoints_xyconf is None or keypoints_xyconf.size == 0:
        return None
    if keypoints_xyconf.ndim == 2:
        return keypoints_xyconf
    scores = keypoints_xyconf[:, :, 2].mean(axis=1)
    best = int(np.argmax(scores))
    return keypoints_xyconf[best]


def run_yolo_metrics(
    model_name: str,
    video_path: Path,
    max_frames: Optional[int],
    imgsz: int,
) -> Dict[str, float]:
    from ultralytics import YOLO

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(str(video_path))

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
        conf_sum += float(person[:, 2].sum())
        conf_count += 17
        lh = person[LEFT_HIP, :2]
        rh = person[RIGHT_HIP, :2]
        mid = (lh + rh) / 2.0
        if hip_mid_prev is not None:
            hip_disp_sum += float(np.linalg.norm(mid - hip_mid_prev))
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


def _ensure_mediapipe_task_file(model_complexity: int) -> Path:
    fname, url = MEDIAPIPE_POSE_TASK_URLS[model_complexity]
    dest = REPO_ROOT / "models" / fname
    if not dest.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"Скачивание MediaPipe task: {url} -> {dest}", flush=True)
        urllib.request.urlretrieve(url, dest)
    return dest


def _run_mediapipe_legacy(
    video_path: Path,
    max_frames: Optional[int],
    model_complexity: int,
) -> Dict[str, float]:
    import mediapipe as mp

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(str(video_path))

    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=model_complexity,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    h_full, w_full = 0, 0
    frames_total = 0
    frames_with = 0
    conf_sum = 0.0
    conf_count = 0
    hip_mid_prev: Optional[np.ndarray] = None
    hip_disp_sum = 0.0
    hip_disp_n = 0

    PL = mp.solutions.pose.PoseLandmark

    t0 = time.perf_counter()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if max_frames is not None and frames_total >= max_frames:
            break
        frames_total += 1
        h_full, w_full = frame.shape[0], frame.shape[1]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)
        if not res.pose_landmarks:
            hip_mid_prev = None
            continue

        frames_with += 1
        lm = res.pose_landmarks.landmark
        vis = []
        coords = []
        for i in range(33):
            p = lm[i]
            vis.append(p.visibility)
            coords.append([p.x * w_full, p.y * h_full])
        coords = np.array(coords, dtype=np.float64)
        conf_sum += float(np.sum(vis))
        conf_count += 33

        lh = coords[PL.LEFT_HIP.value]
        rh = coords[PL.RIGHT_HIP.value]
        mid = (lh + rh) / 2.0
        if hip_mid_prev is not None:
            hip_disp_sum += float(np.linalg.norm(mid - hip_mid_prev))
            hip_disp_n += 1
        hip_mid_prev = mid.copy()

    cap.release()
    pose.close()
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


def _run_mediapipe_tasks(
    video_path: Path,
    max_frames: Optional[int],
    model_complexity: int,
) -> Dict[str, float]:
    """MediaPipe 0.10+ без mp.solutions: Pose Landmarker (Tasks)."""
    import mediapipe as mp

    task_path = _ensure_mediapipe_task_file(model_complexity)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(str(video_path))

    fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(task_path)),
        running_mode=VisionRunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = PoseLandmarker.create_from_options(options)

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

        h, w = frame.shape[0], frame.shape[1]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp_ms = int(frames_total * (1000.0 / fps))
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)
        frames_total += 1

        if not result.pose_landmarks:
            hip_mid_prev = None
            continue

        # Первый скелет: в разных версиях API это либо объект с .landmark, либо уже список точек
        pl = result.pose_landmarks[0]
        if hasattr(pl, "landmark"):
            lms = list(pl.landmark)
        elif isinstance(pl, (list, tuple)):
            lms = list(pl)
        else:
            lms = list(pl)

        vis_list = []
        coords = []
        for lm in lms:
            vis_list.append(float(getattr(lm, "visibility", 1.0)))
            coords.append([lm.x * w, lm.y * h])
        coords = np.array(coords, dtype=np.float64)
        if coords.shape[0] <= max(LEFT_HIP_MP, RIGHT_HIP_MP):
            hip_mid_prev = None
            continue

        frames_with += 1
        conf_sum += float(np.sum(vis_list))
        conf_count += len(vis_list)

        lh = coords[LEFT_HIP_MP]
        rh = coords[RIGHT_HIP_MP]
        mid = (lh + rh) / 2.0
        if hip_mid_prev is not None:
            hip_disp_sum += float(np.linalg.norm(mid - hip_mid_prev))
            hip_disp_n += 1
        hip_mid_prev = mid.copy()

    cap.release()
    landmarker.close()
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


def run_mediapipe_metrics(
    video_path: Path,
    max_frames: Optional[int],
    model_complexity: int = 1,
) -> Dict[str, float]:
    import mediapipe as mp

    if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
        return _run_mediapipe_legacy(video_path, max_frames, model_complexity)
    return _run_mediapipe_tasks(video_path, max_frames, model_complexity)


def resolve_yolo_path(name: str) -> str:
    p = Path(name)
    if p.is_file():
        return str(p.resolve())
    root_candidate = REPO_ROOT / name
    if root_candidate.is_file():
        return str(root_candidate)
    return name


def main() -> None:
    parser = argparse.ArgumentParser(description="YOLO-pose vs MediaPipe на одних видео")
    parser.add_argument("videos", nargs="+", type=Path, help="Пути к .mp4/.mov")
    parser.add_argument(
        "--yolo-models",
        nargs="*",
        default=None,
        help="Веса YOLO (по умолчанию v8 n–x + yolo11 n/s; см. DEFAULT_YOLO_MODELS)",
    )
    parser.add_argument("--no-mediapipe", action="store_true", help="Не запускать MediaPipe")
    parser.add_argument("--mediapipe-complexity", type=int, default=1, choices=[0, 1, 2])
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "results" / "pose_backend_comparison.csv",
    )
    args = parser.parse_args()

    yolo_models = args.yolo_models if args.yolo_models else DEFAULT_YOLO_MODELS
    yolo_models = [resolve_yolo_path(m) for m in yolo_models]

    rows: List[dict] = []
    args.out.parent.mkdir(parents=True, exist_ok=True)

    for video_path in args.videos:
        if not video_path.is_file():
            print(f"Пропуск (нет файла): {video_path}", file=sys.stderr)
            continue
        rel = str(video_path.resolve())

        for m in yolo_models:
            tag = f"yolo:{Path(m).name}"
            print(f"\n=== {tag}  |  {rel} ===", flush=True)
            try:
                metrics = run_yolo_metrics(m, video_path, args.max_frames, args.imgsz)
            except Exception as e:
                print(f"Ошибка: {e}", flush=True)
                rows.append({"video": rel, "backend": tag, "error": str(e)})
                continue
            rows.append({"video": rel, "backend": tag, **metrics})
            print(
                f"  detection_rate={metrics['detection_rate']:.3f}  "
                f"mean_conf={metrics['mean_confidence']:.3f}  "
                f"hip_disp_px={metrics['hip_stability_mean_px']:.2f}  "
                f"sec/frame={metrics['sec_per_frame']:.4f}",
                flush=True,
            )

        if not args.no_mediapipe:
            tag = f"mediapipe:pose_complexity_{args.mediapipe_complexity}"
            print(f"\n=== {tag}  |  {rel} ===", flush=True)
            try:
                metrics = run_mediapipe_metrics(
                    video_path, args.max_frames, model_complexity=args.mediapipe_complexity
                )
            except ImportError:
                print("MediaPipe не установлен: pip install mediapipe", flush=True)
                rows.append({"video": rel, "backend": tag, "error": "ImportError mediapipe"})
            except Exception as e:
                print(f"Ошибка: {e}", flush=True)
                rows.append({"video": rel, "backend": tag, "error": str(e)})
            else:
                rows.append({"video": rel, "backend": tag, **metrics})
                print(
                    f"  detection_rate={metrics['detection_rate']:.3f}  "
                    f"mean_vis={metrics['mean_confidence']:.3f}  "
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
