import urllib.request
import urllib.error
import json
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log(msg, status="OK"):
    symbols = {"OK": "[+]", "ERR": "[X]", "INFO": "[i]"}
    print(f"{symbols.get(status, '[?]')} {msg}")

def do_req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    headers.setdefault("Accept", "application/json")
    
    encoded_data = None
    if data is not None:
        headers.setdefault("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            status_code = resp.status
            return status_code, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        parsed = {}
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"detail": body}
        return e.code, parsed

def main():
    print("=" * 65)
    print("EduResolve AI - Full Frontend-to-Backend Integration Verification")
    print("=" * 65)

    # 1. Health checks
    try:
        code, data = do_req(f"{BASE_URL}/health")
        assert code == 200, f"Health check failed with {code}: {data}"
        log(f"1. /api/v1/health operational: {data.get('status')} ({data.get('app')})")

        code_db, data_db = do_req(f"{BASE_URL}/health/db")
        assert code_db == 200 and data_db.get("database") == "healthy", f"DB Health failed: {data_db}"
        log(f"2. /api/v1/health/db connected: {data_db.get('driver')} on {data_db.get('host')}:{data_db.get('port')} (DB: {data_db.get('database_name')})")
    except Exception as e:
        log(f"Health check failed: {e}", "ERR")
        sys.exit(1)

    # 2. Get categories & institutions
    try:
        code, cats = do_req(f"{BASE_URL}/categories")
        assert code == 200 and len(cats) > 0, f"Categories failed: {cats}"
        cat_id = cats[0]["id"]
        cat_name = cats[0]["name"]
        log(f"3. GET /categories verified ({len(cats)} categories available, using '{cat_name}')")

        code, insts = do_req(f"{BASE_URL}/institutions")
        assert code == 200 and len(insts) > 0, f"Institutions failed: {insts}"
        inst_id = insts[0]["id"]
        inst_name = insts[0]["name"]
        log(f"4. GET /institutions verified ({len(insts)} institutions available, using '{inst_name}')")
    except Exception as e:
        log(f"Categories/Institutions failed: {e}", "ERR")
        sys.exit(1)

    # 5. Student Registration
    test_id = str(uuid.uuid4())[:8]
    student_email = f"student_{test_id}@example.com"
    student_password = "StudentTestPassword123!"
    reg_payload = {
        "email": student_email,
        "password": student_password,
        "full_name": f"Test Student {test_id.upper()}",
        "phone_number": "9876543210",
        "student_id_number": f"ROLL-{test_id.upper()}",
        "institution_id": inst_id
    }
    try:
        code, reg_data = do_req(f"{BASE_URL}/auth/register", method="POST", data=reg_payload)
        assert code in [200, 201], f"Registration failed ({code}): {reg_data}"
        log(f"5. POST /auth/register verified: Registered new student {student_email}")
    except Exception as e:
        log(f"Registration failed: {e}", "ERR")
        sys.exit(1)

    # 6. Student Login
    login_payload = {
        "email": student_email,
        "password": student_password
    }
    try:
        code, login_data = do_req(f"{BASE_URL}/auth/login", method="POST", data=login_payload)
        assert code == 200 and "access_token" in login_data, f"Login failed ({code}): {login_data}"
        token = login_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        log(f"6. POST /auth/login verified: Bearer JWT acquired (type: {login_data.get('token_type')})")
    except Exception as e:
        log(f"Login failed: {e}", "ERR")
        sys.exit(1)

    # 6. AI Categorization inference endpoint (/ai/analyze)
    try:
        ai_payload = {
            "title": "Semester 4 mark sheet delayed by 3 weeks",
            "description": "My final semester exam results were published but the provisional certificate is not yet issued by the evaluation department.",
            "institution_id": inst_id,
            "category_id": cat_id
        }
        code, ai_data = do_req(f"{BASE_URL}/ai/analyze", method="POST", data=ai_payload, headers=auth_headers)
        assert code == 200, f"AI analyze failed: {ai_data}"
        cat_rec = ai_data.get("category", {})
        prio_rec = ai_data.get("priority", {})
        log(f"7. POST /ai/analyze verified: Recommended Category = '{cat_rec.get('category_name')}' (Model: {cat_rec.get('model_used')}), Priority = {prio_rec.get('priority')}")
    except Exception as e:
        log(f"AI Categorize check failed: {e}", "ERR")
        sys.exit(1)

    # 6. Profile GET and PUT
    try:
        code, me_data = do_req(f"{BASE_URL}/auth/me", headers=auth_headers)
        assert code == 200 and me_data.get("email") == student_email, f"Me failed: {me_data}"
        log(f"8. GET /auth/me verified: Full name = '{me_data.get('full_name')}', Role = {me_data.get('default_role')}")

        update_payload = {
            "full_name": f"Updated Student {test_id.upper()}",
            "phone_number": "9123456789"
        }
        code, update_data = do_req(f"{BASE_URL}/auth/me", method="PUT", data=update_payload, headers=auth_headers)
        assert code == 200 and update_data.get("full_name") == f"Updated Student {test_id.upper()}", f"Update failed: {update_data}"
        log(f"9. PUT /auth/me verified: Profile name updated to '{update_data.get('full_name')}'")
    except Exception as e:
        log(f"Profile check failed: {e}", "ERR")
        sys.exit(1)

    # 7. Student Grievance Submission
    grv_payload = {
        "title": f"Delayed Exam Hall Ticket {test_id}",
        "description": "Hall ticket has not arrived for the upcoming exams next week. Please review immediately.",
        "category_id": cat_id,
        "institution_id": inst_id,
        "is_anonymous": False
    }
    try:
        code, grv_data = do_req(f"{BASE_URL}/grievances", method="POST", data=grv_payload, headers=auth_headers)
        assert code in [200, 201], f"Grievance submission failed ({code}): {grv_data}"
        grv_id = grv_data["id"]
        ref_number = grv_data["reference_number"]
        log(f"10. POST /grievances verified: Created Grievance #{grv_id} (Ref: {ref_number}, Status: {grv_data.get('status')})")
    except Exception as e:
        log(f"Grievance submission failed: {e}", "ERR")
        sys.exit(1)

    # 8. Student View Grievance Detail & Timeline
    try:
        code, detail_data = do_req(f"{BASE_URL}/grievances/{grv_id}", headers=auth_headers)
        assert code == 200 and detail_data["reference_number"] == ref_number, f"Detail failed: {detail_data}"
        log(f"11. GET /grievances/{grv_id} verified: Title = '{detail_data['title']}'")

        code, timeline_data = do_req(f"{BASE_URL}/grievances/{grv_id}/timeline", headers=auth_headers)
        assert code == 200 and len(timeline_data) > 0, f"Timeline failed: {timeline_data}"
        log(f"12. GET /grievances/{grv_id}/timeline verified: {len(timeline_data)} timeline event(s) recorded")
    except Exception as e:
        log(f"Detail/Timeline failed: {e}", "ERR")
        sys.exit(1)

    # 9. Public Grievance Tracking (No Auth)
    try:
        code, track_data = do_req(f"{BASE_URL}/grievances/track/{ref_number}")
        assert code == 200 and track_data["reference_number"] == ref_number, f"Tracking failed: {track_data}"
        assert "student_email" not in track_data, "Security violation: student email exposed in public track!"
        log(f"13. GET /grievances/track/{ref_number} verified: Status = {track_data['status']}, Institution = {track_data['institution_name']}")
    except Exception as e:
        log(f"Public tracking failed: {e}", "ERR")
        sys.exit(1)

    # 10. RBAC Confidentiality Enforcement: Student cannot view internal notes
    try:
        code, notes_data = do_req(f"{BASE_URL}/grievances/{grv_id}/internal-notes", headers=auth_headers)
        assert code in [403, 401], f"Expected 403 Forbidden for student accessing internal notes, got {code}"
        log(f"14. RBAC Confidentiality verified: Student forbidden from internal notes (HTTP {code})")
    except Exception as e:
        log(f"RBAC Confidentiality check failed: {e}", "ERR")
        sys.exit(1)

    # 11. Student Two-Way Messaging
    try:
        msg_payload = {"message": "Please confirm the expected release date for the hall tickets."}
        code, msg_data = do_req(f"{BASE_URL}/grievances/{grv_id}/messages", method="POST", data=msg_payload, headers=auth_headers)
        assert code in [200, 201], f"Message send failed ({code}): {msg_data}"
        log(f"15. POST /grievances/{grv_id}/messages verified: Student inquiry submitted")

        code, messages_list = do_req(f"{BASE_URL}/grievances/{grv_id}/messages", headers=auth_headers)
        assert code == 200 and len(messages_list) >= 1, f"Message list failed: {messages_list}"
        log(f"16. GET /grievances/{grv_id}/messages verified: {len(messages_list)} message(s) in active thread")
    except Exception as e:
        log(f"Messaging failed: {e}", "ERR")
        sys.exit(1)

    print("=" * 65)
    print("SUCCESS: All 16 Frontend API integration workflows verified operational!")
    print("FastAPI + MariaDB/MySQL via XAMPP are actively responding to frontend requests.")
    print("=" * 65)

if __name__ == "__main__":
    main()
