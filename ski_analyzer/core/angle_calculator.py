"""
Модуль для вычисления углов из ключевых точек
"""
import pandas as pd
import numpy as np
from typing import Optional
from pathlib import Path
from ..config.settings import (
    LEFT_HIP, LEFT_KNEE, LEFT_ANKLE, LEFT_SHOULDER,
    RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE, RIGHT_SHOULDER
)


class AngleCalculator:
    """Класс для вычисления углов из landmarks"""
    
    @staticmethod
    def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """
        Вычисляет угол между тремя точками (в градусах)
        
        Args:
            a, b, c: Точки, где b - вершина угла
            
        Returns:
            Угол в градусах
        """
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return angle
    
    def calculate_angles(self, landmarks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Вычисляет углы из DataFrame с landmarks
        
        Args:
            landmarks_df: DataFrame с ключевыми точками
            
        Returns:
            DataFrame с углами
        """
        angles = []
        
        for i, row in landmarks_df.iterrows():
            # Левая нога
            left_hip = [row[f'x_{LEFT_HIP}'], row[f'y_{LEFT_HIP}']]
            left_knee = [row[f'x_{LEFT_KNEE}'], row[f'y_{LEFT_KNEE}']]
            left_ankle = [row[f'x_{LEFT_ANKLE}'], row[f'y_{LEFT_ANKLE}']]
            left_shoulder = [row[f'x_{LEFT_SHOULDER}'], row[f'y_{LEFT_SHOULDER}']]
            
            # Правая нога
            right_hip = [row[f'x_{RIGHT_HIP}'], row[f'y_{RIGHT_HIP}']]
            right_knee = [row[f'x_{RIGHT_KNEE}'], row[f'y_{RIGHT_KNEE}']]
            right_ankle = [row[f'x_{RIGHT_ANKLE}'], row[f'y_{RIGHT_ANKLE}']]
            right_shoulder = [row[f'x_{RIGHT_SHOULDER}'], row[f'y_{RIGHT_SHOULDER}']]
            
            # Вычисляем углы
            left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
            left_body_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)
            right_body_angle = self.calculate_angle(right_shoulder, right_hip, right_knee)
            
            angles.append({
                'frame': i,
                'left_knee_angle': left_knee_angle,
                'right_knee_angle': right_knee_angle,
                'left_body_angle': left_body_angle,
                'right_body_angle': right_body_angle
            })
        
        angles_df = pd.DataFrame(angles)
        return angles_df
    
    def process_file(self, landmarks_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Обрабатывает файл с landmarks и сохраняет углы
        
        Args:
            landmarks_path: Путь к CSV с landmarks
            output_path: Путь для сохранения (если None, генерируется автоматически)
            
        Returns:
            DataFrame с углами
        """
        if not Path(landmarks_path).exists():
            raise FileNotFoundError(f"Файл не найден: {landmarks_path}")
        
        # Загружаем landmarks
        df = pd.read_csv(landmarks_path, sep=';')
        
        # Вычисляем углы
        angles_df = self.calculate_angles(df)
        
        # Сохраняем
        if output_path is None:
            base = Path(landmarks_path).stem
            output_path = f"{base}_angles.csv"
        
        angles_df.to_csv(output_path, sep=';', index=False, decimal=',', encoding='utf-8-sig')
        print(f"✓ Углы сохранены в: {output_path}")
        
        return angles_df

