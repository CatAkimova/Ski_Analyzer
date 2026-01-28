# Как использовать Pipeline

## 🎯 Варианты использования

### Вариант 1: Только обработка видео (БЕЗ рекомендаций)

**Для чего:** Когда нужно только обработать видео (поза → углы → ресемплинг), без анализа и рекомендаций.

**Команда:**
```bash
python process_video.py "Ski.Videos\User\User1.MOV"
```

**Что происходит:**
- Извлекается поза
- Вычисляются углы
- Данные обрабатываются (сглаживание и ресемплинг)
- Создаются файлы в `results/`

**Результат:** Только обработанные данные, без анализа.

**В коде:**
```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Только обработка, без анализа
files = pipeline.process_video("video.mp4")

# Получаете:
# - files["landmarks"] - путь к landmarks
# - files["angles"] - путь к углам (если save_intermediate=True)
# - files["resampled"] - путь к resampled файлу
# - files["video_annotated"] - путь к видео с аннотациями (если save_annotated_video=True)
```

### Вариант 2: Анализ с базовыми рекомендациями (БЕЗ LLM)

**Для чего:** Когда нужен анализ и базовые рекомендации, но без LLM.

**Команда:**
```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze
```

**Что происходит:**
- Обработка видео
- Анализ (сравнение с эталоном)
- Генерация базовых рекомендаций

**Результат:** Балл, метрики, базовые рекомендации.

**В коде:**
```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Анализ БЕЗ LLM
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=False  # ← БЕЗ LLM
)

# Получаете:
# - result["analysis"]["overall_score"] - балл
# - result["analysis"]["angle_analysis"] - детальный анализ
# - result["analysis"]["recommendations"] - базовые рекомендации
# НЕТ result["llm_recommendations"]
```

### Вариант 3: Полный анализ с LLM рекомендациями

**Для чего:** Когда нужны детальные рекомендации от Gemini.

**Команда:**
```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

**Что происходит:**
- Обработка видео
- Анализ
- Базовые рекомендации
- LLM рекомендации от Gemini

**Результат:** Балл, метрики, базовые + LLM рекомендации.

**В коде:**
```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Анализ С LLM
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=True  # ← С LLM
)

# Получаете:
# - result["analysis"] - базовый анализ
# - result["llm_recommendations"] - LLM рекомендации (если доступен)
```

## 📋 Все команды

### Только обработка:
```bash
python process_video.py "video.mp4"
```

### Обработка + анализ (базовые рекомендации):
```bash
python process_video.py "video.mp4" --analyze
```

### Обработка + анализ + LLM рекомендации:
```bash
python process_video.py "video.mp4" --analyze --use-llm
```

### Сохранить все файлы:
```bash
python process_video.py "video.mp4" --analyze --use-llm --save-all
```

## 💻 Использование в коде

### Пример 1: Только обработка (для других целей)

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Только обработка - получаете обработанные данные
files = pipeline.process_video(
    "video.mp4",
    save_intermediate=True,
    save_annotated_video=False
)

# Используйте файлы для своих целей
landmarks_path = files["landmarks"]
angles_path = files["angles"]
resampled_path = files["resampled"]
```

### Пример 2: Анализ без LLM

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Анализ БЕЗ LLM
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=False  # ← явно отключаем LLM
)

# Используйте только базовые рекомендации
score = result['analysis']['overall_score']
recommendations = result['analysis']['recommendations']
```

### Пример 3: Анализ с LLM

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Анализ С LLM
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=True  # ← включаем LLM
)

# Используйте оба типа рекомендаций
basic_recs = result['analysis']['recommendations']
if 'llm_recommendations' in result:
    llm_recs = result['llm_recommendations']
```

## ✅ Итог

**Для проверки с Gemini рекомендациями:**
```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

**Для использования без рекомендаций (только обработка):**
```bash
python process_video.py "Ski.Videos\User\User1.MOV"
```

**Или в коде:**
```python
# Без рекомендаций
files = pipeline.process_video("video.mp4")

# С базовыми рекомендациями (без LLM)
result = pipeline.analyze_user_video("video.mp4", use_llm=False)

# С LLM рекомендациями
result = pipeline.analyze_user_video("video.mp4", use_llm=True)
```

Все готово! 🎉
