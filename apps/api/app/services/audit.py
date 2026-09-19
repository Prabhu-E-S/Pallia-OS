"""Audit logging foundation.

Every entity mutation that matters should call ``record`` so the system can
answer *who did what, when, on which entity, and what changed*.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def record(
    db: Session,
    *,
    organization_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Append one audit entry and commit it."""
    entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
