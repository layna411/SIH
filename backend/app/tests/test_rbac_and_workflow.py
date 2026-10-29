import pytest
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum

def create_institutions_and_officers(client, db_session):
    # Institution A
    inst_a = Institution(code="INSTA", name="College Alpha", state="Delhi", city="New Delhi", contact_email="alpha@test.edu", is_active=True, is_verified=True)
    # Institution B
    inst_b = Institution(code="INSTB", name="College Beta", state="Karnataka", city="Bengaluru", contact_email="beta@test.edu", is_active=True, is_verified=True)
    cat = GrievanceCategory(code="ACAD", name="Academics", default_sla_days=7, is_active=True)
    db_session.add_all([inst_a, inst_b, cat])
    db_session.commit()
    db_session.refresh(inst_a)
    db_session.refresh(inst_b)
    db_session.refresh(cat)

    # Student at College Alpha
    client.post("/api/v1/auth/register", json={
        "email": "student_alpha@test.edu",
        "password": "Password123!",
        "full_name": "Student Alpha",
        "institution_id": inst_a.id,
        "role": "STUDENT"
    })
    token_student = client.post("/api/v1/auth/login", json={"email": "student_alpha@test.edu", "password": "Password123!"}).json()["access_token"]

    # Officer at College Alpha
    client.post("/api/v1/auth/register", json={
        "email": "officer_alpha@test.edu",
        "password": "Password123!",
        "full_name": "Officer Alpha",
        "institution_id": inst_a.id
    })
    from app.models.user import User
    user_a = db_session.query(User).filter(User.email == "officer_alpha@test.edu").first()
    user_a.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem_a = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_a.id).first()
    if mem_a:
        mem_a.role = UserRoleEnum.COLLEGE_OFFICER
    db_session.commit()
    token_officer_a = client.post("/api/v1/auth/login", json={"email": "officer_alpha@test.edu", "password": "Password123!"}).json()["access_token"]

    # Officer at College Beta
    client.post("/api/v1/auth/register", json={
        "email": "officer_beta@test.edu",
        "password": "Password123!",
        "full_name": "Officer Beta",
        "institution_id": inst_b.id
    })
    user_b = db_session.query(User).filter(User.email == "officer_beta@test.edu").first()
    user_b.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem_b = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_b.id).first()
    if mem_b:
        mem_b.role = UserRoleEnum.COLLEGE_OFFICER
    db_session.commit()
    token_officer_b = client.post("/api/v1/auth/login", json={"email": "officer_beta@test.edu", "password": "Password123!"}).json()["access_token"]

    return inst_a, inst_b, cat, token_student, token_officer_a, token_officer_b


def test_cross_institution_isolation(client, db_session):
    inst_a, inst_b, cat, token_student, token_officer_a, token_officer_b = create_institutions_and_officers(client, db_session)

    # Student submits grievance at College Alpha
    submit_res = client.post("/api/v1/grievances", json={
        "institution_id": inst_a.id,
        "category_id": cat.id,
        "title": "Alpha College library books shortage",
        "description": "Textbooks for computer science semester 3 are completely unavailable in the library.",
        "priority": "NORMAL"
    }, headers={"Authorization": f"Bearer {token_student}"})
    assert submit_res.status_code == 201
    g_id = submit_res.json()["id"]

    # Officer A (College Alpha) can see the grievance
    res_a = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token_officer_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["id"] == g_id

    # Officer B (College Beta) CANNOT see the grievance (Cross-institution access denied!)
    res_b = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token_officer_b}"})
    assert res_b.status_code == 403

def test_internal_notes_confidentiality(client, db_session):
    inst_a, _, cat, token_student, token_officer_a, _ = create_institutions_and_officers(client, db_session)

    # Student submits grievance
    g_res = client.post("/api/v1/grievances", json={
        "institution_id": inst_a.id,
        "category_id": cat.id,
        "title": "Fee payment verification issue",
        "description": "Tuition fee was deducted but fee receipt is not generating on student portal.",
        "priority": "HIGH"
    }, headers={"Authorization": f"Bearer {token_student}"})
    g_id = g_res.json()["id"]

    # Student tries to post an internal note (MUST BE FORBIDDEN)
    student_note_res = client.post(f"/api/v1/grievances/{g_id}/internal-notes", json={
        "note": "Attempted internal note by student"
    }, headers={"Authorization": f"Bearer {token_student}"})
    assert student_note_res.status_code == 403

    # Officer A posts a confidential internal note
    officer_note_res = client.post(f"/api/v1/grievances/{g_id}/internal-notes", json={
        "note": "CONFIDENTIAL: Contacted payment gateway merchant desk; transaction ID confirmed."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})
    assert officer_note_res.status_code == 201

    # Officer views grievance: internal note IS present
    officer_view = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token_officer_a}"}).json()
    assert len(officer_view["internal_notes"]) == 1
    assert "CONFIDENTIAL" in officer_view["internal_notes"][0]["note"]

    # Student views grievance: internal note IS EMPTY / SHIELDED
    student_view = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token_student}"}).json()
    assert len(student_view["internal_notes"]) == 0

def test_full_resolution_and_feedback_lifecycle(client, db_session):
    inst_a, _, cat, token_student, token_officer_a, _ = create_institutions_and_officers(client, db_session)

    # 1. Student files grievance
    g_res = client.post("/api/v1/grievances", json={
        "institution_id": inst_a.id,
        "category_id": cat.id,
        "title": "Air conditioning broken in lecture hall 4",
        "description": "The AC unit in hall 4 is tripping the circuit breaker every 10 minutes during classes.",
        "priority": "NORMAL"
    }, headers={"Authorization": f"Bearer {token_student}"})
    g_id = g_res.json()["id"]
    assert g_res.json()["status"] == "SUBMITTED"

    # 2. Officer sets status to UNDER_REVIEW
    client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "UNDER_REVIEW",
        "reason": "Case under initial review by facilities desk."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})

    # 3. Officer sets status to INVESTIGATION_IN_PROGRESS
    client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "INVESTIGATION_IN_PROGRESS",
        "reason": "Electrician dispatched to inspect hall 4 electrical wiring."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})

    # 4. Officer posts two-way message
    msg_res = client.post(f"/api/v1/grievances/{g_id}/messages", json={
        "message": "Electrician has replaced the breaker. Testing cooling today."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})
    assert msg_res.status_code == 201

    # 5. Officer proposes resolution
    res_prop = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLUTION_PROPOSED",
        "reason": "Compressor breaker replaced and verified.",
        "resolution_summary": "Faulty 32A breaker replaced with upgraded 40A industrial unit. Temperatures normalized."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})
    assert res_prop.status_code == 200

    # 6. Officer sets status to RESOLVED
    client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLVED",
        "reason": "Maintenance confirmed complete."
    }, headers={"Authorization": f"Bearer {token_officer_a}"})

    # 7. Student submits satisfaction feedback
    fb_res = client.post(f"/api/v1/grievances/{g_id}/feedback", json={
        "rating": 5,
        "satisfies_resolution": True,
        "comments": "Great work! AC is functioning perfectly now."
    }, headers={"Authorization": f"Bearer {token_student}"})
    assert fb_res.status_code == 201
    assert fb_res.json()["rating"] == 5

    # 8. Verify status history count
    final_g = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {token_student}"}).json()
    assert len(final_g["status_history"]) >= 5
    assert final_g["feedback"]["rating"] == 5
