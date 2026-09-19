/**
 * TypeScript mirrors of the Pallia OS API (OpenAPI 3.1).
 * Keep in sync with apps/api/app/schemas/*.py.
 */

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string;
  organization_name: string;
  status: UserStatus;
  permissions: string[];
}

export type UserStatus = "ACTIVE" | "INACTIVE" | "SUSPENDED";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  user: CurrentUser;
}

export type UserRole =
  | "ADMIN"
  | "CARE_COORDINATOR"
  | "NURSE"
  | "DOCTOR"
  | "CAREGIVER"
  | "PATIENT";

export type PatientStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "DISCHARGED"
  | "DECEASED"
  | "TRANSFERRED";

export type Gender = "FEMALE" | "MALE" | "OTHER" | "UNSPECIFIED";

export interface PatientSummary {
  id: string;
  full_name: string;
  date_of_birth: string | null;
  gender: Gender | null;
  phone: string | null;
  preferred_language: string | null;
  status: PatientStatus;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface PatientList {
  items: PatientSummary[];
  total: number;
}

export interface CareTeamMember {
  user_id: string;
  full_name: string;
  email: string;
  role: UserRole;
}

export interface PatientCaregiver {
  id: string;
  full_name: string;
  relationship: string;
  is_primary: boolean;
}

export interface CarePlan {
  id: string;
  patient_id: string;
  status: CarePlanStatus;
  start_date: string | null;
  review_date: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export type CarePlanStatus = "DRAFT" | "ACTIVE" | "ON_HOLD" | "COMPLETED" | "ARCHIVED";

export type CareGoalStatus = "OPEN" | "IN_PROGRESS" | "ACHIEVED" | "DROPPED";
export type CareGoalPriority = "LOW" | "NORMAL" | "HIGH";

export interface CareGoal {
  id: string;
  patient_id: string;
  care_plan_id: string | null;
  title: string;
  description: string | null;
  status: CareGoalStatus;
  priority: CareGoalPriority;
  created_at: string;
  updated_at: string;
}

export interface PatientDetail extends PatientSummary {
  address: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  care_team: CareTeamMember[];
  caregivers: PatientCaregiver[];
  care_plan: CarePlan | null;
  care_goals: CareGoal[];
}

export interface PatientCreate {
  full_name: string;
  date_of_birth?: string | null;
  gender?: Gender | null;
  phone?: string | null;
  address?: string | null;
  preferred_language?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
}

export interface PatientUpdate {
  full_name?: string;
  date_of_birth?: string | null;
  gender?: Gender | null;
  phone?: string | null;
  address?: string | null;
  preferred_language?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  status?: PatientStatus;
}

export type ObservationType =
  | "PAIN"
  | "SLEEP"
  | "FOOD_INTAKE"
  | "MOBILITY"
  | "MOOD"
  | "BREATHING"
  | "ENERGY"
  | "OTHER";

export type ObservationSource =
  | "MANUAL"
  | "CAREGIVER_APP"
  | "PHONE"
  | "OTHER"
  | "CAREGIVER_TEXT"
  | "CAREGIVER_VOICE";

export interface Observation {
  id: string;
  patient_id: string;
  recorded_by: string | null;
  type: ObservationType;
  value: string | null;
  unit: string | null;
  notes: string | null;
  observed_at: string;
  source: ObservationSource | null;
  source_reference: string | null;
  ai_generated: boolean;
  human_verified: boolean;
  confidence: number | null;
  model_version: string | null;
  created_at: string;
}

export interface ObservationList {
  items: Observation[];
  total: number;
}

export interface ObservationCreate {
  patient_id: string;
  type: ObservationType;
  value?: string | null;
  unit?: string | null;
  notes?: string | null;
  observed_at?: string | null;
  source?: ObservationSource | null;
}

export type VisitStatus = "SCHEDULED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export interface Visit {
  id: string;
  patient_id: string;
  patient_name: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  status: VisitStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface VisitList {
  items: Visit[];
  total: number;
}

export interface VisitCreate {
  patient_id: string;
  assigned_to?: string | null;
  scheduled_at: string;
  notes?: string | null;
}

export interface VisitUpdate {
  scheduled_at?: string;
  assigned_to?: string | null;
  status?: VisitStatus;
  notes?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export type CareTaskType =
  | "GENERAL"
  | "FOLLOWUP"
  | "SCHEDULING"
  | "COMMUNICATION"
  | "LOGISTICS"
  | "ADMINISTRATIVE";

export type CareTaskPriority = "LOW" | "NORMAL" | "HIGH" | "URGENT";

export type CareTaskStatus =
  | "CREATED"
  | "ASSIGNED"
  | "ACCEPTED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "VERIFIED"
  | "CANCELLED";

export interface CareTask {
  id: string;
  patient_id: string;
  patient_name: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  created_by: string | null;
  title: string;
  description: string | null;
  task_type: CareTaskType;
  priority: CareTaskPriority;
  status: CareTaskStatus;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareTaskList {
  items: CareTask[];
  total: number;
}

export interface CareTaskCreate {
  patient_id: string;
  title: string;
  description?: string | null;
  task_type?: CareTaskType | null;
  priority?: CareTaskPriority | null;
  assigned_to?: string | null;
  due_at?: string | null;
}

export interface CareTaskUpdate {
  title?: string;
  description?: string | null;
  task_type?: CareTaskType | null;
  priority?: CareTaskPriority | null;
  assigned_to?: string | null;
  due_at?: string | null;
  status?: CareTaskStatus;
  completed_at?: string | null;
}

export interface OverviewCounts {
  patients: number;
  active_care_plans: number;
  today_visits: number;
  open_tasks: number;
}

export type ActivityKind =
  | "observation"
  | "visit"
  | "task"
  | "communication"
  | "patient";

export interface ActivityItem {
  id: string;
  kind: ActivityKind;
  patient_id: string | null;
  patient_name: string | null;
  title: string;
  at: string;
}

export interface DashboardSummary {
  counts: OverviewCounts;
  today_visits: Visit[];
  open_tasks: CareTask[];
  recent_activity: ActivityItem[];
}

export type TimelineItemKind =
  | "observation"
  | "visit"
  | "task"
  | "communication"
  | "caregiver_report";

export interface TimelineItem {
  id: string;
  kind: TimelineItemKind;
  title: string;
  detail: string;
  at: string;
}

export interface TimelineResponse {
  items: TimelineItem[];
}

export type CaregiverReportMode =
  | "QUICK_STATUS"
  | "STRUCTURED"
  | "TEXT"
  | "VOICE";

export type CaregiverReportStatus =
  | "DRAFT"
  | "PROCESSING"
  | "REVIEW_REQUIRED"
  | "CONFIRMED"
  | "CANCELLED";

export interface CaregiverReportCreate {
  patient_id: string;
  mode: CaregiverReportMode;
  reported_at?: string | null;
  pain_level?: number | null;
  sleep_hours?: string | null;
  food_intake?: string | null;
  mobility?: string | null;
  mood?: string | null;
  breathing?: string | null;
  energy?: string | null;
  general_concern?: string | null;
  notes?: string | null;
  transcript?: string | null;
  audio_duration_seconds?: number | null;
}

export interface CaregiverReportUpdate {
  reported_at?: string | null;
  pain_level?: number | null;
  sleep_hours?: string | null;
  food_intake?: string | null;
  mobility?: string | null;
  mood?: string | null;
  breathing?: string | null;
  energy?: string | null;
  general_concern?: string | null;
  notes?: string | null;
  transcript?: string | null;
}

export interface CaregiverReport {
  id: string;
  patient_id: string;
  recorded_by: string | null;
  recorded_by_name: string | null;
  reported_at: string;
  mode: CaregiverReportMode;
  status: CaregiverReportStatus;
  pain_level: number | null;
  sleep_hours: string | null;
  food_intake: string | null;
  mobility: string | null;
  mood: string | null;
  breathing: string | null;
  energy: string | null;
  general_concern: string | null;
  notes: string | null;
  transcript: string | null;
  audio_duration_seconds: number | null;
  ai_generated: boolean;
  provider: string | null;
  model: string | null;
  model_version: string | null;
  confidence: number | null;
  extraction: unknown | null;
  human_verified: boolean;
  confirmed_at: string | null;
  confirmed_by: string | null;
  cancelled_at: string | null;
  cancelled_by: string | null;
  cancellation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaregiverReportList {
  items: CaregiverReport[];
  total: number;
}

export interface VoiceTranscriptOut {
  report_id: string;
  patient_id: string;
  transcript: string;
  language: string | null;
  service: string;
}

export interface AISummary {
  provider: string;
  model: string | null;
  model_version: string | null;
  confidence: number | null;
}

export interface ExtractedObservation {
  type: ObservationType;
  value: string | null;
  unit: string | null;
  confidence: number | null;
  note: string | null;
}

export interface ExtractionOut {
  report: CaregiverReport;
  observations: ExtractedObservation[];
  not_mentioned: ObservationType[];
  ai: AISummary;
}

export interface ObservationConfirmPayload {
  report_id: string;
  reported_at?: string | null;
  observations: {
    type: ObservationType;
    value?: string | null;
    unit?: string | null;
    notes?: string | null;
    confidence?: number | null;
  }[];
}

export interface ObservationConfirmOut {
  report: CaregiverReport;
  observations: Observation[];
}

export interface ChangeItem {
  type: string;
  current_value: string | null;
  current_unit: string | null;
  current_observed_at: string | null;
  previous_value: string | null;
  previous_unit: string | null;
  previous_observed_at: string | null;
  comparison: "increased" | "decreased" | "unchanged" | "changed" | "first";
}

export interface RecentChangesOut {
  items: ChangeItem[];
}

export interface CarePlanUpdate {
  status?: CarePlanStatus | null;
  start_date?: string | null;
  review_date?: string | null;
  summary?: string | null;
}

export interface CareGoalCreate {
  care_plan_id?: string | null;
  title: string;
  description?: string | null;
  status?: CareGoalStatus | null;
  priority?: CareGoalPriority | null;
}

export interface CareGoalUpdate {
  title?: string | null;
  description?: string | null;
  status?: CareGoalStatus | null;
  priority?: CareGoalPriority | null;
}

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: string;
  organization_id: string;
}

export interface UserList {
  items: UserSummary[];
  total: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}