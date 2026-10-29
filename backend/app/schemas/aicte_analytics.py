from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AICTEStatusCount(BaseModel):
    status: str
    label: str
    count: int

class AICTEAgeingBucket(BaseModel):
    bucket_key: str
    label: str
    min_days: int
    max_days: Optional[int] = None
    count: int
    percentage: float

class AICTEAgeingResponse(BaseModel):
    total_active_cases: int
    average_active_age_days: Optional[float] = None
    median_active_age_days: Optional[float] = None
    buckets: List[AICTEAgeingBucket]
    average_disposal_time_days: Optional[float] = None

class AICTESLAResponse(BaseModel):
    active_cases_count: int
    overdue_next_action_count: int
    overdue_expected_disposal_count: int
    total_sla_breached_count: int
    escalated_cases_count: int
    missing_next_action_deadline_count: int
    missing_expected_disposal_count: int
    sla_compliance_rate: Optional[float] = None

class AICTEInstitutionSummary(BaseModel):
    institution_id: int
    name: str
    code: str
    aicte_permanent_id: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    total_cases: int
    active_cases: int
    overdue_cases: int
    disposed_cases: int
    disposal_rate: Optional[float] = None

class AICTEInstitutionsAnalyticsResponse(BaseModel):
    total_institutions: int
    institutions: List[AICTEInstitutionSummary]

class AICTEOrganizationalUnitSummary(BaseModel):
    unit_id: int
    code: str
    name: str
    unit_type: str
    region_code: Optional[str] = None
    total_cases: int
    active_cases: int
    overdue_cases: int
    disposed_cases: int
    pending_incoming_transfers: int
    disposal_rate: Optional[float] = None

class AICTEOrganizationalUnitsAnalyticsResponse(BaseModel):
    total_units: int
    units: List[AICTEOrganizationalUnitSummary]

class AICTETrendPoint(BaseModel):
    period: str
    received_count: int
    disposed_count: int
    transferred_count: int

class AICTETrendsResponse(BaseModel):
    granularity: str
    trend_points: List[AICTETrendPoint]

class AICTETransferAnalyticsResponse(BaseModel):
    total_transfers_initiated: int
    pending_acceptance_count: int
    accepted_count: int
    rejected_count: int
    cancelled_count: int
    average_turnaround_hours: Optional[float] = None

class AICTECrossBureauAnalyticsResponse(BaseModel):
    total_overlaps_detected: int
    pending_review_overlaps: int
    confirmed_duplicates: int
    confirmed_related: int
    rejected_overlaps: int
    total_case_links: int

class AICTEOverviewAnalyticsResponse(BaseModel):
    reporting_period_start: Optional[datetime] = None
    reporting_period_end: Optional[datetime] = None
    total_received: int
    total_active: int
    total_disposed: int
    status_distribution: List[AICTEStatusCount]
    overdue_actions_count: int
    overdue_disposal_count: int
    total_sla_breached_count: int
    escalated_count: int
    awaiting_action_count: int
    reopened_count: int
    pending_transfers_count: int
    pending_overlaps_count: int
    disposal_rate: Optional[float] = None
    average_age_active_days: Optional[float] = None
