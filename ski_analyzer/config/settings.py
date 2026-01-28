"""
Конфигурационные настройки для системы анализа
"""
import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent.parent
RESULTS_DIR = BASE_DIR / "results"
VIDEOS_DIR = BASE_DIR / "Ski.Videos"
TEMPLATE_FILE = RESULTS_DIR / "template_angles.csv"

# Настройки обработки видео
YOLO_MODEL_PATH = BASE_DIR / "yolov8n-pose.pt"
VIDEO_OUTPUT_DIR = VIDEOS_DIR

# Настройки ресемплинга
N_RESAMPLE_POINTS = 100  # Количество точек после ресемплинга
SMOOTH_WINDOW = 11  # Окно для сглаживания
SMOOTH_POLY = 3  # Порядок полинома для сглаживания

# Индексы ключевых точек YOLO (COCO формат)
LEFT_HIP = 11
LEFT_KNEE = 13
LEFT_ANKLE = 15
LEFT_SHOULDER = 5

RIGHT_HIP = 12
RIGHT_KNEE = 14
RIGHT_ANKLE = 16
RIGHT_SHOULDER = 6

# Углы для анализа
ANGLES = [
    "left_knee_angle",
    "right_knee_angle",
    "left_body_angle",
    "right_body_angle"
]

# Пороги для анализа (в градусах)
ABS_THRESHOLDS = {
    "left_knee_angle": 10.0,
    "right_knee_angle": 10.0,
    "left_body_angle": 8.0,
    "right_body_angle": 8.0,
}

# Коэффициент стандартного отклонения для определения отклонений
K_STD = 1.5

# Процент отклонений для выдачи рекомендаций
BAD_PERCENT_THRESHOLD = 30.0

# Создаем директории если их нет
RESULTS_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)

