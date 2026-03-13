"""Анализ техники по сравнению с эталоном и генерация рекомендаций."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
from ..config.settings import (
    ANGLES, ABS_THRESHOLDS, K_STD, BAD_PERCENT_THRESHOLD, TEMPLATE_FILE
)


class SkiAnalyzer:
    """Сравнение углов пользователя с эталоном, отчёт и рекомендации."""

    def __init__(self, template_path: Optional[str] = None):
        if template_path is None:
            template_path = TEMPLATE_FILE
        
        if not Path(template_path).exists():
            raise FileNotFoundError(f"Файл эталона не найден: {template_path}")
        
        self.template = pd.read_csv(template_path, sep=';')
    
    def analyze(self, user_angles_path: str) -> Dict:
        """Анализ пользовательских углов относительно эталона."""
        if not Path(user_angles_path).exists():
            raise FileNotFoundError(f"Файл не найден: {user_angles_path}")
        user = pd.read_csv(user_angles_path, sep=';')
        if len(self.template) != len(user):
            raise ValueError(
                f"Длины не совпадают: template={len(self.template)}, user={len(user)}. "
                f"Проверь, что файл пользователя ресэмплирован до {len(self.template)} точек."
            )
        
        feedback = []
        
        for angle in ANGLES:
            mean_col = f"{angle}_mean"
            std_col = f"{angle}_std"
            
            if mean_col not in self.template.columns or std_col not in self.template.columns:
                raise ValueError(f"В эталоне нет колонок {mean_col} / {std_col}")
            if angle not in user.columns:
                raise ValueError(f"В пользовательском файле нет колонки {angle}")
            
            mean = self.template[mean_col].values
            std = self.template[std_col].values
            y = user[angle].values
            
            diff = y - mean
            abs_diff = np.abs(diff)
            bad_mask = (abs_diff > ABS_THRESHOLDS[angle]) | (abs_diff > K_STD * std)
            percent_bad = 100 * bad_mask.sum() / len(bad_mask)
            mean_diff = float(diff.mean())
            max_diff = float(abs_diff.max())
            
            feedback.append({
                "angle": angle,
                "percent_bad": percent_bad,
                "mean_diff_deg": mean_diff,
                "max_diff_deg": max_diff,
                "is_critical": percent_bad > BAD_PERCENT_THRESHOLD
            })
        
        return {
            "feedback": feedback,
            "overall_score": self._calculate_overall_score(feedback)
        }
    
    def _calculate_overall_score(self, feedback: List[Dict]) -> float:
        """Общий балл 0–100 по результатам по углам."""
        if not feedback:
            return 0.0
        
        avg_bad = np.mean([f["percent_bad"] for f in feedback])
        score = max(0, 100 - avg_bad)
        return round(score, 1)
    
    def generate_recommendations(self, analysis_result: Dict, use_llm: bool = False) -> List[str]:
        """Текстовые рекомендации по результатам анализа."""
        recommendations = []
        feedback = analysis_result["feedback"]
        
        for fb in feedback:
            angle = fb["angle"]
            p_bad = fb["percent_bad"]
            mean_diff = fb["mean_diff_deg"]
            
            if p_bad < BAD_PERCENT_THRESHOLD:
                continue
            
            if "knee" in angle:
                side = "левое" if "left" in angle else "правое"
                if mean_diff > 0:
                    recommendations.append(
                        f"Колено ({side}): чаще более разогнуто, чем в эталоне. "
                        f"Рекомендация: увеличить сгибание колена в фазе поворота."
                    )
                else:
                    recommendations.append(
                        f"Колено ({side}): сгибается больше, чем в эталоне. "
                        f"Возможна излишняя посадка."
                    )
            
            if "body" in angle:
                side = "левая" if "left" in angle else "правая"
                if mean_diff > 0:
                    recommendations.append(
                        f"Корпус ({side} сторона): заметно отклонён назад относительно эталона. "
                        f"Рекомендация: сместить центр тяжести вперёд, ближе к носкам лыж."
                    )
                else:
                    recommendations.append(
                        f"Корпус ({side} сторона): подан вперёд сильнее, чем в эталоне. "
                        f"Следите за балансом и сохранением стойки."
                    )
        
        if not recommendations:
            recommendations.append("✔ Техника близка к эталонной. Продолжайте в том же духе!")
        
        return recommendations
    
    def get_detailed_report(self, user_angles_path: str) -> Dict:
        """Отчёт: оценка, анализ по углам, список рекомендаций."""
        analysis = self.analyze(user_angles_path)
        recommendations = self.generate_recommendations(analysis)
        
        return {
            "overall_score": analysis["overall_score"],
            "angle_analysis": analysis["feedback"],
            "recommendations": recommendations
        }

