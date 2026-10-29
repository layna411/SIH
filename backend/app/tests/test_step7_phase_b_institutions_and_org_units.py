import pytest
from datetime import datetime, timezone
from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.enums import UserRoleEnum
from app.models.user import User
from app.models.institution import Institution, InstitutionAlias, InstitutionMembership
from app.models.organizational_unit import OrganizationalUnit
from app.models.bureau_membership import BureauMembership
from app.services.bootstrap_service import seed_organizational_units
from app.core.security import hash_password, create_access_token

def auth_headers(user: User) -> dict:
    role_str = user.default_role.value if hasattr(user.default_role, "value") else str(user.default_role)
    token = create_access_token(subject=user.id, extra_claims={"role": role_str, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def superadmin_user(db_session: Session) -> User:
    admin = db_session.query(User).filter(User.email == "superadmin.phaseb@eduresolve.ai").first()
    if not admin:
        admin = User(
            email="superadmin.phaseb@eduresolve.ai",
            hashed_password=hash_password("SuperAdmin@Pass123"),
            full_name="Super Administrator Phase B",
            default_role=UserRoleEnum.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin

@pytest.fixture
def college_officer_user(db_session: Session) -> User:
    officer = db_session.query(User).filter(User.email == "officer.phaseb@college.edu.in").first()
    if not officer:
        officer = User(
            email="officer.phaseb@college.edu.in",
            hashed_password=hash_password("CollegeOfficer@123"),
            full_name="College Officer Phase B",
            default_role=UserRoleEnum.COLLEGE_OFFICER,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(officer)
        db_session.commit()
        db_session.refresh(officer)
    return officer

@pytest.fixture
def regular_student_user(db_session: Session) -> User:
    student = db_session.query(User).filter(User.email == "student.phaseb@college.edu.in").first()
    if not student:
        student = User(
            email="student.phaseb@college.edu.in",
            hashed_password=hash_password("Student@123"),
            full_name="Student Phase B",
            default_role=UserRoleEnum.STUDENT,
            is_active=True,
            is_verified=True,
            is_email_verified=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
    return student

@pytest.fixture
def sample_institution(db_session: Session) -> Institution:
    inst = db_session.query(Institution).filter(Institution.code == "INST-PHASEB-01").first()
    if not inst:
        inst = Institution(
            code="INST-PHASEB-01",
            name="Delhi Institute of Advanced Engineering",
            institution_type="COLLEGE",
            state="Delhi",
            city="New Delhi",
            contact_email="contact@diae.ac.in",
            is_active=True,
            is_verified=True,
            verification_status="VERIFIED",
            aicte_permanent_id=None,
            is_aicte_verified=False
        )
        db_session.add(inst)
        db_session.commit()
        db_session.refresh(inst)
    return inst


# 1. Tests for Institution Identity & AICTE Permanent ID
def test_institution_allows_nullable_aicte_permanent_id(client, db_session: Session, sample_institution: Institution):
    """Confirm institution records remain completely valid without an AICTE Permanent ID."""
    res = client.get(f"/api/v1/institutions/{sample_institution.id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["code"] == "INST-PHASEB-01"
    assert data["aicte_permanent_id"] is None
    assert data["is_aicte_verified"] is False

def test_duplicate_non_null_aicte_permanent_id_rejected(client, db_session: Session, superadmin_user: User, sample_institution: Institution):
    """Enforce unique constraint on non-null AICTE Permanent IDs."""
    headers = auth_headers(superadmin_user)
    
    # 1. Assign AICTE ID to first institution
    res1 = client.post(
        f"/api/v1/institutions/{sample_institution.id}/verify-aicte",
        headers=headers,
        json={"aicte_permanent_id": "1-9876543210", "region": "NORTH", "is_aicte_verified": True}
    )
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["aicte_permanent_id"] == "1-9876543210"
    assert res1.json()["is_aicte_verified"] is True

    # 2. Create second institution
    inst2 = Institution(
        code="INST-PHASEB-02",
        name="Bangalore Technical Institute",
        state="Karnataka",
        city="Bengaluru",
        contact_email="contact@bti.ac.in",
        is_active=True,
        is_verified=True,
        verification_status="VERIFIED"
    )
    db_session.add(inst2)
    db_session.commit()
    db_session.refresh(inst2)

    # 3. Attempt to assign same AICTE ID to second institution - must be rejected with 400
    res2 = client.post(
        f"/api/v1/institutions/{inst2.id}/verify-aicte",
        headers=headers,
        json={"aicte_permanent_id": "1-9876543210", "region": "SOUTH", "is_aicte_verified": True}
    )
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already assigned" in res2.json()["detail"]

def test_verify_aicte_requires_superadmin(client, college_officer_user: User, sample_institution: Institution):
    """Regular college officers cannot verify AICTE IDs or change official credentials."""
    headers = auth_headers(college_officer_user)
    res = client.post(
        f"/api/v1/institutions/{sample_institution.id}/verify-aicte",
        headers=headers,
        json={"aicte_permanent_id": "1-1122334455", "is_aicte_verified": True}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


# 2. Tests for Institution Aliases & Search
def test_institution_alias_crud_and_normalization(client, db_session: Session, superadmin_user: User, sample_institution: Institution):
    """Test adding, listing, and normalizing aliases for an institution."""
    headers = auth_headers(superadmin_user)

    # Add alias
    res_add = client.post(
        f"/api/v1/institutions/{sample_institution.id}/aliases",
        headers=headers,
        json={"alias_name": "DIAE Delhi", "source": "ACRONYM", "is_verified": True}
    )
    assert res_add.status_code == status.HTTP_201_CREATED
    alias_data = res_add.json()
    assert alias_data["alias_name"] == "DIAE Delhi"
    assert alias_data["normalized_alias"] == "diae delhi"
    alias_id = alias_data["id"]

    # Prevent duplicate normalized alias for the same institution
    res_dup = client.post(
        f"/api/v1/institutions/{sample_institution.id}/aliases",
        headers=headers,
        json={"alias_name": "  diae   delhi  "}
    )
    assert res_dup.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in res_dup.json()["detail"]

    # Search institutions by alias
    res_search = client.get("/api/v1/institutions?search=DIAE")
    assert res_search.status_code == status.HTTP_200_OK
    search_results = res_search.json()
    assert any(inst["id"] == sample_institution.id for inst in search_results)

    # Delete alias
    res_del = client.delete(f"/api/v1/institutions/{sample_institution.id}/aliases/{alias_id}", headers=headers)
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

def test_ambiguous_alias_does_not_merge_institutions(client, db_session: Session, superadmin_user: User):
    """Ensure aliases for different institutions do not cause automated record merging."""
    headers = auth_headers(superadmin_user)

    # Create two colleges in different states
    inst_a = Institution(code="COLL-A-DELHI", name="St. Xavier College of Tech Delhi", state="Delhi", city="Delhi", contact_email="a@delhi.ac.in")
    inst_b = Institution(code="COLL-B-MUMBAI", name="St. Xavier Engineering Mumbai", state="Maharashtra", city="Mumbai", contact_email="b@mumbai.ac.in")
    db_session.add_all([inst_a, inst_b])
    db_session.commit()
    db_session.refresh(inst_a)
    db_session.refresh(inst_b)

    # Add similar alias to both
    client.post(f"/api/v1/institutions/{inst_a.id}/aliases", headers=headers, json={"alias_name": "SXIT"})
    client.post(f"/api/v1/institutions/{inst_b.id}/aliases", headers=headers, json={"alias_name": "SXIT"})

    # Verify both records remain distinct entities with independent IDs and codes
    res_a = client.get(f"/api/v1/institutions/{inst_a.id}")
    res_b = client.get(f"/api/v1/institutions/{inst_b.id}")
    assert res_a.json()["id"] != res_b.json()["id"]
    assert res_a.json()["code"] == "COLL-A-DELHI"
    assert res_b.json()["code"] == "COLL-B-MUMBAI"


@pytest.fixture
def seeded_units(db_session: Session):
    return seed_organizational_units(db_session)

# 3. Tests for Organizational Units
def test_organizational_units_seed_is_idempotent(db_session: Session):
    """Calling seed_organizational_units repeatedly must not create duplicate records."""
    units_1 = seed_organizational_units(db_session)
    count_1 = len(units_1)
    assert count_1 >= 6

    codes = [u.code for u in units_1]
    assert "RB" in codes
    assert "PGRC" in codes
    assert "AB" in codes
    assert "RO_NORTH" in codes

    # Run seed second time
    units_2 = seed_organizational_units(db_session)
    assert len(units_2) == count_1

def test_organizational_unit_code_uniqueness(client, superadmin_user: User, seeded_units):
    """Unit codes must be unique."""
    headers = auth_headers(superadmin_user)
    res = client.post(
        "/api/v1/organizational-units",
        headers=headers,
        json={"code": "RB", "name": "Duplicate Regulation Bureau", "unit_type": "BUREAU"}
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in res.json()["detail"]

def test_organizational_unit_hierarchy_cycle_rejection(client, db_session: Session, superadmin_user: User, seeded_units):
    """Parent unit cycle detection must reject self-referential or cyclic links."""
    headers = auth_headers(superadmin_user)

    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    assert unit is not None

    # Attempt to set unit as its own parent
    res_self = client.put(
        f"/api/v1/organizational-units/{unit.id}",
        headers=headers,
        json={"parent_unit_id": unit.id}
    )
    assert res_self.status_code == status.HTTP_400_BAD_REQUEST
    assert "cycle" in res_self.json()["detail"].lower()


# 4. Tests for Bureau Memberships & Role Isolation
def test_bureau_membership_assignment_and_authorization(client, db_session: Session, superadmin_user: User, college_officer_user: User, seeded_units):
    """Test assigning a user to an AICTE Bureau and verifying permission boundaries."""
    headers = auth_headers(superadmin_user)
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "RB").first()
    assert unit is not None

    # SuperAdmin assigns user to Regulation Bureau
    res_assign = client.post(
        f"/api/v1/organizational-units/{unit.id}/members",
        headers=headers,
        json={
            "user_id": college_officer_user.id,
            "membership_role": "BUREAU_OFFICER",
            "designation": "Scrutiny Officer"
        }
    )
    assert res_assign.status_code == status.HTTP_201_CREATED
    mem_data = res_assign.json()
    assert mem_data["unit_code"] == "RB"
    assert mem_data["membership_role"] == "BUREAU_OFFICER"
    assert mem_data["is_active"] is True
    membership_id = mem_data["id"]

    # Revoke membership
    res_revoke = client.delete(
        f"/api/v1/organizational-units/{unit.id}/members/{membership_id}",
        headers=headers
    )
    assert res_revoke.status_code == status.HTTP_204_NO_CONTENT

def test_college_roles_do_not_automatically_acquire_bureau_access(client, db_session: Session, regular_student_user: User, seeded_units):
    """College roles (STUDENT, etc.) cannot assign bureau staff or modify organizational units."""
    student_headers = auth_headers(regular_student_user)
    unit = db_session.query(OrganizationalUnit).filter(OrganizationalUnit.code == "PGRC").first()
    assert unit is not None

    # Student cannot assign bureau membership
    res = client.post(
        f"/api/v1/organizational-units/{unit.id}/members",
        headers=student_headers,
        json={"user_id": regular_student_user.id, "membership_role": "BUREAU_HEAD"}
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Student cannot create or edit organizational units
    res_unit = client.post(
        "/api/v1/organizational-units",
        headers=student_headers,
        json={"code": "FAKE_BUREAU", "name": "Fake Bureau", "unit_type": "BUREAU"}
    )
    assert res_unit.status_code == status.HTTP_403_FORBIDDEN
