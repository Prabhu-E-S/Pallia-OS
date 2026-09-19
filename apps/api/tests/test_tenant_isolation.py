"""Phase 2 tenant isolation + cross-tenant IDOR tests.

Every resource must be org-scoped; object access across orgs returns 404.
"""


def _create_task(client, headers, patient_id: str) -> str:
    response = client.post(
        "/api/v1/tasks",
        json={"patient_id": patient_id, "title": "Org A secret task"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_visit(client, headers, patient_id: str) -> str:
    response = client.post(
        "/api/v1/visits",
        json={"patient_id": patient_id, "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_nurse_b_cannot_read_org_a_patient(client, beta_headers, tenants):
    response = client.get(f"/api/v1/patients/{tenants['patient_a']['id']}", headers=beta_headers)
    assert response.status_code == 404


def test_nurse_b_cannot_update_org_a_patient(client, beta_headers, tenants):
    response = client.patch(
        f"/api/v1/patients/{tenants['patient_a']['id']}",
        json={"full_name": "Hacked"},
        headers=beta_headers,
    )
    assert response.status_code == 404


def test_caregiver_b_cannot_read_org_a_patient(client, caregiver_b_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a']['id']}", headers=caregiver_b_headers
    )
    assert response.status_code == 404


def test_cross_tenant_task_idor(client, alpha_headers, beta_headers, tenants):
    task_id = _create_task(client, alpha_headers, tenants["patient_a"]["id"])

    patch_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "tampered"},
        headers=beta_headers,
    )
    assert patch_response.status_code == 404


def test_cross_tenant_visit_idor(client, alpha_headers, beta_headers, tenants):
    visit_id = _create_visit(client, alpha_headers, tenants["patient_a"]["id"])

    patch_response = client.patch(
        f"/api/v1/visits/{visit_id}",
        json={"notes": "tampered"},
        headers=beta_headers,
    )
    assert patch_response.status_code == 404


def test_cross_tenant_observation_write(client, beta_headers, tenants):
    response = client.post(
        "/api/v1/observations",
        json={"patient_id": tenants["patient_a"]["id"], "type": "PAIN", "value": "8"},
        headers=beta_headers,
    )
    assert response.status_code == 404


def test_beta_user_sees_only_own_org_data(client, beta_headers, tenants):
    strategy = {
        "/api/v1/patients": {"expected_count": 1, "allowed_id": tenants["patient_b"]["id"]},
        "/api/v1/tasks": {"expected_count": 0, "allowed_id": None},
        "/api/v1/visits": {"expected_count": 0, "allowed_id": None},
    }
    for path, expectations in strategy.items():
        response = client.get(path, headers=beta_headers)
        assert response.status_code == 200, path
        body = response.json()
        assert body["total"] == expectations["expected_count"], path
        ids = {item["id"] for item in body["items"]}
        if expectations["allowed_id"]:
            assert expectations["allowed_id"] in ids


def test_org_a_observation_list_scoped_by_org(client, alpha_headers, beta_headers, tenants):
    created = client.post(
        "/api/v1/observations",
        json={"patient_id": tenants["patient_a"]["id"], "type": "PAIN", "value": "4"},
        headers=alpha_headers,
    )
    assert created.status_code == 201
    obs_id = created.json()["id"]

    beta_list = client.get("/api/v1/observations", headers=beta_headers)
    assert beta_list.status_code == 200
    assert beta_list.json()["total"] == 0
    assert all(item["id"] != obs_id for item in beta_list.json()["items"])


def test_org_a_tasks_visible_only_to_org_a(client, alpha_headers, beta_headers, tenants):
    task_id = _create_task(client, alpha_headers, tenants["patient_a"]["id"])

    alpha_list = client.get("/api/v1/tasks", headers=alpha_headers)
    assert alpha_list.status_code == 200
    assert any(item["id"] == task_id for item in alpha_list.json()["items"])

    beta_list = client.get("/api/v1/tasks", headers=beta_headers)
    assert beta_list.status_code == 200
    assert beta_list.json()["total"] == 0
