# EduResolve AI — Step 6: Security Audit Report

**Date:** 2026-10-28  
**Scope:** EduResolve AI Backend (FastAPI, SQLAlchemy, PyMySQL), Database (MariaDB/MySQL via XAMPP), Frontend (React, TypeScript, Vite)  
**Status:** All High & Critical Vulnerabilities Addressed  

---

## 1. Executive Summary

A comprehensive multi-phase security audit was conducted covering authentication, authorization, multi-tenant boundaries, sensitive grievance workflow data, CSV export security, and runtime safeguards.

Key outcomes:
- **Authentication & Email Verification:** Cryptographic token hashing (SHA-256) implemented. Timing-safe cooldowns and generic responses mitigate user enumeration.
- **Tenant Isolation:** Enforced strict check on analytics dashboards and exports (`403 Forbidden` for cross-institution unauthorized queries).
- **Spreadsheet Formula Injection (CSV Injection):** Sanitization added to prepend single quotes (`'`) to cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r`.
- **Audit Trail & Non-Repudiation:** Server-side context derivation for actor and tenant; JSON details serialization fixed.
- **DDoS & Brute-Force Safeguards:** 15MB request payload limit, sliding-window rate limiting on `/login`, `/register`, and `/resend-verification`, along with modern HTTP security headers.

---

## 2. Findings, Severity, Affected Files, and Fixes

| Vulnerability ID | Finding Description | Severity | Affected Files | Fix Applied | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | **CSV Formula Injection in Export**<br>Exporting grievance titles or descriptions starting with `=`, `+`, `-`, or `@` could trigger spreadsheet formula execution when opened in Excel/Calc. | **High** | `backend/app/api/v1/analytics.py` | Added `sanitize_csv_value()` prepending single quotes (`'`) to dangerous characters without stripping raw tabs/returns. | **Fixed & Tested** |
| **SEC-02** | **Account Enumeration on Verification Resend**<br>Responding differently for existing vs non-existing emails would allow attackers to harvest registered student emails. | **Medium** | `backend/app/api/v1/auth.py` | Uniform generic 200 response returned regardless of user existence. | **Fixed & Tested** |
| **SEC-03** | **Unbounded Export Query (DoS Risk)**<br>Administrative CSV exports without limits could exhaust server memory on large databases. | **Medium** | `backend/app/api/v1/analytics.py` | Enforced strict streaming limit bounded at 5,000 records. | **Fixed & Tested** |
| **SEC-04** | **Cross-Tenant Analytics Leakage Risk**<br>Missing authorization checks when passing arbitrary `institution_id` query parameter to analytics routes. | **High** | `backend/app/api/v1/analytics.py` | Enforced `check_institution_access()` and tenant membership checks returning `403 Forbidden` on foreign institutions. | **Fixed & Tested** |
| **SEC-05** | **Missing HTTP Security Headers**<br>Absence of clickjacking, MIME-sniffing, and referrer-leakage protection headers. | **Medium** | `backend/app/main.py` | Added middleware injecting `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`. | **Fixed & Tested** |
| **SEC-06** | **Brute-Force & Credential Stuffing**<br>No rate limiting on login, registration, or verification email endpoints. | **High** | `backend/app/main.py`, `backend/app/core/config.py` | Implemented sliding-window rate limiting middleware (10/min login, 5/min register, 3/min resend). | **Fixed & Tested** |
| **SEC-07** | **Scheduler Status RBAC Bypass**<br>Scheduler telemetry and manual run endpoints lacked role validation. | **Medium** | `backend/app/main.py` | Enforced `require_roles([UserRoleEnum.SUPER_ADMIN])` on both `/system/scheduler-status` and `/system/scheduler-run`. | **Fixed & Tested** |
| **SEC-08** | **PyMySQL Dict Serialization Error in Audit**<br>Passing dict structures to `log_audit()` raised PyMySQL type error during audit logging. | **Medium** | `backend/app/services/audit_service.py` | Added safe auto-serialization (`json.dumps(details)`) for dictionary payloads. | **Fixed & Tested** |

---

## 3. Data Confidentiality & Student Privacy

- **Internal Notes:** Restrictive queries ensure `GrievanceInternalNote` entries are excluded from student-facing responses. Only staff with authorized institution membership can read internal deliberation notes.
- **Notifications:** Notifications contain only grievance titles and reference IDs; internal staff notes or unverified allegations are never included in notification payloads.
- **Attachments:** All attachment downloads pass through `GET /api/v1/attachments/{id}/download` requiring token authentication and tenant/student ownership validation.
- **Passwords & Tokens:** Passwords hashed with Argon2id; verification tokens and invitation tokens stored exclusively as SHA-256 digests. Raw tokens are never logged or returned in responses.

---

## 4. Remaining Risks & Infrastructure Recommendations

1. **In-Memory Rate Limiting:**
   - *Current Implementation:* Uses an in-memory sliding window store in FastAPI.
   - *Consideration:* Suitable for single-instance or sticky-session deployments. When deploying multiple load-balanced Uvicorn workers, configure a shared Redis instance or reverse proxy (e.g., NGINX / Cloudflare rate limiting).
2. **SMTP Configuration:**
   - When running in local development or test without valid SMTP credentials, emails log to the development console. For production delivery, configure verified SMTP host, TLS, and SPF/DKIM records.
