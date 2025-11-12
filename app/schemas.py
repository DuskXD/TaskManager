from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models import TaskStatus, TaskPriority, ProjectRole



class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str



class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", pattern="^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    created_at: datetime
    tasks_count: int = 0
    members_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectStats(BaseModel):
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    review_tasks: int
    done_tasks: int
    total_members: int
    total_comments: int



class ProjectMemberBase(BaseModel):
    user_id: int
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)



class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    assignee: Optional[UserResponse] = None
    tags: List[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[int]
    due_date: Optional[datetime]
    created_at: datetime
    tags_count: int = 0
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)



class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    task_id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    author: UserResponse

    model_config = ConfigDict(from_attributes=True)



class AttachmentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    task_id: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)



class TaskTagAdd(BaseModel):
    tag_name: str = Field(..., min_length=1, max_length=50)
