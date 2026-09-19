"""Recent observation changes ("what changed?") tests.

Compares the latest observation against its immediate predecessor per type,
labelling the change as increased / decreased / changed / first.
"""


def _record(client, headers, patient_id, obs_type, value):
    return client.post(
        "/api/v1/observations",
        json={"patient_id": patient_id, "type": obs_type, "value": value},
        headers=headers,
    )


def test_numeric_increase(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _record(client, caregiver_a_headers, patient_id, "PAIN", "2")
    _record(client, caregiver_a_headers, patient_id, "PAIN", "5")

    changes = client.get(
        f"/api/v1/patients/{patient_id}/observations/recent", headers=caregiver_a_headers
    ).json()["items"]
    pain = next(c for c in changes if c["type"] == "PAIN")
    assert pain["current_value"] == "5"
    assert pain["previous_value"] == "2"
    assert pain["comparison"] == "increased"


def test_numeric_decrease(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _record(client, caregiver_a_headers, patient_id, "PAIN", "7")
    _record(client, caregiver_a_headers, patient_id, "PAIN", "3")

    changes = client.get(
        f"/api/v1/patients/{patient_id}/observations/recent", headers=caregiver_a_headers
    ).json()["items"]
    pain = next(c for c in changes if c["type"] == "PAIN")
    assert pain["comparison"] == "decreased"


def test_first_observation_has_no_previous(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _record(client, caregiver_a_headers, patient_id, "SLEEP", "7")

    changes = client.get(
        f"/api/v1/patients/{patient_id}/observations/recent", headers=caregiver_a_headers
    ).json()["items"]
    sleep = next(c for c in changes if c["type"] == "SLEEP")
    assert sleep["previous_value"] is None
    assert sleep["comparison"] == "first"


def test_qualitative_change(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    _record(client, caregiver_a_headers, patient_id, "MOOD", "calm")
    _record(client, caregiver_a_headers, patient_id, "MOOD", "anxious")

    changes = client.get(
        f"/api/v1/patients/{patient_id}/observations/recent", headers=caregiver_a_headers
    ).json()["items"]
    mood = next(c for c in changes if c["type"] == "MOOD")
    assert mood["comparison"] == "changed"


def test_recent_scoped_to_patient(client, caregiver_a_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a2']['id']}/observations/recent",
        headers=caregiver_a_headers,
    )
    assert response.status_code == 404


def test_cross_tenant_recent_404(client, beta_headers, tenants):
    response = client.get(
        f"/api/v1/patients/{tenants['patient_a']['id']}/observations/recent",
        headers=beta_headers,
    )
    assert response.status_code == 404
