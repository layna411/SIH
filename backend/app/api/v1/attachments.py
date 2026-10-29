import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.enums import UserRoleEnum
from app.models.grievance import Grievance
from app.models.attachment import GrievanceAttachment
from app.models.user import User
from app.core.permissions import get_current_user, check_grievance_access
from app.core.config import settings
from app.utils.file_handler import validate_and_save_file
from app.schemas.grievance import GrievanceAttachmentResponse
from app.services.audit_service import log_audit

router = APIRouter(prefix="/grievances", tags=["Attachments"])

@router.post("/{id}/attachments", response_model=GrievanceAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    id: int,
    file: UploadFile = File(...),
    is_internal_only: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely upload supporting documentation to a grievance."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Students cannot upload internal-only documents
    if current_user.default_role == UserRoleEnum.STUDENT and is_internal_only:
        is_internal_only = False

    orig_name, stored_name, file_size, content_type = validate_and_save_file(file)

    attachment = GrievanceAttachment(
        grievance_id=grievance.id,
        uploader_id=current_user.id,
        file_name=orig_name,
        stored_file_name=stored_name,
        file_path=os.path.join(settings.UPLOAD_DIR, stored_name),
        file_size_bytes=file_size,
        content_type=content_type,
        is_internal_only=is_internal_only
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    log_audit(db, action="UPLOAD_ATTACHMENT", entity_type="ATTACHMENT", user_id=current_user.id, entity_id=str(attachment.id))

    return GrievanceAttachmentResponse(
        id=attachment.id,
        file_name=attachment.file_name,
        file_size_bytes=attachment.file_size_bytes,
        content_type=attachment.content_type,
        is_internal_only=attachment.is_internal_only,
        created_at=attachment.created_at
    )

@router.get("/{id}/attachments/{att_id}/download")
def download_attachment(
    id: int,
    att_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enforce strict authorization check before downloading file."""
    grievance = db.query(Grievance).filter(Grievance.id == id).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")

    if not check_grievance_access(current_user, grievance, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to download this file.")

    att = db.query(GrievanceAttachment).filter(
        GrievanceAttachment.id == att_id,
        GrievanceAttachment.grievance_id == grievance.id
    ).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    # Students cannot access internal-only files
    if current_user.default_role == UserRoleEnum.STUDENT and att.is_internal_only:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden to internal document.")

    file_path = os.path.join(settings.UPLOAD_DIR, att.stored_file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File content not found on server.")

    log_audit(db, action="DOWNLOAD_ATTACHMENT", entity_type="ATTACHMENT", user_id=current_user.id, entity_id=str(att.id))

    return FileResponse(
        path=file_path,
        filename=att.file_name,
        media_type=att.content_type
    )
