from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.core.permissions import get_current_user
from app.services.ai_service import ai_service
from app.schemas.ai import (
    AICategoryRecommendation,
    AIPriorityRecommendation,
    AIDuplicateCheckResponse,
    AIRoutingRecommendation,
    AIHealthResponse
)

router = APIRouter(prefix="/ai", tags=["AI Assistance"])

@router.get("/health", response_model=AIHealthResponse)
@router.get("/readiness", response_model=AIHealthResponse)
def get_ai_readiness():
    """
    Check operational readiness of the AI engine and loaded model artifacts.
    """
    return ai_service.get_readiness_status()

class AIAnalyzeRequest(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    institution_id: Optional[int] = None
    category_id: Optional[int] = None

class AIAnalyzeResponse(BaseModel):
    category: AICategoryRecommendation
    priority: AIPriorityRecommendation
    duplicate_check: Optional[AIDuplicateCheckResponse] = None
    routing: Optional[AIRoutingRecommendation] = None

@router.post("/analyze", response_model=AIAnalyzeResponse)
def analyze_grievance_draft(
    req: AIAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Real-time interactive AI assist for students or intake officers:
    suggests categories, priority, and warns of duplicates.
    Transparently labels source model or rule-based fallback.
    """
    category_rec = ai_service.recommend_category(req.title, req.description, db)
    priority_rec = ai_service.recommend_priority(req.title, req.description)
    
    dup_resp = None
    if req.institution_id:
        dup_resp = ai_service.detect_duplicates(req.title, req.description, req.institution_id, db)

    routing_resp = None
    if req.institution_id and (req.category_id or category_rec.category_id):
        cat_id = req.category_id or category_rec.category_id
        routing_resp = ai_service.recommend_routing(cat_id, req.institution_id, db)

    return AIAnalyzeResponse(
        category=category_rec,
        priority=priority_rec,
        duplicate_check=dup_resp,
        routing=routing_resp
    )
