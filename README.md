# Ski Analyzer - Система анализа техники катания на горных лыжах

Автоматизированная система для анализа техники катания на горных лыжах через обработку видео и сравнение с эталоном.

## 🚀 Быстрый старт

### Установка

```bash
pip install -r requirements.txt
```

### Использование

#### 1. Построение эталона (один раз)

```bash
# Соберите все resampled файлы в results/ и выполните:
python process_video.py --build-template
```

#### 2. Обработка видео пользователя

```bash
# Простая обработка
python process_video.py path/to/video.mp4

# С анализом и рекомендациями
python process_video.py path/to/video.mp4 --analyze

# Сохранить все промежуточные файлы
python process_video.py path/to/video.mp4 --analyze --save-all
```

## 📁 Структура проекта

```
.
├── ski_analyzer/          # Основной пакет
│   ├── core/              # Модули обработки
│   ├── config/            # Конфигурация
│   └── utils/             # Утилиты
├── results/               # Результаты обработки
├── Ski.Videos/           # Видео файлы
├── process_video.py      # Главный скрипт
└── requirements.txt      # Зависимости
```

## 🔧 Использование в коде

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

# Создаем pipeline
pipeline = SkiAnalysisPipeline()

# Обрабатываем видео
result = pipeline.analyze_user_video(
    "video.mp4",
    save_intermediate=True
)

# Получаем рекомендации
recommendations = result['analysis']['recommendations']
for rec in recommendations:
    print(rec)
```

## 📊 Pipeline обработки

1. **Извлечение позы** - YOLOv8 определяет ключевые точки
2. **Вычисление углов** - Расчет углов коленей и корпуса
3. **Обработка данных** - Сглаживание и ресемплинг до 100 точек
4. **Сравнение с эталоном** - Анализ отклонений
5. **Генерация рекомендаций** - Текстовые советы по улучшению

## 🎯 Для бизнеса

Система готова к интеграции в веб-сервис. Подробные рекомендации по архитектуре см. в [ARCHITECTURE.md](ARCHITECTURE.md).

### Рекомендуемый подход:
- **Эталон + LLM** для генерации рекомендаций
- Быстрая разработка MVP
- Прозрачность и объяснимость
- Легкая интеграция с фронтендом

## 📝 Требования

- Python 3.8+
- PyTorch
- Ultralytics YOLO
- OpenCV
- Pandas, NumPy, SciPy

## 📄 Лицензия

[Укажите лицензию]

