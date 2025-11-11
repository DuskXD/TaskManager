# Документация API

## Все эндпоинты TaskManager API

### 1. Аутентификация и пользователи

#### 1.1 POST /api/v1/auth/register
**Регистрация нового пользователя**

**Запрос:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Иван Иванов"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Иван Иванов",
  "is_active": true,
  "created_at": "2025-10-28T10:00:00Z"
}
```

---

#### 1.2 POST /api/v1/auth/login
**Авторизация и выдача JWT-токена**

**Запрос:**
```json
{
  "username": "username",
  "password": "password123"
}
```

**Ответ (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### 1.3 GET /api/v1/users/me
**Получение профиля текущего пользователя**

**Заголовки:**
```
Authorization: Bearer {access_token}
```

**Ответ (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Иван Иванов",
  "is_active": true,
  "created_at": "2025-10-28T10:00:00Z"
}
```

---

#### 1.4 POST /api/v1/auth/refresh
**Обновление access токена**

**Запрос:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Ответ (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 2. Проекты

#### 2.1 POST /api/v1/projects
**Создание нового проекта**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "name": "Мой проект",
  "description": "Описание проекта"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "name": "Мой проект",
  "description": "Описание проекта",
  "owner_id": 1,
  "is_active": true,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": null
}
```

---

#### 2.2 GET /api/v1/projects
**Получение списка всех проектов пользователя**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (200):**
```json
[
  {
    "id": 1,
    "name": "Мой проект",
    "description": "Описание проекта",
    "owner_id": 1,
    "is_active": true,
    "created_at": "2025-10-28T10:00:00Z",
    "tasks_count": 5,
    "members_count": 3
  }
]
```

---

#### 2.3 GET /api/v1/projects/{project_id}
**Получение деталей проекта**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (200):**
```json
{
  "id": 1,
  "name": "Мой проект",
  "description": "Описание проекта",
  "owner_id": 1,
  "is_active": true,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": null
}
```

---

#### 2.4 PUT /api/v1/projects/{project_id}
**Обновление проекта**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "name": "Обновленное название",
  "description": "Новое описание",
  "is_active": true
}
```

**Ответ (200):**
```json
{
  "id": 1,
  "name": "Обновленное название",
  "description": "Новое описание",
  "owner_id": 1,
  "is_active": true,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": "2025-10-28T11:00:00Z"
}
```

---

#### 2.5 DELETE /api/v1/projects/{project_id}
**Удаление проекта**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (204):** Нет содержимого

---

#### 2.6 GET /api/v1/projects/{project_id}/stats
**Получение статистики по проекту**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (200):**
```json
{
  "total_tasks": 10,
  "todo_tasks": 3,
  "in_progress_tasks": 4,
  "review_tasks": 2,
  "done_tasks": 1,
  "total_members": 5,
  "total_comments": 25
}
```

---

### 3. Задачи

#### 3.1 POST /api/v1/projects/{project_id}/tasks
**Создание задачи в проекте**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "title": "Новая задача",
  "description": "Описание задачи",
  "assignee_id": 2,
  "status": "todo",
  "priority": "high",
  "due_date": "2025-11-01T00:00:00Z"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "title": "Новая задача",
  "description": "Описание задачи",
  "project_id": 1,
  "assignee_id": 2,
  "status": "todo",
  "priority": "high",
  "due_date": "2025-11-01T00:00:00Z",
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": null,
  "assignee": {...},
  "tags": []
}
```

---

#### 3.2 GET /api/v1/projects/{project_id}/tasks
**Получение списка задач в проекте**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (200):**
```json
[
  {
    "id": 1,
    "title": "Новая задача",
    "status": "todo",
    "priority": "high",
    "assignee_id": 2,
    "due_date": "2025-11-01T00:00:00Z",
    "created_at": "2025-10-28T10:00:00Z",
    "tags_count": 2,
    "comments_count": 5
  }
]
```

---

#### 3.3 PUT /api/v1/tasks/{task_id}
**Обновление задачи**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "title": "Обновленная задача",
  "status": "in_progress",
  "priority": "medium"
}
```

**Ответ (200):**
```json
{
  "id": 1,
  "title": "Обновленная задача",
  "description": "Описание задачи",
  "project_id": 1,
  "assignee_id": 2,
  "status": "in_progress",
  "priority": "medium",
  "due_date": "2025-11-01T00:00:00Z",
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": "2025-10-28T12:00:00Z",
  "assignee": {...},
  "tags": []
}
```

---

#### 3.4 DELETE /api/v1/tasks/{task_id}
**Удаление задачи**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (204):** Нет содержимого

---

### 4. Комментарии

#### 4.1 POST /api/v1/tasks/{task_id}/comments
**Добавление комментария к задаче**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "content": "Текст комментария"
}
```

**Ответ (201):**
```json
{
  "id": 1,
  "content": "Текст комментария",
  "task_id": 1,
  "author_id": 1,
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": null,
  "author": {...}
}
```

---

#### 4.2 GET /api/v1/tasks/{task_id}/comments
**Получение списка комментариев к задаче**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (200):**
```json
[
  {
    "id": 1,
    "content": "Текст комментария",
    "task_id": 1,
    "author_id": 1,
    "created_at": "2025-10-28T10:00:00Z",
    "updated_at": null,
    "author": {...}
  }
]
```

---

#### 4.3 DELETE /api/v1/comments/{comment_id}
**Удаление комментария**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (204):** Нет содержимого

---

### 5. Команда проекта

#### 5.1 POST /api/v1/projects/{project_id}/members
**Добавление пользователя в команду проекта**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "user_id": 3,
  "role": "member"
}
```

**Роли:** `owner`, `admin`, `member`, `viewer`

**Ответ (201):**
```json
{
  "id": 1,
  "project_id": 1,
  "user_id": 3,
  "role": "member",
  "joined_at": "2025-10-28T10:00:00Z",
  "user": {...}
}
```

---

#### 5.2 DELETE /api/v1/projects/{project_id}/members/{user_id}
**Удаление участника из команды**

**Заголовки:** `Authorization: Bearer {access_token}`

**Ответ (204):** Нет содержимого

---

### 6. Теги

#### 6.1 POST /api/v1/tasks/{task_id}/tags
**Добавление тега к задаче**

**Заголовки:** `Authorization: Bearer {access_token}`

**Запрос:**
```json
{
  "tag_name": "bug"
}
```

**Ответ (200):**
```json
{
  "id": 1,
  "title": "Задача",
  "description": "Описание",
  "project_id": 1,
  "assignee_id": 2,
  "status": "todo",
  "priority": "high",
  "due_date": "2025-11-01T00:00:00Z",
  "created_at": "2025-10-28T10:00:00Z",
  "updated_at": null,
  "assignee": {...},
  "tags": [
    {
      "id": 1,
      "name": "bug",
      "color": "#ff0000",
      "created_at": "2025-10-28T10:00:00Z"
    }
  ]
}
```

---

## Статусы задач
- `todo` - К выполнению
- `in_progress` - В работе
- `review` - На проверке
- `done` - Выполнено

## Приоритеты задач
- `low` - Низкий
- `medium` - Средний
- `high` - Высокий
- `urgent` - Срочный

## Роли в проекте
- `owner` - Владелец
- `admin` - Администратор
- `member` - Участник
- `viewer` - Наблюдатель
