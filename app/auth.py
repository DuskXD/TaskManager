from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, RefreshToken

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    data = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    data = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Токен недействителен"
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Неправильный тип токена"
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=401,
            detail="Токен не содержит ID пользователя"
        )
    
    user_id = int(user_id_str)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Пользователь заблокирован"
        )
    
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def save_refresh_token(db: Session, user_id: int, token: str):
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    db.add(new_token)
    db.commit()


def check_refresh_token(db: Session, token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    
    if payload.get("type") != "refresh":
        return None
    
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if not db_token:
        return None
    
    now = datetime.utcnow()
    if db_token.expires_at < now:
        db.delete(db_token)
        db.commit()
        return None
    
    user = db.query(User).filter(User.id == db_token.user_id).first()
    return user
