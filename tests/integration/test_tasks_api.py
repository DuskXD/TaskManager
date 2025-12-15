"""
Интеграционные тесты для эндпоинтов задач (app/routers/tasks.py)
"""
import pytest
from datetime import datetime, timedelta

from app.models import Project, Task, TaskStatus, TaskPriority, Comment, Tag


@pytest.fixture
def test_project(db_session, test_user):
    """Фикстура для создания тестового проекта"""
    project = Project(
        name="Test Project",
        description="Test Description",
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_task(db_session, test_project):
    """Фикстура для создания тестовой задачи"""
    task = Task(
        title="Test Task",
        description="Test task description",
        project_id=test_project.id,
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestCreateTask:
    """Тесты создания задачи"""
    
    def test_create_task_success(self, authorized_client, test_project):
        """Тест: успешное создание задачи"""
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={
                "title": "New Task",
                "description": "Task description"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
    
    def test_create_task_with_priority(self, authorized_client, test_project):
        """Тест: создание задачи с приоритетом"""
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={
                "title": "High Priority Task",
                "priority": "high"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["priority"] == "high"
    
    def test_create_task_with_due_date(self, authorized_client, test_project):
        """Тест: создание задачи с датой выполнения"""
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={
                "title": "Task with deadline",
                "due_date": future_date
            }
        )
        
        assert response.status_code == 201
        assert response.json()["due_date"] is not None
    
    def test_create_task_unauthorized(self, client, test_project):
        """Тест: создание задачи без авторизации"""
        response = client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={"title": "New Task"}
        )
        
        assert response.status_code == 401
    
    def test_create_task_project_not_found(self, authorized_client):
        """Тест: создание задачи в несуществующем проекте"""
        response = authorized_client.post(
            "/api/v1/projects/999/tasks",
            json={"title": "New Task"}
        )
        
        assert response.status_code == 404
    
    def test_create_task_empty_title(self, authorized_client, test_project):
        """Тест: создание задачи с пустым заголовком"""
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={"title": ""}
        )
        
        assert response.status_code == 422


class TestGetTasks:
    """Тесты получения списка задач"""
    
    def test_get_tasks_empty(self, authorized_client, test_project):
        """Тест: пустой список задач"""
        response = authorized_client.get(f"/api/v1/projects/{test_project.id}/tasks")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_tasks_with_tasks(self, authorized_client, test_project, test_task):
        """Тест: получение списка задач"""
        response = authorized_client.get(f"/api/v1/projects/{test_project.id}/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Task"


class TestUpdateTask:
    """Тесты обновления задачи"""
    
    def test_update_task_title(self, authorized_client, test_task):
        """Тест: обновление заголовка задачи"""
        response = authorized_client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
    
    def test_update_task_status(self, authorized_client, test_task):
        """Тест: обновление статуса задачи"""
        response = authorized_client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"status": "in_progress"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
    
    def test_update_task_priority(self, authorized_client, test_task):
        """Тест: обновление приоритета задачи"""
        response = authorized_client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"priority": "urgent"}
        )
        
        assert response.status_code == 200
        assert response.json()["priority"] == "urgent"
    
    def test_update_task_not_found(self, authorized_client):
        """Тест: обновление несуществующей задачи"""
        response = authorized_client.put(
            "/api/v1/tasks/999",
            json={"title": "Updated"}
        )
        
        assert response.status_code == 404


class TestDeleteTask:
    """Тесты удаления задачи"""
    
    def test_delete_task_success(self, authorized_client, test_task, test_project):
        """Тест: успешное удаление задачи"""
        response = authorized_client.delete(f"/api/v1/tasks/{test_task.id}")
        
        assert response.status_code == 204
    
    def test_delete_task_not_found(self, authorized_client):
        """Тест: удаление несуществующей задачи"""
        response = authorized_client.delete("/api/v1/tasks/999")
        
        assert response.status_code == 404


class TestTaskComments:
    """Тесты комментариев к задачам"""
    
    def test_add_comment_success(self, authorized_client, test_task):
        """Тест: успешное добавление комментария"""
        response = authorized_client.post(
            f"/api/v1/tasks/{test_task.id}/comments",
            json={"content": "This is a comment"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a comment"
        assert data["task_id"] == test_task.id
    
    def test_get_comments_empty(self, authorized_client, test_task):
        """Тест: пустой список комментариев"""
        response = authorized_client.get(f"/api/v1/tasks/{test_task.id}/comments")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_comments_with_comments(self, authorized_client, test_task, db_session, test_user):
        """Тест: получение комментариев"""
        comment = Comment(
            content="Test comment",
            task_id=test_task.id,
            author_id=test_user.id
        )
        db_session.add(comment)
        db_session.commit()
        
        response = authorized_client.get(f"/api/v1/tasks/{test_task.id}/comments")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Test comment"
    
    def test_delete_comment_success(self, authorized_client, test_task, db_session, test_user):
        """Тест: успешное удаление комментария"""
        comment = Comment(
            content="Test comment",
            task_id=test_task.id,
            author_id=test_user.id
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)
        
        response = authorized_client.delete(f"/api/v1/comments/{comment.id}")
        
        assert response.status_code == 204


class TestTaskTags:
    """Тесты тегов задач"""
    
    def test_add_tag_success(self, authorized_client, test_task):
        """Тест: успешное добавление тега"""
        response = authorized_client.post(
            f"/api/v1/tasks/{test_task.id}/tags",
            json={"tag_name": "bug"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "bug"
    
    def test_add_tag_creates_new_tag(self, authorized_client, test_task, db_session):
        """Тест: добавление тега создает новый тег"""
        response = authorized_client.post(
            f"/api/v1/tasks/{test_task.id}/tags",
            json={"tag_name": "new-feature"}
        )
        
        assert response.status_code == 200
        
        # Проверяем, что тег создан в БД
        tag = db_session.query(Tag).filter(Tag.name == "new-feature").first()
        assert tag is not None
    
    def test_add_duplicate_tag(self, authorized_client, test_task, db_session):
        """Тест: повторное добавление тега"""
        # Добавляем тег первый раз
        tag = Tag(name="duplicate-tag")
        db_session.add(tag)
        test_task.tags.append(tag)
        db_session.commit()
        
        # Пытаемся добавить снова
        response = authorized_client.post(
            f"/api/v1/tasks/{test_task.id}/tags",
            json={"tag_name": "duplicate-tag"}
        )
        
        assert response.status_code == 400
