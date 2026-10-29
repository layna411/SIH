# EduResolve AI - Security & Access Control Architecture

## 1. Authentication & Cryptography
- **Password Hashing**: Memory-hard Argon2id via `argon2-cffi` (`PasswordHasher`).
- **Session Tokens**: PyJWT signed HMAC-SHA256 (`HS256`) access tokens with configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Enumeration Protection**: Generic `"Incorrect email or password."` messages prevent user email enumeration on login.
- **Account Verification**: New accounts require verification before submitting formal grievances.

## 2. Multi-Tenant Authorization & IDOR Protection
- **Role-Based Access Control (RBAC)**: Defined roles: `STUDENT`, `COLLEGE_OFFICER`, `INSTITUTION_HEAD`, `REGULATORY_ADMIN`, `SUPER_ADMIN`.
- **Institution Boundaries**: Grievance Officers and Heads are strictly restricted to cases within their verified institution membership. Any request referencing a grievance outside their institution is rejected with `HTTP 403 Forbidden`.
- **Jurisdictional Boundaries**: Regulatory Admins are restricted to institutions within their explicitly mapped state jurisdiction.
- **Student Ownership**: Students can only view grievances they submitted.

## 3. Confidentiality & Internal Note Shielding
- **Internal Notes Separation**: The `grievance_internal_notes` database table is separate from `grievance_messages`. Serializer models for students never expose internal notes.
- **Confidential Reporting Mode**: Students can mark grievances as confidential, which masks their full name, email, and roll number on departmental queues.

## 4. File Upload & Storage Security
- **No Public Static Exposure**: Uploaded files are saved to `private_uploads/` with UUID-based filenames to prevent path traversal and arbitrary execution.
- **Validation**: Strict enforcement of whitelist extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.docx`, `.doc`, `.txt`), MIME types, and maximum file size (default 10MB).
- **Download Authorization**: Every file download passes through `/grievances/{id}/attachments/{att_id}/download` and verifies user permissions before streaming.

## 5. Audit Logging
- Every sensitive action (`USER_LOGIN`, `SUBMIT_GRIEVANCE`, `UPDATE_GRIEVANCE_STATUS`, `ASSIGN_GRIEVANCE`, `ESCALATE_GRIEVANCE`, `UPLOAD_ATTACHMENT`) is persisted to `audit_logs`.
