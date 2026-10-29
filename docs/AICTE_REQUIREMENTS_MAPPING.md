# EduResolve AI — AICTE Requirements Mapping & System Audit

**Problem Statement:** Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells  
**Version:** Step 7 — Phase A Audit  
**Date:** October 2026  
**Status:** Audit & Architecture Completed (Read-Only Phase)

---

## 1. Executive Summary

This document performs an exhaustive, line-by-line audit of the existing **EduResolve AI** codebase against the official SIH problem statement: **"Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells"**.

The existing EduResolve AI platform is a production-hardened student grievance redressal system built with:
- **Backend:** FastAPI (Python 3.11), SQLAlchemy 2.0, Pydantic v2, Alembic migrations.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS.
- **Database:** XAMPP MySQL / MariaDB (Database: `eduresolve_ai`, Test Database: `eduresolve_ai_test`). SQLite is strictly prohibited.
- **AI Service:** TF-IDF category classifier, urgency pattern triage, and cosine similarity duplicate detection.
- **Security & RBAC:** Multi-tenant boundary checks, Argon2 password cryptography, JWT session management, formula injection protection, rate limiting.

### High-Level Audit Findings

| Category | Total Requirements | Implemented | Partially Implemented | Missing |
| :--- | :---: | :---: | :---: | :---: |
| Institution Profile & Identity | 3 | 0 | 2 | 1 |
| Case Lifecycle & Bureau Management | 5 | 1 | 2 | 2 |
| Cross-Bureau Overlap & Linking | 2 | 0 | 1 | 1 |
| Integrated Dashboard & Analytics | 3 | 0 | 1 | 2 |
| Search, Notifications & Reporting | 2 | 0 | 2 | 0 |
| **Total** | **15** | **1** | **8** | **6** |

---

## 2. Granular Requirements Mapping (Requirements 1 to 15)

---

### Requirement 1: Centralized Institution Profile
- **Official Problem Statement:** A consolidated profile for every technical education institution under AICTE jurisdiction, aggregating all regulatory interactions, complaint history, approval status, and compliance records.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/institution.py`](file:///e:/Layn/SIH/backend/app/models/institution.py), [`backend/app/api/v1/institutions.py`](file:///e:/Layn/SIH/backend/app/api/v1/institutions.py)
  - Tables & Columns: `institutions` (`id`, `code`, `name`, `institution_type`, `state`, `district`, `city`, `address`, `contact_email`, `contact_phone`, `website`, `verification_status`, `is_active`, `is_verified`, `created_at`, `updated_at`).
  - Endpoints: `GET /api/v1/institutions`, `GET /api/v1/institutions/{id}`, `POST /api/v1/institutions`, `PUT /api/v1/institutions/{id}`.
- **Existing Frontend Implementation:**
  - Pages: [`frontend/src/pages/superadmin/SuperAdminDashboard.tsx`](file:///e:/Layn/SIH/frontend/src/pages/superadmin/SuperAdminDashboard.tsx), [`frontend/src/pages/regulatory/RegulatoryDashboard.tsx`](file:///e:/Layn/SIH/frontend/src/pages/regulatory/RegulatoryDashboard.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - The current `institutions` table represents individual colleges from a student/campus perspective.
  - It lacks AICTE-specific attributes: official AICTE Permanent ID, AICTE Region (e.g. Northern, Western, Central), affiliated university, approval status, institutional category (Technical, Management, Pharmacy, Architecture), and a single-pane view aggregating cases across all Bureaus.
- **Exact Changes Required:**
  - Add `aicte_permanent_id` (VARCHAR(50), nullable, unique, indexed) to `institutions`.
  - Add `region` (VARCHAR(50), indexed) to `institutions`.
  - Add alias lookup support (`institution_aliases` table) to prevent missed matches when names vary in complaints.
  - Implement a dedicated API endpoint `GET /api/v1/aicte/institutions/{id}/profile` returning consolidated institutional profile, active cases across all bureaus, overlap indicators, and regulatory timeline.
- **Dependencies & Risks:**
  - Must remain backward compatible with existing student registrations.
  - Uniqueness constraint on `aicte_permanent_id` must permit NULLs for existing colleges until officially verified.

---

### Requirement 2: Unique Institution ID and AICTE Permanent ID
- **Official Problem Statement:** Support for official AICTE Permanent ID (e.g., `1-XXXXXXXXXX`) alongside internal database ID, ensuring unambiguous institution identification and preventing collisions between similarly named institutes.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/institution.py`](file:///e:/Layn/SIH/backend/app/models/institution.py#L12)
  - Tables & Columns: `institutions.code` (VARCHAR(50), unique, indexed) — currently stores generic codes like `NITD01`, `INST001`.
- **Existing Frontend Implementation:**
  - Fields in registration and profile components [`frontend/src/pages/superadmin/SuperAdminDashboard.tsx`](file:///e:/Layn/SIH/frontend/src/pages/superadmin/SuperAdminDashboard.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - `code` is currently an unverified, user-entered or seeded string (e.g., `NITD01`).
  - There is no field dedicated to the official `aicte_permanent_id` with format validation (e.g. `1-\d{10}`).
  - No verification status distinguishing whether an AICTE ID is verified against the AICTE master directory or simply self-reported by an applicant.
- **Exact Changes Required:**
  - Add column `aicte_permanent_id` VARCHAR(50), unique, nullable in `institutions`.
  - Add column `is_aicte_verified` BOOLEAN, default FALSE.
  - Provide strict regex validator for AICTE Permanent ID format.
  - Add search and lookup by AICTE Permanent ID.
- **Dependencies & Risks:**
  - In existing records, `code` is populated but `aicte_permanent_id` is empty. Migration must be non-destructive.

---

### Requirement 3: Institution-Wise Consolidated Case History
- **Official Problem Statement:** Complete historical ledger of all complaints, inquiries, regulatory actions, and compliance notices associated with an institution across all AICTE divisions.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/grievance.py`](file:///e:/Layn/SIH/backend/app/models/grievance.py), [`backend/app/api/v1/grievances.py`](file:///e:/Layn/SIH/backend/app/api/v1/grievances.py)
  - Tables & Columns: `grievances` (`institution_id`, `reference_number`, `status`, `created_at`).
  - Endpoints: `GET /api/v1/grievances?institution_id={id}`.
- **Existing Frontend Implementation:**
  - Filter by institution in SuperAdmin dashboard.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Existing query returns only student-submitted grievances belonging to that institution.
  - It does NOT consolidate regulatory cases, faculty complaints, RTI queries, inspection notices, or cases originating in different Bureaus (RB, PGRC, Approval Bureau).
  - Does not show cross-bureau correlation or repeat-offender patterns.
- **Exact Changes Required:**
  - Create endpoint `GET /api/v1/aicte/institutions/{id}/case-history` returning an aggregated chronological record of all cases across all Bureaus/Cells, categorized by Bureau, case severity, and disposal status.
  - Frontend: Build a dedicated "Institution Case Ledger" component.
- **Dependencies & Risks:**
  - Confidential complainant details in one bureau must not be inadvertently displayed in summary histories to unauthorized personnel.

---

### Requirement 4: Case ID, Receipt Date, Category, Status, and Responsible Bureau/Cell
- **Official Problem Statement:** Every case must possess an official Case ID, receipt date, standard regulatory category, lifecycle status, and attribution to the handling Bureau/Cell (e.g., Regulation Bureau, PGRC, Approval Bureau).
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/grievance.py`](file:///e:/Layn/SIH/backend/app/models/grievance.py), [`backend/app/models/category.py`](file:///e:/Layn/SIH/backend/app/models/category.py)
  - Tables & Columns: `grievances.reference_number`, `grievances.created_at`, `grievances.category_id`, `grievances.status`.
- **Existing Frontend Implementation:**
  - Columns in student, officer, and head dashboard tables.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Existing case reference is purely student-facing (`GRV-YYYY-XXXXXX`).
  - Categories are academic campus categories (Hostel, Mess, Exams, Wi-Fi), NOT AICTE regulatory categories (e.g., Capitation Fee / Non-Refund, Land/Infrastructure Deficit, Unapproved Courses, Faculty Service / Salary Non-Payment, Ragging / Harassment, Fraudulent Degrees).
  - No column or relationship for "Responsible Bureau/Cell" exists anywhere in `grievances` or related tables.
- **Exact Changes Required:**
  - Model `organizational_units` (representing RB, PGRC, Approval Bureau, Regional Offices).
  - Dedicated `aicte_cases` entity (or regulatory case model) carrying `case_number` (e.g. `AICTE/RB/2026/00142`), `receipt_date`, `category_code`, `status`, and `responsible_unit_id` (FK to `organizational_units`).
- **Dependencies & Risks:**
  - Existing `grievances` must continue operating for college students without breakage.

---

### Requirement 5: Assigned Officer, Last Action, Next Action, and Expected Disposal Date
- **Official Problem Statement:** Granular case operational tracking showing the current assigned bureau officer, the most recent procedural step taken, the required next procedural action, and statutory/SLA expected disposal date.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/assignment.py`](file:///e:/Layn/SIH/backend/app/models/assignment.py), [`backend/app/models/grievance.py`](file:///e:/Layn/SIH/backend/app/models/grievance.py#L36-L39)
  - Tables & Columns: `grievances.assigned_officer_id`, `grievance_assignments` table, `grievances.due_date`, `grievances.status_history`.
- **Existing Frontend Implementation:**
  - Officer assignment dropdown in [`frontend/src/pages/officer/OfficerDashboard.tsx`](file:///e:/Layn/SIH/frontend/src/pages/officer/OfficerDashboard.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - `grievance_assignments` strictly validates that the assigned officer is a member of the *college* where the complaint was filed! AICTE bureau officers cannot be assigned.
  - "Last action" is only captured as a status transition or internal note; there is no formal structured "Last Action" vs "Next Action" workflow tracking (e.g., "Explanation Received from Institute" -> Next Action: "Scrutiny Committee Review by 05-Nov-2026").
  - Disposal date is currently based on naive category SLA days; lacks AICTE Citizen Charter disposal timelines.
- **Exact Changes Required:**
  - Support assignment to `User` accounts holding `AICTE_BUREAU_OFFICER` role in the responsible `organizational_unit`.
  - Add `last_action_text`, `last_action_date`, `next_action_text`, `next_action_deadline`, and `expected_disposal_date` to the case model.
- **Dependencies & Risks:**
  - Role check in assignment service must distinguish between college-level officers and AICTE central bureau officers.

---

### Requirement 6: Cross-Bureau Overlap Detection
- **Official Problem Statement:** Automated intelligence alerting officers when multiple complaints, inquiries, or regulatory actions are concurrently active across different AICTE Bureaus/Cells (e.g., RB and PGRC) regarding the same institution.
- **Backend Implementation (Completed in Step 7, Phase D):**
  - Models: [`backend/app/models/aicte_overlap.py`](file:///e:/Layn/SIH/backend/app/models/aicte_overlap.py) (`AICTECaseOverlap`, `aicte_case_overlaps` table with canonical ordering `case_id_low < case_id_high`, unique constraint, explainable signals JSON, detection method, match score, review status).
  - Migration: [`backend/alembic/versions/e9f34a5b6c7d_step7_phase_d_aicte_case_overlaps_and_links.py`](file:///e:/Layn/SIH/backend/alembic/versions/e9f34a5b6c7d_step7_phase_d_aicte_case_overlaps_and_links.py).
  - Service: [`backend/app/services/aicte_overlap_service.py`](file:///e:/Layn/SIH/backend/app/services/aicte_overlap_service.py) (`AICTEOverlapService` providing bounded candidate generation by institution and AICTE PID, multi-signal scoring: Jaccard + Cosine subject similarity, Cosine description similarity, category match, cross-bureau detection, official reference match, temporal proximity, and allegation keywords).
  - Idempotency & Decision Preservation: Repeated scans update detection metadata but never overwrite human review determinations (`review_status != PENDING`).
  - Cross-Bureau Privacy: Unprivileged officers receive masked summaries (`[CONFIDENTIAL: Narrative shielded across bureau boundary]`).
  - Endpoints: `POST /api/v1/aicte/overlaps/detect/{case_id}`, `GET /api/v1/aicte/overlaps`, `GET /api/v1/aicte/overlaps/{overlap_id}`.
- **Frontend Implementation (Completed in Step 7, Phase D):**
  - Review Queue: [`frontend/src/pages/aicte/AICTEOverlapQueue.tsx`](file:///e:/Layn/SIH/frontend/src/pages/aicte/AICTEOverlapQueue.tsx).
  - Overlap Detail & Signals: [`frontend/src/pages/aicte/AICTEOverlapDetail.tsx`](file:///e:/Layn/SIH/frontend/src/pages/aicte/AICTEOverlapDetail.tsx).
- **Status:** **FULLY IMPLEMENTED (Step 7, Phase D)**

---

### Requirement 7: Related-Case Linking and Human Review
- **Official Problem Statement:** Bureau officers must be able to review flagged overlaps, verify whether cases are legitimately related, confirm or dismiss links, add coordination notes, and cross-reference related cases without merging official dockets.
- **Backend Implementation (Completed in Step 7, Phase D):**
  - Models: [`backend/app/models/aicte_overlap.py`](file:///e:/Layn/SIH/backend/app/models/aicte_overlap.py) (`AICTECaseLink`, `aicte_case_links` table with canonical ordering `case_id_low < case_id_high`, link type `DUPLICATE_OF` / `RELATED_TO`, active flag, audit notes).
  - Audit & Notification: Actions logged to `audit_logs` and notifications queued to `notification_outbox` for affected bureau officers.
  - Endpoints:
    - `POST /api/v1/aicte/overlaps/{overlap_id}/review`: record decision (`CONFIRMED_DUPLICATE`, `CONFIRMED_RELATED`, `REJECTED`, `DEFERRED`), require review notes, auto-manage administrative links.
    - `GET /api/v1/aicte/overlaps/{overlap_id}/history`: retrieve full review audit trail.
    - `GET /api/v1/aicte/overlaps/cases/{case_id}/links`: list active links for a case docket.
    - `POST /api/v1/aicte/overlaps/cases/{case_id}/links`: manually establish administrative case link.
    - `PATCH /api/v1/aicte/overlaps/links/{link_id}`: update/deactivate link.
- **Frontend Implementation (Completed in Step 7, Phase D):**
  - Review Modal: [`frontend/src/pages/aicte/AICTEOverlapReviewModal.tsx`](file:///e:/Layn/SIH/frontend/src/pages/aicte/AICTEOverlapReviewModal.tsx).
  - Docket Relationships Card: [`frontend/src/pages/aicte/AICTECaseRelationships.tsx`](file:///e:/Layn/SIH/frontend/src/pages/aicte/AICTECaseRelationships.tsx) embedded in [`frontend/src/pages/aicte/AICTECaseDetail.tsx`](file:///e:/Layn/SIH/frontend/src/pages/aicte/AICTECaseDetail.tsx).
- **Status:** **FULLY IMPLEMENTED (Step 7, Phase D)**
- **Statutory Safeguard Principle:** Cases retain independent dockets, case references, handling units, and official statuses. Confirming a duplicate or related link is an administrative relationship, not permission to merge or auto-close cases.

---

### Requirement 8: Integrated Real-Time Dashboard
- **Official Problem Statement:** A unified, real-time executive and operational command dashboard providing comprehensive visibility into complaint status, bureau caseloads, institutional compliance, and active escalations across AICTE.
- **Existing Backend Implementation:**
  - Files: [`backend/app/api/v1/analytics.py`](file:///e:/Layn/SIH/backend/app/api/v1/analytics.py)
  - Endpoints: `GET /api/v1/analytics/dashboard`.
- **Existing Frontend Implementation:**
  - [`frontend/src/pages/regulatory/RegulatoryDashboard.tsx`](file:///e:/Layn/SIH/frontend/src/pages/regulatory/RegulatoryDashboard.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - The current `/analytics/dashboard` returns single-dimension counts (total, pending, resolved, overdue) tailored to a college head or single-state regulatory viewer.
  - It does NOT aggregate by AICTE Bureau/Cell, does NOT report cross-bureau overlap counts, does NOT break down by AICTE regions, and does NOT support executive filtering by Bureau, Region, or Institution ID.
- **Exact Changes Required:**
  - Create dedicated endpoint `GET /api/v1/aicte/dashboard/overview` providing real-time metrics:
    - Total cases received, pending, under-process, disposed, transferred, escalated, overdue.
    - Bureau-wise caseload breakdown.
    - Region-wise workload breakdown.
    - Pending cross-bureau overlap reviews.
    - High-risk institutions (institutions with >N active cases across >=2 bureaus).
    - Ageing distribution and average disposal latency.
  - Build frontend: `AICTEIntegratedDashboard.tsx` with high-impact visualization cards, charts, and filtering controls.
- **Dependencies & Risks:**
  - Queries must use performant SQL aggregations (`GROUP BY`, indexed timestamps) to avoid slow dashboard loads on large databases.

---

### Requirement 9: Case Status Tracking (Pending, Under-Process, Disposed, Transferred, Escalated, Overdue)
- **Official Problem Statement:** Robust tracking of cases across standard statutory statuses: Pending, Under-Process, Disposed, Transferred, Escalated, and Overdue.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/enums.py`](file:///e:/Layn/SIH/backend/app/models/enums.py#L10-L22), [`backend/app/services/grievance_service.py`](file:///e:/Layn/SIH/backend/app/services/grievance_service.py#L32-L87)
  - Statuses: `SUBMITTED`, `UNDER_REVIEW`, `NEEDS_INFORMATION`, `ASSIGNED`, `INVESTIGATION_IN_PROGRESS`, `RESOLUTION_PROPOSED`, `RESOLVED`, `CLOSED`, `REOPENED`, `ESCALATED`, `REJECTED`.
- **Existing Frontend Implementation:**
  - [`frontend/src/components/common/StatusBadge.tsx`](file:///e:/Layn/SIH/frontend/src/components/common/StatusBadge.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Existing statuses reflect a campus grievance lifecycle.
  - "TRANSFERRED" status is MISSING completely from `GrievanceStatusEnum`.
  - "DISPOSED" is split between `RESOLVED` and `CLOSED`, but lacks formal regulatory disposal categories (e.g. Disposed with Directions, Disposed - Complaint Substantiated, Disposed - Withdrawn/Dismissed).
  - Overdue is calculated on the fly, but not indexed or mapped as a formal monitoring state.
- **Exact Changes Required:**
  - Standardize AICTE case status taxonomy:
    - `PENDING` (Received, awaiting bureau intake/triage)
    - `UNDER_PROCESS` (Under investigation, scrutiny, notice issued)
    - `TRANSFERRED` (Transferred to another Bureau/Cell or Regional Office)
    - `ESCALATED` (Escalated to Bureau Head or Member Secretary)
    - `DISPOSED` (Formally resolved/closed with final disposal order)
    - `OVERDUE` (Operational flag when `current_date > expected_disposal_date` and status is active)
  - Implement formal transition rules with mandatory action reasons.
- **Dependencies & Risks:**
  - Adding new statuses to Python Enum and DB schema requires clean migration without invalidating existing `grievances` status values.

---

### Requirement 10: Bureau-Wise and Region-Wise Workload
- **Official Problem Statement:** Workload analytics displaying the volume of cases handled by each Bureau/Cell (RB, PGRC, Approval, etc.) and each AICTE Regional Office (NRO, WRO, SRO, CRO, ERO, NWRO, SWRO).
- **Existing Backend Implementation:**
  - None.
- **Existing Frontend Implementation:**
  - None.
- **Status:** **MISSING**
- **Gap Analysis:**
  - Neither Bureaus nor Regional Offices exist as database entities.
  - Workload cannot be computed by Bureau or Region in current code.
- **Exact Changes Required:**
  - Implement `GET /api/v1/aicte/analytics/workload-distribution`:
    - Bureau breakdown: active, pending, disposed, escalated count per Bureau.
    - Region breakdown: active, pending, disposed, escalated count per AICTE Regional Office.
  - Add visual stacked bar and donut charts in the Integrated Dashboard.
- **Dependencies & Risks:**
  - Dependent on `organizational_units` table and `aicte_cases` linking.

---

### Requirement 11: Complete Chronological Action and Transfer History
- **Official Problem Statement:** Complete immutable chronological audit trail documenting every action, notice, committee review, hearing, officer assignment, and inter-bureau transfer for every case.
- **Existing Backend Implementation:**
  - Files: [`backend/app/models/grievance.py`](file:///e:/Layn/SIH/backend/app/models/grievance.py#L61-L74), [`backend/app/models/assignment.py`](file:///e:/Layn/SIH/backend/app/models/assignment.py)
  - Tables & Columns: `grievance_status_history`, `grievance_assignments`, `audit_logs`.
- **Existing Frontend Implementation:**
  - Timeline component in grievance detail view.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - `grievance_status_history` only records status enum changes.
  - There is NO mechanism for **Case Transfers** (e.g. transferring a case from PGRC to RB when regulatory violations are discovered, recording transferring officer, receiving officer, transfer reason, and receiving bureau acceptance).
  - Procedural case actions (e.g., Show Cause Notice issued, Institution explanation submitted, Hearing date fixed, Compliance report accepted) cannot be recorded in `grievance_status_history`.
- **Exact Changes Required:**
  - Model `case_transfers`: `case_id`, `from_unit_id`, `to_unit_id`, `transferred_by_user_id`, `transfer_reason`, `status` (`PENDING_ACCEPTANCE`, `ACCEPTED`, `REJECTED`), `accepted_by_user_id`, `transferred_at`, `accepted_at`.
  - Model `case_actions`: `case_id`, `action_type`, `action_title`, `description`, `performed_by_user_id`, `document_attachment_id`, `created_at`.
  - API endpoint `GET /api/v1/aicte/cases/{id}/timeline` combining status history, assignments, transfers, and procedural actions into one unified chronological stream.
- **Dependencies & Risks:**
  - Transferring a case must re-scope officer permissions and re-route notifications cleanly.

---

### Requirement 12: Search and Filtering by Institution, AICTE ID, Case ID, Bureau/Cell, Region, Category, Status, and Date Range
- **Official Problem Statement:** Multi-criteria search and filter engine across all parameters (Institution Name, AICTE Permanent ID, Case Reference ID, Bureau/Cell, Region, Regulatory Category, Lifecycle Status, Date Range).
- **Existing Backend Implementation:**
  - Files: [`backend/app/api/v1/grievances.py`](file:///e:/Layn/SIH/backend/app/api/v1/grievances.py#L81-L154)
  - Filters: `status`, `category_id`, `priority`, `institution_id`, `from_date`, `to_date`, `search` (text search on title/ref/desc).
- **Existing Frontend Implementation:**
  - Basic filter bar in student and officer views.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Cannot search by `aicte_permanent_id`.
  - Cannot filter by `bureau_id` or `region`.
  - Full-text search only operates across `title`, `description`, and `reference_number` of student grievances.
  - Pagination lacks total count metadata (`limit` and `offset` used without returning `total_records`).
- **Exact Changes Required:**
  - Implement comprehensive query endpoint `GET /api/v1/aicte/cases`:
    - Parameters: `search`, `institution_id`, `aicte_permanent_id`, `case_id`, `unit_id` (Bureau), `region`, `category_code`, `status`, `from_date`, `to_date`, `has_overlap` (boolean), `is_overdue` (boolean), `page`, `page_size`.
    - Returns: paginated response with total count, active filters, and result array.
  - Frontend: Build advanced multi-facet filter bar in the Integrated Dashboard.
- **Dependencies & Risks:**
  - Requires composite indexes on `(status, unit_id, created_at)` and `(institution_id, status)` to ensure sub-second response on large datasets.

---

### Requirement 13: Notifications for Overlaps, Pending Cases, Deadlines, and Escalations
- **Official Problem Statement:** Automated event-driven and scheduled notifications alerting officers to newly detected cross-bureau overlaps, approaching SLA deadlines, stalled pending cases, and automatic escalations.
- **Existing Backend Implementation:**
  - Files: [`backend/app/services/notification_service.py`](file:///e:/Layn/SIH/backend/app/services/notification_service.py), [`backend/app/services/scheduler.py`](file:///e:/Layn/SIH/backend/app/services/scheduler.py), [`backend/app/services/escalation_service.py`](file:///e:/Layn/SIH/backend/app/services/escalation_service.py)
  - Tables & Columns: `notifications`, `notification_outbox`.
- **Existing Frontend Implementation:**
  - Notification dropdown in [`frontend/src/layouts/DashboardLayout.tsx`](file:///e:/Layn/SIH/frontend/src/layouts/DashboardLayout.tsx).
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Background scheduler exists (`SLABackgroundScheduler`) and processes SLA warnings and escalations.
  - However, notifications are only sent to Students and College Officers.
  - There are NO notifications for:
    - Cross-bureau overlap detected (should notify case officers in both involved Bureaus).
    - Case transferred (should notify receiving Bureau Head).
    - Supervisory escalations to AICTE Bureau Head or Member Secretary.
- **Exact Changes Required:**
  - Add notification triggers:
    - `notify_cross_bureau_overlap(overlap_record, db)`
    - `notify_case_transferred(transfer_record, db)`
    - `notify_bureau_escalation(case_record, db)`
  - Integrate these triggers into the background scheduler and case service.
- **Dependencies & Risks:**
  - Must use the transactional outbox (`notification_outbox`) to prevent email delivery stalls from blocking HTTP requests.

---

### Requirement 14: Reports and Analytics (Institution-Wise, Bureau-Wise, Region-Wise, Ageing, Disposal-Rate, Overlap Reports)
- **Official Problem Statement:** Comprehensive analytical reports and CSV exports covering institution-wise compliance, bureau-wise throughput, regional performance, pending case ageing brackets, disposal rates, and cross-bureau overlap summaries.
- **Existing Backend Implementation:**
  - Files: [`backend/app/api/v1/analytics.py`](file:///e:/Layn/SIH/backend/app/api/v1/analytics.py#L152-L208)
  - Endpoint: `GET /api/v1/analytics/export/csv`.
- **Existing Frontend Implementation:**
  - "Export Compliance CSV" button in Regulatory Dashboard.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - Current CSV export outputs simple columns (`Reference Number`, `Title`, `Institution`, `Category`, `Status`, `Priority`, `Assigned Officer`, `Created At`, `Resolved At`).
  - Lacks all AICTE reporting dimensions: AICTE Permanent ID, Bureau/Cell, Region, Ageing Days, Disposal Duration, Overlap Status, Disposed Action Type.
  - No dedicated endpoints for Ageing Reports (<15d, 15-30d, 30-60d, >60d) or Bureau Disposal-Rate comparisons.
- **Exact Changes Required:**
  - Implement endpoints:
    - `GET /api/v1/aicte/reports/ageing`: breakdown of pending cases by age buckets.
    - `GET /api/v1/aicte/reports/disposal-rates`: bureau-by-bureau disposal velocity and rate.
    - `GET /api/v1/aicte/reports/overlaps`: summary of all active and resolved overlaps.
    - `GET /api/v1/aicte/reports/export/csv`: comprehensive AICTE report CSV with injection protection.
- **Dependencies & Risks:**
  - CSV Formula Injection protection (`sanitize_csv_value`) must be strictly applied on all export fields.

---

### Requirement 15: Role-Based Access and Confidential Information Protection
- **Official Problem Statement:** Multi-level role-based authorization ensuring AICTE Bureau Officers, Bureau Heads, Regional Officers, and Senior Authorities see only what is permissible within their jurisdiction, while strictly shielding confidential complainant identities, internal notes, and sensitive evidence across bureau boundaries.
- **Existing Backend Implementation:**
  - Files: [`backend/app/core/permissions.py`](file:///e:/Layn/SIH/backend/app/core/permissions.py), [`backend/app/models/enums.py`](file:///e:/Layn/SIH/backend/app/models/enums.py)
  - Roles: `STUDENT`, `COLLEGE_OFFICER`, `INSTITUTION_HEAD`, `REGULATORY_ADMIN`, `SUPER_ADMIN`.
- **Existing Frontend Implementation:**
  - `ProtectedRoute.tsx` role enforcement.
- **Status:** **PARTIALLY IMPLEMENTED**
- **Gap Analysis:**
  - `REGULATORY_ADMIN` is currently a single-state geographical inspector, NOT an AICTE Bureau official.
  - No representation for AICTE Central Bureau Officials (Regulation Bureau Officer, PGRC Officer, Approval Bureau Officer).
  - No distinction between viewing *metadata existence* of a cross-bureau overlap vs viewing *confidential complaint text/attachments*.
- **Exact Changes Required:**
  - Define AICTE operational roles:
    - `AICTE_BUREAU_OFFICER`: manages cases within assigned Bureau/Cell.
    - `AICTE_BUREAU_HEAD`: oversees Bureau workload, approves transfers, reviews escalations.
    - `AICTE_REGIONAL_OFFICER`: oversees regional jurisdiction.
    - `AICTE_EXECUTIVE`: holistic read-only / oversight view across all Bureaus.
  - Implement **Confidentiality Shield Protocol**: When Bureau A views an overlap involving Bureau B, the response provides only non-confidential metadata (Case ID, Category, Institution, Overlap Score, Status). Complainant name, email, phone, raw complaint text, and internal notes remain redacted unless explicit inter-bureau coordination is granted.
- **Dependencies & Risks:**
  - Must not break existing roles (`STUDENT`, `COLLEGE_OFFICER`, `INSTITUTION_HEAD`, `SUPER_ADMIN`).

---

## 3. Existing Model Evaluation: Can Grievances Represent AICTE Cases?

### Comprehensive Schema & Workflow Analysis

A central question of the audit is whether the existing `Grievance` model can directly serve as an AICTE Case, or whether a dedicated model is required.

#### Current Constraints of `grievances` Table:
1. **Mandatory Student Affiliation:**  
   `student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)`  
   `grievance_service.py` explicitly validates:
   ```python
   user_inst_ids = get_user_institution_ids(current_user, db)
   if user_inst_ids and requested_institution_id not in user_inst_ids:
       raise HTTPException(403, "Unauthorized: You can only submit grievances to institutions you are actively registered with.")
   ```
2. **Missing Regulatory Initiator Types:**  
   AICTE cases arise from:
   - Faculty members (not students).
   - Institution management / Trust representatives.
   - Whistleblowers / Anonymous stakeholders.
   - Suo-motu regulatory scrutiny (initiated directly by Regulation Bureau or Regional Office).
   - Transferred regulatory proceedings from other statutory bodies (UGC, Ministry of Education).  
   None of these fit into a required `student_id` foreign key.
3. **Missing Bureau / Cell Architecture:**  
   `grievances` only links to `institution_id` (the college) and `assigned_officer_id` (a college staff member). It has no concept of an AICTE Bureau/Cell, an AICTE Case ID format, or inter-bureau transfer.
4. **Different Lifecycle Semantics:**  
   A campus grievance follows: *Submitted -> Under Review -> Assigned -> Investigation -> Resolved -> Closed*.  
   An AICTE regulatory case follows: *Receipt -> Bureau Triage -> Show Cause Notice -> Institute Explanation -> Scrutiny Committee -> Hearing -> Final Disposal Order / Compliance Directive*.
5. **Regression Risk to Existing Student Portal:**  
   Overloading `grievances` with columns like `bureau_id`, `transferred_from_unit_id`, `case_type`, making `student_id` nullable, and changing allowed transitions would introduce significant regression risk to existing student grievance tests (`test_step3_grievances.py`, etc.) and the student submission portal.

### Architectural Recommendation: Two-Tier Bridged Model

Instead of forcing a single model to do two fundamentally different jobs, the system will use a **Two-Tier Bridged Model**:

```
+-----------------------------------+          +-----------------------------------------+
|     Existing Student Portal       |          |        AICTE Integrated Platform        |
|-----------------------------------|          |-----------------------------------------|
|  Model: Grievance                 |          |  Model: AICTECase                       |
|  - College-level student issues   |          |  - Cross-Bureau regulatory tracking     |
|  - Requires student account       |          |  - Originates from RB, PGRC, Faculty,   |
|  - Reference: GRV-YYYY-XXXX       |          |    Stakeholder, or Escalated Grievance  |
|  - Handled by College Officers    |          |  - Reference: AICTE/{BUREAU}/{YEAR}/NNN |
+-----------------+-----------------+          |  - Handled by AICTE Bureau Officers     |
                  |                            +--------------------+--------------------+
                  | (When escalated to AICTE)                       |
                  +-------------------- source_grievance_id --------+
```

1. **Keep `grievances` fully functional** for campus students, college officers, and heads without altering existing foreign keys or workflows.
2. **Introduce `aicte_cases`** to represent AICTE-level cases across Bureaus/Cells.
3. **Bridge via `source_grievance_id`**: If a college grievance is escalated to AICTE (Level 3 Regulatory Escalation), an `aicte_cases` record is automatically generated with `source_grievance_id = grievance.id`.
4. **Support Direct AICTE Ingestion**: Cases initiated directly by RB, PGRC, faculty complaints, RTI, or whistleblowers are created directly in `aicte_cases` without requiring a student account.

---

## 4. Institution Identity & Permanent ID Audit

### Current State
- `institutions.code`: stores a string such as `NITD01` or `INST001`.
- `institutions.verification_status`: values `PENDING`, `VERIFIED`, `REJECTED`.
- `institutions.name`: string indexed for search.

### Risks Identified
1. **Collisions with Common Names:** Multiple private colleges share near-identical names (e.g., "Saraswati Institute of Technology", "Apex College of Engineering") in different districts or states. Searching by name alone leads to dangerous cross-institution misattributions.
2. **Unverified Identifiers:** Currently, when an institution head registers, they input `institution_code`. There is no verification against the official AICTE approved institution list.
3. **Lack of Alias Resolution:** In formal complaints, complainants write informal abbreviations (e.g., "NIT Delhi" vs "National Institute of Technology Delhi", "COEP" vs "College of Engineering Pune").

### Safe Remediation Strategy
1. Add `aicte_permanent_id` (VARCHAR(50), nullable, unique where not null, indexed) to `institutions`.
2. Add `is_aicte_verified` (BOOLEAN, default False).
3. Introduce `institution_aliases` table (`institution_id`, `alias_name`, `created_at`) allowing fuzzy/phonetic search while resolving strictly to the single canonical verified institution record.
4. AICTE Permanent ID format validation: enforces standard AICTE patterns (e.g., `1-\d{9,11}`).

---

## 5. Bureau/Cell Representation Audit

### Current State
- There is **no database table** representing AICTE Bureaus, Cells, or Regional Offices.
- `InstitutionMembership.department` is a freeform text string scoped to a college.
- `RegulatoryJurisdiction` maps a user to a `state` (e.g., "Delhi"), not to a Bureau or Cell.

### Representation of AICTE Operating Units
AICTE operates via distinct functional Bureaus and Cells:
- **Regulation Bureau (RB):** Enforcement of AICTE Regulations, approval compliance, unapproved institutions, fee anomalies, land/infra verification.
- **Public Grievance Redressal Cell (PGRC):** Central grievance cell handling complaints from students, faculty, staff, and public.
- **Approval Bureau (AB):** Annual approvals, extension of approval (EOA), closure of courses, increase/decrease in intake.
- **Regional Offices (ROs):** Northern, Western, Southern, Central, Eastern, North-West, South-West regional administration.

### Proposed Database Entity: `organizational_units`
To avoid hardcoding Bureaus and to support future reorganizations, we require a database-backed table:
- `id` (PK)
- `code` (e.g. `RB`, `PGRC`, `AB`, `RO_NORTH`, `RO_WEST`, `RO_SOUTH`)
- `name` (e.g. "Regulation Bureau", "Public Grievance Redressal Cell")
- `unit_type` (ENUM: `BUREAU`, `CELL`, `REGIONAL_OFFICE`, `HEADQUARTERS`)
- `description` (TEXT)
- `email` (VARCHAR)
- `is_active` (BOOLEAN)
- `parent_unit_id` (FK to self, nullable, for regional offices or sub-cells)

This allows adding new Bureaus/Cells dynamically via administrative configuration without database migrations or code redeployment.

---

## 6. Cross-Bureau Overlap Detection Audit

### Existing Detector Inspection
- Code location: [`ai-service/similarity/duplicate_detector.py`](file:///e:/Layn/SIH/ai-service/similarity/duplicate_detector.py).
- Logic: Takes incoming text, constructs a corpus from existing complaints in the **same institution**, computes cosine similarity via Scikit-Learn TF-IDF vectorizer, flags duplicate if similarity $\ge 0.60$.

### Why It Fails Cross-Bureau Problem Statement
1. **Wrong Scope:** Filters by `Grievance.institution_id == institution_id`. It never compares across different Bureaus.
2. **False Equivalence (Duplicate vs Overlap):**
   - A *duplicate* is the same complaint submitted twice by the same student or classmates.
   - An *overlap* is when **Bureau A (RB)** has a regulatory case regarding unapproved courses at College X, while **Bureau B (PGRC)** receives a grievance from faculty at College X regarding withheld salaries. These are distinct dockets that must remain separate, but **overlap context must be provided to both bureau officers**.
3. **No Review Workflow:** No mechanism for an officer to see "Potential Overlap with Case AICTE/RB/2026/0042", view similarity reasons, and mark as "Confirmed Overlap — Coordinated Review" or "Dismissed — Unrelated".
4. **Cross-Bureau Privacy Risk:** If raw complaint text is displayed across Bureaus without role verification, confidential complainant identities (e.g. student whistleblowers) could be exposed to unauthorized officials.

### Proposed Solution
1. Distinct `CrossBureauOverlapDetector` service that:
   - Identifies concurrent cases for the same `aicte_permanent_id` across different `organizational_units`.
   - Evaluates multi-factor similarity: institution identity (100% match) + regulatory topic similarity + keyword allegation overlap.
   - Generates persistent `case_overlaps` records.
2. Human-in-the-loop review interface allowing officers to confirm or dismiss overlap flags.
3. Privacy-preserving metadata shield: cross-bureau view displays Case Number, Category, Handling Bureau, and Overlap Score, but redacts complainant personal identity.

---

## 7. Dashboard and Analytics Audit

### Metric-by-Metric Feasibility Matrix

| Metric | Official Requirement | Existing API / Query | Status | Required Changes |
| :--- | :--- | :--- | :--- | :--- |
| **Total Cases Received** | Yes | `/analytics/dashboard` (grievance count) | Partially | Add AICTE case counting with bureau filtering |
| **Pending Cases** | Yes | `/analytics/dashboard` (pending statuses) | Partially | Scope to AICTE case statuses |
| **Under-Process Cases** | Yes | `/analytics/dashboard` (in_investigation) | Partially | Map to `UNDER_PROCESS` status |
| **Disposed Cases** | Yes | `/analytics/dashboard` (resolved statuses) | Partially | Map to `DISPOSED` status |
| **Transferred Cases** | Yes | None | **Missing** | Count cases with status `TRANSFERRED` or from `case_transfers` |
| **Escalated Cases** | Yes | `/analytics/dashboard` (`status == ESCALATED`) | Partially | Track Bureau-level escalations |
| **Overdue Cases** | Yes | `/analytics/dashboard` (`due_date < now`) | Partially | Compute using `expected_disposal_date` |
| **Cases Approaching Deadlines** | Yes | `escalation_service.py` (background check) | Partially | Expose count in dashboard API (within 7d, within 48h) |
| **Potential Overlaps Awaiting Review** | Yes | None | **Missing** | Count `case_overlaps WHERE status = 'PENDING_REVIEW'` |
| **Bureau-Wise Workload** | Yes | None | **Missing** | `COUNT(*) ... GROUP BY unit_id` |
| **Region-Wise Workload** | Yes | None | **Missing** | `COUNT(*) ... GROUP BY region` |
| **Institution-Wise Consolidated History** | Yes | None | **Missing** | Aggregated case counts and status grouped by institution |
| **Pending-Case Ageing** | Yes | None | **Missing** | Age brackets: `<15d`, `15-30d`, `30-60d`, `>60d` |
| **Disposal Rate** | Yes | `/analytics/dashboard` (derived percentage) | Partially | Formal disposal rate: $(Disposed / Total Received) \times 100$ |
| **Monthly/Quarterly Trends** | Yes | `/analytics/dashboard` (last 6 months) | Partially | Group by Month & Quarter with Bureau breakdown |

---

## 8. Authorization and Privacy Audit

### Current Role Matrix vs AICTE Operational Requirements

Existing roles in [`backend/app/models/enums.py`](file:///e:/Layn/SIH/backend/app/models/enums.py):
1. `STUDENT`: Campus student submitting grievances to their own college.
2. `COLLEGE_OFFICER`: Staff officer inside a college redressal committee.
3. `INSTITUTION_HEAD`: Principal / Director of a college.
4. `REGULATORY_ADMIN`: Regional government inspector assigned to geographical states.
5. `SUPER_ADMIN`: Technical platform administrator.

### Why `REGULATORY_ADMIN` Cannot Represent AICTE Bureau Officials
- A `REGULATORY_ADMIN` is scoped by `state` (e.g., Delhi, Maharashtra).
- AICTE Bureau Officials are **central functional officers** located in New Delhi headquarters (Regulation Bureau, PGRC, Approval Bureau) whose jurisdiction spans **all institutions nationwide**, but is partitioned by **functional domain** (Regulations vs Grievances vs Approvals), not merely by state.
- In addition, AICTE Regional Offices (e.g. RO Northern, RO Western) have jurisdiction over multi-state zones.

### Recommended AICTE Role Architecture
To avoid disrupting existing college roles, add:
- `AICTE_BUREAU_OFFICER`: Case handler within an AICTE Bureau/Cell (e.g., RB Scrutiny Officer, PGRC Handling Officer).
- `AICTE_BUREAU_HEAD`: Supervisory head of an AICTE Bureau/Cell (e.g., Advisor-I Regulation, In-charge PGRC).
- `AICTE_REGIONAL_OFFICER`: Officer in an AICTE Regional Office.
- `AICTE_MEMBER_SECRETARY`: Executive apex authority with holistic cross-bureau visibility.

### Confidential Information Protection Rules
1. **Complainant Identity Protection:** Whistleblower, student, or faculty identities must be masked to unauthorized bureau viewers unless explicit cross-bureau coordination is approved.
2. **Internal Notes Confidentiality:** Internal notes in Bureau A are strictly inaccessible to Bureau B.
3. **Evidence Protection:** Sensitive documents (financial audit reports, inquiry findings) are internal to the handling bureau.

---

## 9. Conclusion of Audit

The existing EduResolve AI foundation is clean, modular, and well-architected. It already possesses robust database connectivity, authentication, auditing, scheduling, and AI classification primitives. 

However, it currently models **campus-level student grievance redressal**, whereas the problem statement requires an **inter-bureau regulatory oversight and case tracking system for AICTE central headquarters and regional offices**.

The transition requires:
1. Adding AICTE Permanent ID and alias lookup to `institutions`.
2. Introducing `organizational_units` (Bureaus/Cells).
3. Introducing `aicte_cases` with full transfer and action history.
4. Introducing `case_overlaps` and human review workflows.
5. Providing integrated dashboard analytics by Bureau, Region, and Ageing.

Detailed entity models, relationship diagrams, and the phased implementation roadmap are defined in [`docs/AICTE_CROSS_BUREAU_DESIGN.md`](file:///e:/Layn/SIH/docs/AICTE_CROSS_BUREAU_DESIGN.md).

---

## 10. Phase B Implementation Status (Completed)

**Migration Revision:** `c7b12d3e4f5a` (Parent: `59f5f8fb2f6b`)  
**Implementation Date:** October 2026  
**Status:** **PHASE B COMPLETED**

### Delivered Features in Phase B
1. **Extended Institution Identity:**
   - Added `aicte_permanent_id` (VARCHAR(50), nullable, unique, indexed).
   - Added `region` (VARCHAR(50), nullable, indexed).
   - Added `is_aicte_verified` (Boolean, default False, not null).
   - Preserved all existing institution records, student grievances, and memberships without regressions.
2. **Institution Aliases (`institution_aliases` table):**
   - Columns: `id`, `institution_id` (FK -> `institutions.id`), `alias_name`, `normalized_alias`, `source`, `is_verified`, `created_by_user_id`, `created_at`, `updated_at`.
   - Unique constraint `uq_institution_normalized_alias` (`institution_id`, `normalized_alias`).
   - Alias search resolution integrated into institution queries without merging distinct entities.
3. **AICTE Organizational Units (`organizational_units` table):**
   - Columns: `id`, `code` (VARCHAR(50), unique, indexed), `name`, `unit_type` (`BUREAU`, `CELL`, `REGIONAL_OFFICE`, `OTHER`), `description`, `parent_unit_id` (FK -> `organizational_units.id`), `region_code`, `is_active`, `created_at`, `updated_at`.
   - Cycle detection preventing self-referential or cyclic parent hierarchies.
   - Idempotently seeded initial units: `RB` (Regulation Bureau), `PGRC` (Public Grievance Redressal Cell), `AB` (Approval Bureau), `RO_NORTH` (Regional Office, North), `RO_WEST` (Regional Office, West), `RO_SOUTH` (Regional Office, South).
4. **Bureau Memberships (`bureau_memberships` table):**
   - Columns: `id`, `user_id` (FK -> `users.id`), `organizational_unit_id` (FK -> `organizational_units.id`), `membership_role`, `designation`, `is_active`, `assigned_by_user_id`, `created_at`, `updated_at`.
   - Unique constraint `uq_user_bureau_membership` (`user_id`, `organizational_unit_id`, `is_active`).
   - Server-side role isolation: College officers, students, and institution heads cannot assign or assume bureau memberships without Super Admin authorization.
5. **Frontend Super Admin Dashboard Integration:**
   - New "AICTE Bureaus & Units" tab in SuperAdmin dashboard and sidebar navigation (`/admin/bureaus`).
   - AICTE ID verification action modal with audit trail recording.
   - Institutional alias management modal (add, list, delete).
   - Organizational unit management (create, edit, toggle active, seed baseline units).
   - Bureau membership management modal (assign personnel with roles, revoke membership).

---

## 11. Phase C Implementation Status (Completed)

**Migration Revision:** `d8c23e4f5a6b` (Parent: `c7b12d3e4f5a`)  
**Implementation Date:** October 2026  
**Status:** **PHASE C COMPLETED**

### Delivered Features in Phase C

1. **Dedicated AICTE Case Model (`aicte_cases` table):**
   - Columns: `id`, `case_reference` (VARCHAR(64), unique, indexed), `institution_id` (FK -> `institutions.id`), `source_type` (`DIRECT`, `CAMPUS_REFERRAL`, `REGULATORY_INQUIRY`, `WHISTLEBLOWER`, `OTHER`), `source_grievance_id` (FK -> `grievances.id`, nullable), `official_reference_number` (VARCHAR(100), nullable, indexed), `received_at`, `complainant_type` (`STUDENT`, `FACULTY`, `STAKEHOLDER`, `INSTITUTION`, `PUBLIC_AUTHORITY`, `ANONYMOUS`, `OTHER`), `category` (VARCHAR(100), indexed), `subject` (VARCHAR(255)), `description`, `status` (`RECEIVED`, `PENDING_REVIEW`, `UNDER_PROCESS`, `AWAITING_RESPONSE`, `TRANSFER_PENDING`, `TRANSFERRED`, `ESCALATED`, `DISPOSED`, `CLOSED`, `REOPENED`), `current_unit_id` (FK -> `organizational_units.id`), `assigned_officer_id` (FK -> `users.id`, nullable), `region` (VARCHAR(50), nullable, indexed), `priority` (`LOW`, `NORMAL`, `HIGH`, `URGENT`), `last_action_at`, `next_action_required`, `next_action_due_at`, `expected_disposal_at`, `disposed_at`, `created_by_user_id` (FK -> `users.id`), `created_at`, `updated_at`.
   - Distinct lifecycle workflow separate from student campus grievances.

2. **Procedural Case Action History (`case_actions` table):**
   - Columns: `id`, `case_id` (FK -> `aicte_cases.id`, CASCADE), `action_type` (`INTAKE`, `ASSIGNMENT`, `INITIAL_SCRUTINY`, `INFO_REQUESTED`, `EXPLANATION_RECEIVED`, `COMMITTEE_REVIEW`, `HEARING_SCHEDULED`, `HEARING_COMPLETED`, `COMPLIANCE_VERIFIED`, `TRANSFER_INITIATED`, `TRANSFER_ACCEPTED`, `ESCALATION`, `DISPOSAL_ORDER`, `STATUS_UPDATE`, `REOPENED`, `NOTE_RECORDED`), `action_title`, `action_description`, `previous_status`, `new_status`, `unit_id` (FK -> `organizational_units.id`), `performed_by_user_id` (FK -> `users.id`), `action_at`, `remarks`, `supporting_document_ref`, `next_action_required`, `next_action_due_at`, `created_at`.
   - Immutable procedural audit ledger with state-machine lifecycle validation.

3. **Direct Case Intake & Controlled Campus Grievance Referral:**
   - Direct intake generates collision-free case references (`AICTE-YYYY-XXXXXX`).
   - Campus grievance referral workflow preserves original grievance history while creating linked AICTE case (`source_type="CAMPUS_REFERRAL"`) and prevents duplicate referrals within transactions.

4. **Consolidated Institution Profile API:**
   - `GET /api/v1/aicte/institutions/{id}/consolidated-history` aggregates verified AICTE identifiers, historical aliases, total/active/disposed case counts, multi-bureau distribution (RB, PGRC, AB, ROs), and case docket.

5. **Frontend AICTE Suite:**
   - `AICTEIntegratedDashboard.tsx`: Cross-Bureau case overview and KPI analytics.
   - `AICTECaseList.tsx`: Paginated, searchable case directory with status, Bureau, and priority filters.
   - `AICTECaseDetail.tsx`: Comprehensive case view, assignment controls, and action history.
   - `AICTEInstitutionProfile.tsx`: Consolidated institutional profile with cross-bureau case docket.
   - `ProceduralActionLog.tsx` & `ProceduralActionModal.tsx`: Procedural action timeline and entry modal.
   - `CreateAICTECaseModal.tsx` & `ReferGrievanceModal.tsx`: Authorized direct intake and grievance referral workflows.

---

## 12. Phase D Implementation Status (Completed)

**Migration Revision:** `e9f34a5b6c7d` (Parent: `d8c23e4f5a6b`)  
**Implementation Date:** October 2026  
**Status:** **PHASE D COMPLETED**

### Delivered Features in Phase D
1. **Dedicated Cross-Bureau Overlap Table (`aicte_case_overlaps`):**
   - Columns: `id`, `case_a_id`, `case_b_id`, `institution_id`, `status` (`PENDING_REVIEW`, `CONFIRMED_DUPLICATE`, `CONFIRMED_RELATED`, `REJECTED`, `DEFERRED`), `similarity_score`, `match_reasons`, `signals`, `reviewed_by_user_id`, `reviewed_at`, `review_notes`, `created_at`, `updated_at`.
   - Canonical ordering constraint `case_a_id < case_b_id` and unique constraint `uq_aicte_case_overlaps_pair`.
2. **Case Linking Table (`aicte_case_links`):**
   - Columns: `id`, `case_a_id`, `case_b_id`, `institution_id`, `link_type` (`DUPLICATE_OF`, `RELATED_TO`), `coordination_notes`, `linked_by_user_id`, `is_active`, `created_at`, `updated_at`.
   - Preserves independent statutory dockets, reference numbers, and life-cycles without automated merging or case destruction.
3. **Multi-Signal Overlap Detection Engine:**
   - Jaccard + Cosine word overlap on subjects, TF-IDF cosine similarity on descriptions, category concordance, official reference number exact matching, temporal proximity (90 days), and regulatory allegation keywords.
   - Narrative redaction protecting complainant identities and private details across unauthorized Bureaus.
4. **Human Review Lifecycle & API Endpoints:**
   - `POST /api/v1/aicte/cases/{id}/detect-overlaps`: Scan for potential overlaps.
   - `GET /api/v1/aicte/overlaps/pending`: Paginated queue of unreviewed overlap alerts.
   - `POST /api/v1/aicte/overlaps/{id}/review`: Decision workflow with mandatory notes.
   - `POST /api/v1/aicte/cases/{id}/links`: Coordinated case linking.
5. **Frontend Overlap Management Suite:**
   - `AICTEOverlapQueue.tsx`, `AICTEOverlapDetail.tsx`, `AICTECaseRelationships.tsx`.

---

## 13. Phase E Implementation Status (Completed)

**Migration Revision:** `f0a45b6c7d8e` (Parent: `e9f34a5b6c7d`)  
**Implementation Date:** October 2026  
**Status:** **PHASE E COMPLETED**

### Delivered Features in Phase E
1. **Formal Inter-Bureau Transfer Ledger (`aicte_case_transfers` table):**
   - Columns: `id`, `case_id` (FK -> `aicte_cases.id`, CASCADE), `from_unit_id` (FK -> `organizational_units.id`), `to_unit_id` (FK -> `organizational_units.id`), `initiated_by_user_id` (FK -> `users.id`), `proposed_assignee_id` (FK -> `users.id`, nullable), `transfer_reason` (Text, required substantive reason), `handover_summary` (Text, confidential context), `transfer_status` (`PENDING_ACCEPTANCE`, `ACCEPTED`, `REJECTED`, `CANCELLED`), `prior_case_status` (VARCHAR(50), required for exact restoration), `initiated_at`, `responded_at`, `responded_by_user_id` (FK -> `users.id`, nullable), `response_notes` (Text, nullable), `accepted_assignee_id` (FK -> `users.id`, nullable), `created_at`, `updated_at`.
   - Check constraint `ck_case_transfer_distinct_units`: `from_unit_id != to_unit_id`.
   - Optimized indexes on `case_id`, `transfer_status`, `from_unit_id`, `to_unit_id`, and `initiated_at`.
2. **Transfer Lifecycle & State Machine:**
   - **Initiate Transfer:** Authorized officer in originating Bureau proposes transfer with required reason and optional receiving officer. Validates destination unit activity and proposed officer's active membership. Case moves to `TRANSFER_PENDING`. **Handling unit (`current_unit_id`) and assigned officer remain strictly unchanged until formal acceptance.**
   - **Accept Transfer:** Receiving Bureau official accepts transfer. Atomically sets transfer status to `ACCEPTED`, updates case `current_unit_id = to_unit_id`, optionally reassigns to receiving officer, advances case status to `TRANSFERRED`, logs `CaseAction`, writes audit event, and queues notification to originating unit.
   - **Reject Transfer:** Receiving Bureau official declines proposal with mandatory substantive reason. Atomically marks transfer `REJECTED`, preserves originating unit and assignment, restores case to exact `prior_case_status` (e.g. `UNDER_PROCESS`), logs procedural action, writes audit event, and queues outbox notification.
   - **Cancel Transfer:** Initiator or Super Admin cancels pending proposal prior to receiving decision. Marks transfer `CANCELLED`, restores exact prior status, and logs procedural audit.
3. **Concurrency & Integrity Safeguards:**
   - Duplicate pending transfer prevention: Active pending transfers for the same case return `HTTP 409 Conflict`.
   - Row-level locking (`with_for_update()`) and state check prevent concurrent decisions (e.g. concurrent accept and reject).
   - Direct unit reassignment protection: Modified `/cases/{case_id}/assign` to strictly prohibit altering `current_unit_id` for non-SuperAdmin users, preventing bypass of the formal transfer workflow.
4. **Cross-Bureau Confidentiality & Authorization:**
   - Bureau-scoped visibility: Transfer listings and reviews are restricted to members of the originating and receiving Bureaus (or `SUPER_ADMIN`).
   - Narrative shielding: Unprivileged cross-bureau viewers see case references and transfer metadata, while confidential complainant particulars remain shielded.
5. **Outbox Notification Integration:**
   - Automatically enqueues notifications in `notification_outbox` for unit members on proposal initiation, acceptance, rejection, and cancellation without premature delivery before transaction commit.
6. **Frontend Transfer Management Suite:**
   - `AICTETransferQueue.tsx`: Central queue with Incoming and Outgoing tabs, status filters, search, and quick decision modals.
   - `AICTECaseDetail.tsx` Integration: "Initiate Transfer" action button, active `TRANSFER_PENDING` alert banner, and complete "Inter-Bureau Transfer Ledger" history card.
   - `InitiateTransferModal.tsx`: Destination unit selector, receiving officer selector (filtered by destination membership), substantive reason, and statutory handover checklist.
   - `TransferDecisionModal.tsx`: Modal supporting Accept, Reject (with mandatory reason), and Cancel actions with double-confirmation.
   - `AICTEIntegratedDashboard.tsx`: Live counter and quick link to Pending Incoming Transfers.
   - `Sidebar.tsx`: Navigation link for Regulatory Admin and Super Admin to `/aicte/transfers`.
7. **Automated Verification:**
   - Dedicated suite `test_step7_phase_e_aicte_transfers.py` covering all 14 core transfer lifecycle and concurrency requirements (100% passing against XAMPP MySQL `eduresolve_ai_test`).
   - Complete backend regression suite: **138 tests passed, 0 failed in 32.37s**.
   - Frontend production build: `npm run build` completed with **0 errors**.



