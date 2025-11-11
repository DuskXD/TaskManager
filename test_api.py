"""
Скрипт для тестирования всех эндпоинтов TaskManager API
"""
import requests
import json
from datetime import datetime, timedelta
import time

# Отключаем предупреждения о прокси
import urllib3
urllib3.disable_warnings()

BASE_URL = "http://127.0.0.1:8000"

# Настройки сессии без прокси
session = requests.Session()
session.trust_env = False  # Игнорируем системные прокси
token = None
refresh_token_value = None
project_id = None
task_id = None
comment_id = None
member_user_id = None


def print_result(test_name, response):
    """Печать результата теста"""
    status = "✅ PASS" if response.status_code < 400 else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")


print("=" * 80)
print("🚀 ТЕСТИРОВАНИЕ ВСЕХ ЭНДПОИНТОВ TASKMANAGER API")
print("=" * 80)

# 1. POST /api/v1/auth/register - Регистрация
print("\n[1/20] Регистрация нового пользователя")
response = session.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123",
        "full_name": "Test User"
    }
)
print_result("POST /api/v1/auth/register", response)

# 2. POST /api/v1/auth/login - Авторизация
print("\n[2/20] Авторизация")
response = session.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": "danil",
        "password": "123321"
    }
)
print_result("POST /api/v1/auth/login", response)
if response.status_code == 200:
    data = response.json()
    token = data["access_token"]
    refresh_token_value = data["refresh_token"]
    print(f"🔑 Получен токен: {token[:50]}...")

# 3. GET /api/v1/users/me - Получение профиля
print("\n[3/20] Получение профиля текущего пользователя")
headers = {"Authorization": f"Bearer {token}"}
response = session.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
print_result("GET /api/v1/users/me", response)

# 4. POST /api/v1/projects - Создание проекта
print("\n[4/20] Создание нового проекта")
response = session.post(
    f"{BASE_URL}/api/v1/projects",
    headers=headers,
    json={
        "name": "Тестовый проект",
        "description": "Описание тестового проекта"
    }
)
print_result("POST /api/v1/projects", response)
if response.status_code == 201:
    project_id = response.json()["id"]
    print(f"📁 ID проекта: {project_id}")

# 18. GET /api/v1/projects - Список всех проектов
print("\n[18/20] Получение списка всех проектов")
response = session.get(f"{BASE_URL}/api/v1/projects", headers=headers)
print_result("GET /api/v1/projects", response)

# 5. GET /api/v1/projects/{id} - Получение деталей проекта
print("\n[5/20] Получение деталей проекта")
response = session.get(f"{BASE_URL}/api/v1/projects/{project_id}", headers=headers)
print_result(f"GET /api/v1/projects/{project_id}", response)

# 17. PUT /api/v1/projects/{id} - Обновление проекта
print("\n[17/20] Обновление проекта")
response = session.put(
    f"{BASE_URL}/api/v1/projects/{project_id}",
    headers=headers,
    json={
        "name": "Обновленный проект",
        "description": "Новое описание"
    }
)
print_result(f"PUT /api/v1/projects/{project_id}", response)

# 14. GET /api/v1/projects/{id}/stats - Статистика по проекту
print("\n[14/20] Получение статистики по проекту")
response = session.get(f"{BASE_URL}/api/v1/projects/{project_id}/stats", headers=headers)
print_result(f"GET /api/v1/projects/{project_id}/stats", response)

# 7. POST /api/v1/projects/{id}/tasks - Создание задачи
print("\n[7/20] Создание задачи в проекте")
due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
response = session.post(
    f"{BASE_URL}/api/v1/projects/{project_id}/tasks",
    headers=headers,
    json={
        "title": "Тестовая задача",
        "description": "Описание задачи",
        "status": "todo",
        "priority": "high",
        "due_date": due_date
    }
)
print_result(f"POST /api/v1/projects/{project_id}/tasks", response)
if response.status_code == 201:
    task_id = response.json()["id"]
    print(f"📝 ID задачи: {task_id}")

# 19. GET /api/v1/projects/{id}/tasks - Список задач проекта
print("\n[19/20] Получение списка задач в проекте")
response = session.get(f"{BASE_URL}/api/v1/projects/{project_id}/tasks", headers=headers)
print_result(f"GET /api/v1/projects/{project_id}/tasks", response)

# 8. PUT /api/v1/tasks/{id} - Обновление задачи
print("\n[8/20] Обновление задачи")
response = session.put(
    f"{BASE_URL}/api/v1/tasks/{task_id}",
    headers=headers,
    json={
        "title": "Обновленная задача",
        "status": "in_progress",
        "priority": "medium"
    }
)
print_result(f"PUT /api/v1/tasks/{task_id}", response)

# 10. POST /api/v1/tasks/{id}/comments - Добавление комментария
print("\n[10/20] Добавление комментария к задаче")
response = session.post(
    f"{BASE_URL}/api/v1/tasks/{task_id}/comments",
    headers=headers,
    json={
        "content": "Тестовый комментарий к задаче"
    }
)
print_result(f"POST /api/v1/tasks/{task_id}/comments", response)
if response.status_code == 201:
    comment_id = response.json()["id"]
    print(f"💬 ID комментария: {comment_id}")

# 20. GET /api/v1/tasks/{id}/comments - Список комментариев
print("\n[20/20] Получение списка комментариев к задаче")
response = session.get(f"{BASE_URL}/api/v1/tasks/{task_id}/comments", headers=headers)
print_result(f"GET /api/v1/tasks/{task_id}/comments", response)

# 15. POST /api/v1/tasks/{id}/tags - Добавление тега
print("\n[15/20] Добавление тега к задаче")
response = session.post(
    f"{BASE_URL}/api/v1/tasks/{task_id}/tags",
    headers=headers,
    json={
        "tag_name": "bug"
    }
)
print_result(f"POST /api/v1/tasks/{task_id}/tags", response)

# 12. POST /api/v1/projects/{id}/members - Добавление участника
print("\n[12/20] Добавление пользователя в команду проекта")
response = session.post(
    f"{BASE_URL}/api/v1/projects/{project_id}/members",
    headers=headers,
    json={
        "user_id": 2,  # testuser
        "role": "member"
    }
)
print_result(f"POST /api/v1/projects/{project_id}/members", response)

# 16. POST /api/v1/auth/refresh - Обновление токена
print("\n[16/20] Обновление access токена")
response = session.post(
    f"{BASE_URL}/api/v1/auth/refresh",
    json={
        "refresh_token": refresh_token_value
    }
)
print_result("POST /api/v1/auth/refresh", response)

# 11. DELETE /api/v1/comments/{id} - Удаление комментария
print("\n[11/20] Удаление комментария")
response = session.delete(f"{BASE_URL}/api/v1/comments/{comment_id}", headers=headers)
print_result(f"DELETE /api/v1/comments/{comment_id}", response)

# 13. DELETE /api/v1/projects/{id}/members/{user_id} - Удаление участника
print("\n[13/20] Удаление участника из команды")
response = session.delete(
    f"{BASE_URL}/api/v1/projects/{project_id}/members/2",
    headers=headers
)
print_result(f"DELETE /api/v1/projects/{project_id}/members/2", response)

# 9. DELETE /api/v1/tasks/{id} - Удаление задачи
print("\n[9/20] Удаление задачи")
response = session.delete(f"{BASE_URL}/api/v1/tasks/{task_id}", headers=headers)
print_result(f"DELETE /api/v1/tasks/{task_id}", response)

# 6. DELETE /api/v1/projects/{id} - Удаление проекта
print("\n[6/20] Удаление проекта")
response = session.delete(f"{BASE_URL}/api/v1/projects/{project_id}", headers=headers)
print_result(f"DELETE /api/v1/projects/{project_id}", response)

print("\n" + "=" * 80)
print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
print("=" * 80)
