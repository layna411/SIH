from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.enums import AICTECaseStatusEnum, GrievancePriorityEnum
from app.models.user import User
from app.core.permissions import get_current_active_user
from app.services.aicte_analytics_service import AICTEAnalyticsService
from app.schemas.aicte_analytics import (
    AICTEOverviewAnalyticsResponse,
    AICTEAgeingResponse,
    AICTESLAResponse,
    AICTEInstitutionsAnalyticsResponse,
    AICTEOrganizationalUnitsAnalyticsResponse,
    AICTETrendsResponse,
    AICTETransferAnalyticsResponse,
    AICTECrossBureauAnalyticsResponse,
)

router = APIRouter(prefix="/aicte/analytics", tags=["AICTE Analytics"])

@router.get("/overview", response_model=AICTEOverviewAnalyticsResponse)
def get_analytics_overview(
    from_date: Optional[datetime] = Query(None, description="Start date filter (UTC)"),
    to_date: Optional[datetime] = Query(None, description="End date filter (UTC)"),
    institution_id: Optional[int] = Query(None, description="Specific institution ID"),
    organizational_unit_id: Optional[int] = Query(None, description="Specific organizational unit ID"),
    region: Optional[str] = Query(None, description="Regional office or geographical territory"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get consolidated AICTE case overview KPIs and lifecycle distribution.
    Access strictly scoped by server-side user role and Bureau membership.
    """
    return AICTEAnalyticsService.get_overview(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        institution_id=institution_id,
        organizational_unit_id=organizational_unit_id,
        region=region,
    )

@router.get("/ageing", response_model=AICTEAgeingResponse)
def get_case_ageing(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    institution_id: Optional[int] = Query(None),
    organizational_unit_id: Optional[int] = Query(None),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Active-case ageing distribution (0–7d, 8–15d, 16–30d, 31–60d, >60d) and historical disposal time.
    """
    return AICTEAnalyticsService.get_ageing(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        institution_id=institution_id,
        organizational_unit_id=organizational_unit_id,
        region=region,
    )

@router.get("/sla", response_model=AICTESLAResponse)
def get_sla_monitoring(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    institution_id: Optional[int] = Query(None),
    organizational_unit_id: Optional[int] = Query(None),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    SLA metrics distinguishing overdue next actions, overdue disposal dates, escalated dockets,
    and cases missing scheduled deadlines.
    """
    return AICTEAnalyticsService.get_sla(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        institution_id=institution_id,
        organizational_unit_id=organizational_unit_id,
        region=region,
    )

@router.get("/institutions", response_model=AICTEInstitutionsAnalyticsResponse)
def get_institution_analytics(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Institution-wise workload ranking: active caseload, overdue dockets, and disposal rates.
    """
    return AICTEAnalyticsService.get_institutions_summary(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        region=region,
        limit=limit,
        offset=offset,
    )

@router.get("/organizational-units", response_model=AICTEOrganizationalUnitsAnalyticsResponse)
def get_organizational_unit_analytics(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Bureau, Cell, and Regional Office workload summaries within authorized scope.
    """
    return AICTEAnalyticsService.get_organizational_units_summary(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )

@router.get("/trends", response_model=AICTETrendsResponse)
def get_analytics_trends(
    months_back: int = Query(6, ge=1, le=24),
    organizational_unit_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Chronological trends for received, disposed, and transferred dockets over months.
    """
    return AICTEAnalyticsService.get_trends(
        db=db,
        user=current_user,
        months_back=months_back,
        organizational_unit_id=organizational_unit_id,
        institution_id=institution_id,
    )

@router.get("/transfers", response_model=AICTETransferAnalyticsResponse)
def get_transfer_analytics(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Inter-Bureau transfer lifecycle volume, acceptance/rejection counts, and turnaround time.
    """
    return AICTEAnalyticsService.get_transfers_analytics(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )

@router.get("/cross-bureau", response_model=AICTECrossBureauAnalyticsResponse)
def get_cross_bureau_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cross-Bureau overlap detection counts, review status distributions, and active case links.
    """
    return AICTEAnalyticsService.get_cross_bureau_analytics(
        db=db,
        user=current_user,
    )

@router.get("/reports/cases.csv")
def export_cases_csv(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    institution_id: Optional[int] = Query(None),
    organizational_unit_id: Optional[int] = Query(None),
    region: Optional[str] = Query(None),
    case_status: Optional[AICTECaseStatusEnum] = Query(None, alias="status"),
    priority: Optional[GrievancePriorityEnum] = Query(None),
    overdue_only: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Authorized case-level CSV export with formula injection sanitization.
    """
    csv_data = AICTEAnalyticsService.export_cases_csv(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        institution_id=institution_id,
        organizational_unit_id=organizational_unit_id,
        region=region,
        case_status=case_status,
        priority=priority,
        overdue_only=overdue_only,
    )

    filename = f"aicte_cases_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/reports/summary.csv")
def export_summary_csv(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Authorized aggregate KPI and workload summary CSV export with formula injection sanitization.
    """
    csv_data = AICTEAnalyticsService.export_summary_csv(
        db=db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )

    filename = f"aicte_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
