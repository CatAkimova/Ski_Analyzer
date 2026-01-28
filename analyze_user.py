import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

TEMPLATE_FILE = r"results\template_angles.csv"

USER_FILE = r"Ski.Videos\User\User1.MOV"

angles = [
    "left_knee_angle",
    "right_knee_angle",
    "left_body_angle",
    "right_body_angle"
]

ABS_THRESH = {
    "left_knee_angle": 10.0,
    "right_knee_angle": 10.0,
    "left_body_angle": 8.0,
    "right_body_angle": 8.0,
}

K_STD = 1,5

template = pd.read_csv(TEMPLATE_FILE)
user = pd.read_csv(USER_FILE, sep=';')

if len(template) != len(user):
    raise ValueError(
        f"Длины не совпадают: template={len(template)}, user={len(user)}. "
        f"Проверь, что и эталон, и пользовательский файл ресэмплированы до одинакового числа точек (например, 100)."
    )

feedback = []

for angle in angles:
    mean_col = f"{angle}_mean"
    std_col = f"{angle}_std"

    if mean_col not in template.columns or std_col not in template.columns:
        raise ValueError(f"В эталоне нет колонок {mean_col} / {std_col}")
    if angle not in user.columns:
        raise ValueError(f"В пользовательском файле нет колонки {angle}")

    mean = template[mean_col].values
    std = template[std_col].values
    y = user[angle].values

    diff = y - mean
    abs_diff = np.abs(diff)

    bad_mask = (abs_diff > ABS_THRESH[angle]) | (abs_diff > K_STD * std)
    percent_bad = 100 * bad_mask.sum() / len(bad_mask)
    mean_diff = float(diff.mean())

    feedback.append({
        "angle": angle,
        "percent_bad": percent_bad,
        "mean_diff_deg": mean_diff
    })

    x = np.linspace(0, 100, len(mean))

    plt.figure(figsize=(10, 5))
    plt.plot(x, mean, label="Эталон", color='blue')
    plt.fill_between(x, mean - std, mean + std,
                     alpha=0.2, color='blue', label="±1σ")
    plt.plot(x, y, label="Пользователь", color='red')
    plt.title(f"Сравнение кривых: {angle}")
    plt.xlabel("Фаза движения (0–100%)")
    plt.ylabel("Угол (град.)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


# -------- текстовый вывод рекомендаций --------
print("\n========= РЕЗУЛЬТАТ АНАЛИЗА =========")

for fb in feedback:
    angle = fb["angle"]
    p_bad = fb["percent_bad"]
    mean_diff = fb["mean_diff_deg"]

    print(f"\nУгол: {angle}")
    print(f"  Доля фазы вне нормы: {p_bad:.1f}%")
    print(f"  Среднее отклонение: {mean_diff:+.1f}°")

    if "knee" in angle:
        if p_bad > 30 and mean_diff > 0:
            print("  ➜ Колено чаще более разогнуто, чем в эталоне. "
                  "Рекомендация: увеличить сгибание колена в фазе поворота.")
        elif p_bad > 30 and mean_diff < 0:
            print("  ➜ Колено сгибается больше, чем в эталоне. Возможна излишняя посадка.")
        else:
            print("  ✔ Сгибание колена в допустимых пределах относительно эталона.")

    if "body" in angle:
        if p_bad > 30 and mean_diff > 0:
            print("  ➜ Корпус заметно отклонён назад относительно эталона. "
                  "Рекомендация: сместить центр тяжести вперёд, ближе к носкам лыж.")
        elif p_bad > 30 and mean_diff < 0:
            print("  ➜ Корпус подан вперёд сильнее, чем в эталоне. Следите за балансом и сохранением стойки.")
        else:
            print("  ✔ Наклон корпуса близок к эталонному.")