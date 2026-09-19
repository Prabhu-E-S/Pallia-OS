"""Patient timeline Phase 3 tests.

Confirmed caregiver reports appear on the timeline with a kind of
``caregiver_report`` (``caregiver_update`` accepted as a filter alias); draft
reports never do. The kind filter narrows the timeline to a single category.
"""


def _quick_report(client, headers, patient_id, pain=4):
    return client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports",
        json={"patient_id": patient_id, "mode": "QUICK_STATUS", "pain_level": pain},
        headers=headers,
    )


def test_confirmed_report_appears_on_timeline(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _quick_report(client, caregiver_a_headers, patient_id).json()

    timeline = client.get(
        f"/api/v1/patients/{patient_id}/timeline", headers=caregiver_a_headers
    ).json()["items"]
    items = [i for i in timeline if i["kind"] == "caregiver_report"]
    assert any(i["id"] == report["id"] for i in items)
    entry = next(i for i in items if i["id"] == report["id"])
    assert "Pain 4" in entry["detail"] or "Pain: 4" in entry["detail"]


def test_draft_report_never_on_timeline(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    draft = client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports",
        json={"patient_id": patient_id, "mode": "VOICE"},
        headers=caregiver_a_headers,
    ).json()
    assert draft["status"] == "DRAFT"

    items = client.get(
        f"/api/v1/patients/{patient_id}/timeline", headers=caregiver_a_headers
    ).json()["items"]
    assert all(i["id"] != draft["id"] for i in items)


def test_kind_filter_caregiver_only(client, alpha_headers, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _quick_report(client, caregiver_a_headers, patient_id, pain=6)
    client.post(
        "/api/v1/observations",
        json={"patient_id": patient_id, "type": "MOOD", "value": "calm"},
        headers=caregiver_a_headers,
    )

    filtered = client.get(
        f"/api/v1/patients/{patient_id}/timeline?kind=caregiver_update",
        headers=alpha_headers,
    ).json()["items"]
    assert filtered, "confirmed caregiver report should be in timeline"
    assert all(i["kind"] == "caregiver_report" for i in filtered)

    observations = client.get(
        f"/api/v1/patients/{patient_id}/timeline?kind=observations",
        headers=alpha_headers,
    ).json()["items"]
    assert all(i["kind"] == "observation" for i in observations)


def test_timeline_scoped_to_patient(client, caregiver_a_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a2']['id']}/timeline?kind=caregiver_update",
        headers=caregiver_a_headers,
    )
    assert response.status_code == 404


def test_nurse_sees_caregiver_updates(client, caregiver_b_headers, beta_headers, tenants):
    patient_id = tenants["patient_b"]["id"]
    _quick_report(client, caregiver_b_headers, patient_id, pain=7)
    items = client.get(
        f"/api/v1/patients/{patient_id}/timeline?kind=caregiver_report",
        headers=beta_headers,
    ).json()["items"]
    assert any(i["kind"] == "caregiver_report" for i in items)
