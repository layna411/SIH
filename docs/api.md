# EduResolve AI - REST API Specification

Base URL: `/api/v1`

Interactive Swagger UI: `http://127.0.0.1:8000/docs`  
ReDoc Reference: `http://127.0.0.1:8000/redoc`

---

## 1. Authentication (`/auth`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/auth/register` | Register student account | Public |
| `POST` | `/auth/login` | Authenticate & retrieve JWT access token | Public |
| `GET` | `/auth/me` | Fetch active user profile and memberships | Authenticated |
| `PUT` | `/auth/me` | Update student profile details | Authenticated |

---

## 2. Grievances (`/grievances`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/grievances` | Submit a grievance (runs AI triage) | Student / Any |
| `GET` | `/grievances` | List grievances (scoped by role & institution) | Authenticated |
| `GET` | `/grievances/{id}` | Grievance details, messages, timeline | Authorized Tenant |
| `PUT` | `/grievances/{id}/status` | Update workflow status (mandatory reason) | Officer / Head / Admin |
| `POST` | `/grievances/{id}/assign` | Assign grievance to institutional officer | Officer / Head / Admin |
| `POST` | `/grievances/{id}/escalate` | Escalate delayed or critical grievance | Authorized Tenant |

---

## 3. Communication & Internal Notes (`/grievances`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/grievances/{id}/messages` | Post case message visible to student | Authorized Tenant |
| `POST` | `/grievances/{id}/internal-notes` | Add confidential internal note | Officer / Head / Admin (Hidden from students) |

---

## 4. Evidence Attachments (`/grievances`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/grievances/{id}/attachments` | Upload supporting document | Authorized Tenant |
| `GET` | `/grievances/{id}/attachments/{att_id}/download` | Stream attachment securely | Authorized Tenant |

---

## 5. Feedback & Reviews (`/grievances`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/grievances/{id}/feedback` | Submit 1-5 star resolution rating | Student Owner |

---

## 6. AI Assistance (`/ai`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/ai/analyze` | Real-time draft category, priority & duplicate check | Authenticated |

---

## 7. Analytics & Reports (`/analytics`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/analytics/dashboard` | Role-tailored operational metrics | Authenticated |
| `GET` | `/analytics/export/csv` | Export grievances to CSV format | Staff / Head / Admin |
