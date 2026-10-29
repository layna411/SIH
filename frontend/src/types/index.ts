export type UserRole = 
  | 'STUDENT'
  | 'COLLEGE_OFFICER'
  | 'INSTITUTION_HEAD'
  | 'REGULATORY_ADMIN'
  | 'SUPER_ADMIN';

export type GrievanceStatus = 
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'NEEDS_INFORMATION'
  | 'ASSIGNED'
  | 'INVESTIGATION_IN_PROGRESS'
  | 'RESOLUTION_PROPOSED'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REOPENED'
  | 'ESCALATED'
  | 'REJECTED';

export type GrievancePriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export interface InstitutionMembership {
  id: number;
  institution_id: number;
  institution_name: string;
  institution_code: string;
  role: UserRole;
  department?: string;
  designation?: string;
}

export interface RegulatoryJurisdiction {
  id: number;
  user_id: number;
  jurisdiction_type: string;
  state: string;
  region?: string;
  institution_id?: number;
  jurisdiction_code: string;
  notes?: string;
  is_active: boolean;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  is_email_verified?: boolean;
  default_role: UserRole;
  student_id_number?: string;
  created_at: string;
  memberships: InstitutionMembership[];
  regulatory_jurisdictions?: RegulatoryJurisdiction[];
}

export interface UserInvitation {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id?: number;
  institution_name?: string;
  department?: string;
  designation?: string;
  staff_id_number?: string;
  jurisdiction_state?: string;
  jurisdiction_code?: string;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED';
  expires_at: string;
  created_at: string;
  delivery_status: string;
  invitation_link?: string;
  notes?: string;
}

export type UserInviteResponse = UserInvitation;

export interface UserInviteRequest {
  email: string;
  full_name: string;
  role: UserRole;
  institution_id?: number;
  department?: string;
  designation?: string;
  staff_id_number?: string;
  jurisdiction_state?: string;
  jurisdiction_code?: string;
  jurisdiction_notes?: string;
}

export interface InvitationValidateResponse {
  is_valid: boolean;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id?: number;
  institution_name?: string;
  department?: string;
  designation?: string;
  expires_at: string;
}

export interface Institution {
  id: number;
  code: string;
  institution_code?: string;
  name: string;
  state: string;
  city: string;
  address?: string;
  contact_email: string;
  official_email?: string;
  contact_phone?: string;
  website?: string;
  is_active: boolean;
  is_verified: boolean;
  aicte_permanent_id?: string;
  region?: string;
  is_aicte_verified?: boolean;
  alias_names?: string[];
  aliases?: InstitutionAlias[];
  created_at: string;
  admin_account_email?: string;
  default_password?: string;
  account_created?: boolean;
}

export interface InstitutionAlias {
  id: number;
  institution_id: number;
  alias_name: string;
  normalized_alias: string;
  source?: string;
  is_verified: boolean;
  created_at: string;
  updated_at?: string;
}

export type OrgUnitType = 'BUREAU' | 'CELL' | 'REGIONAL_OFFICE' | 'OTHER';

export interface OrganizationalUnit {
  id: number;
  code: string;
  name: string;
  unit_type: OrgUnitType;
  description?: string;
  parent_unit_id?: number;
  region_code?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  parent_code?: string;
  parent_name?: string;
  active_members_count?: number;
}

export interface BureauMembership {
  id: number;
  user_id: number;
  organizational_unit_id: number;
  membership_role: string;
  designation?: string;
  is_active: boolean;
  assigned_by_user_id?: number;
  created_at: string;
  updated_at?: string;
  user_full_name?: string;
  user_email?: string;
  unit_code?: string;
  unit_name?: string;
}

export interface GrievanceCategory {
  id: number;
  code: string;
  name: string;
  description?: string;
  default_sla_days: number;
  is_active: boolean;
  created_at: string;
}

export interface GrievanceStatusHistoryItem {
  id: number;
  from_status?: GrievanceStatus;
  to_status: GrievanceStatus;
  changed_by_name: string;
  reason: string;
  created_at: string;
}

export interface GrievanceMessageItem {
  id: number;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  message: string;
  is_student_visible: boolean;
  created_at: string;
}

export interface GrievanceInternalNoteItem {
  id: number;
  author_id: number;
  author_name: string;
  note: string;
  created_at: string;
}

export interface GrievanceAttachmentItem {
  id: number;
  file_name: string;
  file_size_bytes: number;
  content_type: string;
  is_internal_only: boolean;
  created_at: string;
}

export interface GrievanceFeedbackItem {
  id: number;
  rating: number;
  satisfies_resolution: boolean;
  comments?: string;
  created_at: string;
}

export interface Grievance {
  id: number;
  reference_number: string;
  institution_id: number;
  institution_name: string;
  category_id: number;
  category_name: string;
  subcategory?: string;
  title: string;
  description?: string;
  status: GrievanceStatus;
  priority: GrievancePriority;
  is_confidential: boolean;
  preferred_contact?: string;
  student_id?: number;
  student_name?: string;
  student_email?: string;
  student_id_number?: string;
  assigned_officer_name?: string;
  due_date?: string;
  resolution_summary?: string;
  resolved_at?: string;
  closed_at?: string;
  
  // AI Suggestions
  ai_suggested_category_id?: number;
  ai_suggested_category_name?: string;
  ai_confidence?: number;
  ai_suggested_priority?: GrievancePriority;
  ai_explanation?: string;
  ai_duplicate_suspected?: boolean;
  ai_duplicate_ref?: string;

  created_at: string;
  updated_at: string;
  
  status_history?: GrievanceStatusHistoryItem[];
  messages?: GrievanceMessageItem[];
  internal_notes?: GrievanceInternalNoteItem[];
  attachments?: GrievanceAttachmentItem[];
  feedback?: GrievanceFeedbackItem;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  link?: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_grievances: number;
  pending_grievances: number;
  in_investigation_grievances: number;
  resolved_grievances: number;
  overdue_grievances: number;
  escalated_grievances: number;
  avg_resolution_days: number;
  satisfaction_rate: number;
  status_breakdown: { name: string; value: number }[];
  category_breakdown: { name: string; value: number }[];
  priority_breakdown: { name: string; value: number }[];
  monthly_trends: { month: string; submitted: number; resolved: number }[];
}

export interface AIAnalysisResult {
  category: {
    category_id: number;
    category_name: string;
    confidence: number;
    explanation: string;
    is_rule_based: boolean;
    model_version: string;
  };
  priority: {
    priority: GrievancePriority;
    confidence: number;
    urgency_indicators: string[];
    explanation: string;
    is_rule_based: boolean;
  };
  duplicate_check?: {
    is_duplicate_suspected: boolean;
    highest_similarity: number;
    matches: {
      reference_number: string;
      title: string;
      similarity_score: number;
      status: string;
    }[];
    explanation: string;
  };
  routing?: {
    suggested_department?: string;
    suggested_officer_id?: number;
    suggested_officer_name?: string;
    reason: string;
  };
}

// ---------------------------------------------------------------------------
// Step 7, Phase C: AICTE Case Management & Consolidated Institution Types
// ---------------------------------------------------------------------------

export type AICTECaseStatus =
  | 'RECEIVED'
  | 'PENDING_REVIEW'
  | 'UNDER_PROCESS'
  | 'AWAITING_RESPONSE'
  | 'TRANSFER_PENDING'
  | 'TRANSFERRED'
  | 'ESCALATED'
  | 'DISPOSED'
  | 'CLOSED'
  | 'REOPENED';

export type AICTECaseSourceType =
  | 'DIRECT'
  | 'CAMPUS_REFERRAL'
  | 'REGULATORY_INQUIRY'
  | 'WHISTLEBLOWER'
  | 'OTHER';

export type AICTEComplainantType =
  | 'STUDENT'
  | 'FACULTY'
  | 'STAKEHOLDER'
  | 'INSTITUTION'
  | 'PUBLIC_AUTHORITY'
  | 'ANONYMOUS'
  | 'OTHER';

export type AICTECaseActionType =
  | 'INTAKE'
  | 'ASSIGNMENT'
  | 'INITIAL_SCRUTINY'
  | 'INFO_REQUESTED'
  | 'EXPLANATION_RECEIVED'
  | 'COMMITTEE_REVIEW'
  | 'HEARING_SCHEDULED'
  | 'HEARING_COMPLETED'
  | 'COMPLIANCE_VERIFIED'
  | 'TRANSFER_INITIATED'
  | 'TRANSFER_ACCEPTED'
  | 'ESCALATION'
  | 'DISPOSAL_ORDER'
  | 'STATUS_UPDATE'
  | 'REOPENED'
  | 'NOTE_RECORDED';

export interface CaseAction {
  id: number;
  case_id: number;
  action_type: AICTECaseActionType;
  action_title: string;
  action_description?: string;
  previous_status?: string;
  new_status?: string;
  unit_id: number;
  unit_code?: string;
  unit_name?: string;
  performed_by_user_id: number;
  performed_by_name?: string;
  performed_by_email?: string;
  action_at: string;
  remarks?: string;
  supporting_document_ref?: string;
  next_action_required?: string;
  next_action_due_at?: string;
}

export interface AICTECase {
  id: number;
  case_reference: string;
  institution_id: number;
  institution_name?: string;
  institution_code?: string;
  aicte_permanent_id?: string;
  source_type: AICTECaseSourceType;
  source_grievance_id?: number;
  source_grievance_ref?: string;
  official_reference_number?: string;
  received_at: string;
  complainant_type: AICTEComplainantType;
  category: string;
  subject: string;
  description: string;
  status: AICTECaseStatus;
  current_unit_id: number;
  current_unit_code?: string;
  current_unit_name?: string;
  assigned_officer_id?: number;
  assigned_officer_name?: string;
  assigned_officer_email?: string;
  region?: string;
  priority: GrievancePriority;
  last_action_at: string;
  next_action_required?: string;
  next_action_due_at?: string;
  expected_disposal_at?: string;
  disposed_at?: string;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
}

export interface AICTECaseDetail extends AICTECase {
  actions: CaseAction[];
}

export interface AICTECaseListResponse {
  cases: AICTECase[];
  total: number;
  page: number;
  page_size: number;
}

export interface InstitutionConsolidatedHistory {
  institution_id: number;
  name: string;
  code: string;
  aicte_permanent_id?: string;
  is_aicte_verified: boolean;
  region?: string;
  aliases: string[];
  total_cases: number;
  active_cases: number;
  disposed_cases: number;
  status_counts: Record<string, number>;
  unit_counts: Record<string, number>;
  recent_cases: AICTECase[];
}

export interface CreateAICTECasePayload {
  institution_id: number;
  current_unit_id: number;
  category: string;
  subject: string;
  description: string;
  complainant_type?: AICTEComplainantType;
  complainant_name?: string;
  complainant_email?: string;
  complainant_phone?: string;
  official_reference_number?: string;
  priority?: GrievancePriority;
  region?: string;
  assigned_officer_id?: number;
  expected_disposal_at?: string;
  next_action_required?: string;
  next_action_due_at?: string;
}

export interface ReferGrievancePayload {
  source_grievance_id: number;
  destination_unit_id: number;
  referral_reason: string;
  complainant_type?: AICTEComplainantType;
  priority?: GrievancePriority;
  official_reference_number?: string;
}

export interface AddCaseActionPayload {
  action_type: AICTECaseActionType;
  action_title: string;
  action_description?: string;
  new_status?: AICTECaseStatus;
  remarks?: string;
  supporting_document_ref?: string;
  next_action_required?: string;
  next_action_due_at?: string;
}

// ---------------------------------------------------------------------------
// Step 7, Phase D: AICTE Case Overlaps & Case Linking Types
// ---------------------------------------------------------------------------

export type AICTEOverlapType =
  | 'POTENTIAL_DUPLICATE'
  | 'RELATED_CASE'
  | 'INSUFFICIENT_EVIDENCE';

export type AICTEOverlapReviewStatus =
  | 'PENDING'
  | 'CONFIRMED_DUPLICATE'
  | 'CONFIRMED_RELATED'
  | 'REJECTED'
  | 'DEFERRED';

export type AICTEDetectionMethod =
  | 'RULE_BASED'
  | 'TEXT_SIMILARITY'
  | 'HYBRID'
  | 'MANUAL';

export type AICTECaseLinkType =
  | 'DUPLICATE_OF'
  | 'RELATED_TO';

export interface AICTEOverlapReasons {
  same_institution: boolean;
  same_verified_pid?: boolean;
  cross_bureau: boolean;
  unit_low_code?: string;
  unit_high_code?: string;
  category_match: boolean;
  category_low?: string;
  category_high?: string;
  official_ref_match: boolean;
  subject_similarity: number;
  description_similarity: number;
  temporal_proximity_days: number;
  shared_keywords: string[];
  explanation: string;
}

export interface MaskedCaseSummary {
  id: number;
  case_reference: string;
  official_reference_number?: string;
  institution_id: number;
  institution_name?: string;
  institution_code?: string;
  aicte_permanent_id?: string;
  current_unit_id: number;
  current_unit_code?: string;
  current_unit_name?: string;
  category: string;
  subject: string;
  description?: string;
  status: string;
  priority: string;
  received_at: string;
  last_action_at: string;
  complainant_type: string;
  complainant_name?: string;
  complainant_email?: string;
  complainant_phone?: string;
  assigned_officer_name?: string;
  next_action_required?: string;
  next_action_due_at?: string;
  has_full_access: boolean;
}

export interface AICTECaseOverlap {
  id: number;
  case_id_low: number;
  case_id_high: number;
  overlap_type: AICTEOverlapType;
  match_score?: number;
  match_reasons: AICTEOverlapReasons;
  detection_method: AICTEDetectionMethod;
  review_status: AICTEOverlapReviewStatus;
  detected_at: string;
  reviewed_at?: string;
  reviewed_by_user_id?: number;
  reviewed_by_name?: string;
  review_notes?: string;
  case_low?: MaskedCaseSummary;
  case_high?: MaskedCaseSummary;
  active_link_type?: string;
  created_at: string;
  updated_at: string;
}

export interface AICTECaseOverlapListResponse {
  items: AICTECaseOverlap[];
  total: number;
  page: number;
  page_size: number;
}

export interface AICTECaseLink {
  id: number;
  case_id_low: number;
  case_id_high: number;
  linked_case_id: number;
  linked_case_reference: string;
  linked_case_subject: string;
  linked_case_category: string;
  linked_case_unit_code?: string;
  linked_case_status: string;
  link_type: AICTECaseLinkType;
  source_overlap_id?: number;
  created_by_user_id: number;
  created_by_name?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
}

export interface OverlapHistoryItem {
  id: number;
  action: string;
  actor_name?: string;
  timestamp: string;
  details: Record<string, any>;
}

export interface OverlapReviewPayload {
  action: AICTEOverlapReviewStatus;
  review_notes: string;
}

export interface ManualLinkCreatePayload {
  target_case_id: number;
  link_type: AICTECaseLinkType;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Step 7, Phase E: AICTE Inter-Bureau Case Transfers
// ---------------------------------------------------------------------------

export type AICTETransferStatus =
  | 'PENDING_ACCEPTANCE'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'CANCELLED';

export interface AICTECaseTransfer {
  id: number;
  case_id: number;
  case_reference: string;
  case_subject: string;
  institution_id: number;
  institution_name: string;
  institution_aicte_pid?: string;
  from_unit_id: number;
  from_unit_code: string;
  from_unit_name: string;
  to_unit_id: number;
  to_unit_code: string;
  to_unit_name: string;
  initiated_by_user_id: number;
  initiated_by_name: string;
  proposed_assignee_id?: number;
  proposed_assignee_name?: string;
  transfer_reason: string;
  handover_summary?: string;
  prior_case_status: string;
  transfer_status: AICTETransferStatus;
  initiated_at: string;
  responded_at?: string;
  responded_by_user_id?: number;
  responded_by_name?: string;
  response_notes?: string;
  accepted_assignee_id?: number;
  accepted_assignee_name?: string;
  created_at: string;
  updated_at: string;
}

export interface AICTECaseTransferListResponse {
  items: AICTECaseTransfer[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransferInitiatePayload {
  to_unit_id: number;
  proposed_assignee_id?: number;
  transfer_reason: string;
  handover_summary?: string;
}

export interface TransferAcceptPayload {
  response_notes?: string;
  accepted_assignee_id?: number;
}

export interface TransferRejectPayload {
  rejection_reason: string;
}

export interface TransferCancelPayload {
  cancellation_reason: string;
}

// ---------------------------------------------------------------------------
// AICTE Analytics & Reporting Types (Step 7, Phase F)
// ---------------------------------------------------------------------------

export interface AICTEStatusCount {
  status: string;
  label: string;
  count: number;
}

export interface AICTEAgeingBucket {
  bucket_key: string;
  label: string;
  min_days: number;
  max_days?: number;
  count: number;
  percentage: number;
}

export interface AICTEAgeingResponse {
  total_active_cases: number;
  average_active_age_days?: number;
  median_active_age_days?: number;
  buckets: AICTEAgeingBucket[];
  average_disposal_time_days?: number;
}

export interface AICTESLAResponse {
  active_cases_count: number;
  overdue_next_action_count: number;
  overdue_expected_disposal_count: number;
  total_sla_breached_count: number;
  escalated_cases_count: number;
  missing_next_action_deadline_count: number;
  missing_expected_disposal_count: number;
  sla_compliance_rate?: number;
}

export interface AICTEInstitutionSummary {
  institution_id: number;
  name: string;
  code: string;
  aicte_permanent_id?: string;
  state?: string;
  region?: string;
  total_cases: number;
  active_cases: number;
  overdue_cases: number;
  disposed_cases: number;
  disposal_rate?: number;
}

export interface AICTEInstitutionsAnalyticsResponse {
  total_institutions: number;
  institutions: AICTEInstitutionSummary[];
}

export interface AICTEOrganizationalUnitSummary {
  unit_id: number;
  code: string;
  name: string;
  unit_type: string;
  region_code?: string;
  total_cases: number;
  active_cases: number;
  overdue_cases: number;
  disposed_cases: number;
  pending_incoming_transfers: number;
  disposal_rate?: number;
}

export interface AICTEOrganizationalUnitsAnalyticsResponse {
  total_units: number;
  units: AICTEOrganizationalUnitSummary[];
}

export interface AICTETrendPoint {
  period: string;
  received_count: number;
  disposed_count: number;
  transferred_count: number;
}

export interface AICTETrendsResponse {
  granularity: string;
  trend_points: AICTETrendPoint[];
}

export interface AICTETransferAnalyticsResponse {
  total_transfers_initiated: number;
  pending_acceptance_count: number;
  accepted_count: number;
  rejected_count: number;
  cancelled_count: number;
  average_turnaround_hours?: number;
}

export interface AICTECrossBureauAnalyticsResponse {
  total_overlaps_detected: number;
  pending_review_overlaps: number;
  confirmed_duplicates: number;
  confirmed_related: number;
  rejected_overlaps: number;
  total_case_links: number;
}

export interface AICTEOverviewAnalyticsResponse {
  reporting_period_start?: string;
  reporting_period_end?: string;
  total_received: number;
  total_active: number;
  total_disposed: number;
  status_distribution: AICTEStatusCount[];
  overdue_actions_count: number;
  overdue_disposal_count: number;
  total_sla_breached_count: number;
  escalated_count: number;
  awaiting_action_count: number;
  reopened_count: number;
  pending_transfers_count: number;
  pending_overlaps_count: number;
  disposal_rate?: number;
  average_age_active_days?: number;
}

export interface AICTENotification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  link?: string;
  notification_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  category?: string;
  reference_id?: string;
  is_read: boolean;
  requires_acknowledgement: boolean;
  is_acknowledged: boolean;
  acknowledged_at?: string;
  created_at: string;
}

export interface AICTENotificationListResponse {
  items: AICTENotification[];
  total: number;
  unread_count: number;
  unacknowledged_count: number;
  page: number;
  page_size: number;
}

export interface AICTEAlertSummaryResponse {
  total_unread: number;
  total_unacknowledged: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  by_category: Record<string, number>;
  active_overdue_cases_count: number;
  pending_transfers_count: number;
  pending_overlaps_count: number;
  failed_deliveries_count: number;
}

export interface AICTEOverdueAlertItem {
  case_id: number;
  case_reference: string;
  subject: string;
  institution_id: number;
  institution_name: string;
  current_unit_id: number;
  current_unit_code: string;
  current_unit_name: string;
  assigned_officer_id?: number;
  assigned_officer_name?: string;
  status: string;
  priority: string;
  next_action_required?: string;
  next_action_due_at?: string;
  expected_disposal_at?: string;
  overdue_type: 'NEXT_ACTION' | 'EXPECTED_DISPOSAL' | 'BOTH' | 'MISSING_DEADLINE';
  overdue_days: number;
}

export interface AICTEOverdueAlertListResponse {
  items: AICTEOverdueAlertItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AICTEAlertConfiguration {
  warning_window_hours: number;
  dedup_window_hours: number;
  transfer_pending_hours: number;
  poll_interval_seconds: number;
  scheduler_enabled: boolean;
}


