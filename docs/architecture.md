# EduResolve AI - System Architecture

EduResolve AI is a centralized, AI-powered student grievance redressal and institutional monitoring platform designed for multi-institution higher education governance.

```
                           +----------------------------------------+
                           |           React Frontend               |
                           | (Vite, TypeScript, Tailwind, Recharts) |
                           +-------------------+--------------------+
                                               |
                                     REST APIs / JWT Auth
                                               |
                                               v
                           +----------------------------------------+
                           |          FastAPI Backend               |
                           |    (Python 3.11, Pydantic v2, RBAC)    |
                           +---------+-------------------+----------+
                                     |                   |
                     SQLAlchemy 2.0  |                   |  Local NLP
                                     v                   v
                     +----------------------+  +---------------------+
                     |    XAMPP MySQL 8+  |  |   AI Service Layer  |
                     | (Multi-tenant schema)|  |  - TF-IDF Classifier|
                     +----------------------+  |  - Cosine Similarity|
                                               |  - Urgency Engine   |
                                               +---------------------+
```

## Core Architectural Components

### 1. Frontend Client
- **Framework**: React 18 with TypeScript and Vite.
- **Styling**: Tailwind CSS tailored with consistent design tokens (primary blue `#2563EB`, rounded cards, clean typography).
- **State & Data**: TanStack Query (React Query) and React Context API for authentication and session persistence.
- **Routing**: React Router v6 with strict role-based route guards (`ProtectedRoute`).

### 2. Backend Application
- **Framework**: FastAPI (asynchronous ASGI with Uvicorn).
- **Validation**: Pydantic v2 request/response schemas with strict input sanitation.
- **Authentication**: JWT access tokens signed with HMAC-SHA256, Argon2 password cryptography via `argon2-cffi`.
- **Authorization**: Granular multi-tenant RBAC dependencies enforcing institutional boundaries and regulatory jurisdictions.

### 3. Database Layer
- **ORM**: SQLAlchemy 2.x with declarative mapped columns.
- **Engines Supported**: XAMPP MySQL / MariaDB (Server 127.0.0.1:3306, database: eduresolve_ai). SQLite is prohibited.
- **Migration**: Alembic database migrations.

### 4. Pluggable AI Service Layer
- **Text Classification**: Scikit-learn TF-IDF vectorization with domain keyword matching.
- **Duplicate Detection**: Cosine similarity against institutional complaint corpus (preserving multi-tenant isolation).
- **Urgency Scoring**: Heuristic pattern recognition for anti-ragging, safety threats, and academic deadlines.
- **Transparency**: AI suggestions are advisory; authorized human officers retain final decision authority.
