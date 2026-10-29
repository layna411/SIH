import re
import json
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.enums import (
    UserRoleEnum,
    AICTEOverlapTypeEnum,
    AICTEOverlapReviewStatusEnum,
    AICTEDetectionMethodEnum,
    AICTECaseLinkTypeEnum,
)
from app.models.user import User
from app.models.institution import Institution, InstitutionAlias
from app.models.aicte_case import AICTECase
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.core.permissions import check_bureau_access, get_user_bureau_unit_ids

# Stopwords for lightweight, deterministic tokenization
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", 
    "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", 
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", 
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", 
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", 
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", 
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text removing punctuation and common stopwords."""
    if not text:
        return []
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]

def _jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Deterministic Jaccard similarity between two token sets."""
    set_a, set_b = set(tokens_a), set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return round(intersection / union, 3)

def _cosine_token_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Deterministic term-frequency cosine similarity between token lists."""
    if not tokens_a or not tokens_b:
        return 0.0
    freq_a: Dict[str, int] = {}
    freq_b: Dict[str, int] = {}
    for t in tokens_a:
        freq_a[t] = freq_a.get(t, 0) + 1
    for t in tokens_b:
        freq_b[t] = freq_b.get(t, 0) + 1

    all_tokens = set(freq_a.keys()).union(set(freq_b.keys()))
    dot_product = sum(freq_a.get(t, 0) * freq_b.get(t, 0) for t in all_tokens)
    norm_a = math.sqrt(sum(v ** 2 for v in freq_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in freq_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(dot_product / (norm_a * norm_b), 3)


class AICTEOverlapService:
    """
    Deterministic, explainable cross-bureau overlap detection & case linking engine.
    - Identifies candidate overlaps across bureaus regarding the same technical education institution.
    - Evaluates multiple independent explainable signals (PID, institution, category, subject, description, ref numbers).
    - Guarantees canonical pair ordering (case_id_low < case_id_high).
    - Preserves human review decisions during re-detection cycles (idempotent).
    - Enforces cross-bureau confidentiality and shielding of raw descriptions.
    """

    @staticmethod
    def detect_overlaps_for_case(case_id: int, db: Session, current_user: Optional[User] = None) -> List[AICTECaseOverlap]:
        """
        Run bounded overlap detection for a given target AICTE case.
        Generates or updates candidate overlaps against eligible cases of the same institution/PID.
        """
        target_case = db.query(AICTECase).filter(AICTECase.id == case_id).first()
        if not target_case:
            return []

        # Find candidate comparison cases bounded by institutional identity:
        # 1. Exact same institution_id
        # 2. Or same verified AICTE Permanent ID (if present)
        # 3. Or related via verified aliases
        inst = target_case.institution
        eligible_institution_ids = {target_case.institution_id}

        if inst and inst.aicte_permanent_id and inst.is_aicte_verified:
            same_pid_insts = db.query(Institution.id).filter(
                Institution.aicte_permanent_id == inst.aicte_permanent_id,
                Institution.is_aicte_verified == True
            ).all()
            for (pid_id,) in same_pid_insts:
                eligible_institution_ids.add(pid_id)

        # Query candidates excluding the target case itself
        candidates = db.query(AICTECase).filter(
            AICTECase.institution_id.in_(list(eligible_institution_ids)),
            AICTECase.id != target_case.id
        ).all()

        detected_overlaps: List[AICTECaseOverlap] = []

        for candidate in candidates:
            overlap = AICTEOverlapService._evaluate_pair(target_case, candidate, db, current_user)
            if overlap:
                detected_overlaps.append(overlap)

        db.commit()
        return detected_overlaps

    @staticmethod
    def _evaluate_pair(
        case_a: AICTECase, 
        case_b: AICTECase, 
        db: Session, 
        current_user: Optional[User] = None
    ) -> Optional[AICTECaseOverlap]:
        """Evaluate matching signals between two cases and upsert an AICTECaseOverlap candidate."""
        if case_a.id == case_b.id:
            return None

        # Canonical pair order
        case_low = case_a if case_a.id < case_b.id else case_b
        case_high = case_b if case_a.id < case_b.id else case_a
        low_id = case_low.id
        high_id = case_high.id

        # 1. Evaluate independent explainable signals
        same_inst = (case_low.institution_id == case_high.institution_id)
        same_verified_pid = bool(
            case_low.institution and case_high.institution and
            case_low.institution.aicte_permanent_id and case_high.institution.aicte_permanent_id and
            case_low.institution.aicte_permanent_id == case_high.institution.aicte_permanent_id and
            case_low.institution.is_aicte_verified and case_high.institution.is_aicte_verified
        )
        cross_bureau = (case_low.current_unit_id != case_high.current_unit_id)
        category_match = (case_low.category.strip().lower() == case_high.category.strip().lower())

        official_ref_match = bool(
            case_low.official_reference_number and case_high.official_reference_number and
            case_low.official_reference_number.strip().lower() == case_high.official_reference_number.strip().lower()
        )

        temporal_proximity_days = abs((case_low.received_at - case_high.received_at).days)

        # Subject similarity (Jaccard + Cosine)
        subj_tokens_low = _tokenize(case_low.subject)
        subj_tokens_high = _tokenize(case_high.subject)
        subject_jaccard = _jaccard_similarity(subj_tokens_low, subj_tokens_high)
        subject_cosine = _cosine_token_similarity(subj_tokens_low, subj_tokens_high)
        subject_similarity = round((subject_jaccard * 0.4) + (subject_cosine * 0.6), 3)

        # Description similarity
        desc_tokens_low = _tokenize(case_low.description)
        desc_tokens_high = _tokenize(case_high.description)
        description_cosine = _cosine_token_similarity(desc_tokens_low, desc_tokens_high)

        # Shared key allegation terms
        shared_keywords = list(set(subj_tokens_low + desc_tokens_low).intersection(set(subj_tokens_high + desc_tokens_high)))[:10]

        # 2. Match Score Calculation (bounded 0.0 to 1.0)
        # Weights: Subject (0.45), Description (0.35), Category (0.10), Official Ref (0.10)
        base_score = (
            (subject_similarity * 0.45) +
            (description_cosine * 0.35) +
            (0.10 if category_match else 0.0) +
            (0.10 if official_ref_match else 0.0)
        )
        match_score = round(min(1.0, base_score), 3)

        # 3. Explainable Candidate Classification
        # IMPORTANT RULE: Institution identity alone is NEVER sufficient to mark duplicate!
        is_potential_duplicate = False
        is_related_case = False

        if (
            (subject_similarity >= 0.70 and description_cosine >= 0.50) or
            (official_ref_match and (subject_similarity >= 0.35 or category_match)) or
            (category_match and subject_similarity >= 0.75)
        ):
            is_potential_duplicate = True
            overlap_type = AICTEOverlapTypeEnum.POTENTIAL_DUPLICATE
        elif (
            (same_inst or same_verified_pid) and
            (category_match or subject_similarity >= 0.30 or description_cosine >= 0.30 or cross_bureau) and
            match_score >= 0.20
        ):
            is_related_case = True
            overlap_type = AICTEOverlapTypeEnum.RELATED_CASE
        else:
            # Low confidence; do not create unnecessary candidate
            return None

        # Build explainable matching reasons dict
        match_reasons_dict = {
            "same_institution": same_inst,
            "same_verified_pid": same_verified_pid,
            "cross_bureau": cross_bureau,
            "unit_low_code": case_low.current_unit.code if case_low.current_unit else None,
            "unit_high_code": case_high.current_unit.code if case_high.current_unit else None,
            "category_match": category_match,
            "category_low": case_low.category,
            "category_high": case_high.category,
            "official_ref_match": official_ref_match,
            "subject_similarity": subject_similarity,
            "description_similarity": description_cosine,
            "temporal_proximity_days": temporal_proximity_days,
            "shared_keywords": shared_keywords,
            "explanation": (
                "Multiple matching signals suggest potential duplicate complaint filed across bureaus."
                if is_potential_duplicate else
                "Independent matters concerning the same institution with topical or category overlap."
            )
        }
        match_reasons_json = json.dumps(match_reasons_dict)

        # 4. Upsert with Human Decision Preservation
        existing_overlap = db.query(AICTECaseOverlap).filter(
            AICTECaseOverlap.case_id_low == low_id,
            AICTECaseOverlap.case_id_high == high_id
        ).first()

        if existing_overlap:
            # If already reviewed by a human (CONFIRMED, REJECTED, DEFERRED), DO NOT alter review_status!
            if existing_overlap.review_status != AICTEOverlapReviewStatusEnum.PENDING:
                # Update match score and reasons metadata without overwriting human decision
                existing_overlap.match_score = match_score
                existing_overlap.match_reasons = match_reasons_json
                existing_overlap.updated_at = datetime.now(timezone.utc)
                return existing_overlap

            # If still pending review, refresh classification and score
            existing_overlap.overlap_type = overlap_type
            existing_overlap.match_score = match_score
            existing_overlap.match_reasons = match_reasons_json
            existing_overlap.detection_method = AICTEDetectionMethodEnum.RULE_BASED
            existing_overlap.updated_at = datetime.now(timezone.utc)
            return existing_overlap

        # Create new candidate
        new_overlap = AICTECaseOverlap(
            case_id_low=low_id,
            case_id_high=high_id,
            overlap_type=overlap_type,
            match_score=match_score,
            match_reasons=match_reasons_json,
            detection_method=AICTEDetectionMethodEnum.RULE_BASED,
            review_status=AICTEOverlapReviewStatusEnum.PENDING,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(new_overlap)
        db.flush()

        # Audit log candidate detection
        actor_id = current_user.id if current_user else case_low.created_by_user_id
        AuditLog(
            user_id=actor_id,
            action="AICTE_OVERLAP_DETECTED",
            entity_type="AICTE_OVERLAP",
            entity_id=str(new_overlap.id),
            details=json.dumps({
                "case_id_low": low_id,
                "case_id_high": high_id,
                "overlap_type": overlap_type.value,
                "match_score": match_score,
                "cross_bureau": cross_bureau
            })
        )
        return new_overlap

    @staticmethod
    def mask_case_summary(case: AICTECase, user: User, db: Session) -> Dict[str, Any]:
        """
        Produce an access-safe representation of an AICTE case for overlap views.
        If user lacks authorization to the case's Bureau, sensitive fields
        (raw description, complainant contact info, internal notes) are strictly shielded.
        """
        has_access = check_bureau_access(user, case.current_unit_id, db)

        data = {
            "id": case.id,
            "case_reference": case.case_reference,
            "official_reference_number": case.official_reference_number,
            "institution_id": case.institution_id,
            "institution_name": case.institution.name if case.institution else None,
            "institution_code": case.institution.code if case.institution else None,
            "aicte_permanent_id": case.institution.aicte_permanent_id if case.institution else None,
            "current_unit_id": case.current_unit_id,
            "current_unit_code": case.current_unit.code if case.current_unit else None,
            "current_unit_name": case.current_unit.name if case.current_unit else None,
            "category": case.category,
            "subject": case.subject,
            "status": case.status.value if hasattr(case.status, 'value') else case.status,
            "priority": case.priority.value if hasattr(case.priority, 'value') else case.priority,
            "received_at": case.received_at.isoformat() if case.received_at else None,
            "last_action_at": case.last_action_at.isoformat() if case.last_action_at else None,
            "complainant_type": case.complainant_type.value if hasattr(case.complainant_type, 'value') else case.complainant_type,
            "has_full_access": has_access,
        }

        if has_access:
            data["description"] = case.description
            data["complainant_name"] = case.complainant_name
            data["complainant_email"] = case.complainant_email
            data["complainant_phone"] = case.complainant_phone
            data["assigned_officer_name"] = case.assigned_officer.full_name if case.assigned_officer else None
            data["next_action_required"] = case.next_action_required
            data["next_action_due_at"] = case.next_action_due_at.isoformat() if case.next_action_due_at else None
        else:
            data["description"] = "[CONFIDENTIAL: Case description protected under AICTE cross-bureau confidentiality controls]"
            data["complainant_name"] = "[PROTECTED]"
            data["complainant_email"] = None
            data["complainant_phone"] = None
            data["assigned_officer_name"] = None
            data["next_action_required"] = None
            data["next_action_due_at"] = None

        return data
