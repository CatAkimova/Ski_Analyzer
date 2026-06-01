"""Unit tests: сглаживание, ресемплинг, десятичная запятая в CSV-подобных данных."""
import numpy as np
import pandas as pd

from ski_analyzer.core.data_processor import DataProcessor
from ski_analyzer.config.settings import N_RESAMPLE_POINTS, ANGLES


def test_resample_curve_target_length():
    dp = DataProcessor()
    y = np.linspace(0.0, 1.0, 20)
    out = dp.resample_curve(y, target_len=50)
    assert len(out) == 50
    assert np.isclose(out[0], y[0], atol=1e-6)
    assert np.isclose(out[-1], y[-1], atol=1e-6)


def test_process_angles_comma_decimal_strings():
    """Как в реальных angles.csv: строки с запятой как десятичный разделитель."""
    dp = DataProcessor()
    n = 25
    rows = {c: [f"{(i * 3.1):.2f}".replace(".", ",") for i in range(n)] for c in ANGLES}
    df = pd.DataFrame(rows)
    out = dp.process_angles(df)
    assert list(out.columns) == list(ANGLES)
    assert len(out) == N_RESAMPLE_POINTS


def test_smooth_curve_short_series_no_crash():
    dp = DataProcessor()
    y = np.array([1.0, 2.0, 3.0])
    out = dp.smooth_curve(y)
    assert len(out) == len(y)
