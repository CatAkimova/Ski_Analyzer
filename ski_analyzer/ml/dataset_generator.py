"""
Генератор синтетических данных для обучения модели
Модифицирует существующие видео для увеличения разнообразия датасета
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import random


class VideoAugmenter:
    """Класс для аугментации видео с разными параметрами"""
    
    def __init__(self):
        self.augmentation_params = {
            'hue_range': (-30, 30),      # Изменение цвета костюма
            'saturation_range': (0.7, 1.3),  # Насыщенность
            'brightness_range': (0.8, 1.2),   # Яркость
            'scale_range': (0.85, 1.15),      # Масштаб (рост)
            'rotation_range': (-5, 5),         # Поворот
            'crop_range': (0.9, 1.0),         # Обрезка
        }
    
    def augment_frame(self, frame: np.ndarray, 
                     hue_shift: Optional[int] = None,
                     saturation: Optional[float] = None,
                     brightness: Optional[float] = None,
                     scale: Optional[float] = None,
                     rotation: Optional[float] = None) -> np.ndarray:
        """
        Аугментирует один кадр
        
        Args:
            frame: Входной кадр
            hue_shift: Сдвиг оттенка (для изменения цвета костюма)
            saturation: Изменение насыщенности
            brightness: Изменение яркости
            scale: Масштаб (симуляция роста)
            rotation: Поворот в градусах
            
        Returns:
            Аугментированный кадр
        """
        result = frame.copy()
        
        # Изменение цвета (HSV)
        if hue_shift is not None or saturation is not None or brightness is not None:
            hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
            
            if hue_shift is not None:
                hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
            
            if saturation is not None:
                hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
            
            if brightness is not None:
                hsv[:, :, 2] = np.clip(hsv[:, :, 2] * brightness, 0, 255)
            
            result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # Масштабирование (симуляция роста)
        if scale is not None and scale != 1.0:
            h, w = result.shape[:2]
            new_h, new_w = int(h * scale), int(w * scale)
            result = cv2.resize(result, (new_w, new_h))
            
            # Обрезаем или добавляем padding для сохранения размера
            if scale > 1.0:
                # Обрезаем
                start_y = (new_h - h) // 2
                start_x = (new_w - w) // 2
                result = result[start_y:start_y+h, start_x:start_x+w]
            else:
                # Добавляем padding
                pad_y = (h - new_h) // 2
                pad_x = (w - new_w) // 2
                result = cv2.copyMakeBorder(
                    result, pad_y, h-new_h-pad_y, pad_x, w-new_w-pad_x,
                    cv2.BORDER_CONSTANT, value=[0, 0, 0]
                )
        
        # Поворот
        if rotation is not None and rotation != 0:
            h, w = result.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotation, 1.0)
            result = cv2.warpAffine(result, M, (w, h), borderValue=[0, 0, 0])
        
        return result
    
    def augment_video(self, video_path: str, output_path: str,
                     num_variations: int = 5,
                     seed: Optional[int] = None) -> List[str]:
        """
        Создает несколько вариаций видео с разными параметрами
        
        Args:
            video_path: Путь к исходному видео
            output_path: Путь для сохранения (будет добавлен суффикс)
            num_variations: Количество вариаций
            seed: Seed для воспроизводимости
            
        Returns:
            Список путей к созданным видео
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Открываем видео
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")
        
        # Получаем параметры видео
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Читаем все кадры
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        if not frames:
            raise ValueError("Видео пустое")
        
        created_files = []
        base_path = Path(output_path)
        
        # Создаем вариации
        for i in range(num_variations):
            # Генерируем случайные параметры
            params = self._generate_random_params()
            
            # Создаем аугментированные кадры
            augmented_frames = []
            for frame in frames:
                aug_frame = self.augment_frame(
                    frame,
                    hue_shift=params['hue_shift'],
                    saturation=params['saturation'],
                    brightness=params['brightness'],
                    scale=params['scale'],
                    rotation=params['rotation']
                )
                augmented_frames.append(aug_frame)
            
            # Сохраняем видео
            output_file = base_path.parent / f"{base_path.stem}_aug_{i}{base_path.suffix}"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_file), fourcc, fps, (width, height))
            
            for frame in augmented_frames:
                out.write(frame)
            out.release()
            
            created_files.append(str(output_file))
            print(f"✓ Создано: {output_file}")
        
        return created_files
    
    def _generate_random_params(self) -> dict:
        """Генерирует случайные параметры аугментации"""
        return {
            'hue_shift': random.randint(*self.augmentation_params['hue_range']),
            'saturation': random.uniform(*self.augmentation_params['saturation_range']),
            'brightness': random.uniform(*self.augmentation_params['brightness_range']),
            'scale': random.uniform(*self.augmentation_params['scale_range']),
            'rotation': random.uniform(*self.augmentation_params['rotation_range']),
        }
    
    def create_dataset_variations(self, input_dir: str, output_dir: str,
                                  variations_per_video: int = 5) -> List[str]:
        """
        Создает вариации для всех видео в директории
        
        Args:
            input_dir: Директория с исходными видео
            output_dir: Директория для сохранения
            variations_per_video: Количество вариаций на видео
            
        Returns:
            Список всех созданных файлов
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        video_files = list(input_path.glob("*.mp4")) + \
                      list(input_path.glob("*.MOV")) + \
                      list(input_path.glob("*.avi"))
        
        all_created = []
        
        for video_file in video_files:
            output_file = output_path / f"{video_file.stem}_aug.mp4"
            created = self.augment_video(
                str(video_file),
                str(output_file),
                num_variations=variations_per_video
            )
            all_created.extend(created)
        
        return all_created


# Пример использования
if __name__ == "__main__":
    augmenter = VideoAugmenter()
    
    # Создать вариации одного видео
    augmenter.augment_video(
        "input_video.mp4",
        "output_video.mp4",
        num_variations=5
    )
    
    # Создать вариации для всех видео в директории
    augmenter.create_dataset_variations(
        "Ski.Videos/Professional",
        "Ski.Videos/Professional_Augmented",
        variations_per_video=5
    )



