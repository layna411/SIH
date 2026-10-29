from datetime import timedelta
import pytest
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.role import Role
from app.models.enums import UserRoleEnum
from app.core.security import create_access_token, verify_password
from app.services.bootstrap_service import seed_roles, bootstrap_super_admin

def test_1_registration_succeeds_with_valid_data(client):
    payload = {
        "email": "student_reg_valid@campus.edu",
        "password": "SecurePassword123!",
        "full_name": "Rohan Verma",
        "phone_number": "+91-9876543210",
        "student_id_number": "STU-2026-999"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student_reg_valid@campus.edu"
    assert data["full_name"] == "Rohan Verma"
    assert data["default_role"] == "STUDENT"
    assert data["is_active"] is True
    assert data["is_email_verified"] is False  # Accurately represented
    assert "id" in data

def test_2_duplicate_email_registration_rejected(client):
    payload = {
        "email": "duplicate_check@campus.edu",
        "password": "SecurePassword123!",
        "full_name": "First User"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with uppercase/spaces variation
    payload_dup = {
        "email": "  DUPLICATE_CHECK@campus.edu  ",
        "password": "SecurePassword123!",
        "full_name": "Second User"
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_3_passwords_are_hashed(client, db_session):
    payload = {
        "email": "hashed_pass_test@campus.edu",
        "password": "MySuperSecretPlainPassword123!",
        "full_name": "Hash Student"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    user_id = res.json()["id"]

    # Check direct database record
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None
    assert user.hashed_password != "MySuperSecretPlainPassword123!"
    assert user.hashed_password.startswith("$argon2id$")
    assert verify_password("MySuperSecretPlainPassword123!", user.hashed_password)

def test_4_password_hashes_never_returned_in_api_responses(client):
    payload = {
        "email": "no_hash_leak@campus.edu",
        "password": "SecretPassword123!",
        "full_name": "Safe User"
    }
    reg_res = client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201
    reg_json = reg_res.json()
    assert "password" not in reg_json
    assert "hashed_password" not in reg_json
    assert "password_hash" not in reg_json

    login_res = client.post("/api/v1/auth/login", json={
        "email": "no_hash_leak@campus.edu",
        "password": "SecretPassword123!"
    })
    assert login_res.status_code == 200
    login_json = login_res.json()
    assert "password" not in login_json["user"]
    assert "hashed_password" not in login_json["user"]
    assert "password_hash" not in login_json["user"]

def test_5_login_succeeds_with_valid_credentials(client):
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": "login_valid@campus.edu",
        "password": "PasswordValid123!",
        "full_name": "Login User"
    })
    # Login
    res = client.post("/api/v1/auth/login", json={
        "email": "login_valid@campus.edu",
        "password": "PasswordValid123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["email"] == "login_valid@campus.edu"

def test_6_invalid_credentials_rejected(client):
    res_wrong_pw = client.post("/api/v1/auth/login", json={
        "email": "login_valid@campus.edu",
        "password": "CompletelyWrongPassword!"
    })
    assert res_wrong_pw.status_code == 401
    assert "Incorrect email or password." in res_wrong_pw.json()["detail"]

    res_nonexistent = client.post("/api/v1/auth/login", json={
        "email": "does_not_exist_user@campus.edu",
        "password": "Password123!"
    })
    assert res_nonexistent.status_code == 401
    assert "Incorrect email or password." in res_nonexistent.json()["detail"]

def test_7_expired_or_invalid_tokens_rejected(client):
    # Malformed token
    res_malformed = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-jwt-token"})
    assert res_malformed.status_code == 401

    # Expired token
    expired_token = create_access_token(subject=9999, expires_delta=timedelta(seconds=-60))
    res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401

def test_8_unauthenticated_request_denied(client):
    # Request without Authorization header
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

def test_9_student_cannot_assign_themselves_administrative_role(client, db_session):
    # Caller attempts to submit role="SUPER_ADMIN" during public registration
    payload = {
        "email": "privilege_escalation@campus.edu",
        "password": "Password123!",
        "full_name": "Attacker Trying Admin",
        "role": "SUPER_ADMIN"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    # Must be strictly assigned STUDENT
    assert data["default_role"] == "STUDENT"

    # Verify directly in database
    user = db_session.query(User).filter(User.email == "privilege_escalation@campus.edu").first()
    assert user.default_role == UserRoleEnum.STUDENT

def test_10_institution_memberships_validated(client, db_session):
    # Create test institution
    inst = Institution(
        code="TESTINST01",
        name="Test Technical College",
        state="Maharashtra",
        district="Pune",
        city="Pune",
        contact_email="contact@testtech.edu",
        is_active=True,
        is_verified=True
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    # Register student with institution_id
    res = client.post("/api/v1/auth/register", json={
        "email": "member_student@testtech.edu",
        "password": "Password123!",
        "full_name": "Tech Student",
        "institution_id": inst.id
    })
    assert res.status_code == 201
    memberships = res.json()["memberships"]
    assert len(memberships) == 1
    assert memberships[0]["institution_id"] == inst.id
    assert memberships[0]["role"] == "STUDENT"

def test_11_unauthorized_institutional_access_denied(client, db_session):
    inst1 = Institution(code="COLLEGE1", name="College One", state="Delhi", contact_email="c1@test.edu", is_active=True, is_verified=True)
    inst2 = Institution(code="COLLEGE2", name="College Two", state="Delhi", contact_email="c2@test.edu", is_active=True, is_verified=True)
    db_session.add_all([inst1, inst2])
    db_session.commit()

    # Officer registered for College One
    client.post("/api/v1/auth/register", json={
        "email": "officer_c1@test.edu",
        "password": "Password123!",
        "full_name": "Officer College One"
    })
    user_c1 = db_session.query(User).filter(User.email == "officer_c1@test.edu").first()
    user_c1.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem = InstitutionMembership(user_id=user_c1.id, institution_id=inst1.id, role=UserRoleEnum.COLLEGE_OFFICER, is_active=True)
    db_session.add(mem)
    db_session.commit()

    token_c1 = client.post("/api/v1/auth/login", json={"email": "officer_c1@test.edu", "password": "Password123!"}).json()["access_token"]

    # Officer from College One attempts to update College Two details
    update_res = client.put(f"/api/v1/institutions/{inst2.id}", json={
        "name": "Malicious Name Change"
    }, headers={"Authorization": f"Bearer {token_c1}"})
    assert update_res.status_code == 403
    assert "Access denied" in update_res.json()["detail"]

def test_12_regulatory_scope_restrictions(client, db_session):
    inst_delhi = Institution(code="REG_DELHI", name="Delhi College", state="Delhi", contact_email="delhi@test.edu", is_active=True, is_verified=True)
    inst_punjab = Institution(code="REG_PUNJAB", name="Punjab College", state="Punjab", contact_email="punjab@test.edu", is_active=True, is_verified=True)
    db_session.add_all([inst_delhi, inst_punjab])
    db_session.commit()

    # Create Regulatory Admin scoped strictly to "Delhi"
    client.post("/api/v1/auth/register", json={
        "email": "regulator_delhi@gov.in",
        "password": "Password123!",
        "full_name": "Delhi Regulator"
    })
    reg_user = db_session.query(User).filter(User.email == "regulator_delhi@gov.in").first()
    reg_user.default_role = UserRoleEnum.REGULATORY_ADMIN
    jurisdiction = RegulatoryJurisdiction(
        user_id=reg_user.id,
        state="Delhi",
        jurisdiction_code="REG-DL-01",
        is_active=True
    )
    db_session.add(jurisdiction)
    db_session.commit()

    from app.core.permissions import check_institution_access, check_regulatory_access
    assert check_institution_access(reg_user, inst_delhi.id, db_session) is True
    assert check_institution_access(reg_user, inst_punjab.id, db_session) is False
    assert check_regulatory_access(reg_user, "Delhi", db_session) is True
    assert check_regulatory_access(reg_user, "Punjab", db_session) is False

def test_13_role_seeding_is_repeatable(db_session):
    roles1 = seed_roles(db_session)
    count1 = db_session.query(Role).count()
    assert count1 == 5

    # Run seeding again: must be idempotent and not create duplicate roles
    roles2 = seed_roles(db_session)
    count2 = db_session.query(Role).count()
    assert count2 == 5
    assert len(roles1) == len(roles2)

def test_14_database_records_persist_in_mysql(db_session):
    # Verify that real objects write and persist in MySQL test schema
    test_user = User(
        email="persistence_test@campus.edu",
        full_name="Persisted User",
        hashed_password="dummy_hash_value",
        default_role=UserRoleEnum.STUDENT,
        is_active=True
    )
    db_session.add(test_user)
    db_session.commit()

    queried = db_session.query(User).filter(User.email == "persistence_test@campus.edu").first()
    assert queried is not None
    assert queried.full_name == "Persisted User"

def test_15_existing_health_endpoints_continue_working(client):
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "online"

    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    r_db = client.get("/api/health/db")
    assert r_db.status_code == 200
    assert r_db.json()["status"] == "connected"
    assert r_db.json()["driver"] == "mysql+pymysql"
