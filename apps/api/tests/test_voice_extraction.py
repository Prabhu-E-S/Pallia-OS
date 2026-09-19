"""Voice pipeline tests: transcribe -> extract -> confirm.

Uses the local speech provider (UTF-8 text as audio payload) and the local
deterministic extraction provider so the full flow runs offline. The safety
rules (explicit numbers only, no fabrication, ambiguity preserved) are asserted.
"""

import uuid

from app.models import AuditLog
from app.services import caregiver_reports as reports_service
from app.services.ai.extraction import AIProviderError


def _create_voice_report(client, headers, patient_id):
    created = client.post(
        f"/api/v1/patients/{patient_id}/caregiver-reports",
        json={"patient_id": patient_id, "mode": "VOICE"},
        headers=headers,
    )
    assert created.status_code == 201
    return created.json()


def _transcribe(client, headers, patient_id, report_id, payload: bytes):
    return client.post(
        f"/api/v1/patients/{patient_id}/voice/transcribe",
        data={"report_id": report_id},
        files={"audio": ("note.mp3", payload, "audio/mpeg")},
        headers=headers,
    )


def test_transcribe_success(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    response = _transcribe(
        client, caregiver_a_headers, patient_id, report["id"], b"pain is five today"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report_id"] == report["id"]
    assert body["transcript"] == "pain is five today"
    assert body["service"] == "local"


def test_transcribe_garbage_returns_503_and_keeps_draft(client, db, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    response = _transcribe(
        client, caregiver_a_headers, patient_id, report["id"], b"\xff\xfe invalid audio"
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "VOICE_SERVICE_UNAVAILABLE"

    failed = (
        db.query(AuditLog)
        .filter_by(action="voice.transcription_failed", entity_id=uuid.UUID(report["id"]))
        .first()
    )
    assert failed is not None

    listing = client.get(
        f"/api/v1/patients/{patient_id}/caregiver-reports", headers=caregiver_a_headers
    ).json()["items"]
    item = next(i for i in listing if i["id"] == report["id"])
    assert item["status"] == "DRAFT"
    assert item["transcript"] is None


def test_extract_requires_transcript(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    response = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 422


def test_extract_explicit_numbers(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(
        client, caregiver_a_headers, patient_id, report["id"], b"pain six, slept five hours"
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    body = response.json()
    types = {obs["type"] for obs in body["observations"]}
    assert "PAIN" in types
    assert body["report"]["status"] == "REVIEW_REQUIRED"
    assert body["ai"]["provider"] == "local"
    assert body["ai"]["model_version"] == "v1"

    pain = next(obs for obs in body["observations"] if obs["type"] == "PAIN")
    assert pain["value"] == "6"
    sleep = next(obs for obs in body["observations"] if obs["type"] == "SLEEP")
    assert sleep["value"] == "5"


def test_extract_no_fabrication_and_ambiguity_preserved(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(
        client,
        caregiver_a_headers,
        patient_id,
        report["id"],
        b"she slept badly last night and the pain is kind of bad",
    )

    response = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    body = response.json()

    types = {obs["type"] for obs in body["observations"]}
    sleep = next(obs for obs in body["observations"] if obs["type"] == "SLEEP")
    assert sleep["value"] == "badly", "sleep quality is kept qualitative, never coerced to a number"
    assert "FOOD_INTAKE" not in types, "food must never be fabricated"

    pain = next(obs for obs in body["observations"] if obs["type"] == "PAIN")
    assert pain["value"] is None, "ambiguous pain must not be given a number"
    assert pain["confidence"] <= 0.4

    assert "FOOD_INTAKE" in body["not_mentioned"]
    assert "SLEEP" not in body["not_mentioned"]


def test_confirm_creates_provenanced_observations(client, db, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(client, caregiver_a_headers, patient_id, report["id"], b"pain is six today")
    extraction = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    ).json()

    pain = next(obs for obs in extraction["observations"] if obs["type"] == "PAIN")
    payload = {
        "report_id": report["id"],
        "observations": [
            {
                "type": pain["type"],
                "value": pain["value"],
                "unit": pain["unit"],
            }
        ],
    }
    response = client.post(
        f"/api/v1/patients/{patient_id}/observations/confirm",
        json=payload,
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report"]["status"] == "CONFIRMED"
    assert len(body["observations"]) == 1

    obs = body["observations"][0]
    assert obs["value"] == "6"
    assert obs["ai_generated"] is True
    assert obs["human_verified"] is True
    assert obs["source"] == "CAREGIVER_VOICE"
    assert obs["source_reference"] == report["id"]

    confirmed = (
        db.query(AuditLog)
        .filter_by(action="observation.confirmed", entity_id=uuid.UUID(obs["id"]))
        .first()
    )
    assert confirmed is not None


def test_confirm_edits_are_marked_edited(client, db, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(client, caregiver_a_headers, patient_id, report["id"], b"pain is five today")
    extraction = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    ).json()
    pain = next(obs for obs in extraction["observations"] if obs["type"] == "PAIN")

    response = client.post(
        f"/api/v1/patients/{patient_id}/observations/confirm",
        json={
            "report_id": report["id"],
            "observations": [{"type": pain["type"], "value": "8", "unit": pain["unit"]}],
        },
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    obs = response.json()["observations"][0]
    assert obs["value"] == "8"
    edited = (
        db.query(AuditLog)
        .filter_by(action="observation.edited", entity_id=uuid.UUID(obs["id"]))
        .first()
    )
    assert edited is not None


def test_confirm_empty_observations_still_confirms_report(client, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(
        client, caregiver_a_headers, patient_id, report["id"], b"everything is fine, no pain"
    )
    client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    )
    response = client.post(
        f"/api/v1/patients/{patient_id}/observations/confirm",
        json={"report_id": report["id"], "observations": []},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 200
    assert response.json()["report"]["status"] == "CONFIRMED"
    assert response.json()["observations"] == []


def test_confirm_cross_tenant_404(client, caregiver_b_headers, tenants, alpha_headers):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, alpha_headers, patient_id)
    _transcribe(client, alpha_headers, patient_id, report["id"], b"pain is six today")
    response = client.post(
        f"/api/v1/patients/{patient_id}/observations/confirm",
        json={"report_id": report["id"], "observations": []},
        headers=caregiver_b_headers,
    )
    assert response.status_code == 404


def test_nurse_can_confirm_report(client, caregiver_b_headers, beta_headers, tenants):
    # Caregiver of org B records a voice update; the org B nurse confirms it.
    patient_id = tenants["patient_b"]["id"]
    report = _create_voice_report(client, caregiver_b_headers, patient_id)
    _transcribe(client, caregiver_b_headers, patient_id, report["id"], b"pain is six today")
    client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_b_headers,
    )
    response = client.post(
        f"/api/v1/patients/{patient_id}/observations/confirm",
        json={"report_id": report["id"], "observations": []},
        headers=beta_headers,
    )
    assert response.status_code == 200


def test_ai_provider_failure_surfaces_as_422(client, monkeypatch, caregiver_a_headers, tenants):
    patient_id = tenants["patient_a"]["id"]
    report = _create_voice_report(client, caregiver_a_headers, patient_id)
    _transcribe(client, caregiver_a_headers, patient_id, report["id"], b"pain is six today")

    def boom(transcript):
        raise AIProviderError("provider returned junk")

    monkeypatch.setattr(reports_service, "extract_from_transcript", boom)
    response = client.post(
        f"/api/v1/patients/{patient_id}/voice/extract",
        json={"report_id": report["id"]},
        headers=caregiver_a_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "AI_EXTRACTION_FAILED"
