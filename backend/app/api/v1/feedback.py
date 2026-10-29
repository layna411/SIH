from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.enums import UserRoleEnum, GrievanceStatusEnum
from app.models.grievance import Grievance
from app.models.feedback import GrievanceFeedback
from app.models.user import User
from app.core.permissions import get_current_user
from app.schemas.feedback import FeedbackCreate
from app.schemas.grievance import GrievanceFeedbackResponse
from app.services.audit_service import log_audit

router = APIRouter(prefix="/grievances", tags=["Feedback"])

@router.post("/{id}/feedback", response_model=GrievanceFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    id: int,
    req: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student submits feedback and satisfaction rating after grievance resolution."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if grievance.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the grievance submitter can leave feedback.")

    if grievance.status not in (GrievanceStatusEnum.RESOLVED, GrievanceStatusEnum.CLOSED, GrievanceStatusEnum.RESOLUTION_PROPOSED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted once resolution has been proposed or resolved."
        )

    existing_feedback = db.query(GrievanceFeedback).filter(GrievanceFeedback.grievance_id == id).first()
    if existing_feedback:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback already submitted for this case.")

    feedback = GrievanceFeedback(
        grievance_id=grievance.id,
        student_id=current_user.id,
        rating=req.rating,
        satisfies_resolution=req.satisfies_resolution,
        comments=req.comments
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    log_audit(db, action="SUBMIT_FEEDBACK", entity_type="FEEDBACK", user_id=current_user.id, entity_id=str(feedback.id))

    return GrievanceFeedbackResponse(
        id=feedback.id,
        rating=feedback.rating,
        satisfies_resolution=feedback.satisfies_resolution,
        comments=feedback.comments,
        created_at=feedback.created_at
    )
