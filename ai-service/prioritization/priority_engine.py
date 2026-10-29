"""
EduResolve AI - Priority Scoring Engine
Identifies safety threats, emergency conditions, and time-critical academic deadlines.
"""
import re
from typing import Dict, Any, List

class PriorityEngine:
    def __init__(self):
        self.urgent_keywords = [
            "ragging", "harassment", "suicide", "threat", "physical abuse", 
            "violence", "assault", "safety danger", "police"
        ]
        self.high_keywords = [
            "deadline", "admit card missing", "exam tomorrow", "re-evaluation", 
            "duplicate fee deduction", "water supply cutoff"
        ]

    def evaluate_priority(self, title: str, description: str) -> Dict[str, Any]:
        text = f"{title} {description}".lower()
        urgent_matches = [w for w in self.urgent_keywords if re.search(r'\b' + re.escape(w) + r'\b', text)]
        high_matches = [w for w in self.high_keywords if re.search(r'\b' + re.escape(w) + r'\b', text)]

        if urgent_matches:
            return {
                "priority": "URGENT",
                "confidence": 0.95,
                "urgency_triggers": urgent_matches,
                "rationale": "High-risk safety or anti-ragging flags identified."
            }
        elif high_matches:
            return {
                "priority": "HIGH",
                "confidence": 0.85,
                "urgency_triggers": high_matches,
                "rationale": "Time-sensitive academic or financial deadline keywords found."
            }
        elif len(text.split()) > 60:
            return {
                "priority": "NORMAL",
                "confidence": 0.75,
                "urgency_triggers": [],
                "rationale": "Standard institutional operational complaint."
            }
        else:
            return {
                "priority": "LOW",
                "confidence": 0.70,
                "urgency_triggers": [],
                "rationale": "General inquiry or low-impact feedback."
            }
