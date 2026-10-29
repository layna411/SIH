import io
import csv
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, case, distinct

from app.models.enums import (
    UserRoleEnum,
    AICTECaseStatusEnum,
    GrievancePriorityEnum,
    AICTETransferStatusEnum,
    AICTEOverlapReviewStatusEnum,
)
from app.models.aicte_case import AICTECase, CaseAction
from app.models.aicte_transfer import AICTECaseTransfer
from app.models.aicte_overlap import AICTECaseOverlap, AICTECaseLink
from app.models.organizational_unit import OrganizationalUnit
from app.models.institution import Institution, RegulatoryJurisdiction
from app.models.user import User
from app.core.permissions import get_user_bureau_unit_ids
from app.schemas.aicte_analytics import (
    AICTEStatusCount,
    AICTEAgeingBucket,
    AICTEAgeingResponse,
    AICTESLAResponse,
    AICTEInstitutionSummary,
    AICTEInstitutionsAnalyticsResponse,
    AICTEOrganizationalUnitSummary,
    AICTEOrganizationalUnitsAnalyticsResponse,
    AICTETrendPoint,
    AICTETrendsResponse,
    AICTETransferAnalyticsResponse,
    AICTECrossBureauAnalyticsResponse,
    AICTEOverviewAnalyticsResponse,
)

ACTIVE_STATUSES = [
    AICTECaseStatusEnum.RECEIVED,
    AICTECaseStatusEnum.PENDING_REVIEW,
    AICTECaseStatusEnum.UNDER_PROCESS,
    AICTECaseStatusEnum.AWAITING_RESPONSE,
    AICTECaseStatusEnum.TRANSFER_PENDING,
    AICTECaseStatusEnum.TRANSFERRED,
    AICTECaseStatusEnum.ESCALATED,
    AICTECaseStatusEnum.REOPENED,
]

DISPOSED_STATUSES = [
    AICTECaseStatusEnum.DISPOSED,
    AICTECaseStatusEnum.CLOSED,
]

def sanitize_csv_value(val: Any) -> str:
    """Neutralize spreadsheet command injection / DDE attacks."""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

class AICTEAnalyticsService:
    @staticmethod
    def _get_authorized_units_and_insts(
        user: User, db: Session
    ) -> Tuple[Optional[List[int]], Optional[List[int]]]:
        """
        Determine user's authorized organizational units and/or institution IDs.
        Returns (authorized_unit_ids, allowed_inst_ids).
        If user is SUPER_ADMIN, returns (None, None).
        If user is unauthorized, raises HTTP 403.
        """
        if user.default_role == UserRoleEnum.SUPER_ADMIN:
            return None, None

        if user.default_role == UserRoleEnum.REGULATORY_ADMIN:
            jurisdictions = db.query(RegulatoryJurisdiction).filter(
                RegulatoryJurisdiction.user_id == user.id,
                RegulatoryJurisdiction.is_active == True,
            ).all()
            assigned_states = [j.state.strip().lower() for j in jurisdictions if j.state]
            direct_inst_ids = [j.institution_id for j in jurisdictions if j.institution_id is not None]
            
            state_inst_ids = []
            if assigned_states:
                state_insts = db.query(Institution.id).filter(
                    func.lower(Institution.state).in_(assigned_states)
                ).all()
                state_inst_ids = [r[0] for r in state_insts]
            
            allowed_inst_ids = list(set(direct_inst_ids + state_inst_ids))
            return None, allowed_inst_ids

        # Bureau members
        bureau_unit_ids = get_user_bureau_unit_ids(user, db)
        if bureau_unit_ids:
            return bureau_unit_ids, None

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not possess authorized regulatory analytics permissions.",
        )

    @classmethod
    def build_case_query(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        institution_id: Optional[int] = None,
        organizational_unit_id: Optional[int] = None,
        region: Optional[str] = None,
        case_status: Optional[AICTECaseStatusEnum] = None,
        priority: Optional[GrievancePriorityEnum] = None,
        overdue_only: Optional[bool] = None,
    ):
        """Build base query enforcing strict authorization and validated filters."""
        if from_date and to_date and from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: 'from_date' cannot be later than 'to_date'.",
            )

        auth_units, allowed_insts = cls._get_authorized_units_and_insts(user, db)

        query = db.query(AICTECase)

        if auth_units is not None:
            query = query.filter(AICTECase.current_unit_id.in_(auth_units))
        if allowed_insts is not None:
            query = query.filter(AICTECase.institution_id.in_(allowed_insts))

        # Explicit filters
        if organizational_unit_id:
            if auth_units is not None and organizational_unit_id not in auth_units:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: outside your authorized organizational unit jurisdiction.",
                )
            query = query.filter(AICTECase.current_unit_id == organizational_unit_id)

        if institution_id:
            if allowed_insts is not None and institution_id not in allowed_insts:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: outside your assigned regulatory jurisdiction.",
                )
            query = query.filter(AICTECase.institution_id == institution_id)

        if from_date:
            query = query.filter(AICTECase.received_at >= from_date)
        if to_date:
            query = query.filter(AICTECase.received_at <= to_date)

        if region:
            query = query.filter(
                or_(
                    AICTECase.region == region,
                    AICTECase.institution.has(Institution.region == region),
                )
            )
        if case_status:
            query = query.filter(AICTECase.status == case_status)
        if priority:
            query = query.filter(AICTECase.priority == priority)

        now = datetime.now(timezone.utc)
        if overdue_only:
            query = query.filter(
                AICTECase.status.in_(ACTIVE_STATUSES),
                or_(
                    and_(AICTECase.next_action_due_at.isnot(None), AICTECase.next_action_due_at < now),
                    and_(AICTECase.expected_disposal_at.isnot(None), AICTECase.expected_disposal_at < now),
                ),
            )

        return query

    @classmethod
    def get_overview(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        institution_id: Optional[int] = None,
        organizational_unit_id: Optional[int] = None,
        region: Optional[str] = None,
    ) -> AICTEOverviewAnalyticsResponse:
        base_query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
            institution_id=institution_id,
            organizational_unit_id=organizational_unit_id,
            region=region,
        )

        # Status distribution via database aggregation
        status_rows = (
            db.query(AICTECase.status, func.count(distinct(AICTECase.id)))
            .filter(AICTECase.id.in_(base_query.with_entities(AICTECase.id)))
            .group_by(AICTECase.status)
            .all()
        )
        counts_by_status = {s: count for s, count in status_rows}

        total_received = sum(counts_by_status.values())
        total_active = sum(counts_by_status.get(s, 0) for s in ACTIVE_STATUSES)
        total_disposed = sum(counts_by_status.get(s, 0) for s in DISPOSED_STATUSES)
        escalated_count = counts_by_status.get(AICTECaseStatusEnum.ESCALATED, 0)
        reopened_count = counts_by_status.get(AICTECaseStatusEnum.REOPENED, 0)

        now = datetime.now(timezone.utc)
        active_ids_query = base_query.filter(AICTECase.status.in_(ACTIVE_STATUSES)).with_entities(AICTECase.id)

        overdue_actions_count = (
            db.query(func.count(distinct(AICTECase.id)))
            .filter(
                AICTECase.id.in_(active_ids_query),
                AICTECase.next_action_due_at.isnot(None),
                AICTECase.next_action_due_at < now,
            )
            .scalar()
            or 0
        )

        overdue_disposal_count = (
            db.query(func.count(distinct(AICTECase.id)))
            .filter(
                AICTECase.id.in_(active_ids_query),
                AICTECase.expected_disposal_at.isnot(None),
                AICTECase.expected_disposal_at < now,
            )
            .scalar()
            or 0
        )

        total_sla_breached_count = (
            db.query(func.count(distinct(AICTECase.id)))
            .filter(
                AICTECase.id.in_(active_ids_query),
                or_(
                    and_(AICTECase.next_action_due_at.isnot(None), AICTECase.next_action_due_at < now),
                    and_(AICTECase.expected_disposal_at.isnot(None), AICTECase.expected_disposal_at < now),
                ),
            )
            .scalar()
            or 0
        )

        awaiting_action_count = (
            db.query(func.count(distinct(AICTECase.id)))
            .filter(
                AICTECase.id.in_(active_ids_query),
                AICTECase.next_action_required.isnot(None),
                AICTECase.next_action_required != "",
            )
            .scalar()
            or 0
        )

        # Average age of active cases
        avg_age_val = (
            db.query(func.avg(func.datediff(now, AICTECase.received_at)))
            .filter(AICTECase.id.in_(active_ids_query))
            .scalar()
        )
        average_age_active_days = round(float(avg_age_val), 1) if avg_age_val is not None else None

        # Period Disposal Rate: (disposed in period / received in period) * 100
        disposal_rate = None
        if total_received > 0:
            disposal_rate = round((total_disposed / total_received) * 100, 1)

        # Pending transfers count (authorized for user)
        auth_units, _ = cls._get_authorized_units_and_insts(user, db)
        transfer_q = db.query(func.count(distinct(AICTECaseTransfer.id))).filter(
            AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.PENDING_ACCEPTANCE
        )
        if auth_units is not None:
            transfer_q = transfer_q.filter(
                or_(
                    AICTECaseTransfer.from_unit_id.in_(auth_units),
                    AICTECaseTransfer.to_unit_id.in_(auth_units),
                )
            )
        pending_transfers_count = transfer_q.scalar() or 0

        # Pending overlaps count
        pending_overlaps_count = (
            db.query(func.count(distinct(AICTECaseOverlap.id)))
            .filter(AICTECaseOverlap.review_status == AICTEOverlapReviewStatusEnum.PENDING)
            .scalar()
            or 0
        )

        # Build complete status distribution response
        status_dist: List[AICTEStatusCount] = []
        for s in AICTECaseStatusEnum:
            cnt = counts_by_status.get(s, 0)
            status_dist.append(
                AICTEStatusCount(
                    status=s.value,
                    label=s.value.replace("_", " "),
                    count=cnt,
                )
            )

        return AICTEOverviewAnalyticsResponse(
            reporting_period_start=from_date,
            reporting_period_end=to_date,
            total_received=total_received,
            total_active=total_active,
            total_disposed=total_disposed,
            status_distribution=status_dist,
            overdue_actions_count=overdue_actions_count,
            overdue_disposal_count=overdue_disposal_count,
            total_sla_breached_count=total_sla_breached_count,
            escalated_count=escalated_count,
            awaiting_action_count=awaiting_action_count,
            reopened_count=reopened_count,
            pending_transfers_count=pending_transfers_count,
            pending_overlaps_count=pending_overlaps_count,
            disposal_rate=disposal_rate,
            average_age_active_days=average_age_active_days,
        )

    @classmethod
    def get_ageing(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        institution_id: Optional[int] = None,
        organizational_unit_id: Optional[int] = None,
        region: Optional[str] = None,
    ) -> AICTEAgeingResponse:
        base_query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
            institution_id=institution_id,
            organizational_unit_id=organizational_unit_id,
            region=region,
        )

        now = datetime.now(timezone.utc)
        active_cases = (
            base_query.filter(AICTECase.status.in_(ACTIVE_STATUSES))
            .with_entities(AICTECase.id, AICTECase.received_at)
            .all()
        )

        total_active = len(active_cases)
        bucket_defs = [
            ("0_7_DAYS", "0–7 Days", 0, 7),
            ("8_15_DAYS", "8–15 Days", 8, 15),
            ("16_30_DAYS", "16–30 Days", 16, 30),
            ("31_60_DAYS", "31–60 Days", 31, 60),
            ("OVER_60_DAYS", ">60 Days", 61, None),
        ]

        bucket_counts = {k: 0 for k, _, _, _ in bucket_defs}
        ages: List[int] = []

        for _, received_at in active_cases:
            diff_days = max(0, (now.date() - received_at.date()).days)
            ages.append(diff_days)
            if diff_days <= 7:
                bucket_counts["0_7_DAYS"] += 1
            elif diff_days <= 15:
                bucket_counts["8_15_DAYS"] += 1
            elif diff_days <= 30:
                bucket_counts["16_30_DAYS"] += 1
            elif diff_days <= 60:
                bucket_counts["31_60_DAYS"] += 1
            else:
                bucket_counts["OVER_60_DAYS"] += 1

        buckets: List[AICTEAgeingBucket] = []
        for key, label, min_d, max_d in bucket_defs:
            cnt = bucket_counts[key]
            pct = round((cnt / total_active * 100), 1) if total_active > 0 else 0.0
            buckets.append(
                AICTEAgeingBucket(
                    bucket_key=key,
                    label=label,
                    min_days=min_d,
                    max_days=max_d,
                    count=cnt,
                    percentage=pct,
                )
            )

        avg_age = round(sum(ages) / total_active, 1) if total_active > 0 else None
        median_age = None
        if ages:
            ages.sort()
            n = len(ages)
            median_age = float(ages[n // 2] if n % 2 != 0 else (ages[n // 2 - 1] + ages[n // 2]) / 2)

        # Average historical disposal time
        disposed_cases = (
            base_query.filter(AICTECase.status.in_(DISPOSED_STATUSES))
            .with_entities(AICTECase.received_at, AICTECase.disposed_at, AICTECase.updated_at)
            .all()
        )
        disp_times: List[int] = []
        for recv, disp, upd in disposed_cases:
            end_t = disp or upd
            if end_t and recv:
                disp_times.append(max(0, (end_t.date() - recv.date()).days))
        avg_disp_time = round(sum(disp_times) / len(disp_times), 1) if disp_times else None

        return AICTEAgeingResponse(
            total_active_cases=total_active,
            average_active_age_days=avg_age,
            median_active_age_days=median_age,
            buckets=buckets,
            average_disposal_time_days=avg_disp_time,
        )

    @classmethod
    def get_sla(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        institution_id: Optional[int] = None,
        organizational_unit_id: Optional[int] = None,
        region: Optional[str] = None,
    ) -> AICTESLAResponse:
        base_query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
            institution_id=institution_id,
            organizational_unit_id=organizational_unit_id,
            region=region,
        )

        now = datetime.now(timezone.utc)
        active_query = base_query.filter(AICTECase.status.in_(ACTIVE_STATUSES))
        active_count = active_query.count()

        overdue_next_action = active_query.filter(
            AICTECase.next_action_due_at.isnot(None),
            AICTECase.next_action_due_at < now,
        ).count()

        overdue_disposal = active_query.filter(
            AICTECase.expected_disposal_at.isnot(None),
            AICTECase.expected_disposal_at < now,
        ).count()

        total_sla_breached = active_query.filter(
            or_(
                and_(AICTECase.next_action_due_at.isnot(None), AICTECase.next_action_due_at < now),
                and_(AICTECase.expected_disposal_at.isnot(None), AICTECase.expected_disposal_at < now),
            )
        ).count()

        escalated_count = active_query.filter(AICTECase.status == AICTECaseStatusEnum.ESCALATED).count()

        missing_next_action = active_query.filter(AICTECase.next_action_due_at.is_(None)).count()
        missing_expected_disposal = active_query.filter(AICTECase.expected_disposal_at.is_(None)).count()

        cases_with_sla = active_count - missing_next_action
        sla_compliance_rate = None
        if cases_with_sla > 0:
            compliant_cases = max(0, cases_with_sla - overdue_next_action)
            sla_compliance_rate = round((compliant_cases / cases_with_sla) * 100, 1)

        return AICTESLAResponse(
            active_cases_count=active_count,
            overdue_next_action_count=overdue_next_action,
            overdue_expected_disposal_count=overdue_disposal,
            total_sla_breached_count=total_sla_breached,
            escalated_cases_count=escalated_count,
            missing_next_action_deadline_count=missing_next_action,
            missing_expected_disposal_count=missing_expected_disposal,
            sla_compliance_rate=sla_compliance_rate,
        )

    @classmethod
    def get_institutions_summary(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        region: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AICTEInstitutionsAnalyticsResponse:
        base_query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
            region=region,
        )

        now = datetime.now(timezone.utc)

        # Aggregate counts grouped by institution
        rows = (
            db.query(
                Institution.id,
                Institution.name,
                Institution.code,
                Institution.aicte_permanent_id,
                Institution.state,
                Institution.region,
                func.count(distinct(AICTECase.id)).label("total_cases"),
                func.sum(
                    case((AICTECase.status.in_(ACTIVE_STATUSES), 1), else_=0)
                ).label("active_cases"),
                func.sum(
                    case((AICTECase.status.in_(DISPOSED_STATUSES), 1), else_=0)
                ).label("disposed_cases"),
                func.sum(
                    case(
                        (
                            and_(
                                AICTECase.status.in_(ACTIVE_STATUSES),
                                or_(
                                    and_(AICTECase.next_action_due_at.isnot(None), AICTECase.next_action_due_at < now),
                                    and_(AICTECase.expected_disposal_at.isnot(None), AICTECase.expected_disposal_at < now),
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("overdue_cases"),
            )
            .join(AICTECase, AICTECase.institution_id == Institution.id)
            .filter(AICTECase.id.in_(base_query.with_entities(AICTECase.id)))
            .group_by(
                Institution.id,
                Institution.name,
                Institution.code,
                Institution.aicte_permanent_id,
                Institution.state,
                Institution.region,
            )
            .order_by(func.count(distinct(AICTECase.id)).desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results: List[AICTEInstitutionSummary] = []
        for r in rows:
            tot = int(r.total_cases or 0)
            act = int(r.active_cases or 0)
            disp = int(r.disposed_cases or 0)
            over = int(r.overdue_cases or 0)
            disp_rate = round((disp / tot * 100), 1) if tot > 0 else None
            results.append(
                AICTEInstitutionSummary(
                    institution_id=r.id,
                    name=r.name,
                    code=r.code,
                    aicte_permanent_id=r.aicte_permanent_id,
                    state=r.state,
                    region=r.region,
                    total_cases=tot,
                    active_cases=act,
                    overdue_cases=over,
                    disposed_cases=disp,
                    disposal_rate=disp_rate,
                )
            )

        return AICTEInstitutionsAnalyticsResponse(
            total_institutions=len(results),
            institutions=results,
        )

    @classmethod
    def get_organizational_units_summary(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> AICTEOrganizationalUnitsAnalyticsResponse:
        auth_units, _ = cls._get_authorized_units_and_insts(user, db)

        now = datetime.now(timezone.utc)
        base_query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
        )

        units_query = db.query(OrganizationalUnit).filter(OrganizationalUnit.is_active == True)
        if auth_units is not None:
            units_query = units_query.filter(OrganizationalUnit.id.in_(auth_units))
        active_units = units_query.all()

        results: List[AICTEOrganizationalUnitSummary] = []
        for u in active_units:
            unit_case_ids = base_query.filter(AICTECase.current_unit_id == u.id).with_entities(AICTECase.id)
            
            tot = unit_case_ids.count()
            act = (
                db.query(func.count(distinct(AICTECase.id)))
                .filter(AICTECase.id.in_(unit_case_ids), AICTECase.status.in_(ACTIVE_STATUSES))
                .scalar()
                or 0
            )
            disp = (
                db.query(func.count(distinct(AICTECase.id)))
                .filter(AICTECase.id.in_(unit_case_ids), AICTECase.status.in_(DISPOSED_STATUSES))
                .scalar()
                or 0
            )
            over = (
                db.query(func.count(distinct(AICTECase.id)))
                .filter(
                    AICTECase.id.in_(unit_case_ids),
                    AICTECase.status.in_(ACTIVE_STATUSES),
                    or_(
                        and_(AICTECase.next_action_due_at.isnot(None), AICTECase.next_action_due_at < now),
                        and_(AICTECase.expected_disposal_at.isnot(None), AICTECase.expected_disposal_at < now),
                    ),
                )
                .scalar()
                or 0
            )

            pending_inc = (
                db.query(func.count(distinct(AICTECaseTransfer.id)))
                .filter(
                    AICTECaseTransfer.to_unit_id == u.id,
                    AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.PENDING_ACCEPTANCE,
                )
                .scalar()
                or 0
            )

            disp_rate = round((disp / tot * 100), 1) if tot > 0 else None

            results.append(
                AICTEOrganizationalUnitSummary(
                    unit_id=u.id,
                    code=u.code,
                    name=u.name,
                    unit_type=u.unit_type.value if hasattr(u.unit_type, "value") else str(u.unit_type),
                    region_code=u.region_code,
                    total_cases=tot,
                    active_cases=act,
                    overdue_cases=over,
                    disposed_cases=disp,
                    pending_incoming_transfers=pending_inc,
                    disposal_rate=disp_rate,
                )
            )

        return AICTEOrganizationalUnitsAnalyticsResponse(
            total_units=len(results),
            units=results,
        )

    @classmethod
    def get_trends(
        cls,
        db: Session,
        user: User,
        months_back: int = 6,
        organizational_unit_id: Optional[int] = None,
        institution_id: Optional[int] = None,
    ) -> AICTETrendsResponse:
        base_query = cls.build_case_query(
            db=db,
            user=user,
            organizational_unit_id=organizational_unit_id,
            institution_id=institution_id,
        )

        now = datetime.now(timezone.utc)
        periods: List[str] = []
        for i in range(months_back - 1, -1, -1):
            dt = now - timedelta(days=i * 30)
            periods.append(dt.strftime("%Y-%m"))
        periods = sorted(list(set(periods)))

        # Group received by month
        received_rows = (
            db.query(
                func.date_format(AICTECase.received_at, "%Y-%m").label("period"),
                func.count(distinct(AICTECase.id)),
            )
            .filter(AICTECase.id.in_(base_query.with_entities(AICTECase.id)))
            .group_by("period")
            .all()
        )
        recv_map = {r[0]: r[1] for r in received_rows if r[0]}

        # Group disposed by month
        disposed_rows = (
            db.query(
                func.date_format(
                    func.coalesce(AICTECase.disposed_at, AICTECase.updated_at), "%Y-%m"
                ).label("period"),
                func.count(distinct(AICTECase.id)),
            )
            .filter(
                AICTECase.id.in_(base_query.with_entities(AICTECase.id)),
                AICTECase.status.in_(DISPOSED_STATUSES),
            )
            .group_by("period")
            .all()
        )
        disp_map = {r[0]: r[1] for r in disposed_rows if r[0]}

        # Group accepted transfers by month
        auth_units, _ = cls._get_authorized_units_and_insts(user, db)
        transfer_q = db.query(
            func.date_format(AICTECaseTransfer.responded_at, "%Y-%m").label("period"),
            func.count(distinct(AICTECaseTransfer.id)),
        ).filter(
            AICTECaseTransfer.transfer_status == AICTETransferStatusEnum.ACCEPTED,
            AICTECaseTransfer.responded_at.isnot(None),
        )
        if auth_units is not None:
            transfer_q = transfer_q.filter(
                or_(
                    AICTECaseTransfer.from_unit_id.in_(auth_units),
                    AICTECaseTransfer.to_unit_id.in_(auth_units),
                )
            )
        transf_rows = transfer_q.group_by("period").all()
        transf_map = {r[0]: r[1] for r in transf_rows if r[0]}

        trend_points: List[AICTETrendPoint] = []
        for p in periods:
            trend_points.append(
                AICTETrendPoint(
                    period=p,
                    received_count=recv_map.get(p, 0),
                    disposed_count=disp_map.get(p, 0),
                    transferred_count=transf_map.get(p, 0),
                )
            )

        return AICTETrendsResponse(
            granularity="month",
            trend_points=trend_points,
        )

    @classmethod
    def get_transfers_analytics(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> AICTETransferAnalyticsResponse:
        auth_units, _ = cls._get_authorized_units_and_insts(user, db)

        query = db.query(AICTECaseTransfer)
        if auth_units is not None:
            query = query.filter(
                or_(
                    AICTECaseTransfer.from_unit_id.in_(auth_units),
                    AICTECaseTransfer.to_unit_id.in_(auth_units),
                )
            )
        if from_date:
            query = query.filter(AICTECaseTransfer.initiated_at >= from_date)
        if to_date:
            query = query.filter(AICTECaseTransfer.initiated_at <= to_date)

        rows = (
            db.query(
                AICTECaseTransfer.transfer_status,
                func.count(distinct(AICTECaseTransfer.id)),
            )
            .filter(AICTECaseTransfer.id.in_(query.with_entities(AICTECaseTransfer.id)))
            .group_by(AICTECaseTransfer.transfer_status)
            .all()
        )
        counts = {s: cnt for s, cnt in rows}

        total_init = sum(counts.values())
        pending = counts.get(AICTETransferStatusEnum.PENDING_ACCEPTANCE, 0)
        accepted = counts.get(AICTETransferStatusEnum.ACCEPTED, 0)
        rejected = counts.get(AICTETransferStatusEnum.REJECTED, 0)
        cancelled = counts.get(AICTETransferStatusEnum.CANCELLED, 0)

        # Average turnaround hours for decided transfers
        decided_transfers = (
            query.filter(
                AICTECaseTransfer.transfer_status.in_(
                    [AICTETransferStatusEnum.ACCEPTED, AICTETransferStatusEnum.REJECTED]
                ),
                AICTECaseTransfer.responded_at.isnot(None),
            )
            .with_entities(AICTECaseTransfer.initiated_at, AICTECaseTransfer.responded_at)
            .all()
        )
        hours_list = [
            max(0, (resp - init).total_seconds() / 3600.0)
            for init, resp in decided_transfers
            if resp and init
        ]
        avg_hours = round(sum(hours_list) / len(hours_list), 1) if hours_list else None

        return AICTETransferAnalyticsResponse(
            total_transfers_initiated=total_init,
            pending_acceptance_count=pending,
            accepted_count=accepted,
            rejected_count=rejected,
            cancelled_count=cancelled,
            average_turnaround_hours=avg_hours,
        )

    @classmethod
    def get_cross_bureau_analytics(
        cls,
        db: Session,
        user: User,
    ) -> AICTECrossBureauAnalyticsResponse:
        cls._get_authorized_units_and_insts(user, db)

        overlap_rows = (
            db.query(AICTECaseOverlap.review_status, func.count(distinct(AICTECaseOverlap.id)))
            .group_by(AICTECaseOverlap.review_status)
            .all()
        )
        counts = {s: cnt for s, cnt in overlap_rows}

        total_overlaps = sum(counts.values())
        pending = counts.get(AICTEOverlapReviewStatusEnum.PENDING, 0)
        confirmed_dup = counts.get(AICTEOverlapReviewStatusEnum.CONFIRMED_DUPLICATE, 0)
        confirmed_rel = counts.get(AICTEOverlapReviewStatusEnum.CONFIRMED_RELATED, 0)
        rejected = counts.get(AICTEOverlapReviewStatusEnum.REJECTED, 0)

        links_count = (
            db.query(func.count(distinct(AICTECaseLink.id)))
            .filter(AICTECaseLink.is_active == True)
            .scalar()
            or 0
        )

        return AICTECrossBureauAnalyticsResponse(
            total_overlaps_detected=total_overlaps,
            pending_review_overlaps=pending,
            confirmed_duplicates=confirmed_dup,
            confirmed_related=confirmed_rel,
            rejected_overlaps=rejected,
            total_case_links=links_count,
        )

    @classmethod
    def export_cases_csv(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        institution_id: Optional[int] = None,
        organizational_unit_id: Optional[int] = None,
        region: Optional[str] = None,
        case_status: Optional[AICTECaseStatusEnum] = None,
        priority: Optional[GrievancePriorityEnum] = None,
        overdue_only: Optional[bool] = None,
    ) -> str:
        """Export authorized case records to sanitised CSV with bounded limit."""
        query = cls.build_case_query(
            db=db,
            user=user,
            from_date=from_date,
            to_date=to_date,
            institution_id=institution_id,
            organizational_unit_id=organizational_unit_id,
            region=region,
            case_status=case_status,
            priority=priority,
            overdue_only=overdue_only,
        )

        cases = query.order_by(AICTECase.received_at.desc()).limit(5000).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Case Reference",
            "Official Reference Number",
            "Institution",
            "AICTE Permanent ID",
            "State",
            "Region",
            "Handling Bureau/Unit",
            "Category",
            "Subject",
            "Status",
            "Priority",
            "Received Date",
            "Next Action Required",
            "Next Action Due",
            "Expected Disposal Date",
            "Disposed Date",
        ])

        for c in cases:
            writer.writerow([
                sanitize_csv_value(c.case_reference),
                sanitize_csv_value(c.official_reference_number),
                sanitize_csv_value(c.institution.name if c.institution else ""),
                sanitize_csv_value(c.institution.aicte_permanent_id if c.institution else ""),
                sanitize_csv_value(c.institution.state if c.institution else ""),
                sanitize_csv_value(c.region or ""),
                sanitize_csv_value(c.current_unit.name if c.current_unit else ""),
                sanitize_csv_value(c.category),
                sanitize_csv_value(c.subject),
                sanitize_csv_value(c.status.value),
                sanitize_csv_value(c.priority.value),
                sanitize_csv_value(c.received_at.strftime("%Y-%m-%d %H:%M:%S") if c.received_at else ""),
                sanitize_csv_value(c.next_action_required or ""),
                sanitize_csv_value(c.next_action_due_at.strftime("%Y-%m-%d %H:%M:%S") if c.next_action_due_at else "Not Recorded"),
                sanitize_csv_value(c.expected_disposal_at.strftime("%Y-%m-%d %H:%M:%S") if c.expected_disposal_at else "Not Recorded"),
                sanitize_csv_value(c.disposed_at.strftime("%Y-%m-%d %H:%M:%S") if c.disposed_at else ""),
            ])

        return output.getvalue()

    @classmethod
    def export_summary_csv(
        cls,
        db: Session,
        user: User,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> str:
        """Export aggregate operational summary report to sanitised CSV."""
        overview = cls.get_overview(db, user, from_date=from_date, to_date=to_date)
        ageing = cls.get_ageing(db, user, from_date=from_date, to_date=to_date)
        sla = cls.get_sla(db, user, from_date=from_date, to_date=to_date)
        units = cls.get_organizational_units_summary(db, user, from_date=from_date, to_date=to_date)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["AICTE OPERATIONAL ANALYTICS & MONITORING SUMMARY"])
        writer.writerow(["Generated At", sanitize_csv_value(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))])
        writer.writerow([])

        writer.writerow(["KEY WORKLOAD INDICATORS", "VALUE"])
        writer.writerow(["Total Cases Received", sanitize_csv_value(overview.total_received)])
        writer.writerow(["Active Backlog", sanitize_csv_value(overview.total_active)])
        writer.writerow(["Disposed Cases", sanitize_csv_value(overview.total_disposed)])
        writer.writerow(["Disposal Rate (%)", sanitize_csv_value(overview.disposal_rate if overview.disposal_rate is not None else "N/A")])
        writer.writerow(["Average Active Case Age (Days)", sanitize_csv_value(overview.average_age_active_days if overview.average_age_active_days is not None else "N/A")])
        writer.writerow([])

        writer.writerow(["SLA & TIMELINESS COMPLIANCE", "VALUE"])
        writer.writerow(["Overdue Next Actions", sanitize_csv_value(sla.overdue_next_action_count)])
        writer.writerow(["Overdue Expected Disposals", sanitize_csv_value(sla.overdue_expected_disposal_count)])
        writer.writerow(["Total SLA Breached Cases", sanitize_csv_value(sla.total_sla_breached_count)])
        writer.writerow(["Escalated Cases", sanitize_csv_value(sla.escalated_cases_count)])
        writer.writerow(["Cases Missing Next Action Deadline", sanitize_csv_value(sla.missing_next_action_deadline_count)])
        writer.writerow(["Cases Missing Expected Disposal Date", sanitize_csv_value(sla.missing_expected_disposal_count)])
        writer.writerow(["SLA Compliance Rate (%)", sanitize_csv_value(sla.sla_compliance_rate if sla.sla_compliance_rate is not None else "N/A")])
        writer.writerow([])

        writer.writerow(["CASE AGEING DISTRIBUTION", "COUNT", "PERCENTAGE (%)"])
        for b in ageing.buckets:
            writer.writerow([sanitize_csv_value(b.label), sanitize_csv_value(b.count), sanitize_csv_value(b.percentage)])
        writer.writerow([])

        writer.writerow(["BUREAU & REGIONAL OFFICE WORKLOAD", "CODE", "TYPE", "TOTAL", "ACTIVE", "OVERDUE", "DISPOSED", "DISPOSAL RATE (%)"])
        for u in units.units:
            writer.writerow([
                sanitize_csv_value(u.name),
                sanitize_csv_value(u.code),
                sanitize_csv_value(u.unit_type),
                sanitize_csv_value(u.total_cases),
                sanitize_csv_value(u.active_cases),
                sanitize_csv_value(u.overdue_cases),
                sanitize_csv_value(u.disposed_cases),
                sanitize_csv_value(u.disposal_rate if u.disposal_rate is not None else "N/A"),
            ])

        return output.getvalue()
