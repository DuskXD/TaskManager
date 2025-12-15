"""
Интеграционные тесты для эндпоинтов проектов (app/routers/projects.py)
"""
import pytest

from app.models import Project, ProjectMember, ProjectRole


@pytest.fixture
def test_project(db_session, test_user):
    """Фикстура для создания тестового проекта"""
    project = Project(
        name="Test Project",
        description="Test Description",
        owner_id=test_user.id
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestCreateProject:
    """Тесты создания проекта"""
    
    def test_create_project_success(self, authorized_client):
        """Тест: успешное создание проекта"""
        response = authorized_client.post("/api/v1/projects", json={
            "name": "New Project",
            "description": "Project description"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "Project description"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_create_project_without_description(self, authorized_client):
        """Тест: создание проекта без описания"""
        response = authorized_client.post("/api/v1/projects", json={
            "name": "New Project"
        })
        
        assert response.status_code == 201
        assert response.json()["description"] is None
    
    def test_create_project_unauthorized(self, client):
        """Тест: создание проекта без авторизации"""
        response = client.post("/api/v1/projects", json={
            "name": "New Project"
        })
        
        assert response.status_code == 401
    
    def test_create_project_empty_name(self, authorized_client):
        """Тест: создание проекта с пустым именем"""
        response = authorized_client.post("/api/v1/projects", json={
            "name": ""
        })
        
        assert response.status_code == 422


class TestGetProjects:
    """Тесты получения списка проектов"""
    
    def test_get_projects_empty(self, authorized_client):
        """Тест: пустой список проектов"""
        response = authorized_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_projects_with_owned(self, authorized_client, test_project):
        """Тест: получение своих проектов"""
        response = authorized_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"
    
    def test_get_projects_unauthorized(self, client):
        """Тест: получение проектов без авторизации"""
        response = client.get("/api/v1/projects")
        
        assert response.status_code == 401


class TestGetProject:
    """Тесты получения одного проекта"""
    
    def test_get_project_success(self, authorized_client, test_project):
        """Тест: успешное получение проекта"""
        response = authorized_client.get(f"/api/v1/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == "Test Project"
    
    def test_get_project_not_found(self, authorized_client):
        """Тест: проект не найден"""
        response = authorized_client.get("/api/v1/projects/999")
        
        assert response.status_code == 404
    
    def test_get_project_no_access(self, authorized_client, db_session, second_user):
        """Тест: нет доступа к чужому проекту"""
        # Создаем проект другого пользователя
        other_project = Project(
            name="Other Project",
            owner_id=second_user.id
        )
        db_session.add(other_project)
        db_session.commit()
        
        response = authorized_client.get(f"/api/v1/projects/{other_project.id}")
        
        assert response.status_code == 403


class TestUpdateProject:
    """Тесты обновления проекта"""
    
    def test_update_project_success(self, authorized_client, test_project):
        """Тест: успешное обновление проекта"""
        response = authorized_client.put(f"/api/v1/projects/{test_project.id}", json={
            "name": "Updated Name",
            "description": "Updated description"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
    
    def test_update_project_partial(self, authorized_client, test_project):
        """Тест: частичное обновление проекта"""
        response = authorized_client.put(f"/api/v1/projects/{test_project.id}", json={
            "name": "Only Name Updated"
        })
        
        assert response.status_code == 200
        assert response.json()["name"] == "Only Name Updated"
    
    def test_update_project_not_owner(self, authorized_client, db_session, second_user):
        """Тест: обновление чужого проекта"""
        other_project = Project(
            name="Other Project",
            owner_id=second_user.id
        )
        db_session.add(other_project)
        db_session.commit()
        
        response = authorized_client.put(f"/api/v1/projects/{other_project.id}", json={
            "name": "Hacked Name"
        })
        
        assert response.status_code == 403


class TestDeleteProject:
    """Тесты удаления проекта"""
    
    def test_delete_project_success(self, authorized_client, test_project):
        """Тест: успешное удаление проекта"""
        response = authorized_client.delete(f"/api/v1/projects/{test_project.id}")
        
        assert response.status_code == 204
        
        # Проверяем, что проект удален
        get_response = authorized_client.get(f"/api/v1/projects/{test_project.id}")
        assert get_response.status_code == 404
    
    def test_delete_project_not_found(self, authorized_client):
        """Тест: удаление несуществующего проекта"""
        response = authorized_client.delete("/api/v1/projects/999")
        
        assert response.status_code == 404
    
    def test_delete_project_not_owner(self, authorized_client, db_session, second_user):
        """Тест: удаление чужого проекта"""
        other_project = Project(
            name="Other Project",
            owner_id=second_user.id
        )
        db_session.add(other_project)
        db_session.commit()
        
        response = authorized_client.delete(f"/api/v1/projects/{other_project.id}")
        
        assert response.status_code == 403


class TestProjectMembers:
    """Тесты управления участниками проекта"""
    
    def test_add_member_success(self, authorized_client, test_project, second_user):
        """Тест: успешное добавление участника"""
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/members",
            json={
                "user_id": second_user.id,
                "role": "member"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == second_user.id
        assert data["role"] == "member"
    
    def test_add_member_not_found_user(self, authorized_client, test_project):
        """Тест: добавление несуществующего пользователя"""
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/members",
            json={
                "user_id": 999,
                "role": "member"
            }
        )
        
        assert response.status_code == 404
    
    def test_add_member_duplicate(self, authorized_client, test_project, db_session, second_user):
        """Тест: повторное добавление участника"""
        # Добавляем участника
        member = ProjectMember(
            project_id=test_project.id,
            user_id=second_user.id,
            role=ProjectRole.MEMBER
        )
        db_session.add(member)
        db_session.commit()
        
        # Пытаемся добавить снова
        response = authorized_client.post(
            f"/api/v1/projects/{test_project.id}/members",
            json={
                "user_id": second_user.id,
                "role": "member"
            }
        )
        
        assert response.status_code == 409
    
    def test_remove_member_success(self, authorized_client, test_project, db_session, second_user):
        """Тест: успешное удаление участника"""
        # Добавляем участника
        member = ProjectMember(
            project_id=test_project.id,
            user_id=second_user.id,
            role=ProjectRole.MEMBER
        )
        db_session.add(member)
        db_session.commit()
        
        # Удаляем участника
        response = authorized_client.delete(
            f"/api/v1/projects/{test_project.id}/members/{second_user.id}"
        )
        
        assert response.status_code == 204
    
    def test_remove_member_not_found(self, authorized_client, test_project):
        """Тест: удаление несуществующего участника"""
        response = authorized_client.delete(
            f"/api/v1/projects/{test_project.id}/members/999"
        )
        
        assert response.status_code == 404


class TestProjectStats:
    """Тесты статистики проекта"""
    
    def test_get_project_stats(self, authorized_client, test_project):
        """Тест: получение статистики проекта"""
        response = authorized_client.get(f"/api/v1/projects/{test_project.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "todo_tasks" in data
        assert "in_progress_tasks" in data
        assert "done_tasks" in data
        assert "total_members" in data
