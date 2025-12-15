"""
Unit-тесты для модуля аутентификации (app/auth.py)
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.config import settings


class TestPasswordHashing:
    """Тесты хеширования паролей"""
    
    def test_get_password_hash_returns_hash(self):
        """Тест: функция возвращает хеш пароля"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_get_password_hash_different_for_same_password(self):
        """Тест: разные хеши для одного пароля (из-за соли)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Хеши должны быть разными из-за случайной соли
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Тест: верификация правильного пароля"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Тест: верификация неправильного пароля"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_password(self):
        """Тест: верификация с пустым паролем"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestTokenCreation:
    """Тесты создания токенов"""
    
    def test_create_access_token(self):
        """Тест: создание access токена"""
        user_id = 1
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_contains_user_id(self):
        """Тест: access токен содержит ID пользователя"""
        user_id = 42
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload.get("sub") == str(user_id)
        assert payload.get("type") == "access"
    
    def test_create_access_token_has_expiration(self):
        """Тест: access токен имеет срок действия"""
        user_id = 1
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"])
        assert exp_time > datetime.utcnow()
    
    def test_create_refresh_token(self):
        """Тест: создание refresh токена"""
        user_id = 1
        token = create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token_contains_user_id(self):
        """Тест: refresh токен содержит ID пользователя"""
        user_id = 42
        token = create_refresh_token(user_id)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload.get("sub") == str(user_id)
        assert payload.get("type") == "refresh"
    
    def test_access_and_refresh_tokens_are_different(self):
        """Тест: access и refresh токены разные"""
        user_id = 1
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        assert access_token != refresh_token
    
    def test_refresh_token_expires_later_than_access(self):
        """Тест: refresh токен действует дольше access токена"""
        user_id = 1
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert refresh_payload["exp"] > access_payload["exp"]
