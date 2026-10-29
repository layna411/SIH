import pytest

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "EduResolve AI" in data["app"]

def test_register_and_login_flow(client):
    # 1. Register student
    reg_payload = {
        "email": "teststudent@campus.edu",
        "password": "SecurePassword123!",
        "full_name": "Test Student",
        "phone_number": "+91-9999999999",
        "student_id_number": "STU-2026-001"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "teststudent@campus.edu"
    assert user_data["default_role"] == "STUDENT"

    # 2. Login with valid credentials
    login_payload = {
        "email": "teststudent@campus.edu",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Access protected /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "teststudent@campus.edu"

def test_invalid_login_credentials(client):
    login_payload = {
        "email": "nonexistent@campus.edu",
        "password": "WrongPassword123"
    }
    res = client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 401
    assert "Incorrect email or password." in res.json()["detail"]
