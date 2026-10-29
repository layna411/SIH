from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    grievance_id: Mapped[int] = mapped_column(Integer, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False) # CATEGORY, PRIORITY, DUPLICATE, ROUTING
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_payload: Mapped[str] = mapped_column(Text, nullable=False) # JSON encoded recommendations
    accepted_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievance: Mapped["Grievance"] = relationship("Grievance")
    accepted_by: Mapped[Optional["User"]] = relationship("User")

from app.models.grievance import Grievance
from app.models.user import User
