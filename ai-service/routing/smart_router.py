"""
EduResolve AI - Intelligent Routing Engine
Recommends department and officer assignments based on institutional organizational structure.
"""
from typing import Dict, Any, List, Optional

class SmartRouter:
    def suggest_assignment(self, category_code: str, officers: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not officers:
            return {
                "suggested_officer_id": None,
                "suggested_department": "General Grievance Cell",
                "notes": "No active officers registered for this institution."
            }

        cat_upper = category_code.upper()
        for officer in officers:
            dept = officer.get("department", "").upper()
            if cat_upper in dept or any(token in dept for token in cat_upper.split("_")):
                return {
                    "suggested_officer_id": officer["user_id"],
                    "suggested_officer_name": officer.get("full_name"),
                    "suggested_department": officer.get("department"),
                    "notes": f"Officer matched based on department specialty '{officer.get('department')}'."
                }

        # Fallback to first officer
        first = officers[0]
        return {
            "suggested_officer_id": first["user_id"],
            "suggested_officer_name": first.get("full_name"),
            "suggested_department": first.get("department", "Intake Cell"),
            "notes": "Default institutional grievance intake routing."
        }
