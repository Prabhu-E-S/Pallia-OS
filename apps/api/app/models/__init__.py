"""Domain models package. All models must be imported here so SQLAlchemy
configures them on startup and Alembic can discover the metadata."""

from app.models import auth as _auth  # noqa: F401
from app.models import care as _care  # noqa: F401  (registers table metadata)
from app.models import caregiver_reports as _caregiver_reports  # noqa: F401
from app.models import clinical as _clinical  # noqa: F401
from app.models import communications as _communications  # noqa: F401
from app.models import organization as _organization  # noqa: F401
from app.models.auth import AuthSession
from app.models.care import (
    Caregiver,
    CareGoal,
    CarePlan,
    CareTeam,
    Patient,
    PatientCaregiver,
    PatientCareTeamMember,
)
from app.models.caregiver_reports import CaregiverReport
from app.models.clinical import (
    CareTask,
    MedicationPlan,
    Observation,
    Visit,
)
from app.models.communications import (
    Alert,
    Attachment,
    AuditLog,
    Communication,
    Consent,
)
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    CaregiverRelationship,
    CaregiverReportMode,
    CaregiverReportStatus,
    CareGoalPriority,
    CareGoalStatus,
    CarePlanStatus,
    CareTaskPriority,
    CareTaskStatus,
    CareTaskType,
    CommunicationType,
    ConsentPurpose,
    ConsentStatus,
    Gender,
    MedicationPlanStatus,
    ObservationSource,
    ObservationType,
    OrganizationStatus,
    OrganizationType,
    PatientStatus,
    UserRole,
    UserStatus,
    VisitStatus,
)
from app.models.organization import Organization, User

__all__ = [
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "AlertType",
    "Attachment",
    "AuditLog",
    "AuthSession",
    "CareGoal",
    "CareGoalPriority",
    "CareGoalStatus",
    "CarePlan",
    "CarePlanStatus",
    "CareTask",
    "CareTaskPriority",
    "CareTaskStatus",
    "CareTaskType",
    "CareTeam",
    "Caregiver",
    "CaregiverRelationship",
    "CaregiverReport",
    "CaregiverReportMode",
    "CaregiverReportStatus",
    "Communication",
    "CommunicationType",
    "Consent",
    "ConsentPurpose",
    "ConsentStatus",
    "Gender",
    "MedicationPlan",
    "MedicationPlanStatus",
    "Observation",
    "ObservationSource",
    "ObservationType",
    "Organization",
    "OrganizationStatus",
    "OrganizationType",
    "Patient",
    "PatientCareTeamMember",
    "PatientCaregiver",
    "PatientStatus",
    "User",
    "UserRole",
    "UserStatus",
    "Visit",
    "VisitStatus",
]
