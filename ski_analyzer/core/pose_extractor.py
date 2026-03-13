"""Извлечение позы из видео (YOLOv8-pose)."""
import cv2
import pandas as pd
import os
from pathlib import Path
from ultralytics import YOLO
from typing import Optional, Tuple


class PoseExtractor:
    """Извлечение ключевых точек позы из видео (YOLO)."""

    def __init__(self, model_path: str = "yolov8n-pose.pt"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель не найдена: {model_path}")
        self.model = YOLO(model_path)
    
    def extract_pose(self, video_path: str,
                     output_csv: Optional[str] = None,
                     output_video: Optional[str] = None,
                     show: bool = False) -> Tuple[pd.DataFrame, Optional[str]]:
        """Извлекает позу из видео, возвращает DataFrame с landmarks и путь к CSV."""
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
        
        # Получаем характеристики видео
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Настраиваем VideoWriter если нужно
        out = None
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        
        # Подготовка данных
        data = []
        header = ['frame']
        for i in range(17):  # YOLOv8 Pose использует 17 ключевых точек (COCO формат)
            header += [f'x_{i}', f'y_{i}', f'conf_{i}']
        
        frame_num = 0
        
        print(f"Обработка видео: {video_path}")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Предсказание позы
            results = self.model(frame, verbose=False)
            
            # Извлекаем keypoints
            if len(results) > 0 and results[0].keypoints is not None:
                for person in results[0].keypoints.data.cpu().numpy():
                    row = [frame_num]
                    for (x, y, conf) in person:
                        row += [x, y, conf]
                    data.append(row)
                
                # Рисуем позу и сохраняем в видео
                if out:
                    annotated = results[0].plot()
                    out.write(annotated)
                
                # Показываем на экране
                if show:
                    annotated = results[0].plot()
                    cv2.imshow('YOLO Pose', annotated)
                    if cv2.waitKey(10) & 0xFF == 27:
                        break
            
            frame_num += 1
        
        # Сохраняем DataFrame в CSV
        df = pd.DataFrame(data, columns=header)
        df.to_csv(output_csv, sep=';', index=False, encoding='utf-8-sig')
        
        # Освобождаем ресурсы
        cap.release()
        if out:
            out.release()
        if show:
            cv2.destroyAllWindows()
        
        print(f"✓ Landmarks сохранены в: {output_csv}")
        if output_video:
            print(f"✓ Видео с аннотациями сохранено в: {output_video}")
        
        return df, output_csv

