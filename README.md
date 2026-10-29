# EduResolve AI
### AI-Powered Centralized Student Grievance Redressal and Monitoring Platform
<!-- Supported Bureau Membership Roles
BUREAU_HEAD: Bureau Director, Cell In-Charge, Regional Director.
BUREAU_OFFICER: Grievance Scrutiny Officer, Legal Examiner.
GRIEVANCE_CELL_OFFICER: Specialized PGRC case intake handler.
REGIONAL_DIRECTOR: Territorial Regional Office Head.
LIAISON_OFFICER: Inter-bureau coordinating officer.
ADVISOR: Statutory apex advisory officer. -->
EduResolve@123(DEFUALT PASSWORD)
EduResolve AI is a centralized, AI-assisted student grievance redressal and institutional monitoring platform designed for higher education institutions. The system supports multi-institutional governance, role-based access control, NLP-driven triage, transparent audit history, and student satisfaction feedback.

---

## 🌟 Key Capabilities

- **Multi-Role Portals**: Dedicated, role-tailored dashboards for `STUDENT`, `COLLEGE_OFFICER`, `INSTITUTION_HEAD`, `REGULATORY_ADMIN`, and `SUPER_ADMIN`.
- **Strict Multi-Tenant Isolation**: Institutional boundaries are enforced on every database query. Officers and heads cannot access grievances outside their assigned college.
- **AI Triage Assistance**:
  - Domain NLP text classification suggests appropriate grievance categories.
  - Cosine similarity scans for suspected duplicate complaints within the institution.
  - Urgency and priority scoring detects critical safety threats, anti-ragging flags, and exam deadlines.
  - Advisory only: Human officers verify all classifications and make all final determinations.
- **Workflow State Machine & Audit Trail**: Every status transition records a mandatory justification reason, actor, and timestamp.
- **Shielded Internal Notes**: Officers collaborate using confidential case notes strictly invisible to students.
- **Two-Way In-Portal Communication**: Real-time official case messaging between students and grievance officers.
- **Secure File Storage**: Private server-side storage with authorization validation on every document download.
- **High-Performance Relational Backend**: Powered by XAMPP MySQL with SQLAlchemy 2.x and PyMySQL connection pooling.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, React Router v6, TanStack Query, Recharts.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.x, PyMySQL, Pydantic v2, PyJWT, Argon2 (`argon2-cffi`), python-multipart.
- **Database**: XAMPP MySQL / MariaDB (Server default 127.0.0.1:3306, database: `eduresolve_ai`).
- **AI Service**: Scikit-learn TF-IDF Vectorizer, Cosine Similarity, heuristic urgency pattern engine.

---

## 📁 Repository Structure

```text
EduResolve-AI/
├── frontend/                     # React TypeScript Vite application
│   ├── src/
│   │   ├── components/common/    # Navbar, Footer, Sidebar, StatusBadge, PriorityBadge, Modal
│   │   ├── contexts/             # AuthContext (JWT, session, role checking)
│   │   ├── layouts/              # PublicLayout, DashboardLayout
│   │   ├── pages/
│   │   │   ├── public/           # Landing, About, HowItWorks, Features, Privacy, Contact, Track
│   │   │   ├── auth/             # Login (with 1-click Demo selectors), Student Register
│   │   │   ├── student/          # Dashboard, SubmitGrievance (with live AI), Detail, Profile
│   │   │   ├── officer/          # OfficerDashboard (case queue, status transition, notes)
│   │   │   ├── institution/      # HeadDashboard (trends, overdue, department analytics)
│   │   │   ├── regulatory/       # RegulatoryDashboard (jurisdiction-scoped benchmarks)
│   │   │   └── superadmin/       # SuperAdminDashboard (institutions, users, categories SLA)
│   │   ├── routes/               # AppRoutes & ProtectedRoute (RBAC route guards)
│   │   ├── services/             # Centralized API fetch client with JWT interceptor
│   │   └── types/                # Complete TypeScript domain interfaces
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── api/v1/               # Versioned REST routers (auth, grievances, ai, analytics, etc.)
│   │   ├── core/                 # Config, Argon2 security, RBAC permissions, logging
│   │   ├── database/             # SQLAlchemy 2.0 connection & base
│   │   ├── models/               # Declarative mapped models (User, Grievance, Institution, etc.)
│   │   ├── schemas/              # Pydantic v2 request/response schemas
│   │   ├── services/             # AI service, audit service, notification service
│   │   ├── utils/                # Reference number generator, secure file handler
│   │   ├── tests/                # Automated pytest suite (auth, isolation, status, AI)
│   │   └── main.py               # Application factory, CORS, exception handlers
│   ├── alembic/                  # Database migration scripts
│   ├── requirements.txt          # Python dependencies
│   ├── seed_data.py              # Baseline categories, institutions, and demo accounts
│   ├── .env.example
│   └── .env
├── ai-service/                   # Pluggable standalone AI package
│   ├── classifiers/              # TF-IDF category prediction
│   ├── similarity/               # Cosine similarity duplicate detection
│   ├── prioritization/           # Urgency & safety trigger engine
│   └── routing/                  # Institutional department matching
├── docs/                         # Architecture, API, Database, Security documentation
├── docker-compose.yml            # Dockerized deployment configuration
└── README.md
```

---

## ⚡ Quick Start Guide (Windows PowerShell)

### Prerequisites
1. **Python 3.11+**: Check with `python --version`
2. **Node.js LTS (v18+) & npm**: Check with `node -v` and `npm -v`
3. **XAMPP MySQL / MariaDB**: Running in XAMPP Control Panel (default port 3306 or custom port)

---

### Step 1: XAMPP MySQL Setup & Configuration

Follow these 8 steps to set up the database and backend:

1. **Start MySQL in the XAMPP Control Panel**:
   - Open the XAMPP Control Panel.
   - Click **Start** next to MySQL (and Apache if using phpMyAdmin).
   - Note the port shown in the Control Panel (default is `3306`). Use your actual configured port if it differs.

2. **Open phpMyAdmin**:
   - Navigate to `http://localhost/phpmyadmin` in your browser, or click **Admin** next to MySQL in the XAMPP Control Panel.

3. **Create the Database**:
   - In phpMyAdmin, click the **SQL** tab and execute:
   ```sql
   CREATE DATABASE eduresolve_ai
   CHARACTER SET utf8mb4
   COLLATE utf8mb4_unicode_ci;
   ```

4. **Configure Database Credentials in `backend/.env`**:
   - Copy `backend/.env.example` to `backend/.env` if not already present.
   - Update `MYSQL_PORT` with the actual MySQL port configured in your XAMPP installation (do not assume 3306 if your XAMPP uses a different port like 3307).
   - Update `MYSQL_USER` and `MYSQL_PASSWORD` to match your XAMPP MySQL credentials (do not assume root has no password or that it does; configure whatever password is set on your environment):
   ```ini
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DATABASE=eduresolve_ai
   ```

5. **Install Backend Dependencies**:
   - Open PowerShell in the project directory:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   ```

6. **Run Alembic Migrations**:
   - Apply database schema migrations to XAMPP MySQL:
   ```powershell
   cd backend
   ..\venv\Scripts\alembic upgrade head
   ```

7. **Start FastAPI**:
   - Start the Uvicorn development server:
   ```powershell
   # From the backend directory
   ..\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

8. **Verify the Health Endpoints**:
   - Open your browser or use curl/Invoke-RestMethod:
     - **Root Endpoint**: `http://127.0.0.1:8000/`
     - **App Health**: `http://127.0.0.1:8000/api/health`
     - **Database Health**: `http://127.0.0.1:8000/api/health/db`
     - **OpenAPI Swagger Docs**: `http://127.0.0.1:8000/docs`
   - The `/api/health/db` endpoint executes a real `SELECT 1` against your XAMPP MySQL instance and returns `"status": "connected"`. If MySQL is offline, it safely returns HTTP 503 without leaking credentials or stack traces.

---

### Step 3: Frontend Setup & Run

Open a second PowerShell window in the `frontend` directory:

```powershell
cd frontend

# Install frontend dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```

The frontend will start at:
- **Application URL**: `http://localhost:5173`

---

## 👥 Demo Accounts (1-Click Login Available)

On the **Login page** (`http://localhost:5173/login`), click on any of the **Quick Demo Account** tabs to pre-fill credentials:

| Role | Email | Password | Scope & Description |
|---|---|---|---|
| **Student** | `student@nitdelhi.ac.in` | `Password@123` | Aarav Sharma (NIT Delhi, Roll: `2023CSB1042`). Can submit grievances, view live AI triage, track status, and chat with officers. |
| **College Grievance Officer** | `officer@nitdelhi.ac.in` | `Password@123` | Prof. Ananya Sen. Manages NIT Delhi queue, performs status transitions with mandatory reasons, and adds private internal notes. |
| **Institution Head** | `head@nitdelhi.ac.in` | `Password@123` | Dr. Rajesh Sharma (Director). Executive overview, department trends charts, overdue metrics, escalation reviews, CSV report export. |
| **Regulatory Admin** | `regulator@education.gov.in` | `Password@123` | V.K. Mehta (Regional Director). Jurisdictional oversight for colleges in Delhi, compliance benchmarks, and resolution statistics. |
| **Super Admin** | `admin@eduresolve.ai` | `Password@123` | Master Administrator. System health, institution registration, user role management, category SLA configuration, and audit logs. |

---

---

## 🔐 Step 2: Database Models, Authentication and RBAC Guide

### 1. Database Models Architecture
- **`User`**: Primary account record with Argon2 password hash (`password_hash` / `hashed_password`), unique indexed normalized email, active status, email verification tracking (`is_email_verified`), and default system role.
- **`Role`**: Baseline system roles (`STUDENT`, `COLLEGE_OFFICER`, `INSTITUTION_HEAD`, `REGULATORY_ADMIN`, `SUPER_ADMIN`) with uniqueness constraints and descriptions.
- **`Institution`**: Higher education institutions with unique `institution_code`, `institution_type`, state, district, city, official contact email, and `verification_status` (`PENDING`, `VERIFIED`, `REJECTED`).
- **`InstitutionMembership`**: Multi-tenant membership linking users to institutions with foreign keys (`user_id`, `institution_id`, `role_id`), role assignment, department, designation, and uniqueness constraint `uq_user_institution_membership` to prevent duplicate active memberships.
- **`RegulatoryJurisdiction`**: Regional oversight authority linking regulatory administrators to authorized state jurisdictions, regions, or explicit institutions.

### 2. Alembic Database Migrations
To apply or inspect migrations on XAMPP MySQL:
```powershell
# From the backend directory
cd backend
..\venv\Scripts\alembic upgrade head
..\venv\Scripts\alembic current
..\venv\Scripts\alembic check
```

### 3. Authentication Endpoints (`/api/v1/auth`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new student account (public registration is restricted to `STUDENT` role) | Public |
| `POST` | `/api/v1/auth/login` | JSON login returning JWT access token and token expiry info | Public |
| `POST` | `/api/v1/auth/token` | OAuth2 password form login compatible with Swagger UI `Authorize` button | Public |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile, roles, and active institution memberships | Authenticated |
| `PUT` | `/api/v1/auth/me` | Update personal profile (full name, phone, student ID; cannot alter roles) | Authenticated |
| `GET` | `/api/v1/auth/roles` | List all system roles definitions | Public |

### 4. Institution Endpoints (`/api/v1/institutions`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/v1/institutions` | Paginated list of verified institutions suitable for student registration | Public |
| `GET` | `/api/v1/institutions/{id}` | View detailed institution information | Public / Authenticated |
| `POST` | `/api/v1/institutions` | Submit institution registration request (`PENDING`) or direct creation | Public / Super Admin |
| `POST` | `/api/v1/institutions/{id}/members` | Assign officer or staff member to an institution | Super Admin / Institution Head |

### 5. Grievance Management Endpoints (`/api/v1/grievances`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/v1/grievances` | Submit a new grievance (institutional verification, non-guessable ref `GRV-YYYY-XXXX`) | Student (or authenticated user) |
| `GET` | `/api/v1/grievances` | List grievances with multi-tenant filtering (status, category, priority, dates, search) | Scoped by Role/Institution |
| `GET` | `/api/v1/grievances/{id}` | View case details (strictly shields internal notes & private attachments from students) | Student owner / Officer / Head / Admin |
| `GET` | `/api/v1/grievances/{id}/timeline` | Permitted status history audit timeline | Case stakeholders |
| `PUT` | `/api/v1/grievances/{id}/status` | Execute authorized status transition with mandatory reason | Officer / Head / Admin (or Student for close) |
| `POST` | `/api/v1/grievances/{id}/assign` | Assign or reassign case to an authorized officer within institution | Officer / Head / Admin |
| `POST` | `/api/v1/grievances/{id}/claim` | Authorized institutional officer self-assigns an open case | College Officer |
| `GET` | `/api/v1/grievances/{id}/assignments` | View full assignment/reassignment audit history | Officers / Heads / Admin |
| `POST` | `/api/v1/grievances/{id}/messages` | Post student-visible clarification or update message | Student owner / Officer / Admin |
| `GET` | `/api/v1/grievances/{id}/messages` | Retrieve student-visible message thread | Student owner / Officer / Admin |
| `POST` | `/api/v1/grievances/{id}/internal-notes` | Add confidential officer note (403 for students) | Officers / Heads / Admin |
| `GET` | `/api/v1/grievances/{id}/internal-notes` | View confidential internal notes (403 for students) | Officers / Heads / Admin |
| `POST` | `/api/v1/grievances/{id}/feedback` | Submit satisfaction rating (1-5) and feedback on resolved cases | Student owner |
| `POST` | `/api/v1/grievances/{id}/reopen-request` | Request reopening of an unsatisfactorily resolved/closed case | Student owner / Officer |
| `POST` | `/api/v1/grievances/{id}/escalate` | Manually escalate overdue/stalled case with audit justification | Authorized Officers / Head / Admin |
| `POST` | `/api/v1/grievances/escalations/process-overdue` | Administrative batch engine to process and auto-escalate overdue SLA cases | Super Admin / Institution Head |
| `GET` | `/api/v1/grievances/track/{ref_number}` | Public anonymous tracking by reference number (personal info masked) | Public |
| `POST` | `/api/v1/grievances/{id}/attachments` | Upload private evidence document (.pdf, .png, .jpg, .docx, .txt) | Authorized Stakeholders |
| `GET` | `/api/v1/grievances/{id}/attachments/{att_id}/download` | Secure private download with strict permission validation | Authorized Stakeholders |

### 6. Workflow Lifecycle & State Machine
The grievance lifecycle supports 11 standardized states:
1. `SUBMITTED` -> Initial student filing with advisory AI recommendations.
2. `UNDER_REVIEW` -> Case acknowledged and placed under review by grievance desk.
3. `ASSIGNED` -> Assigned to an authorized officer belonging to the grievance's institution.
4. `NEEDS_INFORMATION` -> Additional documentation or clarifications requested from student.
5. `INVESTIGATION_IN_PROGRESS` -> Active fact-finding, inspection, or administrative verification.
6. `RESOLUTION_PROPOSED` -> Action taken and formal resolution summary recorded.
7. `RESOLVED` -> Final resolution approved, triggering satisfaction feedback window.
8. `CLOSED` -> Formally closed post-feedback or after review period.
9. `REOPENED` -> Reopened when student or supervisor identifies unresolved issues.
10. `ESCALATED` -> Escalated to Institution Head or Regulatory authority for supervisory intervention.
11. `REJECTED` -> Documented formal rejection for frivolous or out-of-scope complaints.

### 7. How to Register and Log In

#### Using PowerShell:
```powershell
# 1. Register a new student account
$regBody = @{
    email = "new_student@nitdelhi.ac.in"
    password = "StudentPassword123!"
    full_name = "Kavya Nair"
    student_id_number = "2024CSB1099"
} | ConvertTo-Json

$student = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/auth/register" -ContentType "application/json" -Body $regBody

# 2. Log in to obtain JWT access token
$loginBody = @{
    email = "new_student@nitdelhi.ac.in"
    password = "StudentPassword123!"
} | ConvertTo-Json

$tokenResponse = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/auth/login" -ContentType "application/json" -Body $loginBody
$jwtToken = $tokenResponse.access_token

# 3. Access protected profile
$headers = @{ Authorization = "Bearer $jwtToken" }
$profile = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/auth/me" -Headers $headers
$profile
```

### 6. Testing Protected Endpoints in Swagger UI
1. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.
2. Click the green **Authorize** button at the top right.
3. In the dialog, enter your credentials:
   - **username**: `admin@eduresolve.ai` (or any registered user email)
   - **password**: your account password
4. Click **Authorize**, then **Close**.
5. All subsequent requests in Swagger UI will automatically include the Bearer JWT token header.

### 7. How to Safely Bootstrap a Super Administrator
To create or promote the master administrator without hardcoding credentials:
```powershell
# Interactive mode (prompts for email and masked password):
cd backend
..\venv\Scripts\python.exe bootstrap_admin.py

# Non-interactive CLI mode:
..\venv\Scripts\python.exe bootstrap_admin.py --email admin@eduresolve.ai --password "YourStrongPassword123!" --name "Master Administrator"
```

### 8. Frontend Setup & Integration

The frontend is built with React 18, TypeScript, Vite, and Tailwind CSS. It communicates directly with the FastAPI backend through a typed API client with automatic JWT token attachment.

#### 1. Configuration (`frontend/.env`)
Create or verify `frontend/.env`:
```ini
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

#### 2. Install Dependencies
```powershell
cd frontend
npm install
```

#### 3. Run Development Server
```powershell
npm run dev
```
The application will launch at [http://localhost:5173](http://localhost:5173).

#### 4. Build for Production & Typecheck
```powershell
npm run build
```
Generates production assets in `frontend/dist/` with zero TypeScript errors.

---

### 9. Demo & Test Accounts

| Role | Email | Password | Access & Dashboard |
| :--- | :--- | :--- | :--- |
| **Super Administrator** | `superadmin@eduresolve.gov.in` | `SuperAdminSecurePassword123!` | `/admin` - Global institutions, user role elevating, SLA thresholds, live MySQL health |
| **College Grievance Officer** | `officer.test@college.edu` | `OfficerSecurePassword123!` | `/officer` - Intake queue, case claiming, two-way student chat, shielded internal notes |
| **Enrolled Student** | `student_2dacd7e4@example.com` | `StudentTestPassword123!` | `/student` - Live AI assisted filing, timeline, chat, reopening requests, satisfaction ratings |

*(Note: New students can also self-register instantly from the `/register` public page).*

---

### 10. Running Automated Tests Against XAMPP MySQL
The test suite runs against the dedicated, isolated `eduresolve_ai_test` MySQL schema (SQLite is strictly prohibited):
```powershell
cd backend
..\venv\Scripts\pytest.exe -v
```

---

## 👥 Role-Based Account Creation & Onboarding

EduResolve AI features a secure, invitation-based user creation architecture designed to prevent unauthorized account creation while preserving strict multi-tenant boundaries.

### 1. Account Creation Matrix & Hierarchy
| Creator Role | Allowed Target Roles | Constraints & Tenant Scoping |
|---|---|---|
| **Super Admin** | `INSTITUTION_HEAD`, `REGULATORY_ADMIN`, `COLLEGE_OFFICER` | Global scope across all verified institutions and regulatory jurisdictions. |
| **Institution Head** | `COLLEGE_OFFICER` | Strictly scoped to their own verified institution and departments. Cannot create Super Admins, Heads, or Regulators (`HTTP 403`). |
| **Regulatory Admin** | *None* | Read-only regulatory oversight. Account creation requests return `HTTP 403 Forbidden`. |
| **Public Self-Registration** | `STUDENT` only | Any public registration attempt requesting elevated roles is automatically forced to `STUDENT`. |

### 2. Single-Use Expiring Token Invitation Flow
1. **Invite Generation**:
   - The creator submits the invite via **Super Admin Dashboard** (`/admin` -> User Management -> "Add User") or **Institution Head Dashboard** (`/head/officers` -> "Invite Officer").
   - A cryptographically random URL-safe token is generated.
   - The SHA-256 hash of the token is persisted to the `user_invitations` MySQL table with a 7-day expiration timestamp (`expires_at`). Plaintext tokens are never stored in the database.
2. **Delivery & Development Mode**:
   - In production with SMTP configured, an official invitation email is dispatched with the onboarding link.
   - If SMTP is unconfigured in development/testing, the system safely marks delivery as `DEVELOPMENT_LINK_GENERATED` and displays a direct single-use link for immediate testing without faking email delivery.
3. **Public Onboarding & Password Setup**:
   - The recipient visits `/accept-invitation?token=<token>`.
   - The token is verified against the database (checking state and expiration).
   - The user enters their full name and sets their secure password.
   - Upon acceptance, the user account is created or linked, institutional membership or regulatory jurisdiction is assigned, the invitation token is permanently marked `ACCEPTED` (preventing replay attacks), and the user is automatically logged in.
4. **Officer Deactivation & Audit Preservation**:
   - Institution Heads and Super Admins can deactivate officers (`is_active = False`) directly from the dashboard.
   - Deactivated users are immediately blocked from logging in or mutating cases.
   - Grievance history, audit trail transitions, and confidential notes linked to deactivated officers remain fully intact.

### 3. User Management API Endpoints
| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `POST` | `/api/v1/users/invite` | Send role-based user invitation | Super Admin, Institution Head |
| `GET` | `/api/v1/users` | List users with filtering by role, institution, status, and search | Super Admin, Institution Head (tenant-scoped) |
| `GET` | `/api/v1/users/invitations/list` | List active and pending invitations | Super Admin, Institution Head (tenant-scoped) |
| `DELETE` | `/api/v1/users/invitations/{id}` | Revoke an existing invitation | Super Admin, Institution Head |
| `POST` | `/api/v1/users/invitations/{id}/resend` | Resend/regenerate invitation token with refreshed 7-day expiry | Super Admin, Institution Head |
| `PUT` | `/api/v1/users/{id}/status` | Activate or deactivate user account | Super Admin, Institution Head |
| `PUT` | `/api/v1/users/{id}/role` | Change system role of an existing user | Super Admin |
| `GET` | `/api/v1/auth/invitations/{token}` | Validate invitation token and fetch onboarding metadata | Public |
| `POST` | `/api/v1/auth/invitations/{token}/accept` | Accept invitation, set password, assign membership, issue JWT | Public |
| `POST` | `/api/v1/auth/change-password` | Authenticated self-service password change | Authenticated Users |

### 4. Institution Registration & Default Password Flow
- When an institution is registered by the Super Admin, the backend automatically provisions an **`INSTITUTION_HEAD`** account using the institution's official contact email.
- The account is assigned a secure default password: **`EduResolve@123`**.
- The Super Admin is presented with an immediate confirmation modal displaying the login email, default password, and a 1-click credential copy button.
- The Institution Head can log in at `/login` with these credentials and change their password anytime via **Profile Settings** (`/profile` -> Security & Password Change).

---

## 🧪 Running Automated Tests

Run the backend test suite using `pytest`:

```powershell
.\venv\Scripts\pytest backend\app\tests -v
```

**Test Coverage Highlights (152 Passing Tests against XAMPP MySQL `eduresolve_ai_test`)**:
- **Health Endpoints**: `/api/health`, `/api/health/db`, `/api/v1/ai/health`, `/api/v1/ai/readiness`
- **Email Verification & Account Security (Step 6)**:
  - Cryptographically secure verification token generation and SHA-256 database hashing
  - Single-use consumption and replay attack rejection
  - Expiration enforcement (default 24h) and invalid token rejection
  - 60-second resend cooldown (HTTP 429) and user enumeration defense via uniform response
  - Verification status inspection via `/api/v1/auth/verification-status`
- **Reliable Notification Outbox System (Step 6)**:
  - Transactional persistence in MySQL (`notifications` + `notification_outbox`)
  - Outbox batch dispatching with retry tracking and attempt incrementing
  - Recipient ownership isolation, paginated listing, live unread counts, and mark-all-read
  - Prevention of sensitive data or internal notes leakage to students
- **Reliable Background SLA Scheduler (Step 6)**:
  - Non-blocking `SLABackgroundScheduler` running in FastAPI lifespan
  - Approaching SLA warning alerts dispatched within 24-hour statutory threshold
  - Automatic overdue escalation to `ESCALATED` and priority upgrade to `URGENT`
  - Idempotent execution preventing duplicate escalations or duplicate warnings
  - Super Admin operational telemetry endpoint (`/api/v1/system/scheduler-status`) and manual trigger (`/api/v1/system/scheduler-run`)
- **API & Application Security Safeguards (Step 6)**:
  - CSV formula injection protection prepending single quotes (`'`) to `=, +, -, @, \t, \r`
  - Strict tenant isolation returning HTTP 403 on foreign institution analytics or export requests
  - Sliding-window rate limiting middleware protecting `/login`, `/register`, and `/resend-verification`
  - HTTP security response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`)
  - 15MB request payload limit (HTTP 413)
- **Role-Based Account Creation & Onboarding (16 Comprehensive Tests)**:
  - Super Admin invites College Officer, Institution Head, and Regulatory Admin with correct memberships and jurisdictions
  - Institution Head invites College Officer within own institution with department assignment
  - Tenant isolation enforcement: Institution Head cannot invite officers for another institution (`HTTP 403`)
  - Role escalation prevention: Institution Head cannot invite Super Admin, Head, or Regulatory Admin (`HTTP 403`)
  - Regulatory Admin access control: Regulatory Admin cannot invite accounts (`HTTP 403`)
  - Public registration enforcement: Student self-registration cannot escalate to administrative roles
  - Institutional boundary verification: Invitations to non-existent institutions return `HTTP 404`
  - Duplicate invitation prevention: Active pending invitations for same email return `HTTP 400`
  - Single-use token workflow: Acceptance sets password, logs in, creates membership, and invalidates token against replay
  - Immutable audit trail: All invitation creations, acceptances, and status changes logged to `audit_logs`
  - Resend & Revoke: Token regeneration with refreshed expiry and token revocation
  - Account deactivation: Inactivated users are denied access while preserving historical grievance ownership
  - Tenant-scoped user listings: Multi-filter search (role, status, institution) and strict boundary isolation
  - Automatic institution head provisioning with default password `EduResolve@123`
  - Self-service password change workflow: verifies current password, updates Argon2 hash, rejects old password
- **Trained ML Model Pipeline**: `TfidfVectorizer` + `LogisticRegression` pipeline loading and inference
- **NLP Categorization**: Multi-class category classification with calibrated confidence and entropy thresholding
- **Heuristic Urgency Scoring**: Priority triage scoring for anti-ragging, emergency threats, and exam deadlines
- **Semantic Duplicate Detection**: Cosine similarity multi-tenant duplicate complaints detection
- **Department Routing**: Department-aligned officer routing recommendations
- **AI Recommendation Audit Trail**: Database persistence of AI suggestions and graceful fallback degradation
- **Security & RBAC**: Argon2id password hashing, JWT expiration, IDOR prevention, and cross-tenant boundary protections
- **Grievance State Machine**: Formal 11-stage status transitions, mandatory reasons, atomic audit logging, internal confidential notes, and two-way messaging
- **Attachments & SLAs**: Authenticated document storage and automatic overdue escalation batch services
- **AICTE Cross-Bureau Suite (Step 7 — Phases B, C, D, E & F - 58 Comprehensive Tests)**:
  - Phase B (10 tests): Institution identity extension, AICTE Permanent ID verification, institutional aliases, organizational units, and bureau memberships.
  - Phase C (10 tests): AICTE case lifecycle state machine, direct intake, procedural milestone ledger (`case_actions`), campus referral workflow, and consolidated profile.
  - Phase D (10 tests): Overlap detection, candidate bounding, multi-signal scoring, narrative shielding, human review decisions, and non-destructive case linking.
  - Phase E (14 tests): Formal inter-bureau transfer proposals, receiving unit acceptance, mandatory rejection reasons, exact prior status restoration, cancellation, row-level locking, duplicate prevention, direct assignment guard, and outbox notification queuing.
  - Phase F (14 tests): Consolidated AICTE analytics, database-level distinct aggregations, active-case ageing brackets, SLA breach monitoring, zero-denominator disposal rate protection, Bureau/Regional workload breakdown, and formula-injection-safe CSV streaming exports.

---

## 🏛️ AICTE Cross-Bureau Case Management (Step 7 — Phases B, C, D, E & F Completed)

EduResolve AI features an integrated architecture for cross-bureau complaint case tracking across AICTE autonomous Bureaus, Cells, and Regional Offices:

- **Institution Identity (Phase B)**:
  - `aicte_permanent_id`: Canonical AICTE permanent registration identifier (`VARCHAR(50)`, unique nullable index, validated format).
  - `region`: AICTE regional affiliation (Northern, Western, Southern, Central, etc.).
  - `is_aicte_verified`: Official AICTE accreditation and registry verification status flag.
  - `institution_aliases`: Alias dictionary resolving name variations, colloquial acronyms, and AISHE variants without merging separate entities.
- **Organizational Units & Memberships (Phase B)**:
  - `organizational_units`: Models statutory Bureaus (`RB`, `AB`), cells (`PGRC`), and territorial regional offices (`RO_NORTH`, `RO_WEST`, `RO_SOUTH`).
  - `bureau_memberships`: Enforces explicit officer assignments and prevents unauthorized cross-unit or cross-college access.
- **Dedicated AICTE Case Management (Phase C)**:
  - `aicte_cases` table: Distinct regulatory docket with custom lifecycle states (`RECEIVED`, `PENDING_REVIEW`, `UNDER_PROCESS`, `AWAITING_RESPONSE`, `TRANSFER_PENDING`, `TRANSFERRED`, `ESCALATED`, `DISPOSED`, `CLOSED`, `REOPENED`).
  - Collision-free internal reference numbers (`AICTE-YYYY-XXXXXX`) and optional official dispatch references.
  - Complainant typing (`STUDENT`, `FACULTY`, `STAKEHOLDER`, `INSTITUTION`, `PUBLIC_AUTHORITY`, `ANONYMOUS`, `OTHER`) without requiring student account credentials.
- **Procedural Action Ledger (Phase C)**:
  - `case_actions` table: Immutable milestone ledger recording scrutiny, information requests, hearing schedules, committee reviews, transfer steps, and disposal orders.
  - Server-side state machine validation with atomic transactional updates.
- **Campus Grievance to AICTE Referral (Phase C)**:
  - Controlled workflow referring existing campus grievances to an AICTE Bureau docket with duplicate prevention and audit logging.
- **Consolidated Institution Profile (Phase C)**:
  - Cross-bureau institution profile displaying AICTE PID, verified status, aliases, multi-bureau metrics, active/disposed breakdown, and complete case docket.
- **Cross-Bureau Overlap Detection & Case Linking (Phase D)**:
  - `aicte_case_overlaps` table: Bounded candidate generation comparing institutional dockets across Bureaus/Cells.
  - Multi-signal explainability engine: Jaccard + Cosine subject similarity, Cosine description similarity, category concord, cross-bureau flags, official reference matching, temporal proximity, and allegation keywords.
  - Human Review Lifecycle: Authorized reviewers can determine `CONFIRMED_DUPLICATE`, `CONFIRMED_RELATED`, `REJECTED`, or `DEFERRED` with mandatory review notes.
  - Re-detection Idempotency: Re-evaluations update detection metadata but never overwrite human decisions.
  - `aicte_case_links` table: Administrative linking (`DUPLICATE_OF`, `RELATED_TO`) maintaining independent case dockets, references, and statuses without auto-merging.
  - Cross-Bureau Narrative Shielding: Masks confidential complainant details and descriptions across bureau boundaries for unprivileged officers.
- **Formal Inter-Bureau Transfer Workflow (Phase E)**:
  - `aicte_case_transfers` table: Auditable handover ledger with `from_unit_id`, `to_unit_id`, `transfer_status` (`PENDING_ACCEPTANCE`, `ACCEPTED`, `REJECTED`, `CANCELLED`), required substantive reason, confidential handover summary, and prior status tracking.
  - Originating Unit Responsibility Invariant: `case.current_unit_id` and assigned officer remain unchanged while status is `TRANSFER_PENDING` until the destination bureau formally accepts.
  - Exact Prior Status Restoration: On rejection or cancellation, case returns to its specific recorded `prior_case_status` (e.g. `UNDER_PROCESS`), preventing inaccurate status resets.
  - Concurrency Safeguards: Row-level locking (`with_for_update()`) and state validation prevent concurrent accept/reject races. Active pending duplicates return `HTTP 409 Conflict`.
  - Direct Assignment Guard: `/cases/{id}/assign` forbids changing `current_unit_id` for non-SuperAdmin users, preventing bypass of the formal transfer workflow.
  - Outbox Notification Integration: Dispatches notification events to affected Bureau members transactionally.
- **Consolidated AICTE Analytics, Ageing & Reporting (Phase F)**:
  - `AICTEAnalyticsService`: Database-side distinct aggregation for KPIs, status-by-status distributions, active-case ageing brackets (0–7d, 8–15d, 16–30d, 31–60d, >60d), and historical disposal time.
  - SLA & Deadlines Monitoring: Isolates overdue next actions, overdue disposal targets, total SLA breaches, and unmonitored cases missing deadlines.
  - Workload & Trend Distributions: Chronological 6-month monthly trends, Bureau/Regional office caseload breakdown, and top institution complaint ranking.
  - Streaming CSV Reports: Dedicated endpoints (`/reports/cases.csv`, `/reports/summary.csv`) neutralizing formula injection attacks.
- **Centralized AICTE Alert Center, Notifications & Escalation Management (Phase G)**:
  - `AICTEAlertService`: Role-aware notification lifecycle management disaggregating alert conditions, notifications, acknowledgements, and case actions. Reading or acknowledging alerts strictly preserves case procedural status.
  - Periodic SLA Evaluation: Integrated into `SLABackgroundScheduler.run_cycle_sync` to evaluate overdue next actions, overdue expected disposal dates, approaching deadlines, missing deadline compliance, delayed transfers (>72h), and failed email deliveries.
  - Deduplication Engine: Protects recipients against alert floods by enforcing configurable deduplication cooldown windows (default 24h).
  - Cross-Bureau Narrative Shielding: Masks confidential complainant particulars and investigation notes in notifications across bureau boundaries.
  - Centralized Notification & Alert Center APIs (`/api/v1/aicte/notifications`, `/unread-count`, `/read`, `/acknowledge`, `/read-all`, `/api/v1/aicte/alerts/summary`, `/overdue`, `/configuration`).
- **Frontend AICTE Suite (Phases C, D, E, F & G)**:
  - AICTE Integrated Dashboard (`/aicte`) with Recharts visual charts, period presets, Bureau & Region filters, KPI summary cards, live operational alert ribbon, and CSV export buttons
  - AICTE Centralized Alert Center (`/aicte/notifications`) with tabs for All Alerts, Unread, Requires Ack, Live Overdue Cases Queue, and Alert Threshold Configuration
  - AICTE Notification Bell (`AICTENotificationBell.tsx`) with real-time badges, critical pulse, preview dropdown, and dismiss actions
  - AICTE Case Directory (`/aicte/cases`)
  - AICTE Case Docket & Action History (`/aicte/cases/:id`) with transfer action modal, active transfer banner, and transfer history ledger
  - AICTE Inter-Bureau Transfer Queue (`/aicte/transfers`) with incoming/outgoing queues, status filters, and decision modal
  - AICTE Consolidated Institution Profile (`/aicte/institutions/:id`)
  - AICTE Cross-Bureau Overlap Queue (`/aicte/overlaps`)
  - AICTE Overlap Detailed Comparison & Signals (`/aicte/overlaps/:id`)
  - AICTE Case Relationships & Overlap Scan component embedded in Case Detail
- **Security Hardening, Concurrency & Integration (Phase H)**:
  - Role & Bureau Boundary Guard: Enforced strict `HTTP 403 Forbidden` across all AICTE regulatory endpoints (`/cases`, `/transfers/incoming`, `/transfers/outgoing`, `/overlaps`, `/alerts/overdue`) for students and unauthorized campus users.
  - Concurrency & Row-Level Locking: Integrated `with_for_update()` across case updates, assignments, procedural actions, and campus grievance referrals, preventing race conditions and duplicate referrals.
  - Cross-Bureau Narrative Confidentiality: Shielded confidential complainant details and raw narratives (`[CONFIDENTIAL: ...]`, `[PROTECTED]`) in cross-bureau overlap views for unprivileged officers.
  - Advanced CSV Formula Injection Neutralization: Enhanced `sanitize_csv_value` to detect formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`, `%`) even when preceded by leading whitespace (spaces, tabs, carriage returns) while preserving legitimate numbers.
  - Notification IDOR Protection: Cross-user notification requests, read updates, and acknowledgements return `HTTP 404 Not Found` without disclosing ownership metadata.
  - Outbox Retry Bound & Teardown Preservation: Preserved persistent development and test databases on XAMPP MySQL.
- **Role-Based Dashboard Coverage, Navigation Audit & Feature Accessibility (Phase I)**:
  - Discrepancy Resolution: Resolved `/aicte/*` frontend restriction allowing Bureau officers with active `BureauMembership` to access unit-scoped AICTE monitoring, case directory, transfers, overlaps, and alert center.
  - Active Membership Serialization: Updated `/auth/me` and `/auth/login` to serialize active `bureau_memberships` (with unit code, name, and role).
  - Client-Side Scoped Navigation: Added `BureauMembership` interface, `isBureauMember`, and `hasBureauAccess` to AuthContext. Configured `ProtectedRoute` with `allowBureauMembers={true}` and dynamic sidebar rendering with an active Bureau badge.
  - Campus-to-Regulatory Integration: Integrated `ReferGrievanceModal` into `HeadDashboard` (Escalated Grievances queue) and `OfficerDashboard` (Case Overview tab) allowing campus officials to refer complaints to AICTE (`/cases/refer-grievance`).
  - Regulatory Admin State Scoping: Extended AICTE case listing and detail endpoints to support jurisdiction-scoped case oversight for Regulatory Admins based on active `RegulatoryJurisdiction`.
  - Database Audit & Integrity: Audited actual XAMPP MySQL database (`eduresolve_ai`), confirming 6 active organizational units (`RB`, `PGRC`, `AB`, `RO_NORTH`, `RO_WEST`, `RO_SOUTH`) and 0 active staff memberships without fabricating data.
- **Alembic Migration History**:
  - Phase B: `c7b12d3e4f5a` (Parent: `59f5f8fb2f6b`)
  - Phase C: `d8c23e4f5a6b` (Parent: `c7b12d3e4f5a`)
  - Phase D: `e9f34a5b6c7d` (Parent: `d8c23e4f5a6b`)
  - Phase E: `f0a45b6c7d8e` (Parent: `e9f34a5b6c7d`)
  - Phase G: `g1b23c4d5e6f` (Parent: `f0a45b6c7d8e`)


---

## 🛡️ Security & Privacy Architecture

1. **Argon2id Password Hashing**: Utilizes memory-hard password hashing via `argon2-cffi`. Plaintext passwords and secrets are never stored or logged.
2. **Multi-Tenant Scoping**: All queries enforce institutional ownership checks. Cross-institution access requests return `HTTP 403 Forbidden`.
3. **Single-Use Verification & Invitation Tokens**: Tokens are hashed with SHA-256 before database storage. Raw tokens are never stored, preventing token harvesting from database backups.
4. **Confidentiality Shielding**: Internal officer notes are stored in a dedicated table and never serialized to student endpoints.
5. **Private Storage**: Evidence files are saved to `private_uploads/` using UUID-generated server names; direct public URL static access is disabled.
6. **Human-in-the-Loop AI**: AI suggestions are advisory and transparently labeled with confidence scores and model version identifiers.
7. **Rate Limiting & Anti-Abuse**: Sliding-window rate limiters prevent brute force and email spamming on sensitive endpoints.
8. **CSV Formula Injection Neutralization**: Spreadsheets exported through the portal sanitize all dangerous executable formula characters.

---

## 📌 Governance Disclaimer

EduResolve AI is an independent software architecture platform. Regulatory configurations can be adapted to relevant governing authorities and institutional guidelines.


