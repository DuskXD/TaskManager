from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from datetime import datetime,timedelta
from..database import get_db
from..models import User
from..schemas import UserCreate,UserResponse,LoginRequest,Token,TokenRefresh
from..auth import get_password_hash,authenticate_user,create_access_token,create_refresh_token,save_refresh_token,check_refresh_token
from..config import settings
router=APIRouter(prefix='/auth',tags=['Authentication'])
@router.post('/register',response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register(user_data:UserCreate,db:Session=Depends(get_db)):
	B=db;A=user_data;C=B.query(User).filter(User.email==A.email).first()
	if C:raise HTTPException(status_code=409,detail='Email уже зарегистрирован')
	C=B.query(User).filter(User.username==A.username).first()
	if C:raise HTTPException(status_code=409,detail='Имя пользователя уже занято')
	E=get_password_hash(A.password);D=User(email=A.email,username=A.username,full_name=A.full_name,hashed_password=E);B.add(D);B.commit();B.refresh(D);return D
@router.post('/login',response_model=Token)
def login(login_data:LoginRequest,db:Session=Depends(get_db)):
	B=login_data;A=authenticate_user(db,B.username,B.password)
	if not A:raise HTTPException(status_code=401,detail='Неверное имя пользователя или пароль')
	if not A.is_active:raise HTTPException(status_code=403,detail='Пользователь неактивен')
	D=create_access_token(A.id);C=create_refresh_token(A.id);save_refresh_token(db,A.id,C);return{'access_token':D,'refresh_token':C,'token_type':'bearer'}
@router.post('/refresh',response_model=Token)
def refresh_token(token_data:TokenRefresh,db:Session=Depends(get_db)):
	A=check_refresh_token(db,token_data.refresh_token)
	if not A:raise HTTPException(status_code=401,detail='Недействительный refresh токен')
	if not A.is_active:raise HTTPException(status_code=403,detail='Пользователь неактивен')
	C=create_access_token(A.id);B=create_refresh_token(A.id);save_refresh_token(db,A.id,B);return{'access_token':C,'refresh_token':B,'token_type':'bearer'}