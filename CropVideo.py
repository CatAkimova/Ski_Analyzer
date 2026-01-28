from moviepy import VideoFileClip

# Загружаем видео
clip = VideoFileClip("9 of the BEST WC-Racers Free-Skiing in SLOW-MOTION.mp4")

# Обрезаем: с 10 по 20 секунду
cut_clip = clip.subclipped(249, 256)

# Сохраняем результат
cut_clip.write_videofile("Ski15.mp4", codec="libx264", audio_codec="aac")
