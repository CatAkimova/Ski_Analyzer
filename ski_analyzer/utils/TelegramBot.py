import os
import tempfile
import requests
from pathlib import Path
from typing import Optional

import telebot
from dotenv import load_dotenv

from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator

# Always load .env from repository root and override inherited shell env.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Токен бота из переменной окружения TELEGRAM_BOT_TOKEN
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN)

# Адрес API анализа (должен быть запущен отдельно: uvicorn api_service:app)
API_ANALYZE_URL = os.getenv("API_ANALYZE_URL", "http://localhost:8000/analyze-video")

# Профили пользователей: user_id -> { level, experience, goals }
user_profiles: dict[int, dict] = {}


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    text = (
        "Привет! Я помогу тебе улучшить катание на горных лыжах.\n\n"
        "• /reg — зарегистрироваться (уровень, опыт, цели)\n"
        "• Отправь видео своего катания — получишь разбор ошибок и рекомендации.\n\n"
        "Сначала пройди /reg, затем пришли видео."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["reg"])
def start_reg(message):
    bot.send_message(message.chat.id, "Какой твой уровень катания?")
    bot.register_next_step_handler(message, get_level)


def get_level(message):
    user_id = message.from_user.id
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    user_profiles[user_id]["level"] = message.text.strip()
    bot.send_message(message.chat.id, "Какой у тебя опыт катания?")
    bot.register_next_step_handler(message, get_experience)


def get_experience(message):
    user_id = message.from_user.id
    user_profiles[user_id]["experience"] = message.text.strip()
    bot.send_message(message.chat.id, "Какова твоя цель катания?")
    bot.register_next_step_handler(message, get_goals)


def get_goals(message):
    user_id = message.from_user.id
    user_profiles[user_id]["goals"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        "Отлично! Теперь отправь мне видео своего катания — я проанализирую его и дам рекомендации.",
    )


def get_user_profile(user_id: int) -> Optional[dict]:
    """Возвращает профиль пользователя для LLM (level, experience, goals)."""
    if user_id not in user_profiles:
        return None
    return user_profiles[user_id].copy()


@bot.message_handler(content_types=["video"])
def handle_video(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    status_msg = bot.send_message(chat_id, "Загружаю видео и запускаю анализ, это может занять несколько минут…")

    file_id = message.video.file_id
    file_info = bot.get_file(file_id)
    downloaded = bot.download_file(file_info.file_path)

    # Определяем расширение по имени файла или по умолчанию .mp4
    fname = getattr(file_info, "file_path", "") or "video.mp4"
    suffix = Path(fname).suffix.lower()
    if suffix not in [".mp4", ".mov"]:
        suffix = ".mp4"

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(downloaded)
            temp_path = tmp.name

        # Отправляем видео на API анализа
        with open(temp_path, "rb") as f:
            resp = requests.post(
                API_ANALYZE_URL,
                files={"file": (f"video{suffix}", f, "video/mp4")},
                timeout=300,
            )

        if not resp.ok:
            err = resp.json().get("error", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            bot.edit_message_text(
                f"Ошибка анализа: {err}",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )
            return

        data = resp.json()
        analysis = data.get("analysis") or {}

        # Если API уже вернул LLM-рекомендации — используем их
        llm_recs = data.get("llm_recommendations")

        if not llm_recs:
            # Генерируем рекомендации через LLM в боте
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
            provider = "gemini" if os.getenv("GEMINI_API_KEY") else "openai"
            if api_key:
                try:
                    gen = LLMRecommendationGenerator(api_key=api_key, provider=provider)
                    profile = get_user_profile(user_id)
                    llm_recs = gen.generate_recommendations(analysis, user_profile=profile)
                except Exception as e:
                    bot.edit_message_text(
                        f"Анализ выполнен, но не удалось сформировать рекомендации: {e}",
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                    )
                    return
            else:
                llm_recs = {"errors": [], "actions": ["Установи GEMINI_API_KEY или OPENAI_API_KEY для персональных рекомендаций."]}

        errors = llm_recs.get("errors") or []
        actions = llm_recs.get("actions") or []

        # Удаляем сообщение «Анализирую…»
        try:
            bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        except Exception:
            pass

        # Отправляем результат
        if errors:
            err_text = "Ошибки:\n" + "\n".join(f"• {e}" for e in errors[:8])
            bot.send_message(chat_id, err_text)
        if actions:
            act_text = "Рекомендации:\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions[:8]))
            bot.send_message(chat_id, act_text)
        if not errors and not actions:
            bot.send_message(chat_id, "Анализ завершён. Значимых проблем не обнаружено — продолжай в том же духе!")

    except requests.RequestException as e:
        try:
            bot.edit_message_text(
                f"Не удалось связаться с сервером анализа. Запущен ли API? {e}",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )
        except Exception:
            bot.send_message(chat_id, f"Ошибка при обращении к серверу: {e}")
    except Exception as e:
        try:
            bot.edit_message_text(
                f"Произошла ошибка: {e}",
                chat_id=chat_id,
                message_id=status_msg.message_id,
            )
        except Exception:
            bot.send_message(chat_id, f"Ошибка: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def run_bot():
    """Запуск бота (polling)."""
    if not BOT_TOKEN:
        raise ValueError(
            "Установи переменную окружения TELEGRAM_BOT_TOKEN или создай файл .env с TELEGRAM_BOT_TOKEN=..."
        )
    bot.polling(none_stop=True, interval=0)


if __name__ == "__main__":
    run_bot()
