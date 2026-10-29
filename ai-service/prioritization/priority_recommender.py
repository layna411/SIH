"""
EduResolve AI - Explainable Priority Recommendation Service.
Evaluates urgency, immediate harm, safety risks, and time-critical operational deadlines.
Advisory triage tool only: Does not establish guilt or make definitive findings of fact.
"""
import re
from typing import Dict, Any, List

PRIORITY_ENGINE_VERSION = "EduResolve-TriagePriority-v1.2"

URGENT_INDICATORS = [
    "ragging", "harassment", "sexual harassment", "suicide", "self harm", 
    "death threat", "physical abuse", "assault", "violence", "weapon", 
    "extortion", "blackmail", "police", "stalking", "emergency", "danger"
]

HIGH_DEADLINE_INDICATORS = [
    "exam tomorrow", "examination tomorrow", "hall ticket missing", "admit card withheld",
    "debarred", "expulsion", "deadline today", "deadline tomorrow", "last date",
    "forfeiture", "food poisoning", "contaminated water", "gas leak", "chemical leak"
]

class PriorityRecommender:
    def __init__(self, version: str = PRIORITY_ENGINE_VERSION):
        self.version = version

    def evaluate(self, title: str, description: str) -> Dict[str, Any]:
        """
        Evaluate grievance title and narrative for triage urgency.
        """
        combined = f"{title.strip()} {description.strip()}".lower()

        urgent_found = [
            w for w in URGENT_INDICATORS 
            if re.search(r'\b' + re.escape(w) + r'\b', combined)
        ]

        high_found = [
            w for w in HIGH_DEADLINE_INDICATORS 
            if re.search(r'\b' + re.escape(w) + r'\b', combined)
        ]

        disclaimer = "Triage recommendation is an operational advisory; final priority requires human officer confirmation."

        if urgent_found:
            return {
                "priority": "URGENT",
                "confidence": 0.95,
                "urgency_indicators": urgent_found,
                "explanation": f"Critical safety, anti-ragging, or personal protection indicator(s) identified: {', '.join(urgent_found)}. {disclaimer}",
                "is_rule_based": True,
                "model_version": self.version,
                "human_review_required": True
            }
        
        if high_found:
            return {
                "priority": "HIGH",
                "confidence": 0.85,
                "urgency_indicators": high_found,
                "explanation": f"Imminent academic deadline or health/safety risk indicator(s) identified: {', '.join(high_found)}. {disclaimer}",
                "is_rule_based": True,
                "model_version": self.version,
                "human_review_required": True
            }

        word_count = len(combined.split())
        if word_count > 70:
            return {
                "priority": "NORMAL",
                "confidence": 0.75,
                "urgency_indicators": [],
                "explanation": f"Standard operational institutional grievance with detailed documentation. {disclaimer}",
                "is_rule_based": True,
                "model_version": self.version,
                "human_review_required": False
            }

        return {
            "priority": "LOW",
            "confidence": 0.70,
            "urgency_indicators": [],
            "explanation": f"Routine inquiry or low-impact institutional feedback. {disclaimer}",
            "is_rule_based": True,
            "model_version": self.version,
            "human_review_required": False
        }

priority_recommender = PriorityRecommender()
