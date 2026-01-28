from fileinput import filename

import pandas as pd
import numpy as np
import math
import os

def find_angels(filename, out_dir="results"):

    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(filename, sep=';')

    base = os.path.splitext(os.path.basename(filename))[0]
    csv_out = os.path.join(out_dir, base + "_angels.csv")

    def calculate_angle(a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return angle

    # индексы ключевых точек
    LEFT_HIP = 11
    LEFT_KNEE = 13
    LEFT_ANKLE = 15
    LEFT_SHOULDER = 5

    RIGHT_HIP = 12
    RIGHT_KNEE = 14
    RIGHT_ANKLE = 16
    RIGHT_SHOULDER = 6

    # Список для углов
    angles = []

    for i, row in df.iterrows():
        left_hip = [row[f'x_{LEFT_HIP}'], row[f'y_{LEFT_HIP}']]
        left_knee = [row[f'x_{LEFT_KNEE}'], row[f'y_{LEFT_KNEE}']]
        left_ankle = [row[f'x_{LEFT_ANKLE}'], row[f'y_{LEFT_ANKLE}']]
        left_shoulder = [row[f'x_{LEFT_SHOULDER}'], row[f'y_{LEFT_SHOULDER}']]

        right_hip = [row[f'x_{RIGHT_HIP}'], row[f'y_{RIGHT_HIP}']]
        right_knee = [row[f'x_{RIGHT_KNEE}'], row[f'y_{RIGHT_KNEE}']]
        right_ankle = [row[f'x_{RIGHT_ANKLE}'], row[f'y_{RIGHT_ANKLE}']]
        right_shoulder = [row[f'x_{RIGHT_SHOULDER}'], row[f'y_{RIGHT_SHOULDER}']]

        # Углы коленей и корпуса
        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
        left_body_angle = calculate_angle(left_shoulder, left_hip, left_knee)
        right_body_angle = calculate_angle(right_shoulder, right_hip, right_knee)

        angles.append({
            'frame': i,
            'left_knee_angle': left_knee_angle,
            'right_knee_angle': right_knee_angle,
            'left_body_angle': left_body_angle,
            'right_body_angle': right_body_angle
        })

    angles_df = pd.DataFrame(angles)
    angles_df.to_csv(csv_out, sep=';', index=False, decimal=',',  encoding='utf-8-sig')

files = [
    'User1_landmarks.csv',
]

for f in files:
    if os.path.exists(f):
        print('Файл найден')
        find_angels(f, out_dir="results")
    else:
        print('Файл не найден, пропуск')