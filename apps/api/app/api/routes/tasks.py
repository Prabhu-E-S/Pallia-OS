from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_care_task_assign
from app.core.database import get_db
from app.core.permissions import (
    PERMISSION_CARE_TASK_CREATE,
    PERMISSION_CARE_TASK_READ,
    PERMISSION_CARE_TASK_UPDATE,
)
from app.core.security import require_permission
from app.models import User
from app.schemas.task import CareTaskCreate, CareTaskList, CareTaskOut, CareTaskUpdate
from app.services import tasks as tasks_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=CareTaskList)
def list_tasks(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_CARE_TASK_READ)),
):
    items = tasks_service.list_organization(db, actor)
    return CareTaskList(items=items, total=len(items))


@router.post("", response_model=CareTaskOut, status_code=201)
def create_task(
    payload: CareTaskCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_CARE_TASK_CREATE)),
):
    task = tasks_service.create_task(db, actor, payload)
    return tasks_service._task_out(db, task)


@router.patch("/{task_id}", response_model=CareTaskOut)
def update_task(
    task_id: str,
    payload: CareTaskUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_CARE_TASK_UPDATE)),
):
    task = tasks_service.get_task_in_org(db, actor, task_id)
    task = tasks_service.update_task(db, actor, task, payload)
    return tasks_service._task_out(db, task)


@router.post("/{task_id}/assign", response_model=CareTaskOut)
def assign_task(
    task_id: str,
    payload: CareTaskUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_care_task_assign),
):
    task = tasks_service.get_task_in_org(db, actor, task_id)
    task = tasks_service.update_task(db, actor, task, payload)
    return tasks_service._task_out(db, task)
