"""Care plan and care goal Phase 3 tests.

Goals live under a patient's care plan; creating a goal requires the plan to
exist. Permission matrix: staff + caregivers with update permission may edit;
role/permission gaps and cross-tenant access surface as 403 / 404.
"""

import uuid

from sqlalchemy import select

from app.models import CarePlan, CarePlanStatus


def _ensure_plan(db, tenants, patient_id):
    existing = db.scalar(
        select(CarePlan).where(CarePlan.patient_id == uuid.UUID(patient_id)).limit(1)
    )
    if existing:
        return existing
    plan = CarePlan(
        id=uuid.uuid4(),
        organization_id=tenants["org_a"]["id_raw"],
        patient_id=uuid.UUID(patient_id),
        status=CarePlanStatus.ACTIVE,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def test_update_care_plan_summary(client, db, alpha_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _ensure_plan(db, tenants, patient_id)
    response = client.put(
        f"/api/v1/patients/{patient_id}/care-plan",
        json={"summary": "Focus on comfort and sleep hygiene."},
        headers=alpha_headers,
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "Focus on comfort and sleep hygiene."


def test_create_and_update_goal(client, db, alpha_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    plan = _ensure_plan(db, tenants, patient_id)
    created = client.post(
        f"/api/v1/patients/{patient_id}/care-plan/goals",
        json={
            "care_plan_id": str(plan.id),
            "title": "Complete three short walks",
            "priority": "HIGH",
        },
        headers=alpha_headers,
    )
    assert created.status_code == 201
    goal = created.json()
    assert goal["title"] == "Complete three short walks"
    assert goal["priority"] == "HIGH"
    assert goal["status"] == "OPEN"

    updated = client.patch(
        f"/api/v1/patients/{patient_id}/care-plan/goals/{goal['id']}",
        json={"status": "ACHIEVED"},
        headers=alpha_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "ACHIEVED"


def test_goal_requires_plan(client, alpha_headers, tenants):
    response = client.post(
        f"/api/v1/patients/{tenants['patient_a2']['id']}/care-plan/goals",
        json={"title": "Orphan goal"},
        headers=alpha_headers,
    )
    assert response.status_code == 422


def test_caregiver_can_create_but_not_update_goal(
    client, db, caregiver_a_headers, alpha_headers, tenants
):
    patient_id = tenants["patient_a"]["id"]
    plan = _ensure_plan(db, tenants, patient_id)
    created = client.post(
        f"/api/v1/patients/{patient_id}/care-plan/goals",
        json={"care_plan_id": str(plan.id), "title": "Caregiver goal"},
        headers=caregiver_a_headers,
    )
    assert created.status_code == 201

    denied = client.patch(
        f"/api/v1/patients/{patient_id}/care-plan/goals/{created.json()['id']}",
        json={"status": "ACHIEVED"},
        headers=caregiver_a_headers,
    )
    assert denied.status_code == 403


def test_cross_tenant_goal_404(client, beta_headers, tenants):
    response = client.post(
        f"/api/v1/patients/{tenants['patient_a']['id']}/care-plan/goals",
        json={"title": "Sneaky goal"},
        headers=beta_headers,
    )
    assert response.status_code == 404


def test_goal_scoped_to_patient(db, client, alpha_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    plan = _ensure_plan(db, tenants, patient_id)
    goal = client.post(
        f"/api/v1/patients/{patient_id}/care-plan/goals",
        json={"care_plan_id": str(plan.id), "title": "Owned goal"},
        headers=alpha_headers,
    ).json()
    # Updating a goal through a different patient's scope must 404.
    response = client.patch(
        f"/api/v1/patients/{tenants['patient_a2']['id']}/care-plan/goals/{goal['id']}",
        json={"status": "ACHIEVED"},
        headers=alpha_headers,
    )
    assert response.status_code == 404
