"""Phase 2 authorization tests.

Object-level access for CAREGIVER (linked patients only) and PATIENT (own
record only), while staff keep org-wide access. Scope violations return 404.
"""


def test_caregiver_reads_linked_patient(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    response = client.get(f"/api/v1/patients/{patient_id}", headers=caregiver_a_headers)
    assert response.status_code == 200
    assert response.json()["id"] == patient_id


def test_caregiver_cannot_read_unlinked_patient(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a2"]["id"]
    response = client.get(f"/api/v1/patients/{patient_id}", headers=caregiver_a_headers)
    assert response.status_code == 404


def test_caregiver_list_is_scoped(client, caregiver_a_headers, tenants):
    response = client.get("/api/v1/patients", headers=caregiver_a_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == tenants["patient_a"]["id"]


def test_caregiver_cannot_create_patient(client, caregiver_a_headers):
    response = client.post(
        "/api/v1/patients",
        json={"full_name": "Sneaky New Patient"},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_caregiver_idor_task_update(client, caregiver_a_headers, alpha_headers, tenants):
    task = client.post(
        "/api/v1/tasks",
        json={"patient_id": tenants["patient_a2"]["id"], "title": "Secret task"},
        headers=alpha_headers,
    )
    task_id = task.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "tampered"},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 404


def test_caregiver_idor_visit_read(client, caregiver_a_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a2']['id']}/visits",
        headers=caregiver_a_headers,
    )
    assert response.status_code == 404


def test_caregiver_list_visits_scoped(client, caregiver_a_headers, alpha_headers, tenants):
    created = client.post(
        "/api/v1/visits",
        json={"patient_id": tenants["patient_a"]["id"], "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=alpha_headers,
    )
    assert created.status_code == 201

    response = client.get("/api/v1/visits", headers=caregiver_a_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == created.json()["id"]


def test_patient_reads_own_record(client, patient_role_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a']['id']}", headers=patient_role_headers
    )
    assert response.status_code == 200


def test_patient_cannot_read_other_patient(client, patient_role_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a2']['id']}", headers=patient_role_headers
    )
    assert response.status_code == 404


def test_patient_list_is_own_record(client, patient_role_headers, tenants):
    response = client.get("/api/v1/patients", headers=patient_role_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == tenants["patient_a"]["id"]


def test_patient_records_observation_on_own_record(client, patient_role_headers, tenants):
    response = client.post(
        "/api/v1/observations",
        json={"patient_id": tenants["patient_a"]["id"], "type": "MOOD", "value": "calm"},
        headers=patient_role_headers,
    )
    assert response.status_code == 201


def test_patient_cannot_record_observation_on_other(client, patient_role_headers, tenants):
    response = client.post(
        "/api/v1/observations",
        json={"patient_id": tenants["patient_a2"]["id"], "type": "MOOD", "value": "calm"},
        headers=patient_role_headers,
    )
    assert response.status_code == 404


def test_patient_cannot_update_other_patient(client, patient_role_headers, tenants):
    response = client.patch(
        f"/api/v1/patients/{tenants['patient_a2']['id']}",
        json={"full_name": "Hacked"},
        headers=patient_role_headers,
    )
    assert response.status_code == 403


def test_staff_org_wide_access(client, alpha_headers, tenants):
    for patient_id in (tenants["patient_a"]["id"], tenants["patient_a2"]["id"]):
        response = client.get(f"/api/v1/patients/{patient_id}", headers=alpha_headers)
        assert response.status_code == 200
