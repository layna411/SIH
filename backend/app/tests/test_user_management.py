import pytest
from app.models.user import User
from app.models.institution import Institution, InstitutionMembership, RegulatoryJurisdiction
from app.models.invitation import UserInvitation
from app.models.enums import UserRoleEnum
from app.models.audit import AuditLog
from app.core.security import create_access_token, hash_password


@pytest.fixture
def user_mgmt_setup(db_session):
    """Set up institutions, superadmin, institution head, and officers in isolated MySQL test schema."""
    # Institution Alpha & Beta
    inst_a = Institution(
        code="MGMT_INST_A",
        name="Alpha Technical University",
        state="Maharashtra",
        city="Mumbai",
        contact_email="admin@alpha.edu",
        is_active=True,
        is_verified=True
    )
    inst_b = Institution(
        code="MGMT_INST_B",
        name="Beta Institute of Science",
        state="Karnataka",
        city="Bengaluru",
        contact_email="admin@beta.edu",
        is_active=True,
        is_verified=True
    )
    db_session.add_all([inst_a, inst_b])
    db_session.commit()
    db_session.refresh(inst_a)
    db_session.refresh(inst_b)

    # Super Admin
    super_admin = User(
        email="superadmin_mgmt@eduresolve.gov.in",
        hashed_password=hash_password("SuperAdminPass123!"),
        full_name="Platform Super Administrator",
        default_role=UserRoleEnum.SUPER_ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(super_admin)
    db_session.commit()
    db_session.refresh(super_admin)

    # Institution Head (Alpha)
    head_a = User(
        email="head_alpha@alpha.edu",
        hashed_password=hash_password("HeadPass123!"),
        full_name="Director Alpha",
        default_role=UserRoleEnum.INSTITUTION_HEAD,
        is_active=True,
        is_verified=True
    )
    db_session.add(head_a)
    db_session.commit()
    db_session.refresh(head_a)

    mem_head_a = InstitutionMembership(
        user_id=head_a.id,
        institution_id=inst_a.id,
        role=UserRoleEnum.INSTITUTION_HEAD,
        department="Executive Council",
        designation="Director",
        is_active=True
    )
    db_session.add(mem_head_a)
    db_session.commit()

    # Regulatory Admin
    reg_admin = User(
        email="reg_admin_mgmt@eduresolve.gov.in",
        hashed_password=hash_password("RegAdminPass123!"),
        full_name="State Regulatory Officer",
        default_role=UserRoleEnum.REGULATORY_ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(reg_admin)
    db_session.commit()
    db_session.refresh(reg_admin)

    jur = RegulatoryJurisdiction(
        user_id=reg_admin.id,
        jurisdiction_type="STATE",
        state="Maharashtra",
        jurisdiction_code="REG-MH-01",
        is_active=True
    )
    db_session.add(jur)
    db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "super_admin": super_admin,
        "head_a": head_a,
        "reg_admin": reg_admin
    }


def auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.id, extra_claims={"role": user.default_role.value})
    return {"Authorization": f"Bearer {token}"}


# 1. Super Admin invites College Officer, Institution Head, and Regulatory Admin
def test_super_admin_can_invite_all_supported_roles(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # 1a. Invite College Officer
    res_officer = client.post("/api/v1/users/invite", json={
        "email": "officer_new@alpha.edu",
        "full_name": "New College Officer",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id,
        "department": "Examination Cell",
        "designation": "Assistant Controller"
    }, headers=headers)
    assert res_officer.status_code == 201
    data_off = res_officer.json()
    assert data_off["role"] == "COLLEGE_OFFICER"
    assert data_off["institution_id"] == inst_a.id
    assert data_off["status"] == "PENDING"
    assert "invitation_link" in data_off
    assert data_off["delivery_status"] == "DEVELOPMENT_LINK_GENERATED"

    # 1b. Invite Institution Head
    res_head = client.post("/api/v1/users/invite", json={
        "email": "head_new@alpha.edu",
        "full_name": "New Vice Chancellor",
        "role": "INSTITUTION_HEAD",
        "institution_id": inst_a.id,
        "designation": "Vice Chancellor"
    }, headers=headers)
    assert res_head.status_code == 201
    assert res_head.json()["role"] == "INSTITUTION_HEAD"

    # 1c. Invite Regulatory Admin
    res_reg = client.post("/api/v1/users/invite", json={
        "email": "regulatory_new@gov.in",
        "full_name": "Regional Inspector",
        "role": "REGULATORY_ADMIN",
        "jurisdiction_state": "Karnataka",
        "jurisdiction_code": "JUR-KA-01"
    }, headers=headers)
    assert res_reg.status_code == 201
    assert res_reg.json()["role"] == "REGULATORY_ADMIN"
    assert res_reg.json()["jurisdiction_state"] == "Karnataka"


# 2. Institution Head invites College Officer for their own institution
def test_institution_head_can_invite_college_officer_for_own_institution(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    head_a = user_mgmt_setup["head_a"]
    headers = auth_headers(head_a)

    res = client.post("/api/v1/users/invite", json={
        "email": "hostel_warden@alpha.edu",
        "full_name": "Hostel Warden Alpha",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id,
        "department": "Hostel & Mess",
        "designation": "Chief Warden"
    }, headers=headers)
    assert res.status_code == 201
    assert res.json()["role"] == "COLLEGE_OFFICER"
    assert res.json()["department"] == "Hostel & Mess"


# 3. Institution Head cannot invite officer for another institution (403 Forbidden)
def test_institution_head_cannot_invite_officer_for_another_institution(client, db_session, user_mgmt_setup):
    inst_b = user_mgmt_setup["inst_b"]
    head_a = user_mgmt_setup["head_a"]
    headers = auth_headers(head_a)

    res = client.post("/api/v1/users/invite", json={
        "email": "rogue_officer@beta.edu",
        "full_name": "Rogue Officer",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_b.id,
        "department": "Academics"
    }, headers=headers)
    assert res.status_code == 403
    assert "own institution" in res.json()["detail"].lower()


# 4. Institution Head cannot invite privileged roles (Super Admin, Head, Regulatory Admin)
def test_institution_head_cannot_invite_privileged_roles(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    head_a = user_mgmt_setup["head_a"]
    headers = auth_headers(head_a)

    for forbidden_role in ["SUPER_ADMIN", "INSTITUTION_HEAD", "REGULATORY_ADMIN"]:
        res = client.post("/api/v1/users/invite", json={
            "email": f"illegal_{forbidden_role.lower()}@alpha.edu",
            "full_name": "Illegal User",
            "role": forbidden_role,
            "institution_id": inst_a.id
        }, headers=headers)
        assert res.status_code == 403
        assert "can only invite college officers" in res.json()["detail"].lower()


# 5. Regulatory Admin cannot create or invite accounts
def test_regulatory_admin_cannot_invite_accounts(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    reg_admin = user_mgmt_setup["reg_admin"]
    headers = auth_headers(reg_admin)

    res = client.post("/api/v1/users/invite", json={
        "email": "test_invite_by_reg@alpha.edu",
        "full_name": "Attempt By Reg",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id
    }, headers=headers)
    assert res.status_code == 403


# 6. Public registration rejects privileged role assignment (forces student)
def test_public_registration_cannot_self_assign_privileged_role(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    res = client.post("/api/v1/auth/register", json={
        "email": "fake_admin@alpha.edu",
        "password": "Password123!",
        "full_name": "Fake Admin Student",
        "institution_id": inst_a.id,
        "role": "SUPER_ADMIN" # Attempting privilege escalation
    })
    # Must succeed as a student only, ignoring client-provided role
    assert res.status_code == 201
    assert res.json()["default_role"] == "STUDENT"


# 7. Invalid institution and jurisdiction IDs are rejected
def test_invalid_institution_rejected(client, db_session, user_mgmt_setup):
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    res = client.post("/api/v1/users/invite", json={
        "email": "nonexistent_inst@test.edu",
        "full_name": "No Inst Officer",
        "role": "COLLEGE_OFFICER",
        "institution_id": 999999
    }, headers=headers)
    assert res.status_code == 404
    assert "institution does not exist" in res.json()["detail"].lower()


# 8. Duplicate email and active membership prevention
def test_duplicate_invitation_and_membership_prevention(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # First invite
    res1 = client.post("/api/v1/users/invite", json={
        "email": "duplicate_check@alpha.edu",
        "full_name": "First Invite",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id
    }, headers=headers)
    assert res1.status_code == 201

    # Second invite to the same email and institution while first is pending
    res2 = client.post("/api/v1/users/invite", json={
        "email": "duplicate_check@alpha.edu",
        "full_name": "Second Invite Attempt",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id
    }, headers=headers)
    assert res2.status_code == 400
    assert "pending invitation has already been issued" in res2.json()["detail"].lower()


# 9. Complete invitation acceptance lifecycle and login
def test_invitation_acceptance_and_account_onboarding(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # 1. Super Admin invites officer
    invite_res = client.post("/api/v1/users/invite", json={
        "email": "accepted_officer@alpha.edu",
        "full_name": "Accepted Officer",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id,
        "department": "Finance & Accounts"
    }, headers=headers)
    assert invite_res.status_code == 201
    inv_link = invite_res.json()["invitation_link"]
    token = inv_link.split("token=")[1]

    # 2. Public checks invitation details
    val_res = client.get(f"/api/v1/auth/invitations/{token}")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["email"] == "accepted_officer@alpha.edu"
    assert val_data["role"] == "COLLEGE_OFFICER"
    assert val_data["institution_name"] == inst_a.name

    # 3. User accepts invitation and sets password
    accept_res = client.post(f"/api/v1/auth/invitations/{token}/accept", json={
        "password": "SecurePassword999!",
        "phone_number": "+919876543210"
    })
    assert accept_res.status_code == 200
    login_data = accept_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["default_role"] == "COLLEGE_OFFICER"

    # 4. Confirm user can now log in normally
    login_res = client.post("/api/v1/auth/login", json={
        "email": "accepted_officer@alpha.edu",
        "password": "SecurePassword999!"
    })
    assert login_res.status_code == 200

    # 5. Confirm token cannot be reused (single-use protection)
    reuse_res = client.post(f"/api/v1/auth/invitations/{token}/accept", json={
        "password": "SecondPassword123!"
    })
    assert reuse_res.status_code == 400
    assert "already been accepted" in reuse_res.json()["detail"].lower()


# 10. Audit records are created for administrative changes
def test_audit_records_for_invitations_and_role_changes(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # Trigger invite
    client.post("/api/v1/users/invite", json={
        "email": "audit_user@alpha.edu",
        "full_name": "Audit Tracked User",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id
    }, headers=headers)

    # Check AuditLog table in MySQL
    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "INVITE_USER",
        AuditLog.user_id == sa.id
    ).first()
    assert audit is not None
    assert "audit_user@alpha.edu" in audit.details


# 11. Resending and revoking invitations
def test_resend_and_revoke_invitation(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # 1. Invite
    res = client.post("/api/v1/users/invite", json={
        "email": "resend_revoke@alpha.edu",
        "full_name": "Test Resend User",
        "role": "COLLEGE_OFFICER",
        "institution_id": inst_a.id
    }, headers=headers)
    inv_id = res.json()["id"]

    # 2. Resend
    resend_res = client.post(f"/api/v1/users/invitations/{inv_id}/resend", headers=headers)
    assert resend_res.status_code == 200
    assert "invitation_link" in resend_res.json()

    # 3. Revoke
    revoke_res = client.delete(f"/api/v1/users/invitations/{inv_id}", headers=headers)
    assert revoke_res.status_code == 200

    # 4. Verify token from revoked invite cannot be accepted
    revoked_token = resend_res.json()["invitation_link"].split("token=")[1]
    accept_revoked = client.post(f"/api/v1/auth/invitations/{revoked_token}/accept", json={
        "password": "Password123!"
    })
    assert accept_revoked.status_code == 400
    assert "already been revoked" in accept_revoked.json()["detail"].lower()


# 12. Deactivating a user removes access
def test_deactivating_user_removes_access(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    sa = user_mgmt_setup["super_admin"]
    sa_headers = auth_headers(sa)

    # Create an active officer directly
    officer = User(
        email="deactivate_me@alpha.edu",
        hashed_password=hash_password("OfficerPass123!"),
        full_name="Deactivatable Officer",
        default_role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True,
        is_verified=True
    )
    db_session.add(officer)
    db_session.commit()
    db_session.refresh(officer)

    mem = InstitutionMembership(
        user_id=officer.id,
        institution_id=inst_a.id,
        role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True
    )
    db_session.add(mem)
    db_session.commit()

    # Verify active officer can authenticate
    officer_token = client.post("/api/v1/auth/login", json={
        "email": "deactivate_me@alpha.edu",
        "password": "OfficerPass123!"
    }).json()["access_token"]
    off_headers = {"Authorization": f"Bearer {officer_token}"}

    me_res = client.get("/api/v1/users/me", headers=off_headers)
    assert me_res.status_code == 200

    # Super Admin deactivates officer
    deact_res = client.put(f"/api/v1/users/{officer.id}/status", json={"is_active": False}, headers=sa_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Deactivated officer now denied access on protected active routes
    denied_res = client.get("/api/v1/auth/me", headers=off_headers)
    assert denied_res.status_code == 403
    assert "account is deactivated" in denied_res.json()["detail"].lower()


# 13. Super Admin listing users with search, role, and status filters
def test_super_admin_list_users_filters(client, db_session, user_mgmt_setup):
    sa = user_mgmt_setup["super_admin"]
    headers = auth_headers(sa)

    # Filter by role
    res_role = client.get("/api/v1/users?role=SUPER_ADMIN", headers=headers)
    assert res_role.status_code == 200
    users = res_role.json()
    assert all(u["default_role"] == "SUPER_ADMIN" for u in users)

    # Filter by search
    res_search = client.get("/api/v1/users?search=Director", headers=headers)
    assert res_search.status_code == 200
    assert any("Director Alpha" in u["full_name"] for u in res_search.json())

    # Filter by status
    res_status = client.get("/api/v1/users?status=ACTIVE", headers=headers)
    assert res_status.status_code == 200
    assert all(u["is_active"] is True for u in res_status.json())


# 14. Institution Head user listing is strictly isolated to own institution
def test_institution_head_user_list_isolation(client, db_session, user_mgmt_setup):
    inst_a = user_mgmt_setup["inst_a"]
    inst_b = user_mgmt_setup["inst_b"]
    head_a = user_mgmt_setup["head_a"]
    headers = auth_headers(head_a)

    # Create an officer in Beta
    beta_officer = User(
        email="beta_only_officer@beta.edu",
        hashed_password=hash_password("BetaPass123!"),
        full_name="Beta Exclusive Officer",
        default_role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True,
        is_verified=True
    )
    db_session.add(beta_officer)
    db_session.commit()
    db_session.refresh(beta_officer)

    mem_b = InstitutionMembership(
        user_id=beta_officer.id,
        institution_id=inst_b.id,
        role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True
    )
    db_session.add(mem_b)
    db_session.commit()

    # Head of Alpha lists users
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200
    emails = [u["email"] for u in res.json()]

    # Must NOT see beta officer
    assert "beta_only_officer@beta.edu" not in emails

    # Head of Alpha cannot query beta's institution_id
    cross_res = client.get(f"/api/v1/users?institution_id={inst_b.id}", headers=headers)
    assert cross_res.status_code == 403


# 15. Institution registration auto-provisions head account with default password
def test_institution_registration_creates_head_account_with_default_password(client, db_session, user_mgmt_setup):
    super_admin = user_mgmt_setup["super_admin"]
    headers = auth_headers(super_admin)

    payload = {
        "institution_code": "AUTO_INST_101",
        "code": "AUTO_INST_101",
        "name": "Auto Provision College of Engineering",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "official_email": "dean_autoinst@autoinst.ac.in",
        "contact_email": "dean_autoinst@autoinst.ac.in"
    }

    res = client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["admin_account_email"] == "dean_autoinst@autoinst.ac.in"
    assert data["default_password"] == "EduResolve@123"
    assert data["account_created"] is True

    # Verify head account can log in immediately with default password
    login_res = client.post("/api/v1/auth/login", json={
        "email": "dean_autoinst@autoinst.ac.in",
        "password": "EduResolve@123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["default_role"] == "INSTITUTION_HEAD"


# 16. Logged in user / institution head can change their password
def test_institution_head_can_change_password_after_login(client, db_session, user_mgmt_setup):
    super_admin = user_mgmt_setup["super_admin"]
    headers = auth_headers(super_admin)

    # Register institution
    payload = {
        "institution_code": "CHANGE_PWD_INST",
        "name": "Password Change Institute",
        "state": "Kerala",
        "city": "Kochi",
        "official_email": "director@pwdchange.edu"
    }
    create_res = client.post("/api/v1/institutions", json=payload, headers=headers)
    assert create_res.status_code == 201

    # Login with default password
    login_res = client.post("/api/v1/auth/login", json={
        "email": "director@pwdchange.edu",
        "password": "EduResolve@123"
    })
    assert login_res.status_code == 200
    head_token = login_res.json()["access_token"]
    head_auth = {"Authorization": f"Bearer {head_token}"}

    # Change password
    change_res = client.post("/api/v1/auth/change-password", json={
        "current_password": "EduResolve@123",
        "new_password": "DirectorNewPassword123!",
        "confirm_password": "DirectorNewPassword123!"
    }, headers=head_auth)
    assert change_res.status_code == 200
    assert change_res.json()["message"] == "Password changed successfully."

    # Verify old default password is rejected
    old_login = client.post("/api/v1/auth/login", json={
        "email": "director@pwdchange.edu",
        "password": "EduResolve@123"
    })
    assert old_login.status_code == 401

    # Verify new password is accepted
    new_login = client.post("/api/v1/auth/login", json={
        "email": "director@pwdchange.edu",
        "password": "DirectorNewPassword123!"
    })
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

