# Быстрый старт для разработчиков

## 🎯 Краткое описание задачи

**Что нужно сделать:**
1. **Бэкенд:** REST API для загрузки видео и получения результатов анализа
2. **Фронтенд:** Веб-интерфейс для загрузки видео и отображения результатов

**Что уже готово:**
- ✅ Python-модуль для обработки видео (`ski_analyzer/`)
- ✅ Анализ техники и сравнение с эталоном
- ✅ Генерация рекомендаций

**Что нужно добавить:**
- ⬜ REST API (FastAPI/Flask)
- ⬜ Веб-интерфейс (React/Vue)
- ⬜ Интеграция Python-модуля с API

---

## 📋 Минимальный функционал (MVP)

### Бэкенд
1. Эндпоинт загрузки видео → возвращает `task_id`
2. Эндпоинт проверки статуса → возвращает прогресс и результат
3. Интеграция с `SkiAnalysisPipeline` для обработки

### Фронтенд
1. Страница загрузки видео
2. Отображение прогресса обработки
3. Страница с результатами анализа

---

## 🚀 Быстрый старт

### Шаг 1: Бэкенд (FastAPI пример)

```bash
# Установка
pip install fastapi uvicorn python-multipart

# Создать файл api/main.py
```

**api/main.py:**
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
from pathlib import Path
from ski_analyzer.core.pipeline import SkiAnalysisPipeline
import asyncio
from typing import Dict

app = FastAPI()

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище задач (в продакшене использовать Redis/БД)
tasks: Dict[str, Dict] = {}

# Инициализация pipeline
pipeline = SkiAnalysisPipeline()

@app.post("/api/v1/analyze")
async def analyze_video(video: UploadFile = File(...), user_id: str = None):
    """Загрузка видео для анализа"""
    
    # Валидация формата
    if not video.content_type.startswith('video/'):
        raise HTTPException(400, "Файл должен быть видео")
    
    # Генерируем task_id
    task_id = str(uuid.uuid4())
    
    # Сохраняем видео
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    video_path = upload_dir / f"{task_id}_{video.filename}"
    
    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)
    
    # Инициализируем задачу
    tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "result": None,
        "error": None
    }
    
    # Запускаем обработку в фоне
    asyncio.create_task(process_video_task(task_id, str(video_path)))
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Видео принято в обработку"
    }

async def process_video_task(task_id: str, video_path: str):
    """Асинхронная обработка видео"""
    try:
        tasks[task_id]["progress"] = 10
        tasks[task_id]["message"] = "Извлечение позы..."
        
        # Обработка видео
        result = pipeline.analyze_user_video(
            video_path,
            save_intermediate=False
        )
        
        tasks[task_id]["progress"] = 100
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result["analysis"]
        tasks[task_id]["message"] = "Обработка завершена"
        
        # Удаляем временный файл
        os.remove(video_path)
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = "Ошибка обработки"

@app.get("/api/v1/status/{task_id}")
async def get_status(task_id: str):
    """Проверка статуса обработки"""
    if task_id not in tasks:
        raise HTTPException(404, "Задача не найдена")
    
    task = tasks[task_id]
    response = {
        "status": task["status"],
        "progress": task["progress"],
        "message": task.get("message", ""),
        "result": task["result"] if task["status"] == "completed" else None
    }
    
    if task["status"] == "failed":
        response["error"] = task["error"]
    
    return response

@app.get("/api/v1/result/{task_id}")
async def get_result(task_id: str):
    """Получить результат анализа"""
    if task_id not in tasks:
        raise HTTPException(404, "Результат не найден")
    
    task = tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(400, "Обработка еще не завершена")
    
    return {
        "status": "success",
        "task_id": task_id,
        "analysis": task["result"]
    }

@app.get("/api/v1/health")
async def health():
    """Проверка работоспособности"""
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Запуск:**
```bash
uvicorn api.main:app --reload
```

---

### Шаг 2: Фронтенд (React пример)

```bash
# Создать проект
npx create-react-app frontend --template typescript
cd frontend
npm install axios
```

**src/services/api.ts:**
```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface AnalysisResult {
  overall_score: number;
  angle_analysis: Array<{
    angle: string;
    percent_bad: number;
    mean_diff_deg: number;
    max_diff_deg: number;
    is_critical: boolean;
  }>;
  recommendations: string[];
}

export const uploadVideo = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append('video', file);
  
  const response = await axios.post(`${API_BASE}/analyze`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data.task_id;
};

export const checkStatus = async (taskId: string): Promise<any> => {
  const response = await axios.get(`${API_BASE}/status/${taskId}`);
  return response.data;
};

export const getResult = async (taskId: string): Promise<AnalysisResult> => {
  const response = await axios.get(`${API_BASE}/result/${taskId}`);
  return response.data.analysis;
};
```

**src/components/VideoUpload.tsx:**
```typescript
import React, { useState } from 'react';
import { uploadVideo, checkStatus, getResult, AnalysisResult } from '../services/api';

export const VideoUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      // Загружаем видео
      const taskId = await uploadVideo(file);
      
      // Опрашиваем статус
      const pollStatus = async () => {
        const status = await checkStatus(taskId);
        setProgress(status.progress);

        if (status.status === 'completed') {
          const analysisResult = await getResult(taskId);
          setResult(analysisResult);
          setUploading(false);
        } else if (status.status === 'failed') {
          setError(status.error || 'Ошибка обработки');
          setUploading(false);
        } else {
          // Повторить через 2 секунды
          setTimeout(pollStatus, 2000);
        }
      };

      pollStatus();
    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки');
      setUploading(false);
    }
  };

  return (
    <div>
      <input type="file" accept="video/*" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Обработка...' : 'Загрузить и проанализировать'}
      </button>

      {uploading && (
        <div>
          <progress value={progress} max={100} />
          <p>{progress}%</p>
        </div>
      )}

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {result && (
        <div>
          <h2>Результаты анализа</h2>
          <p>Общий балл: {result.overall_score}/100</p>
          <h3>Рекомендации:</h3>
          <ul>
            {result.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

**src/App.tsx:**
```typescript
import React from 'react';
import { VideoUpload } from './components/VideoUpload';
import './App.css';

function App() {
  return (
    <div className="App">
      <header>
        <h1>Анализ техники катания на лыжах</h1>
      </header>
      <VideoUpload />
    </div>
  );
}

export default App;
```

**Запуск:**
```bash
npm start
```

---

## ✅ Чеклист MVP

### Бэкенд
- [ ] POST /api/v1/analyze - загрузка видео
- [ ] GET /api/v1/status/{task_id} - статус обработки
- [ ] GET /api/v1/result/{task_id} - результат анализа
- [ ] Интеграция с SkiAnalysisPipeline
- [ ] Обработка ошибок

### Фронтенд
- [ ] Компонент загрузки видео
- [ ] Отображение прогресса
- [ ] Отображение результатов
- [ ] Обработка ошибок

---

## 🔗 Полезные ссылки

- **Полное руководство:** `DEVELOPER_GUIDE.md`
- **API спецификация:** `API_SPECIFICATION.md`
- **Архитектура:** `ARCHITECTURE.md`
- **Примеры кода:** `example_usage.py`

---

## 💡 Следующие шаги после MVP

1. Добавить базу данных для хранения результатов
2. Настроить очередь задач (Celery) для масштабирования
3. Улучшить UI/UX (графики, анимации)
4. Добавить аутентификацию пользователей
5. Оптимизировать производительность

