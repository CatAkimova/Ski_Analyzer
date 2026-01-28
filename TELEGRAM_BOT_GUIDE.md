# Руководство по созданию Telegram бота для анализа техники катания

## 📍 Где описаны компоненты

### Pipeline описан в:
1. **`ARCHITECTURE.md`** - полное описание архитектуры и pipeline (строки 25-53)
2. **`ski_analyzer/core/pipeline.py`** - код pipeline класса `SkiAnalysisPipeline`
3. **`process_video.py`** - пример использования pipeline

### LLM интеграция описана в:
1. **`ski_analyzer/utils/llm_recommendations.py`** - класс `LLMRecommendationGenerator`
2. **`ARCHITECTURE.md`** (строки 88-100) - подход "Эталон + LLM"

## 🏗️ Архитектура бота

### Поток данных:
```
Пользователь → Telegram → Бот получает видео
    ↓
Бот сохраняет видео локально
    ↓
Бот вызывает SkiAnalysisPipeline.analyze_user_video()
    ↓
Pipeline обрабатывает: поза → углы → сравнение с эталоном
    ↓
Бот получает результат анализа (метрики, отклонения)
    ↓
Бот передает результат в LLMRecommendationGenerator
    ↓
LLM генерирует персонализированные рекомендации
    ↓
Бот отправляет рекомендации пользователю
```

## 📦 Что нужно установить

```bash
pip install python-telegram-bot
# или
pip install aiogram  # более современная библиотека

# Для LLM (выберите один):
pip install openai      # для OpenAI
# или
pip install anthropic  # для Anthropic
```

## 🎯 Структура бота (что нужно создать)

### 1. Основной файл бота (например `telegram_bot.py`)

**Что должно быть:**
- Инициализация бота с токеном
- Обработчик команды `/start`
- Обработчик загрузки видео (message handler для video)
- Функция обработки видео через pipeline
- Функция генерации рекомендаций через LLM
- Отправка результатов пользователю

**Структура:**
```python
# 1. Импорты
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from ski_analyzer.core.pipeline import SkiAnalysisPipeline
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator
import os
import tempfile

# 2. Инициализация компонентов (один раз при старте)
pipeline = SkiAnalysisPipeline()
llm_generator = LLMRecommendationGenerator(api_key="your-api-key")

# 3. Обработчики команд
async def start(update, context):
    # Приветствие, инструкции

async def handle_video(update, context):
    # Получить видео из сообщения
    # Сохранить во временный файл
    # Обработать через pipeline
    # Получить рекомендации через LLM
    # Отправить пользователю

# 4. Главная функция
def main():
    # Создать Application
    # Добавить handlers
    # Запустить бота
```

### 2. Обработка видео (ключевая функция)

**Что нужно сделать:**

1. **Получить видео из сообщения:**
   - `update.message.video` - объект видео
   - `video.get_file()` - получить файл
   - `file.download()` - скачать на диск

2. **Сохранить во временный файл:**
   - Использовать `tempfile` для создания временного файла
   - Сохранить видео туда

3. **Обработать через pipeline:**
   - Вызвать `pipeline.analyze_user_video(video_path)`
   - Получить результат с метриками

4. **Сгенерировать рекомендации:**
   - Передать результат анализа в `llm_generator.generate_recommendations()`
   - Получить текстовые рекомендации

5. **Отправить пользователю:**
   - Отправить сообщение с рекомендациями
   - Можно добавить общий балл, метрики

6. **Очистка:**
   - Удалить временный файл после обработки

### 3. Интеграция с LLM

**Что нужно:**
- API ключ (OpenAI или Anthropic)
- Инициализировать `LLMRecommendationGenerator` с ключом
- Вызвать `generate_recommendations(analysis_result)`

**Важно:**
- Реализовать метод `call_llm_api()` в `LLMRecommendationGenerator`
- Сейчас там заглушка, нужно добавить реальный вызов API

## 🔧 Детали реализации

### Шаг 1: Получение видео

```python
# В обработчике сообщений
video = update.message.video
file = await video.get_file()
video_path = tempfile.mktemp(suffix='.mp4')
await file.download_to_drive(video_path)
```

**Что происходит:**
- Telegram отправляет видео как объект
- Нужно скачать его на диск
- Использовать временный файл

### Шаг 2: Обработка через Pipeline

```python
# Вызвать pipeline
result = pipeline.analyze_user_video(
    video_path,
    save_intermediate=False  # для бота не нужно сохранять промежуточные файлы
)

# Получить анализ
analysis = result['analysis']
# analysis содержит:
# - overall_score (общий балл)
# - angle_analysis (детальный анализ по углам)
# - recommendations (базовые рекомендации)
```

**Что происходит:**
- Pipeline обрабатывает видео полностью
- Возвращает структурированный результат
- Все этапы выполняются автоматически

### Шаг 3: Генерация LLM рекомендаций

```python
# Передать результат в LLM
llm_recommendations = llm_generator.generate_recommendations(
    analysis,
    user_profile=None  # можно добавить профиль пользователя
)
```

**Что происходит:**
- LLM получает метрики анализа
- Генерирует персонализированные рекомендации
- Возвращает список текстовых советов

### Шаг 4: Форматирование ответа

**Что отправить пользователю:**
- Общий балл (например: "Ваш балл: 53.8/100")
- Основные проблемы (кратко)
- Рекомендации от LLM (детально)

**Формат:**
```
🎿 Анализ техники катания

📊 Общий балл: 53.8/100

⚠️ Основные проблемы:
• Колени недостаточно согнуты
• Корпус отклонен назад

💡 Рекомендации:
[здесь рекомендации от LLM]
```

## ⚠️ Важные моменты

### 1. Асинхронность
- Telegram бот работает асинхронно
- Обработка видео может занять время (1-2 минуты)
- Нужно отправлять "Обрабатываю..." пока идет обработка

**Решение:**
```python
# Отправить сообщение о начале обработки
await update.message.reply_text("⏳ Обрабатываю видео...")

# Обработать видео (это может занять время)
result = pipeline.analyze_user_video(video_path)

# Отправить результат
await update.message.reply_text(recommendations)
```

### 2. Обработка ошибок
- Видео может быть некорректным
- Pipeline может упасть
- LLM API может быть недоступен

**Решение:**
```python
try:
    result = pipeline.analyze_user_video(video_path)
except Exception as e:
    await update.message.reply_text(f"❌ Ошибка: {str(e)}")
finally:
    # Удалить временный файл
    os.remove(video_path)
```

### 3. Ограничения Telegram
- Максимальный размер видео: 50MB
- Обработка может занять время
- Нужно информировать пользователя о прогрессе

### 4. Безопасность
- Не хранить видео после обработки
- Удалять временные файлы
- Не логировать личные данные

## 📝 Примерная структура кода (без полного кода)

```python
# telegram_bot.py

# 1. Импорты
import asyncio
import tempfile
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 2. Глобальные объекты (инициализировать один раз)
pipeline = None
llm_generator = None

# 3. Функция инициализации
def init_components():
    global pipeline, llm_generator
    pipeline = SkiAnalysisPipeline()
    llm_generator = LLMRecommendationGenerator(api_key=os.getenv("LLM_API_KEY"))

# 4. Обработчик /start
async def start_command(update: Update, context):
    # Приветствие и инструкции

# 5. Обработчик видео
async def handle_video_message(update: Update, context):
    # Получить видео
    # Скачать во временный файл
    # Отправить "Обрабатываю..."
    # Обработать через pipeline
    # Получить рекомендации от LLM
    # Отправить результат
    # Удалить временный файл

# 6. Главная функция
def main():
    # Инициализировать компоненты
    # Создать Application
    # Добавить handlers
    # Запустить бота

if __name__ == "__main__":
    main()
```

## 🎯 Что нужно реализовать

### Обязательно:
1. ✅ Получение видео из Telegram
2. ✅ Сохранение во временный файл
3. ✅ Вызов `pipeline.analyze_user_video()`
4. ✅ Вызов `llm_generator.generate_recommendations()`
5. ✅ Отправка результатов пользователю
6. ✅ Удаление временных файлов

### Опционально (для улучшения):
- Прогресс-бар обработки
- Кэширование результатов
- Сохранение истории анализов
- Поддержка разных форматов видео

## 🔗 Связь с существующим кодом

### Используемые классы:
1. **`SkiAnalysisPipeline`** из `ski_analyzer/core/pipeline.py`
   - Метод: `analyze_user_video(video_path)`
   - Возвращает: `{'analysis': {...}, 'files': {...}}`

2. **`LLMRecommendationGenerator`** из `ski_analyzer/utils/llm_recommendations.py`
   - Метод: `generate_recommendations(analysis_result, user_profile=None)`
   - Возвращает: список рекомендаций

### Что нужно доработать:
- В `LLMRecommendationGenerator.call_llm_api()` добавить реальный вызов API
- Сейчас там заглушка, нужно реализовать вызов OpenAI/Anthropic

## 📚 Полезные ресурсы

### Telegram Bot API:
- python-telegram-bot: https://python-telegram-bot.org/
- aiogram: https://docs.aiogram.dev/

### Примеры:
- Официальные примеры python-telegram-bot
- Документация по обработке файлов

## ✅ Чеклист перед запуском

- [ ] Установлены зависимости (python-telegram-bot, openai/anthropic)
- [ ] Получен токен бота от @BotFather
- [ ] Настроен API ключ для LLM
- [ ] Реализован метод `call_llm_api()` в LLMRecommendationGenerator
- [ ] Протестирована обработка одного видео локально
- [ ] Бот запускается и отвечает на команды
- [ ] Обработка видео работает
- [ ] LLM генерирует рекомендации
- [ ] Временные файлы удаляются

## 🚀 Следующие шаги

1. **Создать файл `telegram_bot.py`**
2. **Реализовать обработчики команд** (`/start`)
3. **Реализовать обработчик видео**
4. **Интегрировать pipeline**
5. **Интегрировать LLM**
6. **Протестировать локально**
7. **Задеплоить** (Heroku, Railway, или свой сервер)

**Помните:** Начните с простого - обработка одного видео, затем добавляйте функции!
