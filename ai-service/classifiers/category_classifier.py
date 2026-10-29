"""
EduResolve AI - Category Classification Inference Engine.
Loads the serialized Scikit-learn TF-IDF + LogisticRegression artifact and performs
calibrated multi-class inference.
Falls back transparently to domain heuristic weighting if artifact is uninitialized.
"""
import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import joblib

logger = logging.getLogger("eduresolve.ai.classifier")

MODEL_VERSION = "EduResolve-TFIDF-LogReg-v1.0"
FALLBACK_VERSION = "EduResolve-Heuristic-Fallback-v1.0"

# Default candidate locations for model artifact
ARTIFACT_LOCATIONS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "category_classifier.joblib"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "app", "services", "models", "category_classifier.joblib"),
    os.path.join(os.getcwd(), "ai-service", "artifacts", "category_classifier.joblib")
]

# Robust domain keyword fallback map
CATEGORY_KEYWORD_FALLBACK = {
    "ACADEMIC": ["grade", "marks", "professor", "teacher", "lecture", "syllabus", "attendance", "course", "assignment", "faculty", "curriculum", "class", "cgpa"],
    "EXAM": ["exam", "hall ticket", "re-evaluation", "admit card", "results", "scorecard", "semester", "supplementary", "test", "practical", "viva"],
    "FINANCE": ["fee", "fees", "refund", "receipt", "payment", "tuition", "fine", "overcharge", "dues", "deposit", "caution deposit"],
    "SCHOLARSHIP": ["scholarship", "financial aid", "stipend", "grant", "fellowship", "concession", "merit", "nsp", "jrf", "gate"],
    "HOSTEL": ["hostel", "room", "mess", "food", "warden", "water", "electricity", "dormitory", "bed", "curfew", "hygiene", "cooler"],
    "INFRA": ["lab", "laboratory", "computer", "wifi", "internet", "library", "washroom", "toilet", "projector", "bench", "ac", "classroom", "bus"],
    "ADMIN": ["id card", "certificate", "bonafide", "transcript", "admission", "migration", "leaving certificate", "registrar", "clerk", "counter"],
    "CONDUCT": ["harassment", "ragging", "bully", "abuse", "discrimination", "caste", "gender", "threat", "misconduct", "assault", "violence", "stalking"],
    "SUPPORT": ["disability", "counseling", "mental health", "wheelchair", "ramp", "special needs", "accessibility", "medical", "pwd", "scribe"],
    "OTHER": ["lost and found", "parking", "waste", "atm", "courier", "postal", "canteen", "stray", "noise"]
}

class GrievanceCategoryClassifier:
    _instance: Optional["GrievanceCategoryClassifier"] = None

    def __init__(self):
        self.model = None
        self.model_version = MODEL_VERSION
        self.is_loaded = False
        self.load_model()

    @classmethod
    def get_instance(cls) -> "GrievanceCategoryClassifier":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self) -> bool:
        """Attempt to load serialized model artifact once per process."""
        for path in ARTIFACT_LOCATIONS:
            if os.path.exists(path):
                try:
                    self.model = joblib.load(path)
                    self.is_loaded = True
                    logger.info("Category Classifier model loaded successfully from %s", path)
                    return True
                except Exception as e:
                    logger.warning("Failed loading category model from %s: %s", path, e)
        
        logger.info("Category model artifact not found. Using transparent heuristic fallback.")
        self.is_loaded = False
        return False

    def _match_category(self, code: str, active_categories: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        if not active_categories:
            return None
        code_upper = code.upper()
        for c in active_categories:
            if c.get("code", "").upper() == code_upper:
                return c
        for c in active_categories:
            c_code = c.get("code", "").upper()
            if code_upper in c_code or c_code in code_upper:
                return c
            c_name = c.get("name", "").upper()
            if code_upper in c_name:
                return c
        for c in active_categories:
            if "OTHER" in c.get("code", "").upper() or "GENERAL" in c.get("code", "").upper():
                return c
        return active_categories[0]

    def predict(
        self,
        title: str,
        description: str,
        active_categories: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Predict category using trained ML pipeline when available,
        falling back gracefully to domain heuristic weighting.
        """
        combined = f"{title.strip()} {description.strip()}".lower()

        # 1. Real ML Model Inference
        if self.is_loaded and self.model is not None:
            try:
                # Predict class probabilities
                probs = self.model.predict_proba([combined])[0]
                classes = self.model.classes_
                best_idx = probs.argmax()
                predicted_code = classes[best_idx].upper()
                confidence = float(probs[best_idx])

                is_uncertain = confidence < 0.35
                explanation = f"ML model categorized as '{predicted_code}' with calibrated probability {confidence * 100:.1f}%."
                if is_uncertain:
                    explanation += " High classification entropy; recommended for human verification."

                target_cat = self._match_category(predicted_code, active_categories)
                category_id = target_cat["id"] if target_cat else None
                category_name = target_cat["name"] if target_cat else predicted_code

                return {
                    "category_id": category_id,
                    "category_code": predicted_code,
                    "category_name": category_name,
                    "confidence": round(confidence, 3),
                    "explanation": explanation,
                    "is_rule_based": False,
                    "is_uncertain": is_uncertain,
                    "model_version": self.model_version
                }
            except Exception as e:
                logger.warning("ML inference failed; falling back to heuristic: %s", e)

        # 2. Transparent Domain Rule-Based Fallback
        best_code = "OTHER"
        max_score = 0.0
        match_kw = ""

        for code, keywords in CATEGORY_KEYWORD_FALLBACK.items():
            score = 0.0
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                    score += 1.5
                    if not match_kw:
                        match_kw = kw
            
            # Check if category name words match
            if code.lower() in combined:
                score += 2.0

            if score > max_score:
                max_score = score
                best_code = code

        if max_score > 0:
            confidence = min(0.85, 0.45 + (max_score * 0.08))
            explanation = f"Domain pattern match on keywords related to '{best_code}' (Matched: '{match_kw}')."
            is_rule_based = True
        else:
            confidence = 0.30
            best_code = "OTHER"
            explanation = "No distinct domain pattern identified. Requires human intake officer review."
            is_rule_based = True

        target_cat = self._match_category(best_code, active_categories)
        category_id = target_cat["id"] if target_cat else None
        category_name = target_cat["name"] if target_cat else best_code

        return {
            "category_id": category_id,
            "category_code": best_code,
            "category_name": category_name,
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "is_rule_based": is_rule_based,
            "is_uncertain": confidence < 0.45,
            "model_version": FALLBACK_VERSION
        }

classifier_service = GrievanceCategoryClassifier.get_instance()
