/**
 * Human labels and badge tones for backend enums.
 * Tone keys map to the Badge component's variant prop.
 */

export const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Active",
  INACTIVE: "Inactive",
  SUSPENDED: "Suspended",
  DISCHARGED: "Discharged",
  DECEASED: "Deceased",
  TRANSFERRED: "Transferred",

  SCHEDULED: "Scheduled",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",

  CREATED: "Created",
  ASSIGNED: "Assigned",
  ACCEPTED: "Accepted",
  VERIFIED: "Verified",

  OPEN: "Open",
  ACHIEVED: "Achieved",
  DROPPED: "Dropped",

  DRAFT: "Draft",
  ON_HOLD: "On hold",
  ARCHIVED: "Archived",
};

export const PRIORITY_LABELS: Record<string, string> = {
  LOW: "Low",
  NORMAL: "Normal",
  HIGH: "High",
  URGENT: "Urgent",
};

export const RELATIONSHIP_LABELS: Record<string, string> = {
  FAMILY: "Family",
  FRIEND: "Friend",
  PROFESSIONAL: "Professional",
  OTHER: "Other",
};

export const OBSERVATION_LABELS: Record<string, string> = {
  PAIN: "Pain",
  SLEEP: "Sleep",
  FOOD_INTAKE: "Food intake",
  MOBILITY: "Mobility",
  MOOD: "Mood",
  BREATHING: "Breathing",
  ENERGY: "Energy",
  OTHER: "Other",
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  GENERAL: "General",
  FOLLOWUP: "Follow-up",
  SCHEDULING: "Scheduling",
  COMMUNICATION: "Communication",
  LOGISTICS: "Logistics",
  ADMINISTRATIVE: "Administrative",
};

export const GENDER_LABELS: Record<string, string> = {
  FEMALE: "Female",
  MALE: "Male",
  OTHER: "Other",
  UNSPECIFIED: "Unspecified",
};

export const ROLE_LABELS: Record<string, string> = {
  ADMIN: "Administrator",
  CARE_COORDINATOR: "Care coordinator",
  NURSE: "Nurse",
  DOCTOR: "Doctor",
  CAREGIVER: "Caregiver",
  PATIENT: "Patient",
};

export const SOURCE_LABELS: Record<string, string> = {
  MANUAL: "Manual",
  CAREGIVER_APP: "Caregiver app",
  PHONE: "Phone",
  OTHER: "Other",
  CAREGIVER_TEXT: "Caregiver update",
  CAREGIVER_VOICE: "Voice update",
};

export const REPORT_MODE_LABELS: Record<string, string> = {
  QUICK_STATUS: "Quick status",
  STRUCTURED: "Structured",
  TEXT: "Text",
  VOICE: "Voice",
};

export const REPORT_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  PROCESSING: "Processing",
  REVIEW_REQUIRED: "Needs review",
  CONFIRMED: "Confirmed",
  CANCELLED: "Cancelled",
};

export const COMPARISON_LABELS: Record<string, string> = {
  increased: "Increased",
  decreased: "Decreased",
  unchanged: "Unchanged",
  changed: "Changed",
  first: "First",
};

type Tone = "neutral" | "teal" | "emerald" | "amber" | "rose" | "sky" | "violet";

export function statusTone(status: string): Tone {
  switch (status) {
    case "ACTIVE":
    case "SCHEDULED":
    case "ASSIGNED":
    case "CREATED":
    case "IN_PROGRESS":
    case "OPEN":
    case "ACCEPTED":
      return "sky";
    case "COMPLETED":
    case "VERIFIED":
    case "ACHIEVED":
      return "emerald";
    case "HIGH":
    case "URGENT":
      return "amber";
    case "BLOCKED":
    case "DECEASED":
    case "CANCELLED":
    case "DROPPED":
      return "rose";
    case "DISCHARGED":
    case "TRANSFERRED":
    case "INACTIVE":
    case "ON_HOLD":
    case "ARCHIVED":
    case "DRAFT":
    case "LOW":
    case "NORMAL":
      return "neutral";
    case "REVIEW_REQUIRED":
    case "PROCESSING":
      return "amber";
    default:
      return "neutral";
  }
}

export function activityLabel(kind: string): string {
  switch (kind) {
    case "observation":
      return "Observation";
    case "visit":
      return "Visit";
    case "task":
      return "Task";
    case "communication":
      return "Communication";
    case "caregiver_report":
    case "caregiver_update":
      return "Caregiver update";
    case "patient":
      return "Patient";
    default:
      return kind;
  }
}