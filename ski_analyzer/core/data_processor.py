"""
Модуль для сглаживания и ресемплинга данных
"""
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from pathlib import Path
from typing import Optional
from ..config.settings import N_RESAMPLE_POINTS, SMOOTH_WINDOW, SMOOTH_POLY, ANGLES


class DataProcessor:
    """Класс для обработки данных: сглаживание и ресемплинг"""
    
    @staticmethod
    def smooth_curve(y: np.ndarray, window: int = SMOOTH_WINDOW, poly: int = SMOOTH_POLY) -> np.ndarray:
        """
        Сглаживает кривую с помощью фильтра Савицкого-Голея
        
        Args:
            y: Массив значений
            window: Размер окна
            poly: Порядок полинома
            
        Returns:
            Сглаженный массив
        """
        if len(y) < window:
            return y
        return savgol_filter(y, window_length=window, polyorder=poly)
    
    @staticmethod
    def resample_curve(y: np.ndarray, target_len: int = N_RESAMPLE_POINTS) -> np.ndarray:
        """
        Ресемплирует кривую до заданного количества точек
        
        Args:
            y: Исходный массив
            target_len: Целевое количество точек
            
        Returns:
            Ресемплированный массив
        """
        x_old = np.linspace(0, 1, len(y))
        x_new = np.linspace(0, 1, target_len)
        return np.interp(x_new, x_old, y)
    
    def process_angles(self, angles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Обрабатывает DataFrame с углами: сглаживание и ресемплинг
        
        Args:
            angles_df: DataFrame с углами
            
        Returns:
            Обработанный DataFrame
        """
        new_df = pd.DataFrame()
        
        for col in ANGLES:
            if col not in angles_df.columns:
                print(f"⚠ Предупреждение: колонка {col} не найдена, пропуск")
                continue
            
            # Преобразование строк '124,85' → float 124.85
            y = angles_df[col].astype(str).str.replace(',', '.', regex=False).astype(float).values
            
            # Сглаживание
            y_smooth = self.smooth_curve(y)
            
            # Ресемплирование
            y_resampled = self.resample_curve(y_smooth)
            
            new_df[col] = y_resampled
        
        return new_df
    
    def process_file(self, angles_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Обрабатывает файл с углами и сохраняет результат
        
        Args:
            angles_path: Путь к CSV с углами
            output_path: Путь для сохранения (если None, генерируется автоматически)
            
        Returns:
            Обработанный DataFrame
        """
        if not Path(angles_path).exists():
            raise FileNotFoundError(f"Файл не найден: {angles_path}")
        
        # Загружаем углы
        df = pd.read_csv(angles_path, sep=';')
        
        # Обрабатываем
        processed_df = self.process_angles(df)
        
        # Сохраняем
        if output_path is None:
            base = Path(angles_path).stem
            output_path = f"{base}_resampled.csv"
        
        processed_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"✓ Обработанные данные сохранены в: {output_path}")
        
        return processed_df

