import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import os

N_POINTS = 100

# сглаживание
def smooth_curve(y, window=11, poly=3):
    if len(y) < window:
        return y
    return savgol_filter(y, window_length=window, polyorder=poly)

# Ресэмплирование до N точек
def resample_curve(y, target_len=N_POINTS):
    x_old = np.linspace(0, 1, len(y))
    x_new = np.linspace(0, 1, target_len)
    return np.interp(x_new, x_old, y)   # ✅ тут тоже была ошибка

def process_file(filename):
    print(f"\nОбрабатываю файл: {filename}")

    df = pd.read_csv(filename, sep=';')

    angle_columns = [
        "left_knee_angle",
        "right_knee_angle",
        "left_body_angle",
        "right_body_angle"
    ]

    new_df = pd.DataFrame()

    for col in angle_columns:
        print(f"  → обрабатываю {col}")

        # ✅ Преобразование строк '124,85' → float 124.85
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False).astype(float)

        y = df[col].values

        # сглаживание
        y_smooth = smooth_curve(y)

        # ресэмплирование
        y_resampled = resample_curve(y_smooth)

        new_df[col] = y_resampled

    out_name = filename.replace(".csv", "_resampled.csv")
    new_df.to_csv(out_name, sep=';', index=False)

    print(f"✔ Результат сохранён в {out_name}")


# список файлов
files = [
    "results/Ski9_landmarks_angels.csv",
    "results/Ski10_landmarks_angels.csv",
    "results/Ski11_landmarks_angels.csv",
    "results/Ski12_landmarks_angels.csv",
    "results/Ski13_landmarks_angels.csv",
    "results/Ski14_landmarks_angels.csv",
    "results/Ski15_landmarks_angels.csv"
]

for f in files:
    if os.path.exists(f):
        process_file(f)
    else:
        print(f"Файл {f} не найден, пропуск.")
