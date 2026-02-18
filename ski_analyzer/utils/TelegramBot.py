import telebot
import tempfile
import os

bot = telebot.TeleBot("8576727122:AAEZCsTFz4O0NgsnA735LYfXRz1PQ6AbO9s")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет, я помогу тебе улучщить твое катание")

level = ""
experience = ""
goals = ""


@bot.message_handler(commands-['reg'])
def start(message):
    if message.text == '/reg':
        bot.send_message(message.from_user.id, "Какой твой уровень катания?")
        bot.register_next_step_handler(message, get_level)

def get_level(message):
    global level
    level = message.text
    bot.send_message(message.from_user.id, "Какой у тебя опыт катания?")
    bot.register_next_step_handler(message, get_experience)

def get_experience(message):
    global experience
    experience = message.text
    bot.send_message(message.from_user.id, "Какова твоя цель катания?")
    bot.register_next_step_handler(message, get_goals)

def get_goals(message):
    global goals 
    goals = message.text
    bot.send_message(message.from_user.id, "Отлично, теперь отправь мне видео своего каатания")


@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        file_id = message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix='mp4', 'mov') as tmp_file:
            tmp_file.write(downloaded_file)
            temp_path = tmp_file.name
    
    api_url = "http://localhost:8000/analyze-video"

    


def get_video(message):
    global video
    video = message.video
    bot.send_message(message.from_user.id, "Анализирую твое катание, это займет некоторое время")

bot.polling(none_stop=True, interval=0)