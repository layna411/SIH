Database Engine: **XAMPP MySQL / MariaDB** (Default: `127.0.0.1:3306`, Database: `eduresolve_ai`).  
SQLite is prohibited by design specification.  
Character Encoding: `utf8mb4` with `utf8mb4_unicode_ci`.

---

## Entity Relationship Overview

### 1. `users`
- `id` (PK, INT AUTO_INCREMENT)
- `email` (VARCHAR(255), UNIQUE, INDEX)
- `hashed_password` (VARCHAR(255))
- `full_name` (VARCHAR(150))
- `phone_number` (VARCHAR(30))
- `default_role` (ENUM: STUDENT, COLLEGE_OFFICER, INSTITUTION_HEAD, REGULATORY_ADMIN, SUPER_ADMIN)
- `student_id_number` (VARCHAR(50))
- `is_active` (BOOLEAN), `is_verified` (BOOLEAN)
- `created_at`, `updated_at` (DATETIME UTC)

### 2. `institutions`
- `id` (PK, INT AUTO_INCREMENT)
- `code` (VARCHAR(50), UNIQUE, INDEX) - e.g. `NITD01`
- `name` (VARCHAR(255), INDEX)
- `state` (VARCHAR(100), INDEX), `city` (VARCHAR(100))
- `contact_email` (VARCHAR(255))
- `is_active` (BOOLEAN), `is_verified` (BOOLEAN)
- `created_at` (DATETIME UTC)

### 3. `institution_memberships`
- `id` (PK, INT AUTO_INCREMENT)
- `user_id` (FK -> users.id)
- `institution_id` (FK -> institutions.id)
- `role` (ENUM: UserRoleEnum)
- `department` (VARCHAR(100)), `designation` (VARCHAR(100))
- `is_active` (BOOLEAN)

### 4. `regulatory_jurisdictions`
- `id` (PK, INT AUTO_INCREMENT)
- `user_id` (FK -> users.id)
- `state` (VARCHAR(100), INDEX)
- `jurisdiction_code` (VARCHAR(50))

### 5. `grievance_categories`
- `id` (PK, INT AUTO_INCREMENT)
- `code` (VARCHAR(50), UNIQUE, INDEX)
- `name` (VARCHAR(100))
- `default_sla_days` (INT, default 7)
- `is_active` (BOOLEAN)

### 6. `grievances`
- `id` (PK, INT AUTO_INCREMENT)
- `reference_number` (VARCHAR(50), UNIQUE, INDEX) - e.g. `GRV-2026-EXAM01`
- `student_id` (FK -> users.id)
- `institution_id` (FK -> institutions.id)
- `category_id` (FK -> grievance_categories.id)
- `title` (VARCHAR(255)), `description` (TEXT)
- `status` (ENUM: SUBMITTED, UNDER_REVIEW, NEEDS_INFORMATION, ASSIGNED, INVESTIGATION_IN_PROGRESS, RESOLUTION_PROPOSED, RESOLVED, CLOSED, REOPENED, ESCALATED, REJECTED)
- `priority` (ENUM: LOW, NORMAL, HIGH, URGENT)
- `is_confidential` (BOOLEAN)
- `ai_suggested_category_id` (FK -> grievance_categories.id)
- `ai_confidence` (FLOAT)
- `ai_suggested_priority` (ENUM)
- `due_date` (DATETIME), `resolution_summary` (TEXT)
- `resolved_at`, `closed_at`, `created_at`, `updated_at` (DATETIME UTC)

### 7. `grievance_status_history`
- `id` (PK, INT AUTO_INCREMENT)
- `grievance_id` (FK -> grievances.id)
- `from_status` (ENUM), `to_status` (ENUM)
- `changed_by_user_id` (FK -> users.id)
- `reason` (TEXT - mandatory for audit compliance)
- `created_at` (DATETIME UTC)

### 8. `grievance_messages` & `grievance_internal_notes`
- `grievance_messages`: Student-visible official communications between student and assigned officer.
- `grievance_internal_notes`: Confidential officer observations (never returned to student API requests).

### 9. `grievance_attachments`
- `file_name` (original user file name)
- `stored_file_name` (secure random UUID name in private directory)
- `file_size_bytes`, `content_type`, `is_internal_only`

### 10. `grievance_feedback`
- `rating` (INT 1-5), `satisfies_resolution` (BOOLEAN), `comments` (TEXT)

### 11. `audit_logs`
- `action`, `entity_type`, `user_id`, `entity_id`, `ip_address`, `details`, `created_at`
