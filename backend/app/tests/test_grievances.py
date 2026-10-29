import pytest
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership
from app.models.enums import UserRoleEnum, GrievanceStatusEnum

def setup_institution_and_category(db_session):
    cat = GrievanceCategory(
        code="ACAD",
        name="Academics",
        description="Academic grievances",
        default_sla_days=7,
        is_active=True
    )
    db_session.add(cat)
    
    inst = Institution(
        code="TESTINST",
        name="Test University",
        state="Delhi",
        city="New Delhi",
        contact_email="test@inst.edu",
        is_active=True,
        is_verified=True
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(cat)
    db_session.refresh(inst)
    return inst, cat

def test_grievance_submission_and_isolation(client, db_session):
    inst, cat = setup_institution_and_category(db_session)

    # Register Student 1
    s1_res = client.post("/api/v1/auth/register", json={
        "email": "student1@campus.edu",
        "password": "Password123!",
        "full_name": "Student One",
        "institution_id": inst.id
    })
    token1 = client.post("/api/v1/auth/login", json={"email": "student1@campus.edu", "password": "Password123!"}).json()["access_token"]

    # Register Student 2
    s2_res = client.post("/api/v1/auth/register", json={
        "email": "student2@campus.edu",
        "password": "Password123!",
        "full_name": "Student Two",
        "institution_id": inst.id
    })
    token2 = client.post("/api/v1/auth/login", json={"email": "student2@campus.edu", "password": "Password123!"}).json()["access_token"]

    # Student 1 submits a grievance
    g_payload = {
        "institution_id": inst.id,
        "category_id": cat.id,
        "title": "Unscheduled lecture clash during core hours",
        "description": "Two mandatory core classes are scheduled at 10 AM on Tuesdays causing attendance conflicts.",
        "priority": "NORMAL"
    }
    submit_res = client.post("/api/v1/grievances", json=g_payload, headers={"Authorization": f"Bearer {token1}"})
    assert submit_res.status_code == 201
    g_data = submit_res.json()
    assert g_data["reference_number"].startswith("GRV-")
    assert g_data["status"] == "SUBMITTED"
    g_id = g_data["id"]

    # Student 1 can see their grievance
    list1_res = client.get("/api/v1/grievances", headers={"Authorization": f"Bearer {token1}"})
    assert len(list1_res.json()) == 1

    # Student 2 CANNOT see Student 1's grievance in their list (Data Isolation!)
    list2_res = client.get("/api/v1/grievances", headers={"Authorization": f"Bearer {token2}"})
    assert len(list2_res.json()) == 0

    # Student 2 CANNOT view Student 1's grievance details by ID (IDOR protection!)
    idor_res = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token2}"})
    assert idor_res.status_code == 403

def test_invalid_status_transition_rejection(client, db_session):
    inst, cat = setup_institution_and_category(db_session)

    # Register Student
    client.post("/api/v1/auth/register", json={
        "email": "student3@campus.edu",
        "password": "Password123!",
        "full_name": "Student Three",
        "institution_id": inst.id
    })
    token = client.post("/api/v1/auth/login", json={"email": "student3@campus.edu", "password": "Password123!"}).json()["access_token"]

    # Submit grievance (starts in SUBMITTED)
    g_payload = {
        "institution_id": inst.id,
        "category_id": cat.id,
        "title": "Hostel room electrical socket spark",
        "description": "Room 204 electrical board is giving sparks when plugged in.",
        "priority": "HIGH"
    }
    submit_res = client.post("/api/v1/grievances", json=g_payload, headers={"Authorization": f"Bearer {token}"})
    g_id = submit_res.json()["id"]

    # Attempt illegal transition: Student tries to transition directly from SUBMITTED to RESOLVED without officer investigation
    illegal_res = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLVED",
        "reason": "Attempting invalid client status override"
    }, headers={"Authorization": f"Bearer {token}"})
    assert illegal_res.status_code == 403
