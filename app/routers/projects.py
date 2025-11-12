from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..database import get_db
from ..models import User, Project, ProjectMember, Task, Comment, ProjectRole, TaskStatus
from ..schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStats,
    ProjectMemberCreate,
    ProjectMemberResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])

def check_project_access(project: Project, user: User):
    if project.owner_id == user.id:
        return True
 
    for member in project.members:
        if member.user_id == user.id:
            return True
   
    raise HTTPException(
        status_code=403,
        detail="Нет доступа к проекту"
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


@router.get("", response_model=List[ProjectListResponse])
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    owned_projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    member_projects = db.query(Project).join(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    ).all()
    
    all_projects = {p.id: p for p in owned_projects + member_projects}.values()
    
    result = []
    for project in all_projects:
        tasks_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
        members_count = db.query(func.count(ProjectMember.id)).filter(
            ProjectMember.project_id == project.id
        ).scalar()
        
        result.append(ProjectListResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            is_active=project.is_active,
            created_at=project.created_at,
            tasks_count=tasks_count,
            members_count=members_count
        ))
    
    return result


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение деталей проекта"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    check_project_access(project, current_user)
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только владелец может обновлять проект"
        )
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.is_active is not None:
        project.is_active = project_data.is_active
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление проекта"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только владелец может удалить проект"
        )
    
    db.delete(project)
    db.commit()
    
    return None


@router.get("/{project_id}/stats", response_model=ProjectStats)
def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    
    check_project_access(project, current_user)
    
    total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar()
    
    todo_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.TODO
    ).scalar()
    
    in_progress_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.IN_PROGRESS
    ).scalar()
    
    review_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.REVIEW
    ).scalar()
    
    done_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.DONE
    ).scalar()
    
    total_members = db.query(func.count(ProjectMember.id)).filter(
        ProjectMember.project_id == project_id
    ).scalar()
    
    total_comments = db.query(func.count(Comment.id)).join(Task).filter(
        Task.project_id == project_id
    ).scalar()
    
    return ProjectStats(
        total_tasks=total_tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        review_tasks=review_tasks,
        done_tasks=done_tasks,
        total_members=total_members,
        total_comments=total_comments
    )


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только владелец может добавлять участников"
        )
    
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_data.user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="Пользователь уже является участником проекта"
        )
    
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Проект не найден"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Только владелец может удалять участников"
        )
    
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Участник не найден в проекте"
        )
    
    db.delete(member)
    db.commit()
    
    return None
