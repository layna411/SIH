import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".docx", ".doc", ".txt"
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain"
}

def validate_and_save_file(file: UploadFile) -> Tuple[str, str, int, str]:
    """
    Validate and save uploaded file to private directory.
    Returns: (original_filename, stored_filename, file_size, content_type)
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
        
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{file.content_type}'."
        )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate secure unique filename
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    # Stream write and enforce max file size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_size = 0

    with open(dest_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 64):
            total_size += len(chunk)
            if total_size > max_bytes:
                buffer.close()
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                )
            buffer.write(chunk)

    return (file.filename, stored_name, total_size, file.content_type)
