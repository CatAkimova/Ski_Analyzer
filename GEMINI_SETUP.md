# Настройка Google Gemini API

## 🎯 Быстрый старт

### Шаг 1: Получить API ключ Gemini

1. Перейдите на https://makersuite.google.com/app/apikey
2. Войдите в Google аккаунт
3. Нажмите "Create API Key"
4. Скопируйте ключ (начинается с `AIza...`)

**Важно:** Ключ показывается один раз! Сохраните его.

### Шаг 2: Установить библиотеку

```bash
pip install google-generativeai
```

### Шаг 3: Сохранить ключ

#### Вариант A: В .env файле (рекомендуется)

Создайте или откройте файл `.env` в корне проекта:

```
GEMINI_API_KEY=AIzaваш-полный-ключ-здесь
```

#### Вариант B: Через скрипт

```bash
python setup_api_key_simple.py
```

Или создайте вручную файл `.env` с ключом.

### Шаг 4: Использовать в коде

```python
import os
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator

# Загрузить из .env
from pathlib import Path
env_file = Path(".env")
if env_file.exists():
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                os.environ["GEMINI_API_KEY"] = key
                break

# Создать генератор с Gemini
llm_gen = LLMRecommendationGenerator(
    api_key=os.getenv("GEMINI_API_KEY"),
    provider="gemini"  # ← важно указать!
)
```

### Шаг 5: Протестировать

```bash
python test_gemini.py
```

## 📝 Пример использования

```python
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator
import os

# Инициализация
llm_gen = LLMRecommendationGenerator(
    api_key=os.getenv("GEMINI_API_KEY"),
    provider="gemini"
)

# Генерация рекомендаций
recommendations = llm_gen.generate_recommendations(analysis_result)

# Вывод
for rec in recommendations:
    print(rec)
```

## 🔧 Для Telegram бота

В файле бота:

```python
import os
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator

# Инициализация (один раз при старте)
llm_generator = LLMRecommendationGenerator(
    api_key=os.getenv("GEMINI_API_KEY"),
    provider="gemini"  # ← важно!
)

# Использование в обработчике
async def handle_video(update, context):
    # ... обработка видео ...
    recommendations = llm_generator.generate_recommendations(analysis)
    # ...
```

## ✅ Преимущества Gemini

- ✅ **Бесплатно** (есть бесплатный тариф)
- ✅ **Доступен в большинстве регионов**
- ✅ **Хорошее качество ответов**
- ✅ **Быстрая работа**

## ⚠️ Важно

1. **Ключ начинается с `AIza`** - это нормально для Gemini
2. **Не коммитьте ключ в Git** - используйте `.env` (уже в `.gitignore`)
3. **Лимиты:** Бесплатный тариф имеет лимиты запросов
4. **Модель:** Используется `gemini-pro` (можно изменить в коде)

## 🔍 Проверка работы

После настройки запустите тест:

```bash
python test_gemini.py
```

Должен вывести ответ от Gemini.

## 📚 Документация

- Официальная документация: https://ai.google.dev/docs
- API ключи: https://makersuite.google.com/app/apikey
