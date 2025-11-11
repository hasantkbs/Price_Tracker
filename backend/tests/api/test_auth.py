from fastapi.testclient import TestClient
import pytest

def test_register_user(client: TestClient):
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "user_id" in data
    assert data["user_id"] is not None

def test_register_existing_user(client: TestClient):
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass"
    }
    client.post("/auth/register", json=user_data) # Register once
    response = client.post("/auth/register", json=user_data) # Register again
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_user(client: TestClient):
    user_data = {
        "name": "Test User",
        "email": "login@example.com",
        "password": "loginpass"
    }
    client.post("/auth/register", json=user_data) # Register user first

    login_data = {
        "email": "login@example.com",
        "password": "loginpass"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "user_id" in data
    assert data["user_id"] is not None

def test_login_invalid_credentials(client: TestClient):
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpass"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_wrong_password(client: TestClient):
    user_data = {
        "name": "Test User",
        "email": "wrongpass@example.com",
        "password": "correctpass"
    }
    client.post("/auth/register", json=user_data)

    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpass"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
