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
        # get_detailed_report возвращает "angle_analysis", а не "feedback"
        feedback = analysis_result.get("angle_analysis", analysis_result.get("feedback", []))
        overall_score = analysis_result.get("overall_score", 0)
        
        # Определяем общий уровень техники словами
        if overall_score >= 80:
            score_text = "отличная"
        elif overall_score >= 60:
            score_text = "хорошая"
        elif overall_score >= 40:
            score_text = "средняя"
        else:
            score_text = "требует улучшения"
        
        text = f"Общая оценка техники: {score_text}\n\n"
        text += "Найденные проблемы:\n"
        
        if not feedback:
            text += "  Значимых проблем не обнаружено.\n"
        else:
            for fb in feedback:
                angle_name = fb["angle"]
                angle_ru = {
                    "left_knee_angle": "Левое колено",
                    "right_knee_angle": "Правое колено",
                    "left_body_angle": "Наклон корпуса (левая сторона)",
                    "right_body_angle": "Наклон корпуса (правая сторона)"
                }.get(angle_name, angle_name)
                
                # Определяем проблему словами без чисел
                mean_diff = fb.get('mean_diff_deg', 0)
                is_critical = fb.get('is_critical', False)
                
                # Описание проблемы простым языком
                if "knee" in angle_name:
                    if mean_diff < -15:
                        problem = f"{angle_ru}: слишком сильно согнуто (излишняя посадка)"
                    elif mean_diff > 10:
                        problem = f"{angle_ru}: недостаточно согнуто (нужно больше сгибать)"
                    else:
                        problem = f"{angle_ru}: есть отклонения от правильной техники"
                elif "body" in angle_name:
                    if mean_diff < -20:
                        problem = f"{angle_ru}: корпус слишком сильно подан вперед"
                    elif mean_diff > 10:
                        problem = f"{angle_ru}: корпус отклонен назад (нужно сместить центр тяжести вперед)"
                    else:
                        problem = f"{angle_ru}: есть отклонения в наклоне корпуса"
                else:
                    problem = f"{angle_ru}: есть отклонения от эталона"
                
                # Определяем серьезность
                if is_critical:
                    severity = "серьезная проблема"
                else:
                    severity = "заметная проблема"
                
                text += f"- {problem} ({severity})\n"
        
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
        
        prompt = f"""Ты профессиональный инструктор по горным лыжам. Проанализируй технику катания и дай понятные рекомендации.

{analysis_text}
{profile_text}

ЗАДАНИЕ: Напиши ответ в двух частях - ошибки и рекомендации.

ФОРМАТ ОТВЕТА (строго соблюдай):

Ошибки:
- Перечисли найденные проблемы простым языком
- Каждая ошибка на отдельной строке, начинается с "- "
- БЕЗ чисел, процентов, градусов, баллов - только понятные описания
- Примеры: "Корпус отклонен назад", "Колени недостаточно согнуты", "Излишняя посадка"
- 3-5 ошибок максимум, каждая не длиннее 10 слов

Рекомендации:
1. Конкретное действие или упражнение
2. Следующее действие или упражнение
3. И так далее (3-5 рекомендаций)

Правила:
- НЕ используй числа, проценты, градусы, баллы в ответе - только слова
- Пиши простым языком, понятным новичку
- Будь позитивным и мотивирующим
- Будь кратким - каждая ошибка максимум 8-10 слов
- Каждая рекомендация максимум 2 предложения
- Начинай сразу с "Ошибки:", без вступлений и приветствий
- Не упоминай эталон, проценты, градусы, фразы "фаза вне нормы"

ВАЖНО: 
- Начинай сразу с "Ошибки:", БЕЗ приветствий
- Формат строго: сначала "Ошибки:", потом "Рекомендации:"
- Никаких чисел, процентов, градусов, баллов - только понятные слова

"""
        
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
            
            # Используем актуальную модель
            # Альтернативы: gemini-2.5-pro (более мощная), gemini-2.0-flash
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # Генерируем ответ (промпт уже содержит все инструкции)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
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
                    temperature=0.4,
                    max_tokens=1000
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
                    temperature=0.4,
                    max_tokens=1000
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
                                 user_profile: Optional[Dict] = None) -> Dict[str, List[str]]:
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
        # Парсим ответ на два списка: errors (строки с "-") и actions (строки "1.", "2." и т.д.)
        errors: List[str] = []
        actions: List[str] = []

        response_clean = (llm_response or "").strip()
        lines = [ln.strip() for ln in response_clean.split("\n") if ln.strip()]

        # Определяем секцию (ошибки или рекомендации)
        current_section = None
        
        for line in lines:
            # Определяем секцию по заголовкам
            low = line.lower().strip(":")
            if low == "ошибки":
                current_section = "errors"
                continue
            elif low in ["рекомендации", "что делать"]:
                current_section = "actions"
                continue

            # ошибки: начинаются с "- "
            if line.startswith("-"):
                txt = line.lstrip("-").strip()
                if txt:
                    errors.append(txt)
                continue

            # рекомендации: начинаются с "1." / "2." / "3." ...
            if len(line) >= 2 and line[0].isdigit():
                # поддержка "1." и "1)":
                if line[1] in [".", ")"]:
                    txt = line[2:].strip()
                    if txt:
                        actions.append(txt)
                    continue
            
            # Если секция определена, добавляем строки в соответствующую секцию
            if current_section == "errors" and line and not line.startswith("-"):
                # Если это не маркированный список, но мы в секции ошибок, добавляем как ошибку
                if not any(char.isdigit() for char in line[:3]):  # Не начинается с цифры
                    errors.append(line)
            elif current_section == "actions" and line:
                # Если это не пронумерованный список, но мы в секции рекомендаций
                if not (len(line) >= 2 and line[0].isdigit() and line[1] in [".", ")"]):
                    actions.append(line)

        # Fallback: если модель не соблюла формат
        if not actions and response_clean:
            # пусть весь текст станет одной рекомендацией
            actions = [response_clean]

        # Ограничим длину (на всякий случай)
        errors = errors[:5]
        actions = actions[:5]

        return {"errors": errors, "actions": actions}


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

