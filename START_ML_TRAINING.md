# С чего начать обучение ML модели (пошаговый план)

## 🎯 Цель

Обучить модель, которая будет определять качество техники катания на лыжах.

## 📋 План на первые 2 месяца

### Неделя 1-2: Подготовка данных

#### Задача 1: Собрать базовый датасет
```bash
# Нужно минимум:
- 50 видео хорошего катания
- 50 видео плохого катания

# Где взять:
- Ваши существующие видео (Ski9-Ski15)
- YouTube (скачать видео профессиональных лыжников)
- Записать новые видео
```

#### Задача 2: Разметить данные
```python
# Создать CSV файл с разметкой:
# video_path, label, person_height, person_weight, gender, suit_color
# Ski9.mp4, good, 175, 70, male, blue
# User1.MOV, bad, 170, 65, male, red
```

**Инструменты для разметки:**
- Простой CSV файл (для начала)
- Label Studio (https://labelstud.io/) - более продвинутый
- DVC (Data Version Control) - для управления данными

#### Задача 3: Увеличить датасет через аугментацию
```python
from ski_analyzer.ml.dataset_generator import VideoAugmenter

augmenter = VideoAugmenter()

# Создать 5 вариаций каждого видео
augmenter.create_dataset_variations(
    "Ski.Videos/Professional",
    "Ski.Videos/Professional_Augmented",
    variations_per_video=5
)
```

**Результат:** 50 видео → 250 видео (5x увеличение)

### Неделя 3-4: Изучение основ PyTorch

#### Задача 1: Установить окружение
```bash
# Создать виртуальное окружение
python -m venv ml_env
ml_env\Scripts\activate  # Windows
source ml_env/bin/activate  # Linux/Mac

# Установить зависимости
pip install torch torchvision torchaudio
pip install opencv-python pandas numpy
pip install tensorboard  # для визуализации обучения
```

#### Задача 2: Изучить основы
**Ресурсы:**
- PyTorch Tutorial: https://pytorch.org/tutorials/
- Начать с "Learning PyTorch" (30 минут)
- Практика: создать простую нейросеть для классификации изображений

**Что нужно понять:**
- Что такое тензоры (tensors)
- Как работает autograd
- Что такое loss функция
- Как работает оптимизатор (SGD, Adam)

### Неделя 5-6: Создать первый датасет

#### Задача 1: Создать класс Dataset
```python
# См. пример в ML_TRAINING_GUIDE.md
# Создать ski_analyzer/ml/dataset.py
```

#### Задача 2: Протестировать загрузку данных
```python
from ski_analyzer.ml.dataset import SkiDataset

dataset = SkiDataset(video_paths, labels)
dataloader = DataLoader(dataset, batch_size=4)

# Проверить, что данные загружаются
for videos, labels in dataloader:
    print(videos.shape, labels.shape)
    break
```

### Неделя 7-8: Первая модель

#### Задача 1: Использовать готовую модель
```python
# Взять предобученную модель для видео
from torchvision.models import video

model = video.r3d_18(pretrained=True)
# Заменить последний слой для нашей задачи
model.fc = nn.Linear(512, 2)  # хорошее/плохое
```

#### Задача 2: Обучить на небольшом датасете
```python
# Обучить на 20-30 видео для начала
# Проверить, что модель обучается (loss уменьшается)
```

### Неделя 9-10: Масштабирование

#### Задача 1: Увеличить датасет
- Добавить больше видео
- Использовать аугментацию
- Цель: 200-300 видео

#### Задача 2: Улучшить модель
- Попробовать разные архитектуры
- Настроить гиперпараметры
- Добавить регуляризацию

## 🛠️ Практические шаги прямо сейчас

### Шаг 1: Установить зависимости (5 минут)

```bash
pip install torch torchvision opencv-python pandas numpy
```

### Шаг 2: Создать структуру для ML (10 минут)

```bash
mkdir -p ski_analyzer/ml
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/augmented
mkdir -p models
mkdir -p experiments
```

### Шаг 3: Собрать первые 20 видео (1-2 дня)

```bash
# Скопировать существующие видео
# Или скачать с YouTube
# Разметить: хорошее/плохое
```

### Шаг 4: Создать разметку (30 минут)

```python
# Создать CSV файл: data/labels.csv
import pandas as pd

labels = pd.DataFrame({
    'video_path': ['Ski9.mp4', 'Ski10.mp4', 'User1.MOV', ...],
    'label': ['good', 'good', 'bad', ...],  # или 0/1
    'person_height': [175, 180, 170, ...],
    'person_weight': [70, 75, 65, ...],
    'gender': ['male', 'male', 'male', ...],
    'suit_color': ['blue', 'red', 'black', ...]
})

labels.to_csv('data/labels.csv', index=False)
```

### Шаг 5: Увеличить датасет аугментацией (1 час)

```python
from ski_analyzer.ml.dataset_generator import VideoAugmenter

augmenter = VideoAugmenter()

# Для хороших видео
augmenter.create_dataset_variations(
    "Ski.Videos/Professional",
    "data/augmented/good",
    variations_per_video=5
)

# Для плохих видео
augmenter.create_dataset_variations(
    "Ski.Videos/User",
    "data/augmented/bad",
    variations_per_video=5
)
```

### Шаг 6: Изучить PyTorch (1-2 недели)

**Начать здесь:**
1. https://pytorch.org/tutorials/beginner/basics/intro.html
2. Пройти первые 3-4 урока
3. Попрактиковаться на простых примерах

## 📊 Сколько нужно данных?

### Минимум для начала:
- **20-30 видео** для первого эксперимента
- **50-100 видео** для рабочей модели
- **200-500 видео** для хорошей модели
- **1000+ видео** для production-ready модели

### Стратегия:
1. **Начать с 20-30 видео** - проверить, что все работает
2. **Увеличить до 50-100** - получить базовую модель
3. **Масштабировать до 200-500** - улучшить качество
4. **Добавлять по мере необходимости** - для production

## 🎓 Ресурсы для обучения

### Для начинающих:
1. **PyTorch Tutorials** - официальные туториалы
2. **Fast.ai** - практический подход
3. **3Blue1Brown** - визуализация нейросетей (YouTube)

### Для работы с видео:
1. **Video Understanding** - курсы по анализу видео
2. **PyTorch Video** - библиотека для работы с видео

### Книги:
1. "Deep Learning" by Ian Goodfellow
2. "Hands-On Machine Learning" by Aurélien Géron

## ⚠️ Частые ошибки новичков

1. **Слишком сложная модель с самого начала**
   - ✅ Начните с простой модели
   - ✅ Используйте готовые предобученные модели

2. **Недостаточно данных**
   - ✅ Используйте аугментацию
   - ✅ Начните с малого датасета для проверки

3. **Неправильная разметка**
   - ✅ Проверьте разметку несколько раз
   - ✅ Используйте несколько разметчиков

4. **Переобучение (overfitting)**
   - ✅ Используйте валидационный набор
   - ✅ Добавьте dropout, регуляризацию

5. **Не документируют эксперименты**
   - ✅ Используйте TensorBoard или Weights & Biases
   - ✅ Записывайте все гиперпараметры

## 🎯 Чеклист готовности к обучению

- [ ] Установлен PyTorch
- [ ] Есть GPU (опционально, но желательно)
- [ ] Собрано минимум 20-30 видео
- [ ] Данные размечены (хорошее/плохое)
- [ ] Создан датасет класс
- [ ] Изучены основы PyTorch
- [ ] Готова инфраструктура (папки, структура)

## 🚀 Быстрый старт (сегодня)

```bash
# 1. Установить зависимости
pip install torch torchvision opencv-python

# 2. Создать аугментированные данные
python -c "from ski_analyzer.ml.dataset_generator import VideoAugmenter; \
    VideoAugmenter().create_dataset_variations('Ski.Videos/Professional', 'data/augmented', 5)"

# 3. Начать изучение PyTorch
# Открыть https://pytorch.org/tutorials/beginner/basics/intro.html
```

## 📞 Следующие шаги

1. **Сегодня:** Установить зависимости, создать структуру папок
2. **Эта неделя:** Собрать 20-30 видео, разметить их
3. **Следующая неделя:** Изучить основы PyTorch
4. **Через 2 недели:** Создать первый датасет класс
5. **Через месяц:** Обучить первую модель

**Помните:** Начните с малого, не пытайтесь сделать все сразу!



