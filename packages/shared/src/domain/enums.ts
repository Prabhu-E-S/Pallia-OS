/**
 * Canonical domain enums shared across Pallia OS.
 *
 * The authoritative definitions live in the back end
 * (`apps/api/app/models/enums.py`); this file mirrors them for the front end
 * and is intended to be the single place that drives labels, filters and
 * type unions. Keep the two files in sync by hand during Phase 1; a codegen
 * step can take over later.
 */

export const PATIENT_STATUSES = [
  "ACTIVE",
  "INACTIVE",
  "DISCHARGED",
  "DECEASED",
  "TRANSFERRED",
] as const;
export type PatientStatus = (typeof PATIENT_STATUSES)[number];

export const GENDERS = ["FEMALE", "MALE", "OTHER", "UNSPECIFIED"] as const;
export type Gender = (typeof GENDERS)[number];

export const USER_ROLES = [
  "ADMIN",
  "CARE_COORDINATOR",
  "NURSE",
  "DOCTOR",
  "CAREGIVER",
] as const;
export type UserRole = (typeof USER_ROLES)[number];

export const CARE_TASK_TYPES = [
  "GENERAL",
  "FOLLOWUP",
  "SCHEDULING",
  "COMMUNICATION",
  "LOGISTICS",
  "ADMINISTRATIVE",
] as const;
export type CareTaskType = (typeof CARE_TASK_TYPES)[number];

export const CARE_TASK_PRIORITIES = ["LOW", "NORMAL", "HIGH", "URGENT"] as const;
export type CareTaskPriority = (typeof CARE_TASK_PRIORITIES)[number];

export const CARE_TASK_STATUSES = [
  "CREATED",
  "ASSIGNED",
  "ACCEPTED",
  "IN_PROGRESS",
  "COMPLETED",
  "VERIFIED",
  "CANCELLED",
] as const;
export type CareTaskStatus = (typeof CARE_TASK_STATUSES)[number];

export const VISIT_STATUSES = [
  "SCHEDULED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
] as const;
export type VisitStatus = (typeof VISIT_STATUSES)[number];

export const OBSERVATION_TYPES = [
  "PAIN",
  "SLEEP",
  "FOOD_INTAKE",
  "MOBILITY",
  "MOOD",
  "BREATHING",
  "ENERGY",
  "OTHER",
] as const;
export type ObservationType = (typeof OBSERVATION_TYPES)[number];

export const OBSERVATION_SOURCES = [
  "MANUAL",
  "CAREGIVER_APP",
  "PHONE",
  "OTHER",
] as const;
export type ObservationSource = (typeof OBSERVATION_SOURCES)[number];

export const CARE_PLAN_STATUSES = [
  "DRAFT",
  "ACTIVE",
  "ON_HOLD",
  "COMPLETED",
  "ARCHIVED",
] as const;
export type CarePlanStatus = (typeof CARE_PLAN_STATUSES)[number];

export const CARE_GOAL_STATUSES = ["OPEN", "IN_PROGRESS", "ACHIEVED", "DROPPED"] as const;
export type CareGoalStatus = (typeof CARE_GOAL_STATUSES)[number];

export const CARE_GOAL_PRIORITIES = ["LOW", "NORMAL", "HIGH"] as const;
export type CareGoalPriority = (typeof CARE_GOAL_PRIORITIES)[number];

export const CAREGIVER_RELATIONSHIPS = ["FAMILY", "FRIEND", "PROFESSIONAL", "OTHER"] as const;
export type CaregiverRelationship = (typeof CAREGIVER_RELATIONSHIPS)[number];