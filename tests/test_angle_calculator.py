"""Unit tests: углы по трём точкам и разбор минимального landmarks CSV."""
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from ski_analyzer.core.angle_calculator import AngleCalculator
from ski_analyzer.config.settings import (
    LEFT_HIP,
    LEFT_KNEE,
    LEFT_ANKLE,
)


def test_calculate_angle_right_angle():
    calc = AngleCalculator()
    # Прямой угол в b: a=(1,0), b=(0,0), c=(0,1)
    a, b, c = np.array([1.0, 0.0]), np.array([0.0, 0.0]), np.array([0.0, 1.0])
    ang = calc.calculate_angle(a, b, c)
    assert abs(ang - 90.0) < 1e-5


def test_process_file_landmarks_csv(tmp_path: Path):
    """Минимальный landmarks CSV с нужными колонками x_i, y_i."""
    calc = AngleCalculator()
    # Одна строка: все точки 0..16 (достаточно для обращений в calculate_angles)
    row = {}
    for i in range(17):
        row[f"x_{i}"] = float(i)
        row[f"y_{i}"] = 0.0
    # Сместим колено и голень, чтобы угол колена не был вырожденным
    row[f"x_{LEFT_HIP}"] = 0.0
    row[f"y_{LEFT_HIP}"] = 0.0
    row[f"x_{LEFT_KNEE}"] = 1.0
    row[f"y_{LEFT_KNEE}"] = 0.0
    row[f"x_{LEFT_ANKLE}"] = 1.0
    row[f"y_{LEFT_ANKLE}"] = 1.0

    df = pd.DataFrame([row])
    p = tmp_path / "lm.csv"
    df.to_csv(p, sep=";", index=False)

    out_path = tmp_path / "angles.csv"
    res = calc.process_file(str(p), output_path=str(out_path))
    assert len(res) == 1
    assert "left_knee_angle" in res.columns
    assert out_path.exists()
