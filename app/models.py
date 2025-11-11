from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


# Перечисления для статусов, приоритетов и ролей

class TaskStatus(str, enum.Enum):
    """Возможные статусы задачи"""
    TODO = "todo"              # Нужно сделать
    IN_PROGRESS = "in_progress"  # В работе
    REVIEW = "review"          # На проверке
    DONE = "done"              # Готово


class TaskPriority(str, enum.Enum):
    """Приоритет задачи"""
    LOW = "low"        # Низкий
    MEDIUM = "medium"  # Средний
    HIGH = "high"      # Высокий
    URGENT = "urgent"  # Срочный


class ProjectRole(str, enum.Enum):
    """Роль участника в проекте"""
    OWNER = "owner"    # Владелец
    ADMIN = "admin"    # Администратор
    MEMBER = "member"  # Участник
    VIEWER = "viewer"  # Наблюдатель


# Таблица для связи задач с тегами (одна задача может иметь много тегов и наоборот)
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    # Основные поля
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Хешированный пароль
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)  # Активен ли пользователь
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Когда создан
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Когда обновлен

    # Связи с другими таблицами
    owned_projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    tasks_assigned = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """Таблица для хранения refresh токенов"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)  # Сам токен
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Чей токен
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Когда истечет
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Когда создан

    # Связь с пользователем
    user = relationship("User", back_populates="refresh_tokens")


class Project(Base):
    """Таблица проектов"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Название проекта
    description = Column(Text, nullable=True)  # Описание проекта
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Кто владелец
    is_active = Column(Boolean, default=True)  # Активен ли проект
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    owner = relationship("User", back_populates="owned_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """Таблица участников проекта (команда проекта)"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)  # В каком проекте
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Какой пользователь
    role = Column(Enum(ProjectRole), default=ProjectRole.MEMBER, nullable=False)  # Его роль
    joined_at = Column(DateTime(timezone=True), server_default=func.now())  # Когда присоединился

    # Связи
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")


class Task(Base):
    """Таблица задач"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # Название задачи
    description = Column(Text, nullable=True)  # Описание задачи
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)  # К какому проекту относится
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Кто исполнитель (может быть никто)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)  # Статус задачи
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)  # Приоритет
    due_date = Column(DateTime(timezone=True), nullable=True)  # Срок выполнения (может не быть)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks_assigned")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")  # Связь через промежуточную таблицу


class Comment(Base):
    """Таблица комментариев к задачам"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Текст комментария
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)  # К какой задаче
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Кто автор
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Attachment(Base):
    """Таблица вложений (файлов) к задачам"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # Имя файла
    file_path = Column(String(500), nullable=False)  # Путь где лежит файл
    file_size = Column(Integer, nullable=False)  # Размер в байтах
    mime_type = Column(String(100), nullable=True)  # Тип файла (image/png, text/pdf и т.д.)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)  # К какой задаче
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())  # Когда загружен

    # Связь
    task = relationship("Task", back_populates="attachments")


class Tag(Base):
    """Таблица тегов (меток) для задач"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # Название тега (уникальное)
    color = Column(String(7), default="#808080")  # Цвет тега в формате HEX
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь (одна задача может иметь много тегов, один тег может быть у многих задач)
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
