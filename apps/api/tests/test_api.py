"""Phase 1 backend tests.

Covers:
  * health endpoint
  * database connectivity
  * dev login
  * patient creation + retrieval
  * organization isolation (no cross-tenant reads)
  * basic permission checks
  * consistent error envelope
"""

from sqlalchemy import text


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_database_connection(db):
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_dev_login(client, db, tenants):
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"email": tenants["admin_a"]["user"].email},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@alpha.pallia.dev"


def test_dev_login_rejects_unknown_email(client):
    response = client.post("/api/v1/auth/dev-login", json={"email": "nobody@nowhere.dev"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_patient(client, alpha_headers, tenants):
    response = client.post(
        "/api/v1/patients",
        json={"full_name": "New Patient", "preferred_language": "English"},
        headers=alpha_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["full_name"] == "New Patient"
    assert body["organization_id"] == tenants["org_a"]["id"]


def test_get_patient(client, alpha_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    response = client.get(f"/api/v1/patients/{patient_id}", headers=alpha_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test Patient One"
    assert response.json()["care_plan"] is None


def test_update_patient(client, alpha_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    response = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"full_name": "Renamed Patient"},
        headers=alpha_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Renamed Patient"


def test_organization_isolation(client, beta_headers, tenants):
    """Org B must not be able to read Org A's patients."""
    patient_id = tenants["patient_a"]["id"]
    response = client.get(f"/api/v1/patients/{patient_id}", headers=beta_headers)
    assert response.status_code == 404

    response = client.get("/api/v1/patients", headers=beta_headers)
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert patient_id not in ids
    assert tenants["patient_b"]["id"] in ids


def test_cross_tenant_observation_isolation(client, beta_headers, tenants):
    """A nurse in Org B cannot record an observation for an Org A patient."""
    patient_id = tenants["patient_a"]["id"]
    response = client.post(
        "/api/v1/observations",
        json={"patient_id": patient_id, "type": "MOOD", "value": "calm"},
        headers=beta_headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_permission_denied_for_patient_role(client, patient_role_headers):
    """A PATIENT role has no create permission -> 403 with the error envelope."""
    response = client.post(
        "/api/v1/patients",
        json={"full_name": "Sneaky"},
        headers=patient_role_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_unauthenticated_request(client):
    response = client.get("/api/v1/patients")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_validation_error_envelope(client, alpha_headers):
    response = client.post(
        "/api/v1/patients",
        json={"full_name": ""},
        headers=alpha_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["field"] == "body.full_name"
