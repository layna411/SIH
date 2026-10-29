from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.enums import GrievancePriorityEnum

class AICategoryRecommendation(BaseModel):
    category_id: int
    category_name: str
    confidence: float
    explanation: str
    is_rule_based: bool
    model_version: str
    category_code: Optional[str] = None
    is_uncertain: Optional[bool] = False

class AIPriorityRecommendation(BaseModel):
    priority: GrievancePriorityEnum
    confidence: float
    urgency_indicators: List[str] = Field(default_factory=list)
    explanation: str
    is_rule_based: bool
    model_version: Optional[str] = "EduResolve-TriagePriority-v1.2"
    human_review_required: Optional[bool] = False

class AIDuplicateMatch(BaseModel):
    reference_number: str
    title: str
    similarity_score: float
    status: str

class AIDuplicateCheckResponse(BaseModel):
    is_duplicate_suspected: bool
    highest_similarity: float
    matches: List[AIDuplicateMatch] = Field(default_factory=list)
    explanation: str

class AIRoutingRecommendation(BaseModel):
    suggested_department: Optional[str] = None
    suggested_officer_id: Optional[int] = None
    suggested_officer_name: Optional[str] = None
    reason: str

class AIHealthResponse(BaseModel):
    status: str
    is_model_loaded: bool
    model_version: str
    classifier_type: str
    features_active: List[str]
    device: str
    dataset_provenance: str
