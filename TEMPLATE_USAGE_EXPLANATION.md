# Использование эталона в Pipeline

## 📍 Ответ на ваш вопрос

**Pipeline использует УЖЕ СОЗДАННЫЙ ВАМИ эталон**, а не создает новый.

## 🔍 Как это работает

### 1. Где находится эталон

**Файл:** `results/template_angles.csv`  
**Путь в коде:** `ski_analyzer/config/settings.py` → `TEMPLATE_FILE`

### 2. Как pipeline использует эталон

**В коде `ski_analyzer/core/pipeline.py`:**

```python
def analyze_user_video(self, video_path: str, 
                      template_path: Optional[str] = None,
                      ...):
    # ...
    # Если template_path не указан, используется из настроек
    if template_path is None:
        template_path = str(TEMPLATE_FILE)  # results/template_angles.csv
    
    # Создается анализатор с этим эталоном
    analyzer = SkiAnalyzer(template_path)
    # ...
```

**В коде `ski_analyzer/core/analyzer.py`:**

```python
class SkiAnalyzer:
    def __init__(self, template_path: Optional[str] = None):
        if template_path is None:
            template_path = TEMPLATE_FILE  # Использует ваш эталон
        
        # Загружает ваш эталон
        self.template = pd.read_csv(template_path, sep=';')
```

### 3. Что происходит при анализе

1. **Pipeline обрабатывает видео пользователя:**
   - Извлекает позу → вычисляет углы → ресемплирует
   - Создает файл `user_angles_resampled.csv`

2. **Сравнивает с вашим эталоном:**
   - Загружает `results/template_angles.csv` (ваш эталон)
   - Сравнивает углы пользователя с эталоном
   - Вычисляет отклонения

3. **Генерирует рекомендации:**
   - На основе отклонений от эталона
   - Выдает конкретные советы

## 📊 Ваш эталон

**Файл:** `results/template_angles.csv`

**Содержит:**
- Средние значения углов (mean) для каждого угла
- Стандартные отклонения (std) для каждого угла
- 100 точек (после ресемплинга) для каждого угла

**Структура:**
```csv
left_knee_angle_mean;left_knee_angle_std;right_knee_angle_mean;...
148.9;18.8;148.1;19.6;...
151.9;20.4;153.3;21.5;...
...
```

Этот эталон был создан из ваших профессиональных видео (Ski9-Ski15) через `build_front_template.py`.

## 🔄 Когда создается новый эталон?

**Новый эталон НЕ создается автоматически!**

Чтобы создать/обновить эталон, нужно:

```bash
# Вручную вызвать
python process_video.py --build-template
```

Или в коде:

```python
from ski_analyzer.core.pipeline import SkiAnalysisPipeline

# Построить эталон из всех resampled файлов
SkiAnalysisPipeline.build_template_from_directory(
    directory="results",
    pattern="*_resampled.csv"
)
```

## ✅ Итог

- ✅ Pipeline использует **ваш существующий эталон** (`results/template_angles.csv`)
- ✅ Эталон был создан из ваших профессиональных видео
- ✅ При каждом анализе видео пользователя сравнивается с этим эталоном
- ✅ Новый эталон создается только если вы явно вызываете `build_template`

## 💡 Если нужно обновить эталон

1. Добавить новые профессиональные видео
2. Обработать их через pipeline
3. Вызвать `build_template` для пересоздания эталона

**Текущий эталон остается неизменным до тех пор, пока вы не обновите его вручную!**
