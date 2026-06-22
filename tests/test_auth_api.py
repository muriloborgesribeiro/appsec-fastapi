from fastapi.testclient import TestClient

from app.auth.models import User
from app.auth.utils import hash_password


class TestRegister:
    def test_register_success(self, client: TestClient, db_session):
        response = client.post("/auth/register", json={
            "username": "novouser",
            "email": "novo@test.com",
            "password": "senha123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "novouser"
        assert data["email"] == "novo@test.com"
        assert data["role"] == "professional"
        assert data["is_active"] is True

    def test_register_duplicate_username(self, client: TestClient, db_session):
        client.post("/auth/register", json={
            "username": "duplicado",
            "email": "first@test.com",
            "password": "senha123",
        })
        response = client.post("/auth/register", json={
            "username": "duplicado",
            "email": "second@test.com",
            "password": "senha123",
        })
        assert response.status_code == 409
        assert "ja existe" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client: TestClient, db_session):
        client.post("/auth/register", json={
            "username": "user1",
            "email": "dup@test.com",
            "password": "senha123",
        })
        response = client.post("/auth/register", json={
            "username": "user2",
            "email": "dup@test.com",
            "password": "senha123",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client: TestClient, db_session):
        response = client.post("/auth/register", json={
            "username": "user",
            "email": "user@test.com",
            "password": "abc",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, db_session):
        client.post("/auth/register", json={
            "username": "logintest",
            "email": "login@test.com",
            "password": "senha123",
        })
        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "senha123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, db_session):
        client.post("/auth/register", json={
            "username": "wrongpw",
            "email": "wrong@test.com",
            "password": "senha123",
        })
        response = client.post("/auth/login", json={
            "username": "wrongpw",
            "password": "senha_errada",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient, db_session):
        response = client.post("/auth/login", json={
            "username": "naoexiste",
            "password": "senha123",
        })
        assert response.status_code == 401


class TestMe:
    def test_me_with_valid_token(self, client: TestClient, test_user):
        from tests.conftest import auth_headers
        headers = auth_headers(test_user)
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["username"] == test_user.username

    def test_me_without_token(self, client: TestClient):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, client: TestClient):
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401


class TestUsers:
    def test_list_users_admin_only(self, client: TestClient, test_admin):
        from tests.conftest import auth_headers
        headers = auth_headers(test_admin)
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_users_forbidden_non_admin(self, client: TestClient, test_user):
        from tests.conftest import auth_headers
        headers = auth_headers(test_user)
        response = client.get("/auth/users", headers=headers)
        assert response.status_code == 403


