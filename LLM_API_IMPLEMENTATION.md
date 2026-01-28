# Реализация метода `call_llm_api()` в LLMRecommendationGenerator

## 📍 Где находится код

**Файл:** `ski_analyzer/utils/llm_recommendations.py`  
**Метод:** `call_llm_api()` (строки 98-121)  
**Текущее состояние:** Заглушка, нужно реализовать реальный вызов API

## 🎯 Что нужно сделать

Заменить заглушку на реальный вызов LLM API (OpenAI или Anthropic).

## 🔧 Вариант 1: OpenAI (рекомендуется для начала)

### Шаг 1: Установить библиотеку

```bash
pip install openai
```

### Шаг 2: Получить API ключ

1. Зарегистрироваться на https://platform.openai.com
2. Перейти в API Keys
3. Создать новый ключ
4. Сохранить ключ (он показывается только один раз!)

### Шаг 3: Реализовать метод

**Заменить метод `call_llm_api()` в `llm_recommendations.py`:**

```python
def call_llm_api(self, prompt: str) -> str:
    """
    Вызывает LLM API (OpenAI)
    
    Args:
        prompt: Промпт для LLM
        
    Returns:
        Ответ от LLM
    """
    import openai
    
    # Устанавливаем API ключ
    openai.api_key = self.api_key
    
    try:
        # Вызываем API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # или "gpt-3.5-turbo" для экономии
            messages=[
                {
                    "role": "system",
                    "content": "Ты профессиональный инструктор по горным лыжам. "
                               "Дай конкретные и практичные рекомендации по улучшению техники."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Креативность (0-1)
            max_tokens=500    # Максимальная длина ответа
        )
        
        # Извлекаем текст ответа
        return response.choices[0].message.content
        
    except Exception as e:
        # Обработка ошибок
        return f"Ошибка при обращении к LLM: {str(e)}"
```

### Шаг 4: Использовать новый API (v1.0+)

Если используете новую версию OpenAI библиотеки (v1.0+):

```python
def call_llm_api(self, prompt: str) -> str:
    """
    Вызывает LLM API (OpenAI v1.0+)
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=self.api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # или "gpt-3.5-turbo"
            messages=[
                {
                    "role": "system",
                    "content": "Ты профессиональный инструктор по горным лыжам. "
                               "Дай конкретные и практичные рекомендации по улучшению техники."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Ошибка при обращении к LLM: {str(e)}"
```

## 🔧 Вариант 2: Anthropic (Claude)

### Шаг 1: Установить библиотеку

```bash
pip install anthropic
```

### Шаг 2: Получить API ключ

1. Зарегистрироваться на https://console.anthropic.com
2. Создать API ключ
3. Сохранить ключ

### Шаг 3: Реализовать метод

```python
def call_llm_api(self, prompt: str) -> str:
    """
    Вызывает LLM API (Anthropic Claude)
    """
    import anthropic
    
    client = anthropic.Anthropic(api_key=self.api_key)
    
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",  # или "claude-3-sonnet-20240229"
            max_tokens=500,
            system="Ты профессиональный инструктор по горным лыжам. "
                   "Дай конкретные и практичные рекомендации по улучшению техники.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return message.content[0].text
        
    except Exception as e:
        return f"Ошибка при обращении к LLM: {str(e)}"
```

## 🔧 Вариант 3: Поддержка обоих провайдеров

Можно сделать универсальный метод, который поддерживает оба:

```python
def call_llm_api(self, prompt: str) -> str:
    """
    Вызывает LLM API (поддержка OpenAI и Anthropic)
    """
    if self.provider == "openai":
        return self._call_openai(prompt)
    elif self.provider == "anthropic":
        return self._call_anthropic(prompt)
    else:
        return "Неподдерживаемый провайдер LLM"
    
def _call_openai(self, prompt: str) -> str:
    """Вызов OpenAI API"""
    from openai import OpenAI
    
    client = OpenAI(api_key=self.api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты профессиональный инструктор по горным лыжам."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка OpenAI: {str(e)}"
    
def _call_anthropic(self, prompt: str) -> str:
    """Вызов Anthropic API"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=self.api_key)
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            system="Ты профессиональный инструктор по горным лыжам.",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Ошибка Anthropic: {str(e)}"
```

## ⚙️ Настройки модели

### OpenAI модели:
- **gpt-4** - самый мощный, дороже
- **gpt-3.5-turbo** - быстрее и дешевле, достаточно для рекомендаций
- **gpt-4-turbo** - баланс между качеством и ценой

### Anthropic модели:
- **claude-3-opus** - самый мощный
- **claude-3-sonnet** - баланс (рекомендуется)
- **claude-3-haiku** - быстрый и дешевый

### Параметры:
- **temperature** (0-1): Креативность ответов
  - 0.3-0.5: более детерминированные ответы
  - 0.7-0.9: более креативные ответы
- **max_tokens**: Максимальная длина ответа
  - 300-500: для кратких рекомендаций
  - 1000+: для детальных рекомендаций

## 🔐 Безопасность API ключей

**НЕ храните ключи в коде!** Используйте переменные окружения:

```python
import os

# В коде
llm_generator = LLMRecommendationGenerator(
    api_key=os.getenv("OPENAI_API_KEY")  # или ANTHROPIC_API_KEY
)

# В .env файле или системных переменных
OPENAI_API_KEY=sk-...
```

## 📝 Пример использования

```python
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator
import os

# Инициализация с API ключом
llm_gen = LLMRecommendationGenerator(
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="openai"
)

# Генерация рекомендаций
recommendations = llm_gen.generate_recommendations(analysis_result)

# Вывод
for rec in recommendations:
    print(rec)
```

## ⚠️ Важные моменты

1. **Обработка ошибок:** Всегда оборачивайте в try/except
2. **Лимиты API:** Учитывайте rate limits (количество запросов в минуту)
3. **Стоимость:** Следите за расходами, особенно с GPT-4
4. **Таймауты:** Добавьте таймауты для долгих запросов
5. **Кэширование:** Можно кэшировать похожие запросы для экономии

## 🧪 Тестирование

После реализации протестируйте:

```python
# Простой тест
llm_gen = LLMRecommendationGenerator(api_key="test-key", provider="openai")
test_prompt = "Проанализируй технику: колени недостаточно согнуты."
response = llm_gen.call_llm_api(test_prompt)
print(response)
```

## ✅ Чеклист

- [ ] Установлена библиотека (openai или anthropic)
- [ ] Получен API ключ
- [ ] Реализован метод `call_llm_api()`
- [ ] Добавлена обработка ошибок
- [ ] API ключ хранится в переменных окружения
- [ ] Протестирован вызов API
- [ ] Настроены параметры (модель, temperature, max_tokens)
