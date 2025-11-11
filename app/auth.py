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

# Создаем объект для проверки Bearer токенов
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли пароль с хешем"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Создает хеш пароля"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(user_id: int) -> str:
    """Создает токен доступа (живет 30 минут)"""
    # Время истечения токена
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Данные которые будут в токене
    data = {
        "sub": str(user_id),  # ID пользователя (должен быть строкой)
        "exp": expire,        # Когда истекает
        "type": "access"      # Тип токена
    }
    
    # Создаем токен
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(user_id: int) -> str:
    """Создает refresh токен (живет 7 дней)"""
    # Время истечения токена
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Данные которые будут в токене
    data = {
        "sub": str(user_id),  # ID пользователя
        "exp": expire,        # Когда истекает
        "type": "refresh"     # Тип токена
    }
    
    # Создаем токен
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получает текущего пользователя из токена"""
    # Получаем токен из заголовка Authorization
    token = credentials.credentials
    
    # Пробуем декодировать токен
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Токен недействителен"
        )
    
    # Проверяем что это access токен
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Неправильный тип токена"
        )
    
    # Получаем ID пользователя из токена
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=401,
            detail="Токен не содержит ID пользователя"
        )
    
    # Преобразуем в число
    user_id = int(user_id_str)
    
    # Ищем пользователя в базе
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден"
        )
    
    # Проверяем что пользователь активен
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Пользователь заблокирован"
        )
    
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Проверяет логин и пароль пользователя"""
    # Ищем пользователя по username
    user = db.query(User).filter(User.username == username).first()
    
    # Если не нашли - возвращаем None
    if not user:
        return None
    
    # Проверяем пароль
    if not verify_password(password, user.hashed_password):
        return None
    
    # Всё верно - возвращаем пользователя
    return user


def save_refresh_token(db: Session, user_id: int, token: str):
    """Сохраняет refresh токен в базу данных"""
    # Удаляем старые токены этого пользователя (один пользователь = один активный токен)
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    
    # Создаем новый токен
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    db.add(new_token)
    db.commit()


def check_refresh_token(db: Session, token: str) -> Optional[User]:
    """Проверяет refresh токен и возвращает пользователя"""
    # Пробуем декодировать токен
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    
    # Проверяем что это refresh токен
    if payload.get("type") != "refresh":
        return None
    
    # Ищем токен в базе данных
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if not db_token:
        return None
    
    # Проверяем не истек ли токен
    now = datetime.utcnow()
    if db_token.expires_at < now:
        # Токен истек - удаляем его
        db.delete(db_token)
        db.commit()
        return None
    
    # Получаем пользователя
    user = db.query(User).filter(User.id == db_token.user_id).first()
    return user
