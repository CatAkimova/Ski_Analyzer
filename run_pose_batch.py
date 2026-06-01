import argparse
import os
from pathlib import Path
from typing import Optional, Tuple

import cv2
import pandas as pd
from ultralytics import YOLO

from ski_analyzer.config.settings import YOLO_MODEL_PATH as _PROJECT_YOLO

_DEFAULT_POSE_MODEL = str(_PROJECT_YOLO)


class PoseExtractor:
    """Извлечение ключевых точек позы из видео (YOLOv8-pose)."""

    def __init__(self, model_path: str = _DEFAULT_POSE_MODEL):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель не найдена: {model_path}")
        self.model = YOLO(model_path)

    def extract_pose(
        self,
        video_path: str,
        output_csv: Optional[str] = None,
        output_video: Optional[str] = None,
        show: bool = False,
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Извлекает позу из одного видео."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Видео не найдено: {video_path}")

        base_name = Path(video_path).stem

        if output_csv is None:
            output_csv = f"{base_name}_landmarks.csv"
        if output_video is None:
            output_video = f"{base_name}_pose_output.mp4"

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 25

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = None
        if output_video:
            Path(output_video).parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        if output_csv:
            Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

        data = []
        header = ["frame"]
        for i in range(17):
            header += [f"x_{i}", f"y_{i}", f"conf_{i}"]

        frame_num = 0
        print(f"Обработка видео: {video_path}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame, verbose=False)

            if len(results) > 0 and results[0].keypoints is not None:
                persons = results[0].keypoints.data.cpu().numpy()

                for person in persons:
                    row = [frame_num]
                    for (x, y, conf) in person:
                        row += [x, y, conf]
                    data.append(row)

                annotated = results[0].plot()

                if out:
                    out.write(annotated)

                if show:
                    cv2.imshow("YOLO Pose", annotated)
                    if cv2.waitKey(10) & 0xFF == 27:
                        break

            frame_num += 1

        df = pd.DataFrame(data, columns=header)
        df.to_csv(output_csv, sep=";", index=False, encoding="utf-8-sig")

        cap.release()
        if out:
            out.release()
        if show:
            cv2.destroyAllWindows()

        print(f"✓ Landmarks сохранены в: {output_csv}")
        if output_video:
            print(f"✓ Видео с аннотациями сохранено в: {output_video}")

        return df, output_csv


def find_videos(input_dir: Path):
    """Ищет все видео во всех вложенных папках."""
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".mpeg", ".mpg"}
    return [
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in video_extensions
    ]


def process_folder(
    input_dir: str,
    output_dir: str,
    model_path: str = _DEFAULT_POSE_MODEL,
    show: bool = False,
):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Папка не найдена: {input_dir}")

    video_files = find_videos(input_path)

    if not video_files:
        print("Видео не найдены.")
        return

    print(f"Найдено видео: {len(video_files)}")

    extractor = PoseExtractor(model_path=model_path)

    for video_file in video_files:
        try:
            # относительный путь от входной папки
            relative_parent = video_file.parent.relative_to(input_path)

            # сохраняем структуру подпапок
            target_folder = output_path / relative_parent
            target_folder.mkdir(parents=True, exist_ok=True)

            base_name = video_file.stem
            output_csv = target_folder / f"{base_name}_landmarks.csv"
            output_video = target_folder / f"{base_name}_pose_output.mp4"

            extractor.extract_pose(
                video_path=str(video_file),
                output_csv=str(output_csv),
                output_video=str(output_video),
                show=show,
            )

        except Exception as e:
            print(f"Ошибка при обработке {video_file}: {e}")

    print("Готово.")


def main():
    parser = argparse.ArgumentParser(
        description="Пакетное извлечение позы из всех видео в папке и подпапках"
    )
    parser.add_argument(
        "input_dir",
        help="Папка, где лежат видео"
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Папка для результатов"
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_POSE_MODEL,
        help="Путь к модели (по умолчанию из ski_analyzer/config/settings.py)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Показывать видео во время обработки"
    )

    args = parser.parse_args()

    process_folder(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_path=args.model,
        show=args.show,
    )


if __name__ == "__main__":
    main()