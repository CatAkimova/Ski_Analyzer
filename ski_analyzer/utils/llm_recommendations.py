"""
Модуль для генерации рекомендаций через LLM
Пример интеграции с OpenAI/Anthropic API
"""
from typing import Dict, List, Optional
import json


class LLMRecommendationGenerator:
    """Генератор рекомендаций через LLM"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        """
        Инициализация генератора
        
        Args:
            api_key: API ключ для LLM провайдера
            provider: Провайдер LLM ("gemini", "openai", "anthropic", etc.)
        """
        self.api_key = api_key
        self.provider = provider.lower()  # Приводим к нижнему регистру
        # Здесь можно инициализировать клиент API
    
    def format_analysis_for_llm(self, analysis_result: Dict) -> str:
        """
        Форматирует результаты анализа для LLM промпта
        
        Args:
            analysis_result: Результат анализа от SkiAnalyzer
            
        Returns:
            Отформатированная строка
        """
        feedback = analysis_result.get("feedback", [])
        overall_score = analysis_result.get("overall_score", 0)
        
        text = f"Общий балл техники: {overall_score}/100\n\n"
        text += "Детальный анализ по углам:\n"
        
        for fb in feedback:
            angle_name = fb["angle"]
            angle_ru = {
                "left_knee_angle": "Левое колено",
                "right_knee_angle": "Правое колено",
                "left_body_angle": "Наклон корпуса (левая сторона)",
                "right_body_angle": "Наклон корпуса (правая сторона)"
            }.get(angle_name, angle_name)
            
            text += f"\n{angle_ru}:\n"
            text += f"  - Доля фазы вне нормы: {fb['percent_bad']:.1f}%\n"
            text += f"  - Среднее отклонение от эталона: {fb['mean_diff_deg']:+.1f}°\n"
            text += f"  - Максимальное отклонение: {fb['max_diff_deg']:.1f}°\n"
            if fb.get('is_critical'):
                text += f"  - ⚠ Требует особого внимания\n"
        
        return text
    
    def generate_prompt(self, analysis_result: Dict, user_profile: Optional[Dict] = None) -> str:
        """
        Генерирует промпт для LLM
        
        Args:
            analysis_result: Результат анализа
            user_profile: Профиль пользователя (уровень, опыт и т.д.)
            
        Returns:
            Промпт для LLM
        """
        analysis_text = self.format_analysis_for_llm(analysis_result)
        
        profile_text = ""
        if user_profile:
            level = user_profile.get("level", "не указан")
            experience = user_profile.get("experience", "не указан")
            goals = user_profile.get("goals", "не указаны")
            profile_text = f"""
Профиль пользователя:
- Уровень катания: {level}
- Опыт: {experience}
- Цели: {goals}
"""
        
        prompt = f"""Ты профессиональный инструктор по горным лыжам. Проанализируй технику катания и дай конкретные рекомендации.

{analysis_text}
{profile_text}

ЗАДАНИЕ: Дай 3-5 конкретных рекомендаций по улучшению техники.

ТРЕБОВАНИЯ:
- Каждая рекомендация на отдельной строке
- Начинай с номера: 1. 2. 3. и т.д.
- Каждая рекомендация должна быть конкретной и практичной
- Укажи конкретные действия что делать
- Будь позитивным и мотивирующим
- Пиши кратко, но информативно (2-3 предложения на рекомендацию)

ФОРМАТ ОТВЕТА:
1. [Первая рекомендация с конкретными действиями]
2. [Вторая рекомендация с конкретными действиями]
3. [Третья рекомендация с конкретными действиями]

ВАЖНО: Начинай сразу с рекомендаций, БЕЗ приветствий, вступлений и общих фраз."""
        
        return prompt
    
    def call_llm_api(self, prompt: str) -> str:
        """
        Вызывает LLM API (Gemini, OpenAI или другие)
        
        Args:
            prompt: Промпт для LLM
            
        Returns:
            Ответ от LLM
        """
        if not self.api_key:
            return "Ошибка: API ключ не установлен. Установите API ключ в переменных окружения."
        
        # Выбираем провайдера
        if self.provider == "gemini":
            return self._call_gemini(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            return f"Ошибка: Неподдерживаемый провайдер '{self.provider}'. Используйте 'gemini' или 'openai'."
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Вызывает Google Gemini API
        """
        if not self.api_key:
            return "Ошибка: Gemini API ключ не установлен."
        
        try:
            import google.generativeai as genai
            
            # Настраиваем API ключ
            genai.configure(api_key=self.api_key)
            
            # Используем актуальную модель (gemini-2.5-flash - быстрая и бесплатная)
            # Альтернативы: gemini-2.5-pro (более мощная), gemini-2.0-flash
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # Формируем полный промпт с системным сообщением
            full_prompt = (
                "Ты профессиональный инструктор по горным лыжам. "
                "Дай конкретные и практичные рекомендации по улучшению техники. "
                "Будь позитивным и мотивирующим.\n\n"
                f"{prompt}"
            )
            
            # Генерируем ответ
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,  # Увеличено для полных рекомендаций
                )
            )
            
            # Проверяем что ответ не обрезан
            result_text = response.text
            if not result_text or len(result_text) < 50:
                return "Ошибка: Gemini вернул слишком короткий ответ. Попробуйте снова."
            
            return result_text
            
        except ImportError:
            return "Ошибка: Библиотека 'google-generativeai' не установлена. Установите: pip install google-generativeai"
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return "Ошибка: Неверный Gemini API ключ. Проверьте ключ на https://makersuite.google.com/app/apikey"
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                return "Ошибка: Превышен лимит запросов Gemini. Подождите немного."
            else:
                return f"Ошибка при обращении к Gemini: {error_msg}"
    
    def _call_openai(self, prompt: str) -> str:
        """
        Вызывает OpenAI API
        """
        if not self.api_key:
            return "Ошибка: OpenAI API ключ не установлен."
        
        try:
            # Пробуем новый API (v1.0+)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты профессиональный инструктор по горным лыжам. "
                                       "Дай конкретные и практичные рекомендации по улучшению техники. "
                                       "Будь позитивным и мотивирующим."
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
                
            except ImportError:
                # Fallback на старый API
                import openai
                openai.api_key = self.api_key
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
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
            error_msg = str(e)
            if "Invalid API key" in error_msg or "authentication" in error_msg.lower():
                return "Ошибка: Неверный OpenAI API ключ."
            elif "rate limit" in error_msg.lower():
                return "Ошибка: Превышен лимит запросов OpenAI."
            elif "insufficient_quota" in error_msg.lower():
                return "Ошибка: Недостаточно средств на счету OpenAI."
            else:
                return f"Ошибка при обращении к OpenAI: {error_msg}"
        
    
    def generate_recommendations(self, 
                                 analysis_result: Dict,
                                 user_profile: Optional[Dict] = None) -> List[str]:
        """
        Генерирует рекомендации через LLM
        
        Args:
            analysis_result: Результат анализа от SkiAnalyzer
            user_profile: Профиль пользователя
            
        Returns:
            Список рекомендаций
        """
        prompt = self.generate_prompt(analysis_result, user_profile)
        llm_response = self.call_llm_api(prompt)
        
        # Парсим ответ - разбиваем на рекомендации
        recommendations = []
        
        # Убираем возможные приветствия и вступления
        response_clean = llm_response.strip()
        
        # Ищем строки начинающиеся с цифр (1. 2. 3. и т.д.)
        lines = response_clean.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Пропускаем комментарии
            if line.startswith('#') or (line.startswith('*') and len(line) < 3):
                continue
            
            # Если строка начинается с цифры и точки (1. 2. 3.)
            if line[0].isdigit() and len(line) > 2 and (line[1] == '.' or line[1:3] == '. '):
                # Извлекаем номер и текст
                parts = line.split('.', 1)
                if len(parts) == 2:
                    text = parts[1].strip()
                    if text and len(text) > 10:  # Минимум 10 символов
                        recommendations.append(text)
            # Если строка начинается с маркера
            elif line.startswith('-') or line.startswith('•'):
                text = line.lstrip('-• ').strip()
                if text and len(text) > 10:
                    recommendations.append(text)
            # Если строка достаточно длинная и не начинается с приветствия
            elif len(line) > 30 and not any(word in line.lower()[:50] for word in ['привет', 'здравствуй', 'отлично что ты']):
                recommendations.append(line)
        
        # Если не нашли структурированных рекомендаций, пытаемся разбить по предложениям
        if not recommendations:
            # Убираем приветствия
            response_no_greeting = response_clean
            for greeting in ['Привет!', 'Здравствуй!', 'Отлично, что ты здесь', 'Я очень рад']:
                if greeting in response_no_greeting:
                    idx = response_no_greeting.find(greeting)
                    if idx != -1:
                        response_no_greeting = response_no_greeting[idx + len(greeting):].strip()
            
            # Разбиваем на предложения
            sentences = [s.strip() for s in response_no_greeting.replace('. ', '.\n').split('\n') if len(s.strip()) > 30]
            recommendations = sentences[:5]  # Максимум 5 рекомендаций
        
        # Если все еще пусто, возвращаем весь ответ как одну рекомендацию
        if not recommendations:
            clean_response = response_clean
            if clean_response.lower().startswith('привет'):
                sentences = clean_response.split('.')
                if len(sentences) > 1:
                    clean_response = '.'.join(sentences[1:]).strip()
            recommendations = [clean_response] if clean_response else [llm_response]
        
        return recommendations


# Пример использования
def example_llm_integration():
    """Пример интеграции LLM"""
    from ski_analyzer.core.analyzer import SkiAnalyzer
    
    # Анализируем видео
    analyzer = SkiAnalyzer()
    analysis = analyzer.analyze("path/to/user_angles_resampled.csv")
    
    # Генерируем рекомендации через LLM
    llm_gen = LLMRecommendationGenerator(api_key="your-api-key")
    
    user_profile = {
        "level": "средний",
        "experience": "3 года",
        "goals": "улучшить технику карвинга"
    }
    
    recommendations = llm_gen.generate_recommendations(analysis, user_profile)
    
    for rec in recommendations:
        print(rec)

