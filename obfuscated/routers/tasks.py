from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from..database import get_db
from..models import User,Project,Task,ProjectMember,ProjectRole,Comment,Tag
from..schemas import TaskCreate,TaskUpdate,TaskResponse,TaskListResponse,CommentCreate,CommentResponse,TaskTagAdd
from..auth import get_current_user
router=APIRouter(tags=['Tasks'])
def check_project_access(project_id:int,user:User,db:Session):
	B=project_id;A=db.query(Project).filter(Project.id==B).first()
	if not A:raise HTTPException(status_code=404,detail='Проект не найден')
	if A.owner_id==user.id:return A
	C=db.query(ProjectMember).filter(ProjectMember.project_id==B,ProjectMember.user_id==user.id).first()
	if not C:raise HTTPException(status_code=403,detail='Нет доступа к проекту')
	return A
def check_task_access(task_id:int,user:User,db:Session):
	A=db.query(Task).filter(Task.id==task_id).first()
	if not A:raise HTTPException(status_code=404,detail='Задача не найдена')
	check_project_access(A.project_id,user,db);return A
@router.post('/projects/{project_id}/tasks',response_model=TaskResponse,status_code=status.HTTP_201_CREATED)
def create_task(project_id:int,task_data:TaskCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	C=project_id;B=db;A=task_data;E=check_project_access(C,current_user,B)
	if A.assignee_id:
		F=B.query(User).filter(User.id==A.assignee_id).first()
		if not F:raise HTTPException(status_code=404,detail='Указанный пользователь не найден')
		if E.owner_id!=A.assignee_id:
			G=B.query(ProjectMember).filter(ProjectMember.project_id==C,ProjectMember.user_id==A.assignee_id).first()
			if not G:raise HTTPException(status_code=400,detail='Исполнитель не является участником проекта')
	D=Task(title=A.title,description=A.description,project_id=C,assignee_id=A.assignee_id,status=A.status,priority=A.priority,due_date=A.due_date);B.add(D);B.commit();B.refresh(D);return D
@router.get('/projects/{project_id}/tasks',response_model=List[TaskListResponse])
def get_project_tasks(project_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	B=project_id;check_project_access(B,current_user,db);from sqlalchemy.orm import selectinload as F;C=db.query(Task).filter(Task.project_id==B).options(F(Task.tags)).all();D=[A.id for A in C];G=dict(db.query(Comment.task_id,func.count(Comment.id)).filter(Comment.task_id.in_(D)).group_by(Comment.task_id).all())if D else{};E=[]
	for A in C:E.append(TaskListResponse(id=A.id,title=A.title,status=A.status,priority=A.priority,assignee_id=A.assignee_id,due_date=A.due_date,created_at=A.created_at,tags_count=len(A.tags),comments_count=G.get(A.id,0)))
	return E
@router.put('/tasks/{task_id}',response_model=TaskResponse)
def update_task(task_id:int,task_data:TaskUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	C=db;A=task_data;B=check_task_access(task_id,current_user,C)
	if A.assignee_id is not None and A.assignee_id:
		D=C.query(User).filter(User.id==A.assignee_id).first()
		if not D:raise HTTPException(status_code=404,detail='Указанный пользователь не найден')
		E=C.query(Project).filter(Project.id==B.project_id).first()
		if E.owner_id!=A.assignee_id:
			F=C.query(ProjectMember).filter(ProjectMember.project_id==B.project_id,ProjectMember.user_id==A.assignee_id).first()
			if not F:raise HTTPException(status_code=400,detail='Исполнитель не является участником проекта')
	if A.title is not None:B.title=A.title
	if A.description is not None:B.description=A.description
	if A.assignee_id is not None:B.assignee_id=A.assignee_id
	if A.status is not None:B.status=A.status
	if A.priority is not None:B.priority=A.priority
	if A.due_date is not None:B.due_date=A.due_date
	C.commit();C.refresh(B);return B
@router.delete('/tasks/{task_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	A=current_user;B=check_task_access(task_id,A,db);C=db.query(Project).filter(Project.id==B.project_id).first()
	if C.owner_id!=A.id:raise HTTPException(status_code=403,detail='Только владелец проекта может удалять задачи')
	db.delete(B);db.commit()
@router.post('/tasks/{task_id}/comments',response_model=CommentResponse,status_code=status.HTTP_201_CREATED)
def add_comment(task_id:int,comment_data:CommentCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):C=current_user;B=task_id;D=check_task_access(B,C,db);A=Comment(content=comment_data.content,task_id=B,author_id=C.id);db.add(A);db.commit();db.refresh(A);return A
@router.get('/tasks/{task_id}/comments',response_model=List[CommentResponse])
def get_task_comments(task_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):A=task_id;check_task_access(A,current_user,db);B=db.query(Comment).filter(Comment.task_id==A).order_by(Comment.created_at).all();return B
@router.delete('/comments/{comment_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	C=current_user;A=db;B=A.query(Comment).filter(Comment.id==comment_id).first()
	if not B:raise HTTPException(status_code=404,detail='Комментарий не найден')
	D=check_task_access(B.task_id,C,A)
	if B.author_id!=C.id:
		E=A.query(Project).filter(Project.id==D.project_id).first()
		if E.owner_id!=C.id:raise HTTPException(status_code=403,detail='Только автор комментария или владелец проекта может удалить комментарий')
	A.delete(B);A.commit()
@router.post('/tasks/{task_id}/tags',response_model=TaskResponse)
def add_tag_to_task(task_id:int,tag_data:TaskTagAdd,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
	D=tag_data;A=db;C=check_task_access(task_id,current_user,A);B=A.query(Tag).filter(Tag.name==D.tag_name).first()
	if not B:B=Tag(name=D.tag_name);A.add(B);A.commit();A.refresh(B)
	if B in C.tags:raise HTTPException(status_code=400,detail='Тег уже добавлен к задаче')
	C.tags.append(B);A.commit();A.refresh(C);return C