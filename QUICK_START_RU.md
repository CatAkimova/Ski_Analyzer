# Быстрый старт - Инструкция на русском

## 🎯 Что было сделано

Создана автоматизированная система для анализа техники катания на горных лыжах. Теперь весь процесс обработки видео выполняется одной командой!

## 📦 Что изменилось

### До:
- Нужно было запускать несколько скриптов вручную
- `test_pose_auto.py` → `analyze_angels_auto.py` → `resample.py` → `analyze_user.py`
- Сложно отслеживать промежуточные файлы

### После:
- Одна команда для всего: `python process_video.py video.mp4 --analyze`
- Автоматическая обработка всех этапов
- Четкая структура модулей

## 🚀 Как использовать

### 1. Построение эталона (если еще не сделано)

```bash
python process_video.py --build-template
```

Это создаст `results/template_angles.csv` из всех файлов `*_resampled.csv` в папке `results/`.

### 2. Обработка видео пользователя

#### Простая обработка (без анализа):
```bash
python process_video.py "Ski.Videos/User/User1.MOV"
```

#### С анализом и рекомендациями:
```bash
python process_video.py "Ski.Videos/User/User1.MOV" --analyze
```

#### Сохранение всех промежуточных файлов:
```bash
python process_video.py "Ski.Videos/User/User1.MOV" --analyze --save-all
```

## 📁 Новая структура проекта

```
ski_analyzer/              # Новый модульный пакет
├── core/                 # Основные модули
│   ├── pose_extractor.py      # Извлечение позы
│   ├── angle_calculator.py    # Вычисление углов
│   ├── data_processor.py      # Сглаживание и ресемплинг
│   ├── template_builder.py    # Построение эталона
│   ├── analyzer.py            # Анализ и рекомендации
│   └── pipeline.py            # Единый pipeline
├── config/
│   └── settings.py            # Все настройки
└── utils/

process_video.py          # Главный скрипт для запуска
example_usage.py          # Примеры использования
```

## 💻 Использование в коде

### Простой пример:

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

# Создаем pipeline
pipeline = SkiAnalysisPipeline()

# Обрабатываем и анализируем видео
result = pipeline.analyze_user_video("video.mp4")

# Получаем рекомендации
for rec in result['analysis']['recommendations']:
    print(rec)
```

### Использование отдельных компонентов:

```python
from ski_analyzer.core.pose_extractor import PoseExtractor
from ski_analyzer.core.angle_calculator import AngleCalculator

# Извлечение позы
extractor = PoseExtractor()
landmarks_df, _ = extractor.extract_pose("video.mp4")

# Вычисление углов
calculator = AngleCalculator()
angles_df = calculator.calculate_angles(landmarks_df)
```

## 🎯 Что делать дальше?

### Для разработки MVP:

1. **Интеграция LLM для рекомендаций** (см. `ARCHITECTURE.md`)
   - Использовать OpenAI/Anthropic API
   - Генерировать персонализированные рекомендации
   - Улучшить качество текста рекомендаций

2. **Создание API** (FastAPI/Flask)
   - Эндпоинт для загрузки видео
   - Эндпоинт для получения результатов
   - Интеграция с фронтендом

3. **Улучшение эталона**
   - Добавить больше примеров профессионального катания
   - Создать эталоны для разных стилей (карвинг, фрирайд и т.д.)
   - Эталоны для разных уровней (начальный, средний, продвинутый)

### Для бизнеса:

1. **Рекомендуемый подход: Эталон + LLM**
   - Прозрачность и объяснимость
   - Быстрая разработка
   - Низкие затраты
   - Легкая интеграция

2. **Масштабирование:**
   - Очередь задач для обработки видео (Celery)
   - Кэширование результатов
   - CDN для хранения видео
   - GPU серверы для YOLO

Подробнее см. `ARCHITECTURE.md`

## 🔧 Настройка

Все настройки находятся в `ski_analyzer/config/settings.py`:

- Пороги для анализа (`ABS_THRESHOLDS`, `K_STD`)
- Количество точек ресемплинга (`N_RESAMPLE_POINTS`)
- Пути к файлам и директориям

## ❓ FAQ

**Q: Как обработать несколько видео сразу?**
A: Используйте цикл в Python или создайте скрипт-обертку.

**Q: Можно ли использовать свою модель YOLO?**
A: Да, укажите путь в `SkiAnalysisPipeline(model_path="your_model.pt")`

**Q: Как добавить новые углы для анализа?**
A: Измените `ANGLES` в `settings.py` и добавьте вычисление в `AngleCalculator`

**Q: Как интегрировать LLM?**
A: См. раздел "Интеграция LLM" в `ARCHITECTURE.md`

## 📞 Поддержка

Если возникли вопросы или проблемы, проверьте:
1. `ARCHITECTURE.md` - детальная архитектура
2. `example_usage.py` - примеры кода
3. Логи ошибок при выполнении

