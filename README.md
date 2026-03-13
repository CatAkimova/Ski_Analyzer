# Ski Analyzer

Система анализа техники катания на горных лыжах по видео: извлечение позы (YOLOv8), расчёт углов коленей и корпуса, сравнение с эталоном и генерация рекомендаций. Рекомендации можно получать в виде текста от LLM (Google Gemini или OpenAI). Реализованы REST API (FastAPI) и Telegram-бот.

## Что делает система

- **Обработка видео:** детекция человека и ключевых точек (YOLOv8-pose), расчёт углов по кадрам, сглаживание и ресемплинг к единой фазе движения.
- **Эталон:** строится по нарезке циклов из эталонных видео (например, профессиональное катание); по нему считается отклонение пользователя.
- **Анализ:** сравнение траекторий углов с эталоном, оценка, список отклонений по углам.
- **Рекомендации:** базовые по правилам или через LLM (Gemini/OpenAI) — текст «ошибки + рекомендации» с учётом профиля пользователя (уровень, опыт, цели).
- **API и бот:** загрузка видео через REST API или Telegram, получение отчёта и при необходимости LLM-рекомендаций.

## Стек

- **CV/ML:** PyTorch, Ultralytics YOLOv8-pose, OpenCV, NumPy, SciPy, Pandas
- **LLM:** Google Gemini API, OpenAI API (опционально)
- **Backend:** Python 3.8+, FastAPI
- **Бот:** pyTelegramBotAPI

## Быстрый старт

### Установка

```bash
pip install -r requirements.txt
```

### Построение эталона (один раз)

Соберите в `results/` все нужные `*_resampled.csv` (из эталонных видео), затем:

```bash
python process_video.py --build-template
```

Создаётся `results/template_angles.csv`.

### Обработка видео

```bash
# Только обработка (поза → углы → ресемплинг)
python process_video.py path/to/video.mp4

# С анализом и рекомендациями (без LLM)
python process_video.py path/to/video.mp4 --analyze

# С сохранением промежуточных файлов
python process_video.py path/to/video.mp4 --analyze --save-all
```

Для рекомендаций через LLM нужен API-ключ (см. [GEMINI_SETUP.md](GEMINI_SETUP.md)) и вызов pipeline с `use_llm=True` и переданным `LLMRecommendationGenerator` (в CLI при наличии ключа в `.env` можно добавить флаг, если реализован).

### Использование в коде

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()
result = pipeline.analyze_user_video("video.mp4", save_intermediate=True)
recommendations = result["analysis"]["recommendations"]
```

### API

```bash
uvicorn api_service:app --reload
```

POST `/analyze-video`: загрузка видео (multipart), в ответе — анализ и при настроенном LLM рекомендации.

### Telegram-бот

В `.env` задайте `TELEGRAM_BOT_TOKEN` и `API_ANALYZE_URL` (адрес API). Запуск бота — по инструкции в коде (`ski_analyzer/utils/TelegramBot.py`).

## Структура проекта

```
ski_analyzer/
├── core/                  # Пайплайн обработки
│   ├── pose_extractor.py  # Извлечение позы (YOLOv8)
│   ├── angle_calculator.py
│   ├── data_processor.py  # Сглаживание, ресемплинг
│   ├── template_builder.py
│   ├── analyzer.py       # Сравнение с эталоном, отчёт
│   └── pipeline.py       # Единый сценарий
├── utils/
│   ├── llm_recommendations.py  # LLM (Gemini/OpenAI)
│   └── TelegramBot.py
└── config/
api_service.py             # FastAPI
process_video.py           # CLI
```

## Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура, эталон vs ML, интеграция в сервис
- [API_SPECIFICATION.md](API_SPECIFICATION.md) — описание API
- [GEMINI_SETUP.md](GEMINI_SETUP.md) — настройка Gemini для рекомендаций
- [LLM_API_IMPLEMENTATION.md](LLM_API_IMPLEMENTATION.md) — вызовы LLM (OpenAI/Anthropic)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — для разработчиков
- [DATASET_GUIDE.md](DATASET_GUIDE.md), [ML_SUMMARY.md](ML_SUMMARY.md) — данные и ML

## Требования

- Python 3.8+
- PyTorch, Ultralytics YOLO, OpenCV, Pandas, NumPy, SciPy

Для LLM: `google-generativeai` (Gemini) и/или `openai` (OpenAI). Ключи — в переменных окружения (`.env`), не в коде.
