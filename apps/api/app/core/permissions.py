"""Permission and role definitions.

Permissions are expressed as strings so they stay readable in the database,
audit logs, and API errors, e.g. ``patient.read``.

New permissions are added here and in ``ROLE_PERMISSIONS``. Authorization is
never hardcoded across routes - routes depend on these reusable constants.
"""

from app.models.enums import UserRole

# ---------------------------------------------------------------------------
# Permission catalog
# ---------------------------------------------------------------------------
PERMISSION_ORGANIZATIONS_READ = "organization.read"

PERMISSION_USERS_READ = "user.read"

PERMISSION_PATIENT_READ = "patient.read"
PERMISSION_PATIENT_CREATE = "patient.create"
PERMISSION_PATIENT_UPDATE = "patient.update"

PERMISSION_OBSERVATION_READ = "observation.read"
PERMISSION_OBSERVATION_CREATE = "observation.create"

PERMISSION_VISIT_READ = "visit.read"
PERMISSION_VISIT_CREATE = "visit.create"
PERMISSION_VISIT_UPDATE = "visit.update"

PERMISSION_CARE_TASK_READ = "care_task.read"
PERMISSION_CARE_TASK_CREATE = "care_task.create"
PERMISSION_CARE_TASK_ASSIGN = "care_task.assign"
PERMISSION_CARE_TASK_UPDATE = "care_task.update"

PERMISSION_CARE_PLAN_READ = "care_plan.read"
PERMISSION_CARE_PLAN_UPDATE = "care_plan.update"

# Convenience constants used by routes.
ALL_PERMISSIONS = frozenset(
    {
        PERMISSION_ORGANIZATIONS_READ,
        PERMISSION_USERS_READ,
        PERMISSION_PATIENT_READ,
        PERMISSION_PATIENT_CREATE,
        PERMISSION_PATIENT_UPDATE,
        PERMISSION_OBSERVATION_READ,
        PERMISSION_OBSERVATION_CREATE,
        PERMISSION_VISIT_READ,
        PERMISSION_VISIT_CREATE,
        PERMISSION_VISIT_UPDATE,
        PERMISSION_CARE_TASK_READ,
        PERMISSION_CARE_TASK_CREATE,
        PERMISSION_CARE_TASK_ASSIGN,
        PERMISSION_CARE_TASK_UPDATE,
        PERMISSION_CARE_PLAN_READ,
        PERMISSION_CARE_PLAN_UPDATE,
    }
)


# ---------------------------------------------------------------------------
# Role -> permission mapping
# ---------------------------------------------------------------------------
CAREGIVER_PERMISSIONS = frozenset(
    {
        PERMISSION_PATIENT_READ,
        PERMISSION_OBSERVATION_READ,
        PERMISSION_OBSERVATION_CREATE,
        PERMISSION_CARE_TASK_READ,
        PERMISSION_CARE_TASK_UPDATE,
    }
)

NURSE_PERMISSIONS = CAREGIVER_PERMISSIONS | frozenset(
    {
        PERMISSION_PATIENT_UPDATE,
        PERMISSION_VISIT_READ,
        PERMISSION_VISIT_CREATE,
        PERMISSION_VISIT_UPDATE,
        PERMISSION_CARE_TASK_CREATE,
    }
)

DOCTOR_PERMISSIONS = frozenset(
    {
        PERMISSION_PATIENT_READ,
        PERMISSION_PATIENT_UPDATE,
        PERMISSION_OBSERVATION_READ,
        PERMISSION_VISIT_READ,
        PERMISSION_CARE_TASK_READ,
        PERMISSION_CARE_PLAN_READ,
        PERMISSION_CARE_PLAN_UPDATE,
    }
)

CARE_COORDINATOR_PERMISSIONS = NURSE_PERMISSIONS | frozenset(
    {
        PERMISSION_PATIENT_CREATE,
        PERMISSION_CARE_TASK_ASSIGN,
        PERMISSION_CARE_PLAN_UPDATE,
    }
)

ADMIN_PERMISSIONS = ALL_PERMISSIONS

ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
    UserRole.PATIENT: frozenset({PERMISSION_PATIENT_READ}),
    UserRole.CAREGIVER: CAREGIVER_PERMISSIONS,
    UserRole.NURSE: NURSE_PERMISSIONS,
    UserRole.DOCTOR: DOCTOR_PERMISSIONS,
    UserRole.CARE_COORDINATOR: CARE_COORDINATOR_PERMISSIONS,
    UserRole.ADMIN: ADMIN_PERMISSIONS,
}


def permissions_for_role(role: UserRole) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role, frozenset())
