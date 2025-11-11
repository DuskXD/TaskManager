from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, LoginRequest, Token, TokenRefresh
from ..auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    save_refresh_token,
    check_refresh_token,
    get_current_user
)
from ..config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем существует ли email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email уже зарегистрирован"
        )
    
    # Проверяем существует ли username
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя уже занято"
        )
    
    # Хешируем пароль
    hashed_password = get_password_hash(user_data.password)
    
    # Создаем нового пользователя
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    # Сохраняем в БД
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Вход и получение JWT токенов"""
    # Проверяем логин и пароль
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Пользователь неактивен"
        )
    
    # Создаем токены (передаем только ID пользователя)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Сохраняем refresh токен в БД
    save_refresh_token(db, user.id, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Обновление access токена с помощью refresh токена"""
    # Проверяем refresh токен
    user = check_refresh_token(db, token_data.refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Недействительный refresh токен"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Пользователь неактивен"
        )
    
    # Создаем новые токены
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Сохраняем новый refresh токен
    save_refresh_token(db, user.id, refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
