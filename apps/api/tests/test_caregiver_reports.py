"""Caregiver report workflow tests.

Manual (QUICK_STATUS / STRUCTURED / TEXT) reports are confirmed immediately and
create provenance-tagged observations. VOICE reports start DRAFT and require a
human confirm step. Object scoping is enforced on every route.
"""


def _create_quick(client, headers, patient_id, **extra):
    payload = {
        "patient_id": patient_id,
        "mode": "QUICK_STATUS",
        "pain_level": 4,
        "notes": "A little sore after lunch.",
        **extra,
    }
    return client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports", json=payload, headers=headers
    )


def test_quick_status_report_is_confirmed_and_creates_observation(
    client, caregiver_a_headers, tenants
):
    patient_id = tenants["patient_a"]["id"]
    response = _create_quick(client, caregiver_a_headers, patient_id)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CONFIRMED"
    assert body["mode"] == "QUICK_STATUS"

    obs = client.get(
        f"/api/v1/patients/{patient_id}/observations", headers=caregiver_a_headers
    ).json()["items"]
    linked = [o for o in obs if o.get("source_reference") == body["id"]]
    assert linked, "observation should reference the report"
    assert linked[0]["type"] == "PAIN"
    assert linked[0]["value"] == "4"
    assert linked[0]["source"] == "CAREGIVER_TEXT"
    assert linked[0]["ai_generated"] is False
    assert linked[0]["human_verified"] is True


def test_text_report_requires_content(client, caregiver_a_headers, tenants):
    response = client.post(
        f"/api/v1/patients/{tenants['patient_a']['id']}/caregiver-reports",
        json={"patient_id": tenants["patient_a"]["id"], "mode": "TEXT"},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 422


def test_caregiver_cannot_report_unlinked_patient(client, caregiver_a_headers, tenants):
    response = _create_quick(client, caregiver_a_headers, tenants["patient_a2"]["id"])
    assert response.status_code == 404


def test_cross_tenant_caregiver_cannot_report(client, caregiver_b_headers, tenants):
    response = _create_quick(client, caregiver_b_headers, tenants["patient_a"]["id"])
    assert response.status_code == 404


def test_staff_can_report_any_patient(client, alpha_headers, tenants):
    response = _create_quick(client, alpha_headers, tenants["patient_a2"]["id"], pain_level=2)
    assert response.status_code == 201
    assert response.json()["status"] == "CONFIRMED"


def test_voice_report_starts_draft_and_patch_updates_transcript(
    client, caregiver_a_headers, tenants
):
    patient_id = tenants["patient_a"]["id"]
    created = client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports",
        json={"patient_id": patient_id, "mode": "VOICE"},
        headers=caregiver_a_headers,
    )
    assert created.status_code == 201
    report = created.json()
    assert report["status"] == "DRAFT"

    patched = client.patch(
        f"/api/v1/patients/{patient_id}/caregiver-reports/{report['id']}",
        json={"transcript": "pain is six this morning"},
        headers=caregiver_a_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["transcript"] == "pain is six this morning"


def test_voice_report_can_be_cancelled(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    created = client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports",
        json={"patient_id": patient_id, "mode": "VOICE"},
        headers=caregiver_a_headers,
    ).json()
    response = client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports/{created['id']}/cancel",
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["cancelled_by"] is not None


def test_list_reports_scoped_to_patient(client, caregiver_a_headers, tenants):
    _create_quick(client, caregiver_a_headers, tenants["patient_a"]["id"], pain_level=3)
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a']['id']}/caregiver-reports",
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["patient_id"] == tenants["patient_a"]["id"] for item in body["items"])


def test_patient_has_no_report_write_access(client, patient_role_headers, tenants):
    response = _create_quick(client, patient_role_headers, tenants["patient_a"]["id"])
    assert response.status_code == 403
