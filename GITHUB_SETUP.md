# 📦 Инструкция по загрузке проекта на GitHub

## 🔍 Git vs GitHub - в чем разница?

**Git** - это система контроля версий (программа на вашем компьютере):
- Отслеживает изменения в коде
- Сохраняет историю версий
- Работает локально на вашем компьютере

**GitHub** - это платформа для хостинга репозиториев (веб-сайт):
- Хранит ваш код в облаке
- Позволяет делиться кодом с другими разработчиками
- Предоставляет веб-интерфейс для просмотра кода

**Важно:** Если у вас установлен GitHub Desktop, то Git уже установлен! GitHub Desktop - это графический интерфейс для Git.

## ❓ Нужен ли Git для FastAPI?

**Нет, Git не нужен для работы FastAPI приложения.** FastAPI - это просто Python библиотека, которая работает независимо от Git.

**НО Git нужен для:**
- ✅ Версионирования кода (сохранения истории изменений)
- ✅ Совместной работы с другими разработчиками
- ✅ Резервного копирования кода
- ✅ Отслеживания изменений в проекте

## 🚀 Пошаговая инструкция

### Вариант 1: Через GitHub Desktop (самый простой)

1. **Откройте GitHub Desktop**
2. **Создайте новый репозиторий:**
   - File → Add Local Repository
   - Выберите папку: `c:\Users\User\PycharmProjects\PythonProject3`
   - Нажмите "Add repository"

3. **Создайте репозиторий на GitHub:**
   - Нажмите "Publish repository" (или "Create repository" если репозиторий еще не создан)
   - Введите название (например: `ski-analyzer`)
   - Выберите "Private" или "Public"
   - Нажмите "Publish repository"

4. **Добавьте файлы:**
   - В GitHub Desktop вы увидите список измененных файлов
   - Введите сообщение коммита (например: "Initial commit")
   - Нажмите "Commit to main"
   - Нажмите "Push origin" чтобы загрузить на GitHub

### Вариант 2: Через командную строку (Git Bash или PowerShell)

1. **Проверьте, установлен ли Git:**
   ```powershell
   git --version
   ```
   Если команда не найдена, скачайте Git с [git-scm.com](https://git-scm.com/)

2. **Откройте PowerShell в папке проекта:**
   ```powershell
   cd c:\Users\User\PycharmProjects\PythonProject3
   ```

3. **Инициализируйте репозиторий (если еще не инициализирован):**
   ```powershell
   git init
   ```

4. **Добавьте все файлы:**
   ```powershell
   git add .
   ```

5. **Создайте первый коммит:**
   ```powershell
   git commit -m "Initial commit: Ski Analyzer project"
   ```

6. **Создайте репозиторий на GitHub:**
   - Зайдите на [github.com](https://github.com)
   - Нажмите "+" → "New repository"
   - Введите название (например: `ski-analyzer`)
   - НЕ добавляйте README, .gitignore или лицензию (они уже есть)
   - Нажмите "Create repository"

7. **Подключите локальный репозиторий к GitHub:**
   ```powershell
   git remote add origin https://github.com/ВАШ_НИКНЕЙМ/ski-analyzer.git
   ```
   (Замените `ВАШ_НИКНЕЙМ` на ваш GitHub username)

8. **Загрузите код на GitHub:**
   ```powershell
   git branch -M main
   git push -u origin main
   ```

## 📋 Что будет загружено на GitHub?

Благодаря файлу `.gitignore`, на GitHub НЕ будут загружены:
- ❌ Видео файлы (*.mp4, *.MOV) - они слишком большие
- ❌ Модели (*.pt, *.pth) - они тоже большие
- ❌ Виртуальные окружения (.venv/, venv/)
- ❌ Временные файлы (__pycache__, *.pyc)
- ❌ Результаты обработки (results/, uploads/)
- ❌ Файлы с API ключами (.env)

**Будут загружены:**
- ✅ Весь исходный код Python (ski_analyzer/)
- ✅ Скрипты (process_video.py и другие)
- ✅ requirements.txt
- ✅ Все документация (*.md файлы)
- ✅ .gitignore
- ✅ README.md

## 🔐 Безопасность

**ВАЖНО:** Убедитесь, что файл `.env` с API ключами НЕ загружен на GitHub!

Проверьте:
```powershell
git status
```

Если `.env` в списке, он будет загружен. Удалите его из индекса:
```powershell
git reset HEAD .env
```

## 📝 Для фронтенд разработчика

После загрузки на GitHub, фронтенд разработчик сможет:

1. **Клонировать репозиторий:**
   ```bash
   git clone https://github.com/ВАШ_НИКНЕЙМ/ski-analyzer.git
   ```

2. **Установить зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Изучить структуру проекта:**
   - Прочитать README.md
   - Изучить API_SPECIFICATION.md
   - Посмотреть примеры в QUICK_START_DEVELOPERS.md

4. **Понять архитектуру:**
   - ARCHITECTURE.md - общая архитектура
   - DEVELOPER_GUIDE.md - руководство для разработчиков

## 🎯 Следующие шаги

После загрузки на GitHub:

1. **Добавьте описание репозитория** на странице GitHub
2. **Создайте issues** для задач фронтенд разработчика
3. **Используйте ветки (branches)** для разработки новых функций
4. **Регулярно делайте коммиты** при изменениях

## ❓ Частые вопросы

**Q: Нужно ли загружать видео файлы?**
A: Нет, они слишком большие. GitHub имеет лимит 100MB на файл. Используйте Git LFS для больших файлов, если они действительно нужны.

**Q: Что делать, если забыл добавить .env в .gitignore?**
A: Если .env уже загружен на GitHub:
1. Удалите его из репозитория: `git rm --cached .env`
2. Сделайте коммит: `git commit -m "Remove .env"`
3. Загрузите: `git push`
4. **ВАЖНО:** Смените все API ключи, которые были в .env!

**Q: Как обновить код на GitHub после изменений?**
A: 
```powershell
git add .
git commit -m "Описание изменений"
git push
```

## 📚 Полезные ссылки

- [Git документация](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [GitHub Desktop](https://desktop.github.com/)
