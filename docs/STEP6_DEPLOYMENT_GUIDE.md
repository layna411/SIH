# EduResolve AI — Step 6: Deployment & Operational Guide

## 1. Architecture Overview

EduResolve AI operates as a unified three-tier architecture:
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide icons.
- **Backend:** FastAPI, Python 3.11+, SQLAlchemy 2.x, Pydantic v2.
- **Database:** XAMPP MySQL / MariaDB (port 3306) with PyMySQL driver.
- **Background Engine:** Asynchronous SLA monitoring scheduler (`SLABackgroundScheduler`) with transactional notification outbox processor running in the FastAPI lifespan.

---

## 2. Prerequisites & Environment Setup

### Required Services
1. **XAMPP Control Panel:** Start MySQL / MariaDB (running at `127.0.0.1:3306`).
2. **Python:** 3.11 or higher.
3. **Node.js:** 18 or higher (with `npm`).

### Databases in XAMPP MySQL
Ensure two databases exist in phpMyAdmin / MariaDB:
- `eduresolve_ai`: Main development & staging database.
- `eduresolve_ai_test`: Isolated automated test database.

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env` in the `backend/` directory:

```ini
APP_NAME=EduResolve AI
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1

# XAMPP MySQL Configuration
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=eduresolve_ai
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/eduresolve_ai?charset=utf8mb4

# Dedicated Test Database
MYSQL_TEST_DATABASE=eduresolve_ai_test

# JWT Security (Minimum 32 random characters)
JWT_SECRET_KEY=your_cryptographically_secure_random_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# CORS Allowed Origins
FRONTEND_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173", "https://yourdomain.edu"]

# SMTP Configuration (Optional: fallback to console logger if empty)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=notifications@yourdomain.edu
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=notifications@yourdomain.edu
SMTP_USE_TLS=true
NOTIFICATION_EMAIL_ENABLED=true
FRONTEND_URL=http://localhost:5173

# Verification & Outbox
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60
NOTIFICATION_OUTBOX_MAX_RETRIES=5

# SLA Background Scheduler
SLA_SCHEDULER_ENABLED=true
SLA_POLL_INTERVAL_SECONDS=300
SLA_WARNING_HOURS=24

# Security Safeguards
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_MAX_REQUESTS=10
RATE_LIMIT_REGISTER_MAX_REQUESTS=5
RATE_LIMIT_VERIFY_RESEND_MAX_REQUESTS=3
MAX_CONTENT_LENGTH_MB=15
```

---

## 4. Database Migrations (Alembic)

To apply all forward migrations to the main schema:

```powershell
cd backend
..\venv\Scripts\alembic upgrade head
```

Verify migration status and consistency:

```powershell
..\venv\Scripts\alembic current
# Output should display: 59f5f8fb2f6b (head)

..\venv\Scripts\alembic check
# Output should display: No new upgrade operations detected.
```

---

## 5. Running the Application

### Backend Server

```powershell
cd backend
..\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Upon startup, the server automatically:
- Tests database connectivity to `eduresolve_ai`.
- Initializes and starts the `SLABackgroundScheduler` background task.
- Enforces payload size limits and security headers on every request.

### Frontend Application

Development mode:
```powershell
cd frontend
npm run dev
```

Production build:
```powershell
cd frontend
npm run build
npm run preview
```

---

## 6. Health & Operational Endpoints

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | GET | Public | Application uptime and version check. |
| `/api/health/db` | GET | Public | Live MySQL connectivity check. |
| `/api/v1/system/scheduler-status` | GET | Super Admin | Operational telemetry: runs, last run status, warnings, escalations. |
| `/api/v1/system/scheduler-run` | POST | Super Admin | Synchronously trigger an SLA scan & outbox dispatch cycle. |
| `/api/v1/notifications/unread-count`| GET | Authenticated | Live badge count of unread user notifications. |
| `/api/v1/notifications/outbox/process` | POST | Admin/Head | Manual batch trigger for transactional outbox dispatch. |

---

## 7. Reliability & Failure Handling

- **SMTP Outage:** If SMTP credentials are not supplied or the remote server fails, notifications remain safely recorded in `notifications` (in-app) and `notification_outbox` (marked `FAILED` with retry eligibility). Student submission is never blocked.
- **Scheduler Resilience:** The scheduler is non-blocking and executes cycles inside isolated database sessions. Overlapping runs are automatically skipped via `_is_executing_cycle` guards.
- **Server Shutdown:** FastAPI `lifespan` triggers clean termination of the background scheduler task and closes database connection pools.
