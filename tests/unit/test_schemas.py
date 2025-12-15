"""
Unit-тесты для Pydantic схем (app/schemas.py)
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas import (
    UserCreate,
    UserBase,
    LoginRequest,
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
    TagCreate,
    CommentCreate,
)
from app.models import TaskStatus, TaskPriority


class TestUserSchemas:
    """Тесты схем пользователя"""
    
    def test_user_create_valid(self):
        """Тест: валидное создание пользователя"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"
    
    def test_user_create_with_full_name(self):
        """Тест: создание пользователя с полным именем"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        assert user.full_name == "Test User"
    
    def test_user_create_invalid_email(self):
        """Тест: невалидный email"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                username="testuser",
                password="password123"
            )
    
    def test_user_create_short_username(self):
        """Тест: слишком короткий username (меньше 3 символов)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="password123"
            )
    
    def test_user_create_short_password(self):
        """Тест: слишком короткий пароль (меньше 6 символов)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="12345"
            )
    
    def test_login_request_valid(self):
        """Тест: валидный запрос логина"""
        login = LoginRequest(username="testuser", password="password123")
        assert login.username == "testuser"
        assert login.password == "password123"


class TestProjectSchemas:
    """Тесты схем проекта"""
    
    def test_project_create_valid(self):
        """Тест: валидное создание проекта"""
        project = ProjectCreate(name="Test Project")
        assert project.name == "Test Project"
        assert project.description is None
    
    def test_project_create_with_description(self):
        """Тест: создание проекта с описанием"""
        project = ProjectCreate(
            name="Test Project",
            description="This is a test project"
        )
        assert project.description == "This is a test project"
    
    def test_project_create_empty_name(self):
        """Тест: пустое имя проекта"""
        with pytest.raises(ValidationError):
            ProjectCreate(name="")
    
    def test_project_update_partial(self):
        """Тест: частичное обновление проекта"""
        update = ProjectUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None
        assert update.is_active is None
    
    def test_project_update_all_fields(self):
        """Тест: обновление всех полей проекта"""
        update = ProjectUpdate(
            name="Updated Name",
            description="Updated description",
            is_active=False
        )
        assert update.name == "Updated Name"
        assert update.description == "Updated description"
        assert update.is_active is False


class TestTaskSchemas:
    """Тесты схем задачи"""
    
    def test_task_create_valid(self):
        """Тест: валидное создание задачи"""
        task = TaskCreate(title="Test Task")
        assert task.title == "Test Task"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
    
    def test_task_create_with_all_fields(self):
        """Тест: создание задачи со всеми полями"""
        future_date = datetime.now() + timedelta(days=7)
        task = TaskCreate(
            title="Test Task",
            description="Task description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=future_date
        )
        assert task.description == "Task description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
    
    def test_task_create_empty_title(self):
        """Тест: пустой заголовок задачи"""
        with pytest.raises(ValidationError):
            TaskCreate(title="")
    
    def test_task_create_past_due_date(self):
        """Тест: дата выполнения в прошлом"""
        past_date = datetime.now() - timedelta(days=1)
        with pytest.raises(ValidationError):
            TaskCreate(title="Test Task", due_date=past_date)
    
    def test_task_create_future_due_date(self):
        """Тест: дата выполнения в будущем (валидно)"""
        future_date = datetime.now() + timedelta(days=7)
        task = TaskCreate(title="Test Task", due_date=future_date)
        assert task.due_date is not None
    
    def test_task_update_partial(self):
        """Тест: частичное обновление задачи"""
        update = TaskUpdate(status=TaskStatus.DONE)
        assert update.status == TaskStatus.DONE
        assert update.title is None
        assert update.priority is None


class TestTagSchemas:
    """Тесты схем тегов"""
    
    def test_tag_create_valid(self):
        """Тест: валидное создание тега"""
        tag = TagCreate(name="bug")
        assert tag.name == "bug"
        assert tag.color == "#808080"  # default color
    
    def test_tag_create_with_color(self):
        """Тест: создание тега с цветом"""
        tag = TagCreate(name="feature", color="#FF5733")
        assert tag.color == "#FF5733"
    
    def test_tag_create_invalid_color(self):
        """Тест: невалидный формат цвета"""
        with pytest.raises(ValidationError):
            TagCreate(name="bug", color="red")
    
    def test_tag_create_invalid_color_format(self):
        """Тест: невалидный HEX цвет"""
        with pytest.raises(ValidationError):
            TagCreate(name="bug", color="#GGGGGG")
    
    def test_tag_create_empty_name(self):
        """Тест: пустое имя тега"""
        with pytest.raises(ValidationError):
            TagCreate(name="")


class TestCommentSchemas:
    """Тесты схем комментариев"""
    
    def test_comment_create_valid(self):
        """Тест: валидное создание комментария"""
        comment = CommentCreate(content="This is a comment")
        assert comment.content == "This is a comment"
    
    def test_comment_create_empty_content(self):
        """Тест: пустой комментарий"""
        with pytest.raises(ValidationError):
            CommentCreate(content="")
