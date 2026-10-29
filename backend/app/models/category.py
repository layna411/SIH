from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class GrievanceCategory(Base):
    __tablename__ = "grievance_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    default_sla_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    grievances: Mapped[list["Grievance"]] = relationship("Grievance", foreign_keys="[Grievance.category_id]", back_populates="category")

from app.models.grievance import Grievance
