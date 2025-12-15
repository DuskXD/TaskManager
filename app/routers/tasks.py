from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Project, Task, ProjectMember, ProjectRole, Comment, Tag
from ..schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    CommentCreate,
    CommentResponse,
    TaskTagAdd
)
from ..auth import get_current_user

router = APIRouter(tags=["Tasks"])


def check_project_access(project_id: int, user: User, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    if project.owner_id == user.id:
        return project
    
    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Нет доступа к проекту"
        )
    
    return project


def check_task_access(task_id: int, user: User, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )
    
    check_project_access(task.project_id, user, db)
    
    return task


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = check_project_access(project_id, current_user, db)
    
    if task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail="Указанный пользователь не найден"
            )
        
        if project.owner_id != task_data.assignee_id:
            membership = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == task_data.assignee_id
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=400,
                    detail="Исполнитель не является участником проекта"
                )
    
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        project_id=project_id,
        assignee_id=task_data.assignee_id,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/projects/{project_id}/tasks", response_model=List[TaskListResponse])
def get_project_tasks(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_access(project_id, current_user, db)
    
    
    from sqlalchemy.orm import selectinload
    
    tasks = db.query(Task).filter(Task.project_id == project_id).options(
        selectinload(Task.tags)
    ).all()
    
    
    task_ids = [task.id for task in tasks]
    comments_counts = dict(
        db.query(Comment.task_id, func.count(Comment.id))
        .filter(Comment.task_id.in_(task_ids))
        .group_by(Comment.task_id)
        .all()
    ) if task_ids else {}
    
    result = []
    for task in tasks:
        result.append(TaskListResponse(
            id=task.id,
            title=task.title,
            status=task.status,
            priority=task.priority,
            assignee_id=task.assignee_id,
            due_date=task.due_date,
            created_at=task.created_at,
            tags_count=len(task.tags),
            comments_count=comments_counts.get(task.id, 0)
        ))
    
    return result


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = check_task_access(task_id, current_user, db)
    
    if task_data.assignee_id is not None and task_data.assignee_id:
        assignee = db.query(User).filter(User.id == task_data.assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail="Указанный пользователь не найден"
            )
        
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if project.owner_id != task_data.assignee_id:
            membership = db.query(ProjectMember).filter(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == task_data.assignee_id
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=400,
                    detail="Исполнитель не является участником проекта"
                )
    
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.assignee_id is not None:
        task.assignee_id = task_data.assignee_id
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление задачи"""
    task = check_task_access(task_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == task.project_id).first()
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только владелец проекта может удалять задачи"
        )
    
    db.delete(task)
    db.commit()
    
    return None


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = check_task_access(task_id, current_user, db)
    
    db_comment = Comment(
        content=comment_data.content,
        task_id=task_id,
        author_id=current_user.id
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment


@router.get("/tasks/{task_id}/comments", response_model=List[CommentResponse])
def get_task_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_task_access(task_id, current_user, db)
    
    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at).all()
    
    return comments


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Комментарий не найден"
        )
    
    task = check_task_access(comment.task_id, current_user, db)
    
    if comment.author_id != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        
        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Только автор комментария или владелец проекта может удалить комментарий"
            )
    
    db.delete(comment)
    db.commit()
    
    return None


@router.post("/tasks/{task_id}/tags", response_model=TaskResponse)
def add_tag_to_task(
    task_id: int,
    tag_data: TaskTagAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = check_task_access(task_id, current_user, db)
    
    tag = db.query(Tag).filter(Tag.name == tag_data.tag_name).first()
    
    if not tag:
        tag = Tag(name=tag_data.tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    
    if tag in task.tags:
        raise HTTPException(
            status_code=400,
            detail="Тег уже добавлен к задаче"
        )
    
    task.tags.append(tag)
    db.commit()
    db.refresh(task)
    
    return task
