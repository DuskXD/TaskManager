from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from..database import get_db
from..models import User,Project,ProjectMember,Task,Comment,ProjectRole,TaskStatus
from..schemas import ProjectCreate,ProjectUpdate,ProjectResponse,ProjectListResponse,ProjectStats,ProjectMemberCreate,ProjectMemberResponse
from..auth import get_current_user
router=APIRouter(prefix='/projects',tags=['Projects'])
def check_project_access(project:Project,user:User):
	A=project
	if A.owner_id==user.id:return True
	for B in A.members:
		if B.user_id==user.id:return True
	raise HTTPException(status_code=403,detail='Нет доступа к проекту')
@router.post('',response_model=ProjectResponse,status_code=status.HTTP_201_CREATED)
def create_project(project_data:ProjectCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):B=project_data;A=Project(name=B.name,description=B.description,owner_id=current_user.id);db.add(A);db.commit();db.refresh(A);return A
@router.get('',response_model=List[ProjectListResponse])
def get_projects(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	B=current_user;D=db.query(Project).filter(Project.owner_id==B.id).all();E=db.query(Project).join(ProjectMember).filter(ProjectMember.user_id==B.id).all();F={A.id:A for A in D+E}.values();C=[]
	for A in F:G=db.query(func.count(Task.id)).filter(Task.project_id==A.id).scalar();H=db.query(func.count(ProjectMember.id)).filter(ProjectMember.project_id==A.id).scalar();C.append(ProjectListResponse(id=A.id,name=A.name,description=A.description,owner_id=A.owner_id,is_active=A.is_active,created_at=A.created_at,tasks_count=G,members_count=H))
	return C
@router.get('/{project_id}',response_model=ProjectResponse)
def get_project(project_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	A=db.query(Project).filter(Project.id==project_id,Project.is_active==True).first()
	if not A:raise HTTPException(status_code=404,detail='Проект не найден')
	check_project_access(A,current_user);return A
@router.put('/{project_id}',response_model=ProjectResponse)
def update_project(project_id:int,project_data:ProjectUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	B=project_data;A=db.query(Project).filter(Project.id==project_id,Project.is_active==True).first()
	if not A:raise HTTPException(status_code=404,detail='Проект не найден')
	if A.owner_id!=current_user.id:raise HTTPException(status_code=403,detail='Только владелец может обновлять проект')
	if B.name is not None:A.name=B.name
	if B.description is not None:A.description=B.description
	if B.is_active is not None:A.is_active=B.is_active
	db.commit();db.refresh(A);return A
@router.delete('/{project_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	A=db.query(Project).filter(Project.id==project_id,Project.is_active==True).first()
	if not A:raise HTTPException(status_code=404,detail='Проект не найден')
	if A.owner_id!=current_user.id:raise HTTPException(status_code=403,detail='Только владелец может удалить проект')
	A.is_active=False;db.commit()
@router.get('/{project_id}/stats',response_model=ProjectStats)
def get_project_stats(project_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	B=db;A=project_id;C=B.query(Project).filter(Project.id==A,Project.is_active==True).first()
	if not C:raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='Проект не найден')
	check_project_access(C,current_user);D=B.query(func.count(Task.id)).filter(Task.project_id==A).scalar();E=B.query(func.count(Task.id)).filter(Task.project_id==A,Task.status==TaskStatus.TODO).scalar();F=B.query(func.count(Task.id)).filter(Task.project_id==A,Task.status==TaskStatus.IN_PROGRESS).scalar();G=B.query(func.count(Task.id)).filter(Task.project_id==A,Task.status==TaskStatus.REVIEW).scalar();H=B.query(func.count(Task.id)).filter(Task.project_id==A,Task.status==TaskStatus.DONE).scalar();I=B.query(func.count(ProjectMember.id)).filter(ProjectMember.project_id==A).scalar();J=B.query(func.count(Comment.id)).join(Task).filter(Task.project_id==A).scalar();return ProjectStats(total_tasks=D,todo_tasks=E,in_progress_tasks=F,review_tasks=G,done_tasks=H,total_members=I,total_comments=J)
@router.post('/{project_id}/members',response_model=ProjectMemberResponse,status_code=status.HTTP_201_CREATED)
def add_project_member(project_id:int,member_data:ProjectMemberCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	C=project_id;B=member_data;A=db;E=A.query(Project).filter(Project.id==C).first()
	if not E:raise HTTPException(status_code=404,detail='Проект не найден')
	if E.owner_id!=current_user.id:raise HTTPException(status_code=403,detail='Только владелец может добавлять участников')
	F=A.query(User).filter(User.id==B.user_id).first()
	if not F:raise HTTPException(status_code=404,detail='Пользователь не найден')
	G=A.query(ProjectMember).filter(ProjectMember.project_id==C,ProjectMember.user_id==B.user_id).first()
	if G:raise HTTPException(status_code=409,detail='Пользователь уже является участником проекта')
	D=ProjectMember(project_id=C,user_id=B.user_id,role=B.role);A.add(D);A.commit();A.refresh(D);return D
@router.delete('/{project_id}/members/{user_id}',status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(project_id:int,user_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	C=user_id;B=project_id;A=db.query(Project).filter(Project.id==B,Project.is_active==True).first()
	if not A:raise HTTPException(status_code=404,detail='Проект не найден')
	if A.owner_id!=current_user.id:raise HTTPException(status_code=403,detail='Только владелец может удалять участников')
	if C==A.owner_id:raise HTTPException(status_code=400,detail='Владелец проекта не может удалить сам себя из участников')
	D=db.query(ProjectMember).filter(ProjectMember.project_id==B,ProjectMember.user_id==C).first()
	if not D:raise HTTPException(status_code=404,detail='Участник не найден в проекте')
	db.delete(D);db.commit()