# API Спецификация

## Базовый URL
```
http://localhost:8000/api/v1
```
(или ваш production URL)

---

## Эндпоинты

### 1. POST /analyze
Загрузка видео для анализа

**Request:**
```
POST /api/v1/analyze
Content-Type: multipart/form-data

Form Data:
- video: File (обязательно)
- user_id: String (опционально)
```

**Response 200:**
```json
{
  "status": "success",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Видео принято в обработку"
}
```

**Response 400:**
```json
{
  "status": "error",
  "error": "Неподдерживаемый формат видео"
}
```

---

### 2. GET /status/{task_id}
Проверка статуса обработки

**Request:**
```
GET /api/v1/status/550e8400-e29b-41d4-a716-446655440000
```

**Response 200 (processing):**
```json
{
  "status": "processing",
  "progress": 45,
  "message": "Анализ углов...",
  "result": null
}
```

**Response 200 (completed):**
```json
{
  "status": "completed",
  "progress": 100,
  "message": "Обработка завершена",
  "result": {
    "overall_score": 75.5,
    "angle_analysis": [...],
    "recommendations": [...]
  }
}
```

**Response 200 (failed):**
```json
{
  "status": "failed",
  "progress": 0,
  "message": "Ошибка обработки",
  "error": "Не удалось обнаружить лыжника на видео"
}
```

**Response 404:**
```json
{
  "status": "error",
  "error": "Задача не найдена"
}
```

---

### 3. GET /result/{task_id}
Получить полный результат анализа

**Request:**
```
GET /api/v1/result/550e8400-e29b-41d4-a716-446655440000
```

**Response 200:**
```json
{
  "status": "success",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "analysis": {
    "overall_score": 75.5,
    "angle_analysis": [
      {
        "angle": "left_knee",
        "angle_name": "Левое колено",
        "percent_bad": 15.2,
        "mean_diff_deg": 5.3,
        "max_diff_deg": 12.1,
        "is_critical": false
      },
      {
        "angle": "right_knee",
        "angle_name": "Правое колено",
        "percent_bad": 8.5,
        "mean_diff_deg": -2.1,
        "max_diff_deg": 8.7,
        "is_critical": false
      },
      {
        "angle": "left_body",
        "angle_name": "Левая сторона корпуса",
        "percent_bad": 25.3,
        "mean_diff_deg": 8.2,
        "max_diff_deg": 15.4,
        "is_critical": true
      },
      {
        "angle": "right_body",
        "angle_name": "Правая сторона корпуса",
        "percent_bad": 12.1,
        "mean_diff_deg": 3.5,
        "max_diff_deg": 9.8,
        "is_critical": false
      }
    ],
    "recommendations": [
      "Корпус (левая сторона): заметно отклонён назад относительно эталона. Рекомендация: сместить центр тяжести вперёд, ближе к носкам лыж.",
      "Колено (правое): сгибается больше, чем в эталоне. Возможна излишняя посадка."
    ]
  },
  "files": {
    "annotated_video": "/api/v1/files/550e8400-e29b-41d4-a716-446655440000/annotated.mp4",
    "charts": "/api/v1/files/550e8400-e29b-41d4-a716-446655440000/charts.png"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z"
}
```

**Response 404:**
```json
{
  "status": "error",
  "error": "Результат не найден"
}
```

---

### 4. GET /health
Проверка работоспособности API

**Request:**
```
GET /api/v1/health
```

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 400 | Неверный запрос (неверный формат видео, слишком большое/маленькое) |
| 404 | Ресурс не найден (задача, результат) |
| 422 | Не удалось обработать (лыжник не обнаружен) |
| 500 | Внутренняя ошибка сервера |
| 503 | Сервис недоступен (слишком много задач в очереди) |

---

## Примеры использования

### cURL

```bash
# Загрузка видео
curl -X POST http://localhost:8000/api/v1/analyze \
  -F "video=@user_video.mp4" \
  -F "user_id=user123"

# Проверка статуса
curl http://localhost:8000/api/v1/status/550e8400-e29b-41d4-a716-446655440000

# Получение результата
curl http://localhost:8000/api/v1/result/550e8400-e29b-41d4-a716-446655440000
```

### JavaScript (fetch)

```javascript
// Загрузка видео
const formData = new FormData();
formData.append('video', videoFile);
formData.append('user_id', 'user123');

const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
});

const { task_id } = await response.json();

// Проверка статуса
const checkStatus = async (taskId) => {
  const response = await fetch(`http://localhost:8000/api/v1/status/${taskId}`);
  const data = await response.json();
  
  if (data.status === 'completed') {
    return data.result;
  } else if (data.status === 'processing') {
    // Повторить через 2 секунды
    setTimeout(() => checkStatus(taskId), 2000);
  } else {
    throw new Error(data.error || 'Ошибка обработки');
  }
};

// Получение результата
const result = await checkStatus(task_id);
```

### Python (requests)

```python
import requests
import time

# Загрузка видео
with open('user_video.mp4', 'rb') as f:
    files = {'video': f}
    data = {'user_id': 'user123'}
    response = requests.post(
        'http://localhost:8000/api/v1/analyze',
        files=files,
        data=data
    )
    task_id = response.json()['task_id']

# Проверка статуса
while True:
    response = requests.get(f'http://localhost:8000/api/v1/status/{task_id}')
    data = response.json()
    
    if data['status'] == 'completed':
        result = data['result']
        break
    elif data['status'] == 'failed':
        raise Exception(data.get('error', 'Ошибка обработки'))
    else:
        time.sleep(2)  # Подождать 2 секунды
```

---

## Rate Limiting

Рекомендуется ограничить количество запросов:
- **POST /analyze**: максимум 5 запросов в минуту на пользователя
- **GET /status**: максимум 30 запросов в минуту на пользователя
- **GET /result**: без ограничений

---

## WebSocket (опционально)

Для real-time обновлений статуса можно использовать WebSocket:

```
WS /ws/status/{task_id}

Сообщения от сервера:
{
  "type": "progress",
  "progress": 45,
  "message": "Анализ углов..."
}

{
  "type": "completed",
  "result": { ... }
}

{
  "type": "error",
  "error": "Ошибка обработки"
}
```

