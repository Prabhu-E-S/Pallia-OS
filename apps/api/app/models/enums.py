"""Domain enums.

Enums are stored as plain strings in the database (``native_enum=False``) so
new values can be added later without ALTER statements.
"""

from enum import StrEnum


class OrganizationType(StrEnum):
    HOSPICE = "HOSPICE"
    HOME_CARE = "HOME_CARE"
    PALLIATIVE_CLINIC = "PALLIATIVE_CLINIC"
    OTHER = "OTHER"


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class UserRole(StrEnum):
    PATIENT = "PATIENT"
    CAREGIVER = "CAREGIVER"
    NURSE = "NURSE"
    DOCTOR = "DOCTOR"
    CARE_COORDINATOR = "CARE_COORDINATOR"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class PatientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCHARGED = "DISCHARGED"
    DECEASED = "DECEASED"
    TRANSFERRED = "TRANSFERRED"


class Gender(StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    UNSPECIFIED = "UNSPECIFIED"


class CaregiverRelationship(StrEnum):
    FAMILY = "FAMILY"
    FRIEND = "FRIEND"
    PROFESSIONAL = "PROFESSIONAL"
    OTHER = "OTHER"


class CarePlanStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CareGoalStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"
    DROPPED = "DROPPED"


class CareGoalPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class ObservationType(StrEnum):
    PAIN = "PAIN"
    SLEEP = "SLEEP"
    FOOD_INTAKE = "FOOD_INTAKE"
    MOBILITY = "MOBILITY"
    MOOD = "MOOD"
    BREATHING = "BREATHING"
    ENERGY = "ENERGY"
    OTHER = "OTHER"


class ObservationSource(StrEnum):
    MANUAL = "MANUAL"
    CAREGIVER_APP = "CAREGIVER_APP"
    PHONE = "PHONE"
    OTHER = "OTHER"


class MedicationPlanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class VisitStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CareTaskStatus(StrEnum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"


class CareTaskType(StrEnum):
    GENERAL = "GENERAL"
    FOLLOWUP = "FOLLOWUP"
    SCHEDULING = "SCHEDULING"
    COMMUNICATION = "COMMUNICATION"
    LOGISTICS = "LOGISTICS"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class CareTaskPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AlertType(StrEnum):
    GENERAL = "GENERAL"
    MEDICAL = "MEDICAL"
    MEDICATION = "MEDICATION"
    VISIT = "VISIT"
    SAFETY = "SAFETY"


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class CommunicationType(StrEnum):
    NOTE = "NOTE"
    MESSAGE = "MESSAGE"
    CALL_LOG = "CALL_LOG"
    EMAIL_LOG = "EMAIL_LOG"
    OTHER = "OTHER"


class ConsentPurpose(StrEnum):
    CARE = "CARE"
    COMMUNICATION = "COMMUNICATION"
    DATA_PROCESSING = "DATA_PROCESSING"
    OTHER = "OTHER"


class ConsentStatus(StrEnum):
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
