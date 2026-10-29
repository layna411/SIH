from typing import List, Dict, Any
from pydantic import BaseModel

class KeyValueStat(BaseModel):
    name: str
    value: int

class MonthlyTrendStat(BaseModel):
    month: str
    submitted: int
    resolved: int

class DashboardAnalyticsResponse(BaseModel):
    total_grievances: int
    pending_grievances: int
    in_investigation_grievances: int
    resolved_grievances: int
    overdue_grievances: int
    escalated_grievances: int
    avg_resolution_days: float
    satisfaction_rate: float
    status_breakdown: List[KeyValueStat]
    category_breakdown: List[KeyValueStat]
    priority_breakdown: List[KeyValueStat]
    monthly_trends: List[MonthlyTrendStat]
