# 🚀 Быстрый старт - Как запустить

## ⚠️ Важно: Нужно быть в правильной директории!

### Проблема
Если вы видите ошибку:
```
python: can't open file 'C:\\Users\\User\\process_video.py': [Errno 2] No such file or directory
```

Это значит, что вы запускаете команду не из директории проекта.

## ✅ Правильный способ запуска

### Шаг 1: Откройте командную строку

### Шаг 2: Перейдите в директорию проекта

```bash
cd C:\Users\User\PycharmProjects\PythonProject3
```

### Шаг 3: Активируйте виртуальное окружение (рекомендуется)

**В PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**В CMD:**
```cmd
.venv\Scripts\activate.bat
```

### Шаг 4: Запустите команду

```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

## 📋 Полная последовательность команд

### Вариант 1: PowerShell

```powershell
# Перейти в проект
cd C:\Users\User\PycharmProjects\PythonProject3

# Активировать окружение
.venv\Scripts\Activate.ps1

# Запустить
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

### Вариант 2: CMD

```cmd
# Перейти в проект
cd C:\Users\User\PycharmProjects\PythonProject3

# Активировать окружение
.venv\Scripts\activate.bat

# Запустить
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

### Вариант 3: Без активации окружения (если не работает активация)

```bash
# Перейти в проект
cd C:\Users\User\PycharmProjects\PythonProject3

# Запустить напрямую через python из .venv
.venv\Scripts\python.exe process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

## 🎯 Все команды для проверки

### 1. Только обработка (без рекомендаций):
```bash
python process_video.py "Ski.Videos\User\User1.MOV"
```

### 2. С анализом (базовые рекомендации):
```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze
```

### 3. С LLM рекомендациями:
```bash
python process_video.py "Ski.Videos\User\User1.MOV" --analyze --use-llm
```

## ✅ Проверка что вы в правильной директории

Перед запуском проверьте:

```bash
# Должна показать файлы проекта
dir process_video.py
dir ski_analyzer

# Если видите "файл не найден" - вы не в той директории!
```

## 💡 Альтернатива: Использовать полный путь

Если не хотите переходить в директорию:

```bash
python C:\Users\User\PycharmProjects\PythonProject3\process_video.py "C:\Users\User\PycharmProjects\PythonProject3\Ski.Videos\User\User1.MOV" --analyze --use-llm
```

Но проще перейти в директорию проекта! 😊
