# Интеграция LLM рекомендаций в Pipeline

## ✅ Что сделано

LLM рекомендации теперь интегрированы в `SkiAnalysisPipeline`!

## 📍 Где находится код

**Файл:** `ski_analyzer/core/pipeline.py`  
**Метод:** `analyze_user_video()` (строки 105-182)

## 🎯 Как использовать

### Вариант 1: С автоматическим созданием LLM генератора

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

pipeline = SkiAnalysisPipeline()

# Обработка с LLM рекомендациями
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=True  # ← включить LLM
)

# Результаты
analysis = result['analysis']  # Базовый анализ
llm_recs = result.get('llm_recommendations')  # LLM рекомендации (если есть)
```

### Вариант 2: С передачей своего LLM генератора

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator
import os

pipeline = SkiAnalysisPipeline()

# Создаем LLM генератор
llm_gen = LLMRecommendationGenerator(
    api_key=os.getenv("GEMINI_API_KEY"),
    provider="gemini"
)

# Обработка с LLM
result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=True,
    llm_generator=llm_gen  # ← передаем свой генератор
)
```

### Вариант 3: С профилем пользователя

```python
user_profile = {
    "level": "средний",
    "experience": "3 года",
    "goals": "улучшить технику карвинга"
}

result = pipeline.analyze_user_video(
    "video.mp4",
    use_llm=True,
    user_profile=user_profile  # ← для персонализации
)
```

## 📊 Структура результата

```python
result = {
    "files": {
        "landmarks": "path/to/landmarks.csv",
        "angles": "path/to/angles.csv",
        "resampled": "path/to/resampled.csv",
        "video_annotated": "path/to/video.mp4"  # если save_annotated_video=True
    },
    "analysis": {
        "overall_score": 53.8,
        "angle_analysis": [...],
        "recommendations": [...]  # Базовые рекомендации
    },
    "llm_recommendations": [...]  # LLM рекомендации (если use_llm=True)
}
```

## 🔧 Параметры метода

### `analyze_user_video()`

- **video_path** (обязательно): Путь к видео
- **template_path** (опционально): Путь к эталону (по умолчанию из настроек)
- **save_intermediate** (по умолчанию True): Сохранять промежуточные файлы
- **use_llm** (по умолчанию False): Использовать LLM для рекомендаций
- **llm_generator** (опционально): Экземпляр LLMRecommendationGenerator
- **user_profile** (опционально): Профиль пользователя для персонализации

## 💡 Примеры использования

### Простой пример (без LLM):

```python
result = pipeline.analyze_user_video("video.mp4")
recommendations = result['analysis']['recommendations']
```

### С LLM:

```python
result = pipeline.analyze_user_video("video.mp4", use_llm=True)

# Базовые рекомендации
basic_recs = result['analysis']['recommendations']

# LLM рекомендации
if 'llm_recommendations' in result:
    llm_recs = result['llm_recommendations']
```

### Для Telegram бота:

```python
# В обработчике видео
result = pipeline.analyze_user_video(
    video_path,
    use_llm=True,
    llm_generator=llm_generator  # создан при старте бота
)

# Отправляем пользователю
message = f"Балл: {result['analysis']['overall_score']}/100\n\n"

if 'llm_recommendations' in result:
    message += "Рекомендации:\n"
    for rec in result['llm_recommendations']:
        message += f"• {rec}\n"
else:
    # Fallback на базовые
    for rec in result['analysis']['recommendations']:
        message += f"• {rec}\n"

await update.message.reply_text(message)
```

## ⚠️ Важно

1. **LLM генератор создается автоматически** если `use_llm=True` и `llm_generator=None`
   - Ищет `GEMINI_API_KEY` или `OPENAI_API_KEY` в переменных окружения
   - Если ключ не найден - используются только базовые рекомендации

2. **Обработка ошибок:**
   - Если LLM недоступен - используются базовые рекомендации
   - Ошибки логируются, но не прерывают выполнение

3. **Производительность:**
   - LLM запрос добавляет 2-5 секунд к обработке
   - Можно отключить через `use_llm=False`

## ✅ Готово к использованию!

Теперь pipeline полностью интегрирован с LLM. Можно использовать в Telegram боте или других сервисах!
