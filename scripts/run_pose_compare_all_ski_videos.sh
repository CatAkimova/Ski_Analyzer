#!/usr/bin/env bash
# Сравнение pose-бэкендов на всех видео в Ski.Videos/ (и опционально Bad.Videos/).
# По умолчанию сравниваются все веса из compare_pose_backends (v8 n–x + yolo11 n/s + MediaPipe).
#
#   chmod +x scripts/run_pose_compare_all_ski_videos.sh
#   ./scripts/run_pose_compare_all_ski_videos.sh
#
# Переменные (опционально):
#   MAX_FRAMES=120 — ограничение кадров на клип (быстрее)
#   OUT=results/pose_cmp_$(date +%Y%m%d).csv — не перезатирать старый CSV
#   INCLUDE_BAD=1 — добавить все ролики из Bad.Videos/
#   NO_MEDIAPIPE=1 — только YOLO, без MediaPipe (быстрее)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

MAX_FRAMES="${MAX_FRAMES:-120}"
OUT="${OUT:-results/pose_backend_comparison_all_videos.csv}"

shopt -s nullglob
collect_videos() {
  local dir="$1"
  local ext f
  for ext in mp4 mov MOV MP4; do
    for f in "$dir"/*."$ext"; do
      [[ -f "$f" ]] && echo "$f"
    done
  done
}

videos=()
while IFS= read -r line; do
  [[ -n "$line" ]] && videos+=("$line")
done < <(collect_videos "Ski.Videos" | sort -u)

if [[ "${INCLUDE_BAD:-0}" == "1" ]]; then
  while IFS= read -r line; do
    [[ -n "$line" ]] && videos+=("$line")
  done < <(collect_videos "Bad.Videos" | sort -u)
fi

if [[ ${#videos[@]} -eq 0 ]]; then
  echo "Нет видео в Ski.Videos (и Bad.Videos при INCLUDE_BAD=1)" >&2
  exit 1
fi

echo "Видео: ${#videos[@]} шт., max_frames=$MAX_FRAMES, out=$OUT, INCLUDE_BAD=${INCLUDE_BAD:-0}, NO_MEDIAPIPE=${NO_MEDIAPIPE:-0}"
if [[ "${NO_MEDIAPIPE:-0}" == "1" ]]; then
  python scripts/compare_pose_backends.py "${videos[@]}" --max-frames "$MAX_FRAMES" --out "$OUT" --no-mediapipe
else
  python scripts/compare_pose_backends.py "${videos[@]}" --max-frames "$MAX_FRAMES" --out "$OUT"
fi
echo "Готово: $OUT"
