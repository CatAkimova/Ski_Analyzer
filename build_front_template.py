import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

RESULTS_DIR = "results"


pattern = os.path.join(RESULTS_DIR, "*_resampled.csv")
files = sorted(glob.glob(pattern))

print("Найдено файлов", len(files))
for f in files:
    print("Найден файл", f)

if len(files) == 0:
    raise FileNotFoundError("в папке нет файлов resampled")

angles = [
    "left_knee_angle",
    "right_knee_angle",
    "left_body_angle",
    "right_body_angle"
]

def validate_columns(df, filename):
    for col in angles:
        if col not in df.columns:
            raise ValueError(f"В файле {filename} отсутствует колонка: {col}")

data = {angle: [] for angle in angles}

for f in files:
    df = pd.read_csv(f, sep =';')

    for angle in angles:
        data[angle].append(df[angle].values)

print("Все файлы успешно загружены и содержат нужные колонки.")

template = pd.DataFrame()

for angle in angles:
    curves = np.vstack(data[angle])
    mean_curve = curves.mean(axis=0)
    std_curve = curves.std(axis=0)

    template[f"{angle}_mean"] = mean_curve
    template[f"{angle}_std"] = std_curve

output_path = os.path.join(RESULTS_DIR, "template_angles.csv")
template.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')

for angle in angles:
    plt.figure(figsize=(10, 5))

    for curve in data[angle]:
        plt.plot(curve, color='lightgray', linewidth=1)

    plt.plot(template[f"{angle}_mean"], color='blue', linewidth=2, label='Средняя кривая')

    plt.fill_between(
        range(100),
        template[f"{angle}_mean"] - template[f"{angle}_std"],
        template[f"{angle}_mean"] + template[f"{angle}_std"],
        color='blue', alpha=0.25, label='±1σ'
    )

    plt.title(f"Эталонная кривая: {angle}")
    plt.xlabel("Фаза движения (0–100%)")
    plt.ylabel("Угол (град.)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()
