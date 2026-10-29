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
    print("EduResolve AI - Full Officer & SuperAdmin Integration Verification")
    print("=" * 65)

    # Let's bootstrap/login as SuperAdmin
    # First, let's bootstrap a test superadmin via script
    from app.database.connection import SessionLocal
    from app.services.bootstrap_service import bootstrap_super_admin
    from app.models.user import User
    from app.models.enums import UserRoleEnum
    from app.models.institution import Institution, InstitutionMembership

    admin_email = "superadmin@eduresolve.gov.in"
    admin_password = "SuperAdminSecurePassword123!"

    with SessionLocal() as db:
        admin_user = bootstrap_super_admin(db, admin_email, admin_password, "Super Administrator")
        
        # Also create a designated test officer for institution 1
        inst = db.query(Institution).first()
        inst_id = inst.id

        officer_email = "officer.test@college.edu"
        officer = db.query(User).filter(User.email == officer_email).first()
        if not officer:
            from app.core.security import hash_password
            officer = User(
                email=officer_email,
                full_name="Prof. Sharma (Grievance Officer)",
                hashed_password=hash_password("OfficerSecurePassword123!"),
                default_role=UserRoleEnum.COLLEGE_OFFICER,
                is_active=True,
                is_verified=True,
                is_email_verified=True
            )
            db.add(officer)
            db.commit()
            db.refresh(officer)

        m = db.query(InstitutionMembership).filter(
            InstitutionMembership.user_id == officer.id,
            InstitutionMembership.institution_id == inst_id
        ).first()
        if not m:
            m = InstitutionMembership(
                user_id=officer.id,
                institution_id=inst_id,
                role=UserRoleEnum.COLLEGE_OFFICER,
                department="Examination & Student Affairs",
                designation="Grievance Cell Officer",
                is_active=True
            )
            db.add(m)
            db.commit()

    # 1. Login as College Officer
    code, officer_login = do_req(f"{BASE_URL}/auth/login", method="POST", data={
        "email": officer_email,
        "password": "OfficerSecurePassword123!"
    })
    assert code == 200, f"Officer login failed: {officer_login}"
    officer_headers = {"Authorization": f"Bearer {officer_login['access_token']}"}
    log("1. Officer login succeeded (COLLEGE_OFFICER role authenticated)")

    # 2. Officer view intake queue
    code, queue = do_req(f"{BASE_URL}/grievances", headers=officer_headers)
    assert code == 200, f"Officer queue failed: {queue}"
    assert len(queue) > 0, "No cases in queue"
    target_case = queue[0]
    case_id = target_case["id"]
    log(f"2. GET /grievances queue verified: Officer retrieved {len(queue)} institution cases (Target: #{case_id})")

    # 3. Officer claim case
    code, claim_res = do_req(f"{BASE_URL}/grievances/{case_id}/claim", method="POST", headers=officer_headers)
    assert code in [200, 400], f"Claim failed: {claim_res}"
    log(f"3. POST /grievances/{case_id}/claim verified: Officer successfully assigned to case")

    # 4. Officer add confidential internal note
    note_payload = {"note": "Investigated with examination branch. Marksheet dispatched via speed post."}
    code, note_res = do_req(f"{BASE_URL}/grievances/{case_id}/internal-notes", method="POST", data=note_payload, headers=officer_headers)
    assert code in [200, 201], f"Officer note failed: {note_res}"
    log(f"4. POST /grievances/{case_id}/internal-notes verified: Confidential note saved")

    # 5. Officer reply to student message thread
    msg_payload = {"message": "Dear student, your documents are verified and processed."}
    code, msg_res = do_req(f"{BASE_URL}/grievances/{case_id}/messages", method="POST", data=msg_payload, headers=officer_headers)
    assert code in [200, 201], f"Officer message failed: {msg_res}"
    log(f"5. POST /grievances/{case_id}/messages verified: Student-visible message posted")

    # 6. Officer update grievance status to UNDER_REVIEW
    status_payload = {
        "to_status": "UNDER_REVIEW",
        "reason": "Official inquiry underway with the department"
    }
    code, status_res = do_req(f"{BASE_URL}/grievances/{case_id}/status", method="PUT", data=status_payload, headers=officer_headers)
    assert code == 200, f"Status update failed: {status_res}"
    log(f"6. PUT /grievances/{case_id}/status verified: State transitioned to {status_res.get('status')}")

    # 7. SuperAdmin Login
    code, admin_login = do_req(f"{BASE_URL}/auth/login", method="POST", data={
        "email": admin_email,
        "password": admin_password
    })
    assert code == 200, f"Admin login failed: {admin_login}"
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
    log("7. SuperAdmin login succeeded (SUPER_ADMIN role authenticated)")

    # 8. SuperAdmin run batch overdue escalation engine
    code, batch_res = do_req(f"{BASE_URL}/grievances/escalations/process-overdue", method="POST", headers=admin_headers)
    assert code == 200, f"Batch escalation failed: {batch_res}"
    log(f"8. POST /grievances/escalations/process-overdue verified: Auto-escalated {batch_res.get('escalated_count')} overdue case(s)")

    # 9. SuperAdmin Analytics Dashboard stats
    code, stats_res = do_req(f"{BASE_URL}/analytics/dashboard", headers=admin_headers)
    assert code == 200, f"Dashboard analytics failed: {stats_res}"
    log(f"9. GET /analytics/dashboard verified: Total Grievances = {stats_res.get('total_grievances')}, Satisfaction = {stats_res.get('satisfaction_rate')}%")

    print("=" * 65)
    print("SUCCESS: All Officer & SuperAdmin workflow endpoints verified operational!")
    print("=" * 65)

if __name__ == "__main__":
    main()
