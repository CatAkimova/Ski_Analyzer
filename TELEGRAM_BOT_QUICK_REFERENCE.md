# Быстрая справка: Telegram бот

## 📍 Где что находится

### Pipeline:
- **Описание:** `ARCHITECTURE.md` (строки 25-53)
- **Код:** `ski_analyzer/core/pipeline.py`
- **Класс:** `SkiAnalysisPipeline`
- **Метод:** `analyze_user_video(video_path)` → возвращает `{'analysis': {...}}`

### LLM:
- **Код:** `ski_analyzer/utils/llm_recommendations.py`
- **Класс:** `LLMRecommendationGenerator`
- **Метод:** `generate_recommendations(analysis_result)` → возвращает список строк

## 🔄 Поток работы

```
1. Пользователь отправляет видео в Telegram
   ↓
2. Бот получает: update.message.video
   ↓
3. Бот скачивает: file.download_to_drive(temp_path)
   ↓
4. Бот вызывает: pipeline.analyze_user_video(temp_path)
   ↓
5. Бот получает: result['analysis'] (метрики, отклонения)
   ↓
6. Бот вызывает: llm_generator.generate_recommendations(result['analysis'])
   ↓
7. Бот отправляет: рекомендации пользователю
   ↓
8. Бот удаляет: os.remove(temp_path)
```

## 💻 Ключевые фрагменты кода (структура)

### 1. Инициализация компонентов
```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator

pipeline = SkiAnalysisPipeline()
llm_generator = LLMRecommendationGenerator(api_key="your-key")
```

### 2. Получение видео из Telegram
```python
video = update.message.video
file = await video.get_file()
temp_path = tempfile.mktemp(suffix='.mp4')
await file.download_to_drive(temp_path)
```

### 3. Обработка через Pipeline
```python
result = pipeline.analyze_user_video(
    temp_path,
    save_intermediate=False
)
analysis = result['analysis']  # Метрики и отклонения
```

### 4. Генерация рекомендаций через LLM
```python
recommendations = llm_generator.generate_recommendations(analysis)
# Возвращает список строк с рекомендациями
```

### 5. Отправка пользователю
```python
text = f"🎿 Анализ техники\n\n📊 Балл: {analysis['overall_score']}/100\n\n"
text += "💡 Рекомендации:\n"
for rec in recommendations:
    text += f"• {rec}\n"

await update.message.reply_text(text)
```

### 6. Очистка
```python
os.remove(temp_path)  # Удалить временный файл
```

## ⚠️ Важно помнить

1. **Асинхронность:** Все обработчики должны быть `async`
2. **Временные файлы:** Использовать `tempfile` и удалять после обработки
3. **Обработка ошибок:** Обернуть в `try/except`
4. **Прогресс:** Отправлять "Обрабатываю..." пока идет обработка
5. **LLM API:** Реализовать `call_llm_api()` в `LLMRecommendationGenerator`

## 📦 Зависимости

```bash
pip install python-telegram-bot
pip install openai  # или anthropic
```

## 🎯 Минимальный рабочий бот

1. Обработчик `/start` - приветствие
2. Обработчик видео - получить, обработать, отправить результат
3. Главная функция - запуск бота

**Все остальное - опционально для улучшения UX!**
