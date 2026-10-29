from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.category import GrievanceCategory
from app.models.user import User
from app.models.enums import UserRoleEnum
from app.core.permissions import require_roles
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.audit_service import log_audit

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """List all active grievance categories."""
    return db.query(GrievanceCategory).filter(GrievanceCategory.is_active == True).order_by(GrievanceCategory.name.asc()).all()

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryCreate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new grievance category (Super Admin only)."""
    existing = db.query(GrievanceCategory).filter(GrievanceCategory.code == req.code.upper().strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with code '{req.code}' exists.")

    new_cat = GrievanceCategory(
        code=req.code.upper().strip(),
        name=req.name.strip(),
        description=req.description,
        default_sla_days=req.default_sla_days,
        is_active=True
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    log_audit(db, action="CREATE_CATEGORY", entity_type="CATEGORY", user_id=current_user.id, entity_id=str(new_cat.id))
    return new_cat

@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    id: int,
    req: CategoryUpdate,
    current_user: User = Depends(require_roles(UserRoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update grievance category (Super Admin only)."""
    cat = db.query(GrievanceCategory).filter(GrievanceCategory.id == id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(cat, field, val)

    db.commit()
    db.refresh(cat)
    log_audit(db, action="UPDATE_CATEGORY", entity_type="CATEGORY", user_id=current_user.id, entity_id=str(cat.id))
    return cat
