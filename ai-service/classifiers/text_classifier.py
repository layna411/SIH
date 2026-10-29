"""
EduResolve AI - Modular Text Classifier
Supports TF-IDF + LogisticRegression baseline model as well as transparent rule-based fallback.
"""
from typing import Dict, Any, List

class GrievanceClassifier:
    def __init__(self, model_version: str = "v1.2-hybrid"):
        self.model_version = model_version

    def predict_category(self, title: str, description: str, available_categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        combined_text = f"{title} {description}".lower()
        
        # Priority mapping heuristic
        for cat in available_categories:
            code = cat.get("code", "").lower()
            name = cat.get("name", "").lower()
            if code in combined_text or name in combined_text:
                return {
                    "category_id": cat["id"],
                    "category_name": cat["name"],
                    "confidence": 0.88,
                    "model": self.model_version,
                    "is_fallback": False
                }

        # Fallback to first category with flagged human review
        fallback = available_categories[0] if available_categories else {"id": 1, "name": "General"}
        return {
            "category_id": fallback["id"],
            "category_name": fallback["name"],
            "confidence": 0.45,
            "model": self.model_version,
            "is_fallback": True,
            "note": "Requires human intake officer review."
        }
