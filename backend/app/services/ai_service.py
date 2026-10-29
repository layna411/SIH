import os
import sys
import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

# Ensure ai-service package is accessible on sys.path
ai_service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai-service"))
if ai_service_root not in sys.path:
    sys.path.insert(0, ai_service_root)

from classifiers.category_classifier import classifier_service
from prioritization.priority_recommender import priority_recommender
from similarity.duplicate_detector import duplicate_detector
from routing.assignment_recommender import assignment_recommender

from app.models.enums import GrievancePriorityEnum, UserRoleEnum
from app.models.category import GrievanceCategory
from app.models.grievance import Grievance
from app.models.institution import InstitutionMembership
from app.models.ai_recommendation import AIRecommendation
from app.schemas.ai import (
    AICategoryRecommendation,
    AIPriorityRecommendation,
    AIDuplicateCheckResponse,
    AIDuplicateMatch,
    AIRoutingRecommendation,
    AIHealthResponse
)

logger = logging.getLogger("eduresolve.ai.service")

class AIService:
    """
    Unified AI service layer connecting FastAPI routers to modular AI components.
    Safely coordinates text classification, explainable priority triage,
    multi-tenant duplicate detection, and case routing.
    """

    def __init__(self):
        self.classifier = classifier_service
        self.prioritizer = priority_recommender
        self.duplicates = duplicate_detector
        self.router = assignment_recommender

    def recommend_category(self, title: str, description: str, db: Session) -> AICategoryRecommendation:
        """
        Predict grievance category using trained ML pipeline or rule-based fallback.
        """
        # Load active database categories
        active_cats = db.query(GrievanceCategory).filter(GrievanceCategory.is_active == True).all()
        cat_dicts = [{"id": c.id, "code": c.code, "name": c.name} for c in active_cats]

        pred = self.classifier.predict(title, description, active_categories=cat_dicts)

        return AICategoryRecommendation(
            category_id=pred["category_id"],
            category_name=pred["category_name"],
            category_code=pred.get("category_code"),
            confidence=pred["confidence"],
            explanation=pred["explanation"],
            is_rule_based=pred["is_rule_based"],
            is_uncertain=pred.get("is_uncertain", False),
            model_version=pred["model_version"]
        )

    def recommend_priority(self, title: str, description: str) -> AIPriorityRecommendation:
        """
        Evaluate urgency and sensitivity indicators to recommend a priority level.
        """
        res = self.prioritizer.evaluate(title, description)
        prio_enum = GrievancePriorityEnum(res["priority"])

        return AIPriorityRecommendation(
            priority=prio_enum,
            confidence=res["confidence"],
            urgency_indicators=res.get("urgency_indicators", []),
            explanation=res["explanation"],
            is_rule_based=res["is_rule_based"],
            model_version=res.get("model_version", "EduResolve-TriagePriority-v1.2"),
            human_review_required=res.get("human_review_required", False)
        )

    def detect_duplicates(
        self,
        title: str,
        description: str,
        institution_id: int,
        db: Session,
        exclude_grievance_id: Optional[int] = None,
        threshold: float = 0.60
    ) -> AIDuplicateCheckResponse:
        """
        Perform privacy-preserving duplicate detection strictly scoped to the same institution.
        Never leaks personal student info.
        """
        query = db.query(Grievance).filter(Grievance.institution_id == institution_id)
        if exclude_grievance_id:
            query = query.filter(Grievance.id != exclude_grievance_id)

        # Retrieve up to 100 recent complaints in this college
        candidates = query.order_by(Grievance.created_at.desc()).limit(100).all()
        cand_dicts = [
            {
                "id": g.id,
                "reference_number": g.reference_number,
                "title": g.title,
                "description": g.description,
                "status": g.status.value
            }
            for g in candidates
        ]

        dup_res = self.duplicates.find_similar_in_institution(
            new_title=title,
            new_description=description,
            existing_grievances=cand_dicts,
            threshold=threshold
        )

        matches = [
            AIDuplicateMatch(
                reference_number=m["reference_number"],
                title=m["title"],
                similarity_score=m["similarity_score"],
                status=m["status"]
            )
            for m in dup_res["matches"]
        ]

        return AIDuplicateCheckResponse(
            is_duplicate_suspected=dup_res["is_duplicate_suspected"],
            highest_similarity=dup_res["highest_similarity"],
            matches=matches,
            explanation=dup_res["explanation"]
        )

    def recommend_routing(
        self,
        category_id: int,
        institution_id: int,
        db: Session
    ) -> AIRoutingRecommendation:
        """
        Suggest departmental assignment and officer based on institution membership.
        """
        category = db.query(GrievanceCategory).filter(GrievanceCategory.id == category_id).first()
        dept_name = category.name if category else "General Grievance Cell"

        # Query active officers of this institution
        officer_memberships = db.query(InstitutionMembership).filter(
            InstitutionMembership.institution_id == institution_id,
            InstitutionMembership.role == UserRoleEnum.COLLEGE_OFFICER,
            InstitutionMembership.is_active == True
        ).all()

        officer_dicts = [
            {
                "user_id": m.user_id,
                "full_name": m.user.full_name if m.user else None,
                "department": m.department or ""
            }
            for m in officer_memberships
        ]

        route_res = self.router.recommend(dept_name, officer_dicts)

        return AIRoutingRecommendation(
            suggested_department=route_res.get("suggested_department"),
            suggested_officer_id=route_res.get("suggested_officer_id"),
            suggested_officer_name=route_res.get("suggested_officer_name"),
            reason=route_res.get("reason", "Standard departmental routing.")
        )

    def persist_recommendations(
        self,
        grievance_id: int,
        category_rec: Optional[AICategoryRecommendation],
        priority_rec: Optional[AIPriorityRecommendation],
        db: Session
    ) -> List[AIRecommendation]:
        """
        Persist AI suggestions into the ai_recommendations table.
        Recommendations are kept strictly separate from authoritative decisions.
        """
        saved = []
        try:
            if category_rec:
                rec_cat = AIRecommendation(
                    grievance_id=grievance_id,
                    recommendation_type="CATEGORY",
                    model_version=category_rec.model_version,
                    confidence=category_rec.confidence,
                    explanation=category_rec.explanation,
                    suggested_payload=json.dumps({
                        "category_id": category_rec.category_id,
                        "category_name": category_rec.category_name,
                        "category_code": category_rec.category_code,
                        "is_rule_based": category_rec.is_rule_based,
                        "is_uncertain": category_rec.is_uncertain
                    })
                )
                db.add(rec_cat)
                saved.append(rec_cat)

            if priority_rec:
                rec_prio = AIRecommendation(
                    grievance_id=grievance_id,
                    recommendation_type="PRIORITY",
                    model_version=priority_rec.model_version or "EduResolve-TriagePriority-v1.2",
                    confidence=priority_rec.confidence,
                    explanation=priority_rec.explanation,
                    suggested_payload=json.dumps({
                        "priority": priority_rec.priority.value,
                        "urgency_indicators": priority_rec.urgency_indicators,
                        "is_rule_based": priority_rec.is_rule_based,
                        "human_review_required": priority_rec.human_review_required
                    })
                )
                db.add(rec_prio)
                saved.append(rec_prio)

            db.commit()
            for r in saved:
                db.refresh(r)
            logger.info("Persisted %d AI recommendation records for grievance #%d", len(saved), grievance_id)
        except Exception as e:
            logger.warning("Failed persisting AI recommendations for grievance #%d: %s", grievance_id, e)
            db.rollback()

        return saved

    def get_readiness_status(self) -> AIHealthResponse:
        """
        Report AI service availability and operational readiness.
        """
        is_loaded = self.classifier.is_loaded
        return AIHealthResponse(
            status="operational" if is_loaded else "degraded_fallback",
            is_model_loaded=is_loaded,
            model_version=self.classifier.model_version if is_loaded else "EduResolve-Heuristic-Fallback-v1.0",
            classifier_type="TF-IDF + LogisticRegression" if is_loaded else "Domain Keyword Heuristic",
            features_active=[
                "category_classification",
                "priority_triage",
                "duplicate_detection",
                "departmental_routing"
            ],
            device="cpu",
            dataset_provenance="Curated developmental academic grievance dataset (150 examples)"
        )

ai_service = AIService()
