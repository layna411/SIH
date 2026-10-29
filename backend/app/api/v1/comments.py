from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.enums import UserRoleEnum
from app.models.grievance import Grievance
from app.models.communication import GrievanceMessage, GrievanceInternalNote
from app.models.user import User
from app.core.permissions import get_current_user, check_grievance_access
from app.schemas.communication import MessageCreate, InternalNoteCreate
from app.schemas.grievance import GrievanceMessageResponse, GrievanceInternalNoteResponse
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit

router = APIRouter(prefix="/grievances", tags=["Messages & Internal Notes"])

@router.post("/{id}/messages", response_model=GrievanceMessageResponse, status_code=status.HTTP_201_CREATED)
def post_message(
    id: int,
    req: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post a communication message visible to student and institution staff."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    new_msg = GrievanceMessage(
        grievance_id=grievance.id,
        sender_id=current_user.id,
        message=req.message.strip(),
        is_student_visible=True
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # Notify recipient
    if current_user.id == grievance.student_id:
        # Student wrote -> notify assigned officer or institution staff
        if grievance.assigned_officer_id:
            create_notification(
                db=db,
                user_id=grievance.assigned_officer_id,
                title="New Student Message",
                message=f"Student replied to grievance #{grievance.reference_number}.",
                link=f"/grievances/{grievance.id}"
            )
    else:
        # Officer wrote -> notify student
        create_notification(
            db=db,
            user_id=grievance.student_id,
            title="New Message on Grievance",
            message=f"New update from Grievance Officer on #{grievance.reference_number}.",
            link=f"/grievances/{grievance.id}"
        )

    log_audit(db, action="POST_MESSAGE", entity_type="GRIEVANCE_MESSAGE", user_id=current_user.id, entity_id=str(new_msg.id))

    return GrievanceMessageResponse(
        id=new_msg.id,
        sender_id=new_msg.sender_id,
        sender_name=current_user.full_name,
        sender_role=current_user.default_role.value,
        message=new_msg.message,
        is_student_visible=new_msg.is_student_visible,
        created_at=new_msg.created_at
    )

@router.post("/{id}/internal-notes", response_model=GrievanceInternalNoteResponse, status_code=status.HTTP_201_CREATED)
def post_internal_note(
    id: int,
    req: InternalNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add confidential internal officer note.
    STRICTLY FORBIDDEN FOR STUDENTS.
    """
    if current_user.default_role == UserRoleEnum.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot post internal officer notes.")

    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db, require_officer_edit=True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to add internal note to this grievance.")

    note = GrievanceInternalNote(
        grievance_id=grievance.id,
        author_id=current_user.id,
        note=req.note.strip()
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    log_audit(db, action="POST_INTERNAL_NOTE", entity_type="INTERNAL_NOTE", user_id=current_user.id, entity_id=str(note.id))

    return GrievanceInternalNoteResponse(
        id=note.id,
        author_id=note.author_id,
        author_name=current_user.full_name,
        note=note.note,
        created_at=note.created_at
    )

@router.get("/{id}/messages", response_model=list[GrievanceMessageResponse])
def list_messages(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve communication messages for a grievance case."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    is_student = current_user.default_role == UserRoleEnum.STUDENT
    messages = grievance.messages
    if is_student:
        messages = [m for m in messages if m.is_student_visible]

    return [
        GrievanceMessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            sender_name=m.sender.full_name if m.sender else "User",
            sender_role=m.sender.default_role.value if m.sender else "MEMBER",
            message=m.message,
            is_student_visible=m.is_student_visible,
            created_at=m.created_at
        )
        for m in messages
    ]

@router.get("/{id}/internal-notes", response_model=list[GrievanceInternalNoteResponse])
def list_internal_notes(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve confidential internal notes for a grievance.
    STRICTLY FORBIDDEN FOR STUDENTS.
    """
    if current_user.default_role == UserRoleEnum.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: students cannot access internal officer notes."
        )

    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db, require_officer_edit=True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to view internal notes.")

    return [
        GrievanceInternalNoteResponse(
            id=n.id,
            author_id=n.author_id,
            author_name=n.author.full_name if n.author else "Officer",
            note=n.note,
            created_at=n.created_at
        )
        for n in grievance.internal_notes
    ]
