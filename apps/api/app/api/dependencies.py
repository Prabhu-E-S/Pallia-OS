"""Shared FastAPI dependencies."""

from fastapi import Depends

from app.core.permissions import (
    PERMISSION_CARE_PLAN_UPDATE,
    PERMISSION_CARE_TASK_ASSIGN,
    PERMISSION_OBSERVATION_CREATE,
    PERMISSION_PATIENT_CREATE,
    PERMISSION_PATIENT_READ,
    PERMISSION_PATIENT_UPDATE,
    PERMISSION_VISIT_CREATE,
    PERMISSION_VISIT_UPDATE,
)
from app.core.security import get_current_user, require_permission

actor = Depends(get_current_user)

require_patient_read = require_permission(PERMISSION_PATIENT_READ)
require_patient_create = require_permission(PERMISSION_PATIENT_CREATE)
require_patient_update = require_permission(PERMISSION_PATIENT_UPDATE)
require_observation_create = require_permission(PERMISSION_OBSERVATION_CREATE)
require_visit_create = require_permission(PERMISSION_VISIT_CREATE)
require_visit_update = require_permission(PERMISSION_VISIT_UPDATE)
require_care_task_assign = require_permission(PERMISSION_CARE_TASK_ASSIGN)
require_care_plan_update = require_permission(PERMISSION_CARE_PLAN_UPDATE)

__all__ = [
    "actor",
    "require_care_plan_update",
    "require_care_task_assign",
    "require_observation_create",
    "require_patient_create",
    "require_patient_read",
    "require_patient_update",
    "require_visit_create",
    "require_visit_update",
]
