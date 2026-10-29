"""
EduResolve AI - Intelligent Case Assignment & Routing Service.
Recommends appropriate redressing officer and department based on category
and institutional membership records.
Never assigns cases to officers outside the grievance's institution.
"""
from typing import Dict, Any, List, Optional

class AssignmentRecommender:
    def recommend(
        self,
        category_name: str,
        institution_officers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggests an authorized institutional officer based on departmental specialization.
        """
        dept_name = category_name or "General Grievance Cell"

        if not institution_officers:
            return {
                "suggested_department": dept_name,
                "suggested_officer_id": None,
                "suggested_officer_name": None,
                "reason": f"No active grievance cell officers currently assigned to this institution. Route to {dept_name} intake desk."
            }

        # Check for officers whose department keywords match the category name
        matched_officer = None
        for officer in institution_officers:
            off_dept = officer.get("department", "").lower()
            if off_dept and any(word in off_dept for word in dept_name.lower().split() if len(word) > 3):
                matched_officer = officer
                break

        # Fallback to the first available active officer
        if not matched_officer:
            matched_officer = institution_officers[0]

        return {
            "suggested_department": matched_officer.get("department") or dept_name,
            "suggested_officer_id": matched_officer.get("user_id"),
            "suggested_officer_name": matched_officer.get("full_name"),
            "reason": f"Recommended based on institutional membership and departmental alignment with '{dept_name}'."
        }

assignment_recommender = AssignmentRecommender()
