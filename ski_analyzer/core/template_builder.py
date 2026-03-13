"""Построение эталона (mean/std) из набора resampled файлов."""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional
from ..config.settings import RESULTS_DIR, ANGLES


class TemplateBuilder:
    """Эталон (mean, std по углам) из списка resampled CSV."""

    def build_template(self, resampled_files: List[str], output_path: Optional[str] = None) -> pd.DataFrame:
        """Строит эталон из списка путей к resampled CSV."""
        if not resampled_files:
            raise ValueError("Список файлов пуст")
        data = {angle: [] for angle in ANGLES}
        for f in resampled_files:
            if not Path(f).exists():
                print(f"⚠ Файл не найден, пропуск: {f}")
                continue
            df = pd.read_csv(f, sep=';')
            for angle in ANGLES:
                if angle not in df.columns:
                    raise ValueError(f"В файле {f} отсутствует колонка: {angle}")
                data[angle].append(df[angle].values)
        
        if not any(data.values()):
            raise ValueError("Не удалось загрузить данные из файлов")
        template = pd.DataFrame()
        for angle in ANGLES:
            if not data[angle]:
                continue
            
            curves = np.vstack(data[angle])
            mean_curve = curves.mean(axis=0)
            std_curve = curves.std(axis=0)
            
            template[f"{angle}_mean"] = mean_curve
            template[f"{angle}_std"] = std_curve
        if output_path is None:
            output_path = RESULTS_DIR / "template_angles.csv"
        
        template.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"✓ Эталон сохранен в: {output_path}")
        
        return template
    
    def build_from_directory(self, directory: str = None, pattern: str = "*_resampled.csv") -> pd.DataFrame:
        """Эталон из всех файлов в директории по паттерну."""
        if directory is None:
            directory = RESULTS_DIR
        
        from glob import glob
        files = sorted(glob(str(Path(directory) / pattern)))
        
        if not files:
            raise FileNotFoundError(f"Не найдено файлов по паттерну: {pattern} в {directory}")
        
        print(f"Найдено {len(files)} файлов для построения эталона")
        return self.build_template(files)

