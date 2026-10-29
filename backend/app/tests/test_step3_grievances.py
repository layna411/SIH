import io
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership
from app.models.enums import UserRoleEnum, GrievanceStatusEnum, GrievancePriorityEnum, EscalationLevelEnum
from app.models.grievance import Grievance
from app.models.user import User

@pytest.fixture
def test_setup(client, db_session):
    """Set up two institutions, category, students, and officers in isolated MySQL test schema."""
    # Categories
    cat1 = GrievanceCategory(code="ACAD_TEST", name="Academics Test", default_sla_days=7, is_active=True)
    cat2 = GrievanceCategory(code="HOSTEL_TEST", name="Hostel Test", default_sla_days=3, is_active=True)
    db_session.add_all([cat1, cat2])

    # Institutions
    inst_a = Institution(code="INST_ALPHA", name="Alpha Institute", state="Delhi", city="New Delhi", contact_email="alpha@test.edu", is_active=True, is_verified=True)
    inst_b = Institution(code="INST_BETA", name="Beta Institute", state="Karnataka", city="Bengaluru", contact_email="beta@test.edu", is_active=True, is_verified=True)
    db_session.add_all([inst_a, inst_b])
    db_session.commit()
    db_session.refresh(cat1)
    db_session.refresh(cat2)
    db_session.refresh(inst_a)
    db_session.refresh(inst_b)

    # Student A (registered with Alpha)
    client.post("/api/v1/auth/register", json={
        "email": "student_a@alpha.edu",
        "password": "Password123!",
        "full_name": "Student Alpha",
        "institution_id": inst_a.id,
        "role": "STUDENT"
    })
    token_student_a = client.post("/api/v1/auth/login", json={"email": "student_a@alpha.edu", "password": "Password123!"}).json()["access_token"]

    # Student B (registered with Beta)
    client.post("/api/v1/auth/register", json={
        "email": "student_b@beta.edu",
        "password": "Password123!",
        "full_name": "Student Beta",
        "institution_id": inst_b.id,
        "role": "STUDENT"
    })
    token_student_b = client.post("/api/v1/auth/login", json={"email": "student_b@beta.edu", "password": "Password123!"}).json()["access_token"]

    # Officer A1 (Alpha)
    client.post("/api/v1/auth/register", json={
        "email": "officer_a1@alpha.edu",
        "password": "Password123!",
        "full_name": "Officer Alpha One",
        "institution_id": inst_a.id
    })
    user_a1 = db_session.query(User).filter(User.email == "officer_a1@alpha.edu").first()
    user_a1.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem_a1 = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_a1.id).first()
    if mem_a1:
        mem_a1.role = UserRoleEnum.COLLEGE_OFFICER
    db_session.commit()
    token_officer_a1 = client.post("/api/v1/auth/login", json={"email": "officer_a1@alpha.edu", "password": "Password123!"}).json()["access_token"]

    # Officer A2 (Alpha - for reassignment tests)
    client.post("/api/v1/auth/register", json={
        "email": "officer_a2@alpha.edu",
        "password": "Password123!",
        "full_name": "Officer Alpha Two",
        "institution_id": inst_a.id
    })
    user_a2 = db_session.query(User).filter(User.email == "officer_a2@alpha.edu").first()
    user_a2.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem_a2 = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_a2.id).first()
    if mem_a2:
        mem_a2.role = UserRoleEnum.COLLEGE_OFFICER
    db_session.commit()
    token_officer_a2 = client.post("/api/v1/auth/login", json={"email": "officer_a2@alpha.edu", "password": "Password123!"}).json()["access_token"]

    # Officer B1 (Beta)
    client.post("/api/v1/auth/register", json={
        "email": "officer_b1@beta.edu",
        "password": "Password123!",
        "full_name": "Officer Beta One",
        "institution_id": inst_b.id
    })
    user_b1 = db_session.query(User).filter(User.email == "officer_b1@beta.edu").first()
    user_b1.default_role = UserRoleEnum.COLLEGE_OFFICER
    mem_b1 = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_b1.id).first()
    if mem_b1:
        mem_b1.role = UserRoleEnum.COLLEGE_OFFICER
    db_session.commit()
    token_officer_b1 = client.post("/api/v1/auth/login", json={"email": "officer_b1@beta.edu", "password": "Password123!"}).json()["access_token"]

    # Institution Head Alpha
    client.post("/api/v1/auth/register", json={
        "email": "head_alpha@alpha.edu",
        "password": "Password123!",
        "full_name": "Head of Alpha",
        "institution_id": inst_a.id
    })
    user_head = db_session.query(User).filter(User.email == "head_alpha@alpha.edu").first()
    user_head.default_role = UserRoleEnum.INSTITUTION_HEAD
    mem_head = db_session.query(InstitutionMembership).filter(InstitutionMembership.user_id == user_head.id).first()
    if mem_head:
        mem_head.role = UserRoleEnum.INSTITUTION_HEAD
    db_session.commit()
    token_head_a = client.post("/api/v1/auth/login", json={"email": "head_alpha@alpha.edu", "password": "Password123!"}).json()["access_token"]

    return {
        "cat1": cat1,
        "cat2": cat2,
        "inst_a": inst_a,
        "inst_b": inst_b,
        "token_student_a": token_student_a,
        "token_student_b": token_student_b,
        "token_officer_a1": token_officer_a1,
        "token_officer_a2": token_officer_a2,
        "token_officer_b1": token_officer_b1,
        "token_head_a": token_head_a,
        "user_a1_id": user_a1.id,
        "user_a2_id": user_a2.id,
        "user_b1_id": user_b1.id
    }


def test_1_student_grievance_submission(client, test_setup):
    """Test 1: Student grievance submission succeeds and starts in SUBMITTED status."""
    res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Semester Grade Card Not Dispatched",
        "description": "Final semester grade card has not been delivered after more than 45 days since examination results publication.",
        "priority": "NORMAL"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "SUBMITTED"
    assert data["title"] == "Semester Grade Card Not Dispatched"
    assert data["institution_id"] == test_setup["inst_a"].id


def test_2_unique_reference_number_generation(client, test_setup):
    """Test 2: Unique, non-guessable reference numbers generated."""
    res1 = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Course Textbook Shortage in Central Library",
        "description": "Prescribed textbook for advanced algorithms is missing copies for the entire section of 60 students.",
        "priority": "NORMAL"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res1.status_code == 201
    ref1 = res1.json()["reference_number"]

    res2 = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Laboratory Computer Hardware Failure",
        "description": "Workstations 12 to 18 in computer laboratory 3 have failing hard drives preventing practical tests.",
        "priority": "HIGH"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res2.status_code == 201
    ref2 = res2.json()["reference_number"]

    assert ref1.startswith("GRV-")
    assert ref2.startswith("GRV-")
    assert ref1 != ref2


def test_3_required_field_validation(client, test_setup):
    """Test 3: Required field validations on submission."""
    # Title too short (< 5 chars)
    res_short_title = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Hi",
        "description": "Valid description explaining grievance details properly over twenty characters."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res_short_title.status_code == 422

    # Description too short (< 20 chars)
    res_short_desc = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Valid Issue Title",
        "description": "Too short"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res_short_desc.status_code == 422


def test_4_correct_institution_association(client, test_setup):
    """Test 4: Student cannot submit a grievance against an institution they do not belong to."""
    # Student A (registered with Alpha) attempts to file against Beta
    res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_b"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Cross Institution Filing Attempt",
        "description": "Student attempts to file a grievance directly to an institution where they are not enrolled."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res.status_code == 403
    assert "affiliated" in res.json()["detail"].lower() or "unauthorized" in res.json()["detail"].lower()


def test_5_student_sees_own_grievances(client, test_setup):
    """Test 5: Student sees only their submitted cases."""
    client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Hostel Water Purifier Maintenance",
        "description": "Floor 2 water purifier in hostel block B has a damaged filter cartridge requiring replacement."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})

    list_res = client.get("/api/v1/grievances", headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_6_student_cannot_view_another_students_grievance(client, test_setup):
    """Test 6: Direct access / IDOR protection across students."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Confidential Examination Recheck Request",
        "description": "Discrepancy observed in internal assessment marks tally sheet uploaded on the college portal."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Student B attempts to access Student A's grievance by ID
    view_res = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_student_b']}"})
    assert view_res.status_code == 403


def test_7_officer_sees_authorized_institutional_cases(client, test_setup):
    """Test 7: Authorized institutional officer can view cases of their institution."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Tuition Fee Receipt Double Deducted",
        "description": "Payment was debited twice by netbanking gateway without automatic refund reconciliation."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    officer_view = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert officer_view.status_code == 200
    assert officer_view.json()["id"] == g_id


def test_8_officer_cannot_access_another_institution(client, test_setup):
    """Test 8: Officer of Beta cannot access or modify Alpha's grievances."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Alpha College Wi-Fi Signal Degradation",
        "description": "Access points in library study room have zero coverage since network equipment upgrade."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    officer_b_res = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_officer_b1']}"})
    assert officer_b_res.status_code == 403


def test_9_unauthorized_assignment_denied(client, test_setup):
    """Test 9: Assigning to an officer outside the institution is denied."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Bus Route Transportation Schedule Conflict",
        "description": "College bus 7 departs 15 minutes before the final tutorial hour concludes on Fridays."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Try assigning Alpha's grievance to Officer B1 (belongs to Beta)
    assign_cross_res = client.post(f"/api/v1/grievances/{g_id}/assign", json={
        "assigned_to_user_id": test_setup["user_b1_id"],
        "notes": "Attempting cross-institution assignment"
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert assign_cross_res.status_code == 400

    # Student trying to assign a case
    student_assign_res = client.post(f"/api/v1/grievances/{g_id}/assign", json={
        "assigned_to_user_id": test_setup["user_a1_id"],
        "notes": "Student assigning self"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert student_assign_res.status_code == 403


def test_10_valid_status_transitions_succeed(client, test_setup):
    """Test 10: Step-by-step valid status transitions through workflow lifecycle."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Classroom Projector Bulb Burnout",
        "description": "Projector in room 101 has burnt out bulb preventing multimedia presentations."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # 1. UNDER_REVIEW
    t1 = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "UNDER_REVIEW",
        "reason": "Case acknowledged and placed under review."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert t1.status_code == 200
    assert t1.json()["status"] == "UNDER_REVIEW"

    # 2. ASSIGNED
    t2 = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "ASSIGNED",
        "reason": "Case assigned to audiovisual technician."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert t2.status_code == 200

    # 3. INVESTIGATION_IN_PROGRESS
    t3 = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "INVESTIGATION_IN_PROGRESS",
        "reason": "Technician checking lamp replacement inventory."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert t3.status_code == 200

    # 4. RESOLUTION_PROPOSED
    t4 = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLUTION_PROPOSED",
        "reason": "New OEM projector lamp installed.",
        "resolution_summary": "Replaced bulb with 3000lm OEM unit. Verified projection clarity."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert t4.status_code == 200

    # 5. RESOLVED
    t5 = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLVED",
        "reason": "Technician testing verified complete."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert t5.status_code == 200
    assert t5.json()["status"] == "RESOLVED"
    assert t5.json()["resolved_at"] is not None


def test_11_invalid_status_transitions_fail(client, test_setup):
    """Test 11: Arbitrary status skips are strictly blocked."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Sports Equipment Missing from Gym",
        "description": "Gymnasium badminton racquets and shuttlecocks are locked and unavailable."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # SUBMITTED -> RESOLVED directly is prohibited
    res = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "RESOLVED",
        "reason": "Attempting illegal jump to resolved"
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert res.status_code == 400


def test_12_students_cannot_perform_staff_only_transitions(client, test_setup):
    """Test 12: Students cannot update grievance to staff-only states."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Cafeteria Food Quality Inspection Request",
        "description": "Food served during lunch was undercooked and caused complaints from multiple students."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Student attempts UNDER_REVIEW
    res_ur = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "UNDER_REVIEW",
        "reason": "Student setting under review"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res_ur.status_code == 403

    # Student attempts REJECTED
    res_rej = client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "REJECTED",
        "reason": "Student rejecting"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert res_rej.status_code == 403


def test_13_status_history_is_recorded(client, test_setup):
    """Test 13: Timeline logs each transition with actor and reason."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Library Air Conditioning Defect",
        "description": "Second floor reading room AC leaking water on study desks during operational hours."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "UNDER_REVIEW",
        "reason": "Facilities management initiated case evaluation."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})

    timeline_res = client.get(f"/api/v1/grievances/{g_id}/timeline", headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 2
    assert timeline[0]["to_status"] == "UNDER_REVIEW"
    assert "Facilities management" in timeline[0]["reason"]


def test_14_internal_notes_not_exposed_to_students(client, test_setup):
    """Test 14: Internal notes are strictly shielded from student responses."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Scholarship Disbursement Discrepancy",
        "description": "National scholarship scheme stipend amount deducted without explanatory notification."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Officer writes confidential internal note
    client.post(f"/api/v1/grievances/{g_id}/internal-notes", json={
        "note": "CONFIDENTIAL: Internal audit indicates banking clearance delay at state treasury office."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})

    # Student views grievance details -> internal_notes is empty
    student_view = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_student_a']}"}).json()
    assert len(student_view["internal_notes"]) == 0

    # Student direct GET /internal-notes is 403 Forbidden
    student_notes_res = client.get(f"/api/v1/grievances/{g_id}/internal-notes", headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert student_notes_res.status_code == 403

    # Officer views grievance -> internal note present
    officer_view = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"}).json()
    assert len(officer_view["internal_notes"]) == 1
    assert "CONFIDENTIAL" in officer_view["internal_notes"][0]["note"]


def test_15_student_visible_messages_work(client, test_setup):
    """Test 15: Student-visible communication messages back and forth."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "ID Card Barcode Scanning Failure",
        "description": "Library turnstile refuses to scan newly issued barcode on plastic student identity card."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Officer sends message requesting info
    msg_off = client.post(f"/api/v1/grievances/{g_id}/messages", json={
        "message": "Please confirm the 10-digit number printed below the barcode."
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert msg_off.status_code == 201

    # Student views and responds
    msg_std = client.post(f"/api/v1/grievances/{g_id}/messages", json={
        "message": "The 10-digit number is 2026110042."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert msg_std.status_code == 201

    # Check messages list
    msgs = client.get(f"/api/v1/grievances/{g_id}/messages", headers={"Authorization": f"Bearer {test_setup['token_student_a']}"}).json()
    assert len(msgs) == 2


def test_16_feedback_accepted_only_at_correct_stage(client, test_setup):
    """Test 16: Feedback only permitted once resolution is proposed or resolved."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Hostel Washing Machine Power Cord Damage",
        "description": "Laundry room machine 2 has exposed copper wiring on the main power lead cable."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Feedback in SUBMITTED state must fail
    fb_early = client.post(f"/api/v1/grievances/{g_id}/feedback", json={
        "rating": 4,
        "satisfies_resolution": True,
        "comments": "Too early feedback"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert fb_early.status_code == 400

    # Advance to RESOLUTION_PROPOSED
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "UNDER_REVIEW", "reason": "Reviewing"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "ASSIGNED", "reason": "Assigned to electrician"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "INVESTIGATION_IN_PROGRESS", "reason": "Inspecting cable"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "RESOLUTION_PROPOSED", "reason": "Cable replaced"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})

    # Now feedback succeeds
    fb_valid = client.post(f"/api/v1/grievances/{g_id}/feedback", json={
        "rating": 5,
        "satisfies_resolution": True,
        "comments": "Fixed very promptly, thank you!"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert fb_valid.status_code == 201


def test_17_reopening_requests(client, test_setup):
    """Test 17: Case reopening rules."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Mess Food Hygiene Standards",
        "description": "Mess dining hall tables are not cleaned regularly between meals."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Reopening an active case fails
    reopen_early = client.post(f"/api/v1/grievances/{g_id}/reopen-request", json={
        "reason": "Premature reopening request while case is active"
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert reopen_early.status_code == 400

    # Resolve case
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "UNDER_REVIEW", "reason": "Reviewing"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "ASSIGNED", "reason": "Assigned"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "INVESTIGATION_IN_PROGRESS", "reason": "Working"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "RESOLUTION_PROPOSED", "reason": "Proposed"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    client.put(f"/api/v1/grievances/{g_id}/status", json={"to_status": "RESOLVED", "reason": "Resolved"}, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})

    # Student reopens with reason
    reopen_res = client.post(f"/api/v1/grievances/{g_id}/reopen-request", json={
        "reason": "Problem recurred the very next day. Deep cleaning was not actually conducted."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "REOPENED"


def test_18_escalation_permissions_and_eligibility(client, test_setup):
    """Test 18: Manual and automated escalation enforcement."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Severe Hostile Behavior in Department",
        "description": "Lab attendant repeatedly shouting and threatening students during scheduled laboratory sessions."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Officer escalates to Head
    esc_res = client.post(f"/api/v1/grievances/{g_id}/escalate", json={
        "reason": "Involves staff conduct complaint requiring principal intervention.",
        "level": "LEVEL_2_INSTITUTION_HEAD"
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert esc_res.status_code == 200
    assert esc_res.json()["status"] == "ESCALATED"
    assert esc_res.json()["priority"] == "URGENT"

    # Process overdue escalations service endpoint
    batch_res = client.post("/api/v1/grievances/escalations/process-overdue", headers={"Authorization": f"Bearer {test_setup['token_head_a']}"})
    assert batch_res.status_code == 200
    assert "escalated_count" in batch_res.json()


def test_19_attachment_downloads_require_authorization(client, test_setup):
    """Test 19: Strict authorization check on file uploads and downloads."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Fee Receipt PDF Verification",
        "description": "Attaching the bank transfer slip for verification of fee payment settlement."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Upload attachment as Student A
    file_content = b"%PDF-1.4 test fee receipt file content"
    upload_res = client.post(
        f"/api/v1/grievances/{g_id}/attachments",
        files={"file": ("receipt.pdf", io.BytesIO(file_content), "application/pdf")},
        headers={"Authorization": f"Bearer {test_setup['token_student_a']}"}
    )
    assert upload_res.status_code == 201
    att_id = upload_res.json()["id"]

    # Student B attempts download -> 403 Forbidden
    cross_dl = client.get(f"/api/v1/grievances/{g_id}/attachments/{att_id}/download", headers={"Authorization": f"Bearer {test_setup['token_student_b']}"})
    assert cross_dl.status_code == 403

    # Unauthenticated download -> 401 Unauthorized
    unauth_dl = client.get(f"/api/v1/grievances/{g_id}/attachments/{att_id}/download")
    assert unauth_dl.status_code == 401

    # Authorized Officer A1 download -> 200 OK
    auth_dl = client.get(f"/api/v1/grievances/{g_id}/attachments/{att_id}/download", headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})
    assert auth_dl.status_code == 200
    assert auth_dl.content == file_content


def test_20_ai_failure_does_not_prevent_grievance_submission(client, test_setup):
    """Test 20: Submission remains robust and functional even if AI inference crashes."""
    with patch("app.services.ai_service.ai_service.recommend_category", side_effect=RuntimeError("AI Model Engine Out of Memory")):
        res = client.post("/api/v1/grievances", json={
            "institution_id": test_setup["inst_a"].id,
            "category_id": test_setup["cat1"].id,
            "title": "Auditorium Sound System Echoing",
            "description": "Microphones in main seminar hall have severe feedback loop echo during guest lectures.",
            "priority": "NORMAL"
        }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Auditorium Sound System Echoing"
        assert data["status"] == "SUBMITTED"


def test_21_database_rollback_preserves_data_integrity(client, test_setup):
    """Test 21: Database integrity and rollback on transaction failure."""
    sub_res = client.post("/api/v1/grievances", json={
        "institution_id": test_setup["inst_a"].id,
        "category_id": test_setup["cat1"].id,
        "title": "Parking Lot Flood Water Accumulation",
        "description": "Drainage pipe blocked causing 1 foot deep water logging near two wheeler vehicle stand."
    }, headers={"Authorization": f"Bearer {test_setup['token_student_a']}"})
    g_id = sub_res.json()["id"]

    # Attempt illegal status change to check rollback preserves original status
    client.put(f"/api/v1/grievances/{g_id}/status", json={
        "to_status": "CLOSED",
        "reason": "Premature close attempt"
    }, headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"})

    check = client.get(f"/api/v1/grievances/{g_id}", headers={"Authorization": f"Bearer {test_setup['token_officer_a1']}"}).json()
    assert check["status"] == "SUBMITTED"


def test_22_existing_authentication_and_health_endpoints(client):
    """Test 22: Baseline platform health and auth endpoints remain fully operational."""
    # Health checks
    h_app = client.get("/api/health")
    assert h_app.status_code == 200
    assert h_app.json()["status"] == "healthy"

    h_db = client.get("/api/health/db")
    assert h_db.status_code == 200
    assert h_db.json()["status"] == "connected"
    assert h_db.json()["driver"] == "mysql+pymysql"
