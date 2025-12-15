from datetime import datetime,timedelta
from typing import Optional
from jose import JWTError,jwt
import bcrypt
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from.config import settings
from.database import get_db
from.models import User,RefreshToken
security=HTTPBearer()
def verify_password(plain_password:str,hashed_password:str)->bool:return bcrypt.checkpw(plain_password.encode('utf-8'),hashed_password.encode('utf-8'))
def get_password_hash(password:str)->str:A=bcrypt.gensalt();B=bcrypt.hashpw(password.encode('utf-8'),A);return B.decode('utf-8')
def create_access_token(user_id:int)->str:A=datetime.utcnow()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES);B={'sub':str(user_id),'exp':A,'type':'access'};C=jwt.encode(B,settings.SECRET_KEY,algorithm=settings.ALGORITHM);return C
def create_refresh_token(user_id:int)->str:A=datetime.utcnow()+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS);B={'sub':str(user_id),'exp':A,'type':'refresh'};C=jwt.encode(B,settings.SECRET_KEY,algorithm=settings.ALGORITHM);return C
def get_current_user(credentials:HTTPAuthorizationCredentials=Depends(security),db:Session=Depends(get_db))->User:
	D=credentials.credentials
	try:B=jwt.decode(D,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
	except JWTError:raise HTTPException(status_code=401,detail='Токен недействителен')
	if B.get('type')!='access':raise HTTPException(status_code=401,detail='Неправильный тип токена')
	C=B.get('sub')
	if not C:raise HTTPException(status_code=401,detail='Токен не содержит ID пользователя')
	E=int(C);A=db.query(User).filter(User.id==E).first()
	if not A:raise HTTPException(status_code=401,detail='Пользователь не найден')
	if not A.is_active:raise HTTPException(status_code=403,detail='Пользователь заблокирован')
	return A
def authenticate_user(db:Session,username:str,password:str)->Optional[User]:
	A=db.query(User).filter(User.username==username).first()
	if not A:return
	if not verify_password(password,A.hashed_password):return
	return A
def save_refresh_token(db:Session,user_id:int,token:str):A=user_id;db.query(RefreshToken).filter(RefreshToken.user_id==A).delete();B=datetime.utcnow()+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS);C=RefreshToken(token=token,user_id=A,expires_at=B);db.add(C);db.commit()
def check_refresh_token(db:Session,token:str)->Optional[User]:
	B=token
	try:C=jwt.decode(B,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
	except JWTError:return
	if C.get('type')!='refresh':return
	A=db.query(RefreshToken).filter(RefreshToken.token==B).first()
	if not A:return
	D=datetime.utcnow()
	if A.expires_at<D:db.delete(A);db.commit();return
	E=db.query(User).filter(User.id==A.user_id).first();return E