import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

def log(step, status, detail=""):
    badge = "[PASS]" if status else "[FAIL]"
    print(f"{badge} {step:45} | {detail}")
    if not status:
        sys.exit(1)

def run_live_audit():
    print("=" * 80)
    print("EDURESOLVE AI — LIVE END-TO-END HTTP API & MYSQL AUDIT")
    print("=" * 80)

    session = requests.Session()

    # 1. Root & Health
    r = session.get(f"{BASE_URL}/")
    log("GET / (Root API info)", r.status_code == 200, f"Status: {r.status_code}")

    r = session.get(f"{BASE_URL}/api/health")
    log("GET /api/health (Service Health)", r.status_code == 200, f"App: {r.json().get('app')}")

    r = session.get(f"{BASE_URL}/api/health/db")
    log("GET /api/health/db (MySQL DB Health)", r.status_code == 200, f"DB Status: {r.json().get('status')}")

    # 2. Public Metadata
    r = session.get(f"{API_V1}/institutions")
    log("GET /api/v1/institutions", r.status_code == 200, f"Count: {len(r.json())}")
    institutions = r.json()
    nit_delhi_id = next((inst["id"] for inst in institutions if inst["code"] == "NITD01"), institutions[0]["id"])

    r = session.get(f"{API_V1}/categories")
    log("GET /api/v1/categories", r.status_code == 200, f"Count: {len(r.json())}")
    categories = r.json()
    academic_cat_id = next((c["id"] for c in categories if "Academic" in c["name"]), categories[0]["id"])

    # 3. Authentication for all 5 roles
    roles_credentials = [
        ("STUDENT", "student@nitdelhi.ac.in", "Password@123"),
        ("COLLEGE_OFFICER", "officer@nitdelhi.ac.in", "Password@123"),
        ("INSTITUTION_HEAD", "head@nitdelhi.ac.in", "Password@123"),
        ("REGULATORY_ADMIN", "regulator@education.gov.in", "Password@123"),
        ("SUPER_ADMIN", "admin@eduresolve.ai", "Password@123"),
    ]

    tokens = {}
    for role, email, password in roles_credentials:
        r = session.post(f"{API_V1}/auth/login", json={"email": email, "password": password})
        valid = r.status_code == 200 and "access_token" in r.json()
        log(f"POST /api/v1/auth/login ({role})", valid, f"HTTP {r.status_code}")
        if valid:
            tokens[role] = r.json()["access_token"]

    student_headers = {"Authorization": f"Bearer {tokens['STUDENT']}"}
    officer_headers = {"Authorization": f"Bearer {tokens['COLLEGE_OFFICER']}"}
    head_headers = {"Authorization": f"Bearer {tokens['INSTITUTION_HEAD']}"}
    admin_headers = {"Authorization": f"Bearer {tokens['SUPER_ADMIN']}"}

    # 4. Identity Profile
    r = session.get(f"{API_V1}/auth/me", headers=student_headers)
    log("GET /api/v1/auth/me (Student Profile)", r.status_code == 200, f"Email: {r.json().get('email')}")

    r = session.get(f"{API_V1}/users/me", headers=student_headers)
    log("GET /api/v1/users/me (User Profile Alias)", r.status_code == 200, f"Email: {r.json().get('email')}")

    # 5. AI Service Inference Endpoint
    ai_payload = {
        "title": "Semester 5 Grade Card Transcript Delay",
        "description": "I submitted my grade verification for semester 5 exam two months ago but marksheet is delayed.",
        "institution_id": nit_delhi_id
    }
    r = session.post(f"{API_V1}/ai/analyze", json=ai_payload, headers=student_headers)
    res = r.json()
    ai_ok = r.status_code == 200 and "category" in res and "category_name" in res["category"]
    cat_rec = res.get("category", {})
    prio_rec = res.get("priority", {})
    log(
        "POST /api/v1/ai/analyze (NLP Triage)", 
        ai_ok, 
        f"Category: {cat_rec.get('category_name')} (Conf: {cat_rec.get('confidence')}, Priority: {prio_rec.get('priority')})"
    )

    # 6. Student Submits Grievance
    grievance_payload = {
        "title": "Audit Synthetic Complaint - Lab Equipment Breakdown",
        "description": "Fluid Mechanics lab equipment in Block B has been malfunctioning, affecting scheduled laboratory experiments.",
        "institution_id": nit_delhi_id,
        "category_id": academic_cat_id,
        "department": "Mechanical Engineering",
        "is_anonymous": False
    }
    r = session.post(f"{API_V1}/grievances", json=grievance_payload, headers=student_headers)
    created = r.status_code in [200, 201] and "reference_number" in r.json()
    log("POST /api/v1/grievances (Submit)", created, f"Ref #: {r.json().get('reference_number')}")
    grievance_data = r.json()
    grievance_id = grievance_data["id"]
    ref_num = grievance_data["reference_number"]

    # 7. Public Tracking without Auth
    r = session.get(f"{API_V1}/grievances/track/{ref_num}")
    log(f"GET /api/v1/grievances/track/{ref_num}", r.status_code == 200, f"Status: {r.json().get('status')}")

    # 8. Officer Queue Listing
    r = session.get(f"{API_V1}/grievances", headers=officer_headers)
    log("GET /api/v1/grievances (Officer Queue)", r.status_code == 200, f"Total Cases: {len(r.json())}")

    # 9. Internal Note Shielding Verification
    # Officer posts internal note
    r = session.post(
        f"{API_V1}/grievances/{grievance_id}/internal-notes",
        json={"note": "Officer Confidential Memo: Verified with lab technician."},
        headers=officer_headers
    )
    log("POST /api/v1/grievances/{id}/internal-notes", r.status_code in [200, 201], f"Note ID: {r.json().get('id')}")

    # Officer posts student-visible message
    r = session.post(
        f"{API_V1}/grievances/{grievance_id}/messages",
        json={"message": "Dear Student, maintenance has been scheduled for tomorrow morning."},
        headers=officer_headers
    )
    log("POST /api/v1/grievances/{id}/messages (Public)", r.status_code in [200, 201], f"Message ID: {r.json().get('id')}")

    # Student views grievance detail - internal notes MUST NOT be present in response
    r = session.get(f"{API_V1}/grievances/{grievance_id}", headers=student_headers)
    student_view = r.json()
    student_sees_notes = len(student_view.get("internal_notes", [])) > 0
    log("RBAC Shielding Check (Internal Notes Omitted from Student View)", not student_sees_notes, f"Internal notes count: {len(student_view.get('internal_notes', []))}")

    # Officer views grievance detail - internal notes MUST be present
    r = session.get(f"{API_V1}/grievances/{grievance_id}", headers=officer_headers)
    officer_view = r.json()
    officer_sees_notes = len(officer_view.get("internal_notes", [])) > 0
    log("Officer View Check (Internal Notes Present for Officer)", officer_sees_notes, f"Internal notes count: {len(officer_view.get('internal_notes', []))}")

    # 10. Status Transitions (SUBMITTED -> INVESTIGATION_IN_PROGRESS -> RESOLVED)
    r = session.put(
        f"{API_V1}/grievances/{grievance_id}/status",
        json={"status": "INVESTIGATION_IN_PROGRESS", "reason": "Investigation initiated by departmental officer"},
        headers=officer_headers
    )
    log("PUT /api/v1/grievances/{id}/status (INVESTIGATION_IN_PROGRESS)", r.status_code == 200, f"Current: {r.json().get('status')}")

    r = session.put(
        f"{API_V1}/grievances/{grievance_id}/status",
        json={"status": "RESOLVED", "reason": "Replacement pump installed and tested by lab instructor", "resolution_notes": "Equipment repaired and verified."},
        headers=officer_headers
    )
    log("PUT /api/v1/grievances/{id}/status (RESOLVED)", r.status_code == 200, f"Current: {r.json().get('status')}")

    # 11. Student Submits Feedback
    feedback_payload = {
        "rating": 5,
        "satisfies_resolution": True,
        "comments": "Excellent and rapid resolution before practical exams."
    }
    r = session.post(f"{API_V1}/grievances/{grievance_id}/feedback", json=feedback_payload, headers=student_headers)
    log("POST /api/v1/grievances/{id}/feedback (5-Star Rating)", r.status_code in [200, 201], f"Rating: {r.json().get('rating')}/5")

    # 12. Institutional Analytics
    r = session.get(f"{API_V1}/analytics/dashboard", headers=head_headers)
    log("GET /api/v1/analytics/dashboard (Head Dashboard)", r.status_code == 200, f"Total Cases: {r.json().get('total_grievances')}")

    print("=" * 80)
    print("ALL 16 LIVE AUDIT VERIFICATION STEPS PASSED SUCCESSFULLY AGAINST XAMPP MYSQL!")
    print("=" * 80)

if __name__ == "__main__":
    run_live_audit()
