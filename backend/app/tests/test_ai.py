import os
import json
import pytest
from unittest.mock import patch

from app.services.ai_service import ai_service
from app.models.category import GrievanceCategory
from app.models.institution import Institution, InstitutionMembership
from app.models.user import User
from app.models.enums import UserRoleEnum, GrievancePriorityEnum, GrievanceStatusEnum
from app.models.grievance import Grievance
from app.models.ai_recommendation import AIRecommendation
from app.schemas.grievance import GrievanceCreate
from app.services.grievance_service import grievance_service
from app.core.security import create_access_token, hash_password

def setup_institution_and_student(db_session):
    """Helper fixture to set up test institution, category, and student."""
    inst = Institution(
        code="AI_TEST_COLLEGE",
        name="AI Evaluation Engineering College",
        state="Delhi",
        city="New Delhi",
        contact_email="ai_test@college.edu",
        is_active=True
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    cat_hostel = GrievanceCategory(code="HOSTEL", name="Hostel & Accommodation", default_sla_days=3, is_active=True)
    cat_exam = GrievanceCategory(code="EXAM", name="Examinations & Results", default_sla_days=5, is_active=True)
    cat_academic = GrievanceCategory(code="ACADEMIC", name="Academics & Teaching", default_sla_days=7, is_active=True)
    cat_finance = GrievanceCategory(code="FINANCE", name="Fees & Finance", default_sla_days=5, is_active=True)
    db_session.add_all([cat_hostel, cat_exam, cat_academic, cat_finance])
    db_session.commit()

    student = User(
        email="ai_student@example.com",
        full_name="AI Test Submitter",
        hashed_password=hash_password("Password123!"),
        default_role=UserRoleEnum.STUDENT,
        is_active=True,
        is_verified=True,
        is_email_verified=True
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    membership = InstitutionMembership(
        user_id=student.id,
        institution_id=inst.id,
        role=UserRoleEnum.STUDENT,
        is_active=True
    )
    db_session.add(membership)
    db_session.commit()

    return inst, student, [cat_hostel, cat_exam, cat_academic, cat_finance]

# 1. Model Artifact Loading
def test_ai_model_artifact_loading():
    status = ai_service.get_readiness_status()
    assert status.is_model_loaded is True
    assert "TF-IDF" in status.classifier_type or "LogisticRegression" in status.classifier_type
    assert status.device == "cpu"
    assert "category_classification" in status.features_active

# 2. Classification of Valid Input
def test_ai_category_classification_valid_input(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    rec = ai_service.recommend_category(
        title="Hostel room washroom leakage",
        description="The pipe in the hostel bathroom is leaking water onto the dormitory floor.",
        db=db_session
    )
    assert rec.category_id is not None
    assert "Hostel" in rec.category_name
    assert rec.confidence > 0.30
    assert rec.model_version is not None

# 3. Correct Category Label Mapping
def test_ai_category_label_mapping(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    rec = ai_service.recommend_category(
        title="Delayed end semester marksheet",
        description="My final semester grade card and marks sheet have not been issued by the examination cell.",
        db=db_session
    )
    assert "Exam" in rec.category_name or "Academic" in rec.category_name
    assert rec.category_id in [c.id for c in cats]

# 4. Empty and Low Confidence Input Handling
def test_ai_empty_and_out_of_distribution_input(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    # Random characters that do not match academic vocabulary
    rec = ai_service.recommend_category(
        title="xyz abc qwe 123",
        description="Random unintelligible string without keywords",
        db=db_session
    )
    assert rec.category_id is not None
    assert rec.is_uncertain is True or rec.is_rule_based is True
    assert rec.confidence <= 0.60

# 5. Priority: Urgent Safety Indicators
def test_ai_priority_urgent_keywords():
    rec = ai_service.recommend_priority(
        title="Physical threat and ragging incident in college premises",
        description="A group of senior students threatened violence and physical abuse near the main gate."
    )
    assert rec.priority == GrievancePriorityEnum.URGENT
    assert "ragging" in rec.urgency_indicators or "violence" in rec.urgency_indicators
    assert rec.confidence >= 0.90
    assert rec.human_review_required is True

# 6. Priority: High Imminent Deadline Indicators
def test_ai_priority_high_deadline_indicators():
    rec = ai_service.recommend_priority(
        title="Admit card withheld before exam tomorrow",
        description="My hall ticket is not appearing on the student portal and the theory exam starts tomorrow morning."
    )
    assert rec.priority == GrievancePriorityEnum.HIGH
    assert rec.confidence >= 0.80
    assert rec.human_review_required is True

# 7. Priority: Standard and Low
def test_ai_priority_standard_and_low():
    rec_low = ai_service.recommend_priority(
        title="Inquiry regarding library timing",
        description="What time does the digital reading room close on Saturdays?"
    )
    assert rec_low.priority in [GrievancePriorityEnum.LOW, GrievancePriorityEnum.NORMAL]

# 8. Priority: Explanation and Advisory Disclaimer
def test_ai_priority_explanation_and_disclaimer():
    rec = ai_service.recommend_priority(
        title="Water dispenser broken",
        description="The drinking water machine on the second floor has no cooling."
    )
    assert "advisory" in rec.explanation.lower() or "triage" in rec.explanation.lower()

# 9. Duplicate Detection: Similar Examples
def test_ai_duplicate_detection_similar_examples(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    # Create an existing grievance in this institution
    g1 = Grievance(
        reference_number="GRV-2026-DUP001",
        student_id=student.id,
        institution_id=inst.id,
        category_id=cats[0].id,
        title="Water leakage in Block B hostel bathroom",
        description="The washroom pipes on second floor Block B hostel are overflowing and leaking water.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL
    )
    db_session.add(g1)
    db_session.commit()

    # Draft a complaint with very similar wording
    dup_res = ai_service.detect_duplicates(
        title="Hostel Block B washroom water pipe leaking",
        description="Water is overflowing and leaking from bathroom pipes on Block B second floor hostel.",
        institution_id=inst.id,
        db=db_session,
        threshold=0.50
    )
    assert dup_res.is_duplicate_suspected is True
    assert dup_res.highest_similarity >= 0.50
    assert len(dup_res.matches) >= 1
    assert dup_res.matches[0].reference_number == "GRV-2026-DUP001"

# 10. Duplicate Detection: Unrelated Examples
def test_ai_duplicate_detection_unrelated_examples(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    g1 = Grievance(
        reference_number="GRV-2026-DUP002",
        student_id=student.id,
        institution_id=inst.id,
        category_id=cats[0].id,
        title="Hostel mess food quality poor",
        description="The evening dinner dal had insects and stale rice was served.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL
    )
    db_session.add(g1)
    db_session.commit()

    # Unrelated draft about tuition fee receipts
    dup_res = ai_service.detect_duplicates(
        title="Tuition fee refund not processed by accounts desk",
        description="I cancelled admission in August but the 80000 rupees tuition deposit refund is delayed.",
        institution_id=inst.id,
        db=db_session,
        threshold=0.50
    )
    assert dup_res.is_duplicate_suspected is False
    assert dup_res.highest_similarity < 0.35

# 11. Duplicate Detection: Strict Institution Isolation
def test_ai_duplicate_detection_institution_isolation(db_session):
    inst1, student, cats = setup_institution_and_student(db_session)
    
    # Second institution
    inst2 = Institution(
        code="INST_SECOND",
        name="Second Autonomous College",
        state="Maharashtra",
        city="Pune",
        contact_email="inst2@college.edu",
        is_active=True
    )
    db_session.add(inst2)
    db_session.commit()

    # Create complaint in Institution 2
    g_other = Grievance(
        reference_number="GRV-2026-INST2-001",
        student_id=student.id,
        institution_id=inst2.id,
        category_id=cats[0].id,
        title="Severe electrical short circuit in physics lab",
        description="Wires burnt out in the electrical laboratory and the main circuit breaker tripped.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.HIGH
    )
    db_session.add(g_other)
    db_session.commit()

    # Now check for duplicates in Institution 1 with the identical wording
    dup_res = ai_service.detect_duplicates(
        title="Severe electrical short circuit in physics lab",
        description="Wires burnt out in the electrical laboratory and the main circuit breaker tripped.",
        institution_id=inst1.id,
        db=db_session
    )
    # Must NOT match grievance from inst2
    assert dup_res.is_duplicate_suspected is False
    assert dup_res.highest_similarity == 0.0
    for match in dup_res.matches:
        assert match.reference_number != "GRV-2026-INST2-001"

# 12. Duplicate Detection: Confidentiality Shielding
def test_ai_duplicate_detection_confidentiality(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    g = Grievance(
        reference_number="GRV-2026-SECRET01",
        student_id=student.id,
        institution_id=inst.id,
        category_id=cats[0].id,
        title="Secret grievance testing confidentiality",
        description="This contains private student narrative and confidential details.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL
    )
    db_session.add(g)
    db_session.commit()

    dup_res = ai_service.detect_duplicates(
        title="Secret grievance testing confidentiality",
        description="Checking if private details leak in response.",
        institution_id=inst.id,
        db=db_session,
        threshold=0.40
    )
    for m in dup_res.matches:
        match_dict = m.model_dump()
        assert "student_email" not in match_dict
        assert "student_name" not in match_dict
        assert "description" not in match_dict

# 13. Assignment Recommendation: Department Alignment
def test_ai_assignment_recommendation_department_alignment(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    
    # Create officer in Hostel department
    officer_user = User(
        email="hostel.warden@college.edu",
        full_name="Dr. Verma (Hostel Warden)",
        hashed_password=hash_password("Pass123!"),
        default_role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True
    )
    db_session.add(officer_user)
    db_session.commit()

    m = InstitutionMembership(
        user_id=officer_user.id,
        institution_id=inst.id,
        role=UserRoleEnum.COLLEGE_OFFICER,
        department="Hostel & Accommodation Administration",
        is_active=True
    )
    db_session.add(m)
    db_session.commit()

    # Find category for Hostel
    hostel_cat = next(c for c in cats if c.code == "HOSTEL")
    route = ai_service.recommend_routing(hostel_cat.id, inst.id, db_session)
    assert route.suggested_officer_id == officer_user.id
    assert "Hostel" in (route.suggested_department or "")

# 14. Assignment Recommendation: Strict Institution Boundary
def test_ai_assignment_recommendation_strict_institution_membership(db_session):
    inst1, student, cats = setup_institution_and_student(db_session)
    
    # Institution 2 with an officer
    inst2 = Institution(code="I2", name="College Two", state="Goa", contact_email="contact@inst2.edu", is_active=True)
    db_session.add(inst2)
    db_session.commit()

    foreign_officer = User(
        email="foreign.officer@other.edu",
        full_name="Prof. External",
        hashed_password=hash_password("Pass123!"),
        default_role=UserRoleEnum.COLLEGE_OFFICER,
        is_active=True
    )
    db_session.add(foreign_officer)
    db_session.commit()

    m2 = InstitutionMembership(
        user_id=foreign_officer.id,
        institution_id=inst2.id,
        role=UserRoleEnum.COLLEGE_OFFICER,
        department="Academics & Teaching",
        is_active=True
    )
    db_session.add(m2)
    db_session.commit()

    # Route request for institution 1 (which has no officer in Academics yet)
    acad_cat = next(c for c in cats if c.code == "ACADEMIC")
    route = ai_service.recommend_routing(acad_cat.id, inst1.id, db_session)
    # Must NOT recommend officer from inst2
    assert route.suggested_officer_id != foreign_officer.id

# 15. AI Health & Readiness Endpoint
def test_ai_health_and_readiness_endpoint(client):
    res = client.get("/api/v1/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["operational", "degraded_fallback"]
    assert "is_model_loaded" in data
    assert "features_active" in data
    assert len(data["features_active"]) == 4

# 16. AI Analyze Endpoint Contract
def test_ai_analyze_endpoint_contract(client, db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    token = create_access_token(subject=student.id, extra_claims={"role": student.default_role.value})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "Semester exam timetable clashing",
        "description": "The examination schedule has two papers on the same morning slot.",
        "institution_id": inst.id,
        "category_id": cats[1].id
    }
    res = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "category" in data
    assert "priority" in data
    assert "duplicate_check" in data
    assert "routing" in data
    assert data["category"]["category_id"] is not None
    assert data["priority"]["priority"] in ["LOW", "NORMAL", "HIGH", "URGENT"]

# 17. AI Recommendation Persistence in MySQL
def test_ai_recommendation_persistence_in_mysql(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    g = Grievance(
        reference_number="GRV-2026-PERSIST01",
        student_id=student.id,
        institution_id=inst.id,
        category_id=cats[0].id,
        title="Hostel room broken window",
        description="Cold draft entering through shattered glass in dormitory.",
        status=GrievanceStatusEnum.SUBMITTED,
        priority=GrievancePriorityEnum.NORMAL
    )
    db_session.add(g)
    db_session.commit()
    db_session.refresh(g)

    cat_rec = ai_service.recommend_category(g.title, g.description, db_session)
    prio_rec = ai_service.recommend_priority(g.title, g.description)

    saved_recs = ai_service.persist_recommendations(g.id, cat_rec, prio_rec, db_session)
    assert len(saved_recs) == 2

    # Query from MySQL
    rows = db_session.query(AIRecommendation).filter(AIRecommendation.grievance_id == g.id).all()
    assert len(rows) == 2
    types = [r.recommendation_type for r in rows]
    assert "CATEGORY" in types
    assert "PRIORITY" in types

# 18. Grievance Creation with AI Enabled
def test_grievance_creation_with_ai_enabled(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    req = GrievanceCreate(
        title="Delay in issuing semester examination marksheet",
        description="The university controller of examinations has not released the third semester scorecards.",
        category_id=cats[1].id,
        institution_id=inst.id
    )
    new_g = grievance_service.create_grievance(req, student, db_session)
    assert new_g.id is not None
    assert new_g.reference_number.startswith("GRV-")
    
    # Confirm AI recommendations persisted in MySQL
    recs = db_session.query(AIRecommendation).filter(AIRecommendation.grievance_id == new_g.id).all()
    assert len(recs) >= 1

# 19. Grievance Creation When AI Service Fails (Graceful Degradation)
def test_grievance_creation_when_ai_fails(db_session):
    inst, student, cats = setup_institution_and_student(db_session)
    req = GrievanceCreate(
        title="Cafeteria hygiene inspection required",
        description="Expired packaged food was found being served in the student canteen.",
        category_id=cats[0].id,
        institution_id=inst.id
    )

    # Simulate AI service throwing an unexpected runtime exception
    with patch.object(ai_service, "recommend_category", side_effect=RuntimeError("AI Model GPU out of memory")):
        with patch.object(ai_service, "recommend_priority", side_effect=RuntimeError("AI Timeout")):
            new_g = grievance_service.create_grievance(req, student, db_session)
            # Grievance creation MUST succeed even when AI completely crashes
            assert new_g.id is not None
            assert new_g.reference_number.startswith("GRV-")
            assert new_g.status == GrievanceStatusEnum.SUBMITTED

# 20. Model Version and Metadata Integrity
def test_model_version_and_metadata():
    metadata_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "ai-service", "artifacts", "model_metadata.json"
    )
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        assert "model_version" in meta
        assert "evaluation_summary" in meta
        assert meta["evaluation_summary"]["test_accuracy"] > 0.0
        assert "known_limitations" in meta
