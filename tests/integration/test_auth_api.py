"""
Интеграционные тесты для эндпоинтов аутентификации (app/routers/auth.py)
"""
import pytest


class TestRegister:
    """Тесты регистрации пользователя"""
    
    def test_register_success(self, client):
        """Тест: успешная регистрация"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data  
    
    def test_register_with_full_name(self, client):
        """Тест: регистрация с полным именем"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        assert response.json()["full_name"] == "New User"
    
    def test_register_duplicate_email(self, client, test_user):
        """Тест: регистрация с существующим email"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",  # Уже существует
            "username": "anotheruser",
            "password": "password123"
        })
        
        assert response.status_code == 409
        assert "Email уже зарегистрирован" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client, test_user):
        """Тест: регистрация с существующим username"""
        response = client.post("/api/v1/auth/register", json={
            "email": "another@example.com",
            "username": "testuser",  # Уже существует
            "password": "password123"
        })
        
        assert response.status_code == 409
        assert "Имя пользователя уже занято" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        """Тест: регистрация с невалидным email"""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "username": "newuser",
            "password": "password123"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self, client):
        """Тест: регистрация с коротким паролем"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "123"
        })
        
        assert response.status_code == 422


class TestLogin:
    """Тесты входа в систему"""
    
    def test_login_success(self, client, test_user):
        """Тест: успешный вход"""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Тест: неверный пароль"""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Неверное имя пользователя или пароль" in response.json()["detail"]
    
    def test_login_wrong_username(self, client):
        """Тест: несуществующий пользователь"""
        response = client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client, db_session, test_user):
        """Тест: вход неактивного пользователя"""
        test_user.is_active = False
        db_session.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        assert response.status_code == 403
        assert "Пользователь неактивен" in response.json()["detail"]


class TestRefreshToken:
    """Тесты обновления токена"""
    
    def test_refresh_token_success(self, client, test_user):
        """Тест: успешное обновление токена"""
        # Сначала логинимся
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Обновляем токен
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client):
        """Тест: невалидный refresh токен"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        
        assert response.status_code == 401


class TestGetCurrentUser:
    """Тесты получения текущего пользователя"""
    
    def test_get_me_success(self, authorized_client, test_user):
        """Тест: успешное получение профиля"""
        response = authorized_client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_get_me_unauthorized(self, client):
        """Тест: запрос без авторизации"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401  # Unauthorized (no token)
    
    def test_get_me_invalid_token(self, client):
        """Тест: запрос с невалидным токеном"""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
