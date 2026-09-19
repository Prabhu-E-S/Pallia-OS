"""Development / demo seed data.

Creates two organizations with realistic but entirely FICTIONAL patients,
users (every role, with passwords), care plans, observations, visits and
tasks. A PATIENT and a CAREGIVER account are provided per organization so the
object-level authorization rules can be demoed end to end.

This data must never contain real patient information. The script is
idempotent: it skips an organization that already exists.

Run with: python -m app.seed
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Caregiver,
    CaregiverRelationship,
    CaregiverReport,
    CaregiverReportMode,
    CaregiverReportStatus,
    CareGoal,
    CareGoalPriority,
    CareGoalStatus,
    CarePlan,
    CarePlanStatus,
    CareTask,
    CareTaskPriority,
    CareTaskStatus,
    CareTaskType,
    CareTeam,
    Communication,
    CommunicationType,
    Consent,
    ConsentPurpose,
    ConsentStatus,
    Gender,
    Observation,
    ObservationSource,
    ObservationType,
    Organization,
    OrganizationStatus,
    OrganizationType,
    Patient,
    PatientCaregiver,
    PatientCareTeamMember,
    PatientStatus,
    User,
    UserRole,
    Visit,
    VisitStatus,
)

DEMO_PASSWORD = "pallia123"

ORG_A = {
    "name": "Maple Grove Home Care",
    "type": OrganizationType.HOME_CARE,
    "domain": "pallia.demo",
}
ORG_B = {
    "name": "Willow Creek Hospice",
    "type": OrganizationType.HOSPICE,
    "domain": "willowcreek.demo",
}


def _utc(hours_offset: float) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours_offset)


def _user(*, email: str, full_name: str, role: UserRole, phone: str | None = None) -> User:
    return User(
        email=email,
        full_name=full_name,
        phone=phone,
        role=role,
        password_hash=hash_password(DEMO_PASSWORD),
    )


def _organizations_and_users(org_spec: dict) -> tuple[Organization, dict[str, User]]:
    org = Organization(
        name=org_spec["name"],
        type=org_spec["type"],
        status=OrganizationStatus.ACTIVE,
    )
    domain = org_spec["domain"]
    users = {
        "admin": _user(email=f"admin@{domain}", full_name="Ananya Sharma", role=UserRole.ADMIN),
        "coordinator": _user(
            email=f"coordinator@{domain}",
            full_name="Ravi Iyer",
            phone="+91 98765 40001",
            role=UserRole.CARE_COORDINATOR,
        ),
        "nurse": _user(
            email=f"nurse@{domain}",
            full_name="Meera Nair",
            phone="+91 98765 40002",
            role=UserRole.NURSE,
        ),
        "nurse2": _user(
            email=f"nurse2@{domain}",
            full_name="Kiran Menon",
            phone="+91 98765 40003",
            role=UserRole.NURSE,
        ),
        "doctor": _user(
            email=f"doctor@{domain}",
            full_name="Dr. Lakshmi Rao",
            phone="+91 98765 40004",
            role=UserRole.DOCTOR,
        ),
        "caregiver": _user(
            email=f"caregiver@{domain}",
            full_name="Priya Verma",
            phone="+91 98765 40005",
            role=UserRole.CAREGIVER,
        ),
        "patient": _user(
            email=f"patient@{domain}",
            full_name="Lakshmi Devi",
            role=UserRole.PATIENT,
        ),
    }
    for u in users.values():
        u.organization = org
    return org, users


def _patients_maple_grove(org: Organization) -> list[Patient]:
    return [
        Patient(
            organization_id=org.id,
            full_name="Amma Lakshmi",
            date_of_birth=date(1941, 3, 12),
            gender=Gender.FEMALE,
            phone="+91 94400 10001",
            address="12 Green Street, Palakkad",
            preferred_language="Malayalam",
            emergency_contact_name="Suresh (son)",
            emergency_contact_phone="+91 94400 20001",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Ranganathan Krishnan",
            date_of_birth=date(1938, 9, 2),
            gender=Gender.MALE,
            phone="+91 94400 10002",
            address="3 Temple Lane, Kochi",
            preferred_language="Malayalam",
            emergency_contact_name="Kavitha (daughter)",
            emergency_contact_phone="+91 94400 20002",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Mary Thomas",
            date_of_birth=date(1952, 7, 25),
            gender=Gender.FEMALE,
            phone="+91 94400 10003",
            address="8 Rose Garden, Trivandrum",
            preferred_language="English",
            emergency_contact_name="Anil Thomas",
            emergency_contact_phone="+91 94400 20003",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Haji Ibrahim",
            date_of_birth=date(1947, 11, 30),
            gender=Gender.MALE,
            phone="+91 94400 10004",
            address="21 Market Road, Kozhikode",
            preferred_language="Malayalam",
            emergency_contact_name="Fathima (wife)",
            emergency_contact_phone="+91 94400 20004",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Devika Pillai",
            date_of_birth=date(1955, 1, 19),
            gender=Gender.FEMALE,
            phone="+91 94400 10005",
            address="5 Nilgiri Nagar, Munnar",
            preferred_language="Malayalam",
            emergency_contact_name="Ramesh Pillai",
            emergency_contact_phone="+91 94400 20005",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Arun Nambiar",
            date_of_birth=date(1960, 5, 8),
            gender=Gender.MALE,
            phone="+91 94400 10006",
            address="17 Canal Road, Thrissur",
            preferred_language="English",
            emergency_contact_name="Sneha Nambiar",
            emergency_contact_phone="+91 94400 20006",
            status=PatientStatus.ACTIVE,
        ),
    ]


def _patients_willow_creek(org: Organization) -> list[Patient]:
    return [
        Patient(
            organization_id=org.id,
            full_name="Gopal Metha",
            date_of_birth=date(1944, 12, 1),
            gender=Gender.MALE,
            phone="+91 98800 30001",
            address="2 Palm Avenue, Bengaluru",
            preferred_language="Kannada",
            emergency_contact_name="Rekha Metha",
            emergency_contact_phone="+91 98800 40001",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Sunita Rao",
            date_of_birth=date(1958, 4, 22),
            gender=Gender.FEMALE,
            phone="+91 98800 30002",
            address="9 Lilly Road, Mysuru",
            preferred_language="Kannada",
            emergency_contact_name="Anand Rao",
            emergency_contact_phone="+91 98800 40002",
            status=PatientStatus.ACTIVE,
        ),
        Patient(
            organization_id=org.id,
            full_name="Kamal De",
            date_of_birth=date(1951, 6, 14),
            gender=Gender.MALE,
            phone="+91 98800 30003",
            address="15 Lake View, Kolkata",
            preferred_language="Bengali",
            emergency_contact_name="Maya De",
            emergency_contact_phone="+91 98800 40003",
            status=PatientStatus.ACTIVE,
        ),
    ]


def _add_bundles(
    db: Session,
    org: Organization,
    users: dict[str, User],
    patients: list[Patient],
) -> None:
    coordinator = users["coordinator"]
    nurse = users["nurse"]
    nurse2 = users["nurse2"]
    doctor = users["doctor"]
    caregiver_user = users["caregiver"]

    caregiver = Caregiver(
        organization_id=org.id,
        user_id=caregiver_user.id,
        relationship_type=CaregiverRelationship.FAMILY,
    )
    db.add(caregiver)
    db.flush()  # assign caregiver.id before linking

    for index, patient in enumerate(patients):
        link = PatientCaregiver(
            patient_id=patient.id,
            caregiver_id=caregiver.id,
            relationship_type=CaregiverRelationship.FAMILY,
            is_primary=(index == 0),
        )
        db.add(link)

        team = CareTeam(organization_id=org.id, patient_id=patient.id)
        db.add(team)
        db.flush()
        members = [
            PatientCareTeamMember(
                care_team_id=team.id, user_id=coordinator.id, role=coordinator.role
            ),
            PatientCareTeamMember(care_team_id=team.id, user_id=nurse.id, role=nurse.role),
            PatientCareTeamMember(care_team_id=team.id, user_id=doctor.id, role=doctor.role),
        ]
        db.add_all(members)

        plan = CarePlan(
            organization_id=org.id,
            patient_id=patient.id,
            status=CarePlanStatus.ACTIVE,
            start_date=_utc(-20).date(),
            review_date=_utc(14).date(),
            summary="Comfort-focused home care plan maintained by the care team.",
        )
        db.add(plan)
        db.flush()

        goals = [
            CareGoal(
                patient_id=patient.id,
                care_plan_id=plan.id,
                title="Keep pain well controlled",
                description="Regular pain assessment and medication adherence.",
                status=CareGoalStatus.IN_PROGRESS,
                priority=CareGoalPriority.HIGH,
            ),
            CareGoal(
                patient_id=patient.id,
                care_plan_id=plan.id,
                title="Good sleep routine",
                description="Encourage consistent evening routine and calm environment.",
                status=CareGoalStatus.OPEN,
                priority=CareGoalPriority.NORMAL,
            ),
        ]
        db.add_all(goals)

        db.add_all(
            [
                Observation(
                    organization_id=org.id,
                    patient_id=patient.id,
                    recorded_by=nurse.id,
                    type=ObservationType.PAIN,
                    value="3",
                    unit="scale 0-10",
                    notes="Mild discomfort after morning walk.",
                    observed_at=_utc(-index - 1),
                    source=ObservationSource.MANUAL,
                ),
                Observation(
                    organization_id=org.id,
                    patient_id=patient.id,
                    recorded_by=caregiver_user.id,
                    type=ObservationType.SLEEP,
                    value="6",
                    unit="hours",
                    notes="Woke twice, settled back quickly.",
                    observed_at=_utc(-index - 2),
                    source=ObservationSource.MANUAL,
                ),
            ]
        )

        db.add_all(
            [
                Visit(
                    organization_id=org.id,
                    patient_id=patient.id,
                    assigned_to=nurse.id if index % 2 == 0 else nurse2.id,
                    scheduled_at=_utc(index * 4 + 2),
                    status=VisitStatus.SCHEDULED,
                    notes="Routine nursing visit.",
                ),
                Visit(
                    organization_id=org.id,
                    patient_id=patient.id,
                    assigned_to=nurse.id,
                    scheduled_at=_utc(-index - 1),
                    status=VisitStatus.COMPLETED,
                    started_at=_utc(-index - 2),
                    completed_at=_utc(-index - 1),
                    notes="Visited with caregiver; vitals stable.",
                ),
            ]
        )

        db.add_all(
            [
                CareTask(
                    organization_id=org.id,
                    patient_id=patient.id,
                    assigned_to=nurse.id,
                    created_by=coordinator.id,
                    title=f"Follow up on pain medication for {patient.full_name}",
                    description="Confirm supply and comfortable timing.",
                    task_type=CareTaskType.FOLLOWUP,
                    priority=CareTaskPriority.HIGH,
                    status=CareTaskStatus.ASSIGNED,
                    due_at=_utc(12),
                ),
                CareTask(
                    organization_id=org.id,
                    patient_id=patient.id,
                    assigned_to=nurse2.id,
                    created_by=coordinator.id,
                    title="Confirm next visit date",
                    description="Coordinate with family for a suitable slot.",
                    task_type=CareTaskType.SCHEDULING,
                    priority=CareTaskPriority.NORMAL,
                    status=CareTaskStatus.IN_PROGRESS if index % 2 == 0 else CareTaskStatus.CREATED,
                    due_at=_utc(24 * 2),
                ),
            ]
        )

        date_label = _utc(-index).strftime("%d %b")
        content = f"Caregiver updated family behaviours during visit on {date_label}."
        db.add(
            Communication(
                organization_id=org.id,
                patient_id=patient.id,
                sender_id=nurse.id,
                type=CommunicationType.NOTE,
                content=content,
            )
        )

        db.add(
            Consent(
                organization_id=org.id,
                patient_id=patient.id,
                purpose=ConsentPurpose.CARE,
                status=ConsentStatus.GRANTED,
                granted_at=_utc(-30),
                expires_at=_utc(30 * 24),
            )
        )

    db.add_all(
        [
            Alert(
                organization_id=org.id,
                patient_id=patients[0].id,
                type=AlertType.MEDICATION,
                severity=AlertSeverity.WARNING,
                title="Medication supply running low",
                description="Caregiver reports two days of medication remaining.",
                status=AlertStatus.OPEN,
            ),
            Alert(
                organization_id=org.id,
                patient_id=patients[min(2, len(patients) - 1)].id,
                type=AlertType.VISIT,
                severity=AlertSeverity.INFO,
                title="Upcoming review visit",
                description="Care plan review scheduled next week.",
                status=AlertStatus.OPEN,
            ),
        ]
    )


def _seed_caregiver_reports(db: Session, org: Organization) -> None:
    """Add Phase 3 caregiver report data.

    Idempotent per organization: skipped when the org already has reports, so
    re-seeding a database that was seeded in Phase 2 simply adds the Phase 3
    content without duplicating anything.
    """
    if db.scalar(
        select(CaregiverReport.id).where(CaregiverReport.organization_id == org.id).limit(1)
    ):
        print(f"Organisation '{org.name}' already has caregiver reports; skipping Phase 3 data.")
        return

    domain = "pallia.demo" if org.name == ORG_A["name"] else "willowcreek.demo"

    def org_user(email: str) -> User:
        user = db.scalar(select(User).where(User.organization_id == org.id, User.email == email))
        if user is None:  # pragma: no cover - seed data defines these emails.
            raise RuntimeError(f"Missing seeded user '{email}' in '{org.name}'")
        return user

    caregiver = org_user(f"caregiver@{domain}")
    patients = list(
        db.scalars(
            select(Patient)
            .where(Patient.organization_id == org.id)
            .order_by(Patient.created_at.asc())
        )
    )
    if not patients:
        return

    primary = patients[0]
    secondary = patients[1] if len(patients) > 1 else patients[0]
    reported_on = _utc(-1)
    earlier = _utc(-2)

    quick = CaregiverReport(
        organization_id=org.id,
        patient_id=primary.id,
        recorded_by=caregiver.id,
        reported_at=reported_on,
        mode=CaregiverReportMode.QUICK_STATUS,
        status=CaregiverReportStatus.CONFIRMED,
        pain_level=5,
        notes="Some discomfort after dinner; a warm compress helped settle it.",
        human_verified=True,
        confirmed_at=reported_on,
        confirmed_by=caregiver.id,
    )
    db.add(quick)
    db.flush()
    db.add(
        Observation(
            organization_id=org.id,
            patient_id=primary.id,
            recorded_by=caregiver.id,
            type=ObservationType.PAIN,
            value="5",
            unit="scale 0-10",
            observed_at=reported_on,
            source=ObservationSource.CAREGIVER_TEXT,
            source_reference=quick.id,
            ai_generated=False,
            human_verified=True,
        )
    )

    structured = CaregiverReport(
        organization_id=org.id,
        patient_id=secondary.id,
        recorded_by=caregiver.id,
        reported_at=earlier,
        mode=CaregiverReportMode.STRUCTURED,
        status=CaregiverReportStatus.CONFIRMED,
        sleep_hours="6",
        food_intake="ate well",
        mood="calm",
        general_concern="A little worried about the review visit next week.",
        human_verified=True,
        confirmed_at=earlier,
        confirmed_by=caregiver.id,
    )
    db.add(structured)
    db.flush()
    for _field, obs_type, unit, value in (
        ("sleep_hours", ObservationType.SLEEP, "hours", "6"),
        ("food_intake", ObservationType.FOOD_INTAKE, None, "ate well"),
        ("mood", ObservationType.MOOD, None, "calm"),
    ):
        db.add(
            Observation(
                organization_id=org.id,
                patient_id=secondary.id,
                recorded_by=caregiver.id,
                type=obs_type,
                value=value,
                unit=unit,
                observed_at=earlier,
                source=ObservationSource.CAREGIVER_TEXT,
                source_reference=structured.id,
                ai_generated=False,
                human_verified=True,
            )
        )

    text = CaregiverReport(
        organization_id=org.id,
        patient_id=primary.id,
        recorded_by=caregiver.id,
        reported_at=_utc(-3),
        mode=CaregiverReportMode.TEXT,
        status=CaregiverReportStatus.CONFIRMED,
        notes="Rested most of the afternoon. Took a short walk to the garden "
        "and sat outside until the sun moved.",
        human_verified=True,
        confirmed_at=_utc(-3),
        confirmed_by=caregiver.id,
    )
    db.add(text)

    # A voice report left in the review step so the record/transcribe/extract/
    # confirm flow can be demonstrated and continued by a human reviewer.
    voice_reported = _utc(-4)
    voice = CaregiverReport(
        organization_id=org.id,
        patient_id=primary.id,
        recorded_by=caregiver.id,
        reported_at=voice_reported,
        mode=CaregiverReportMode.VOICE,
        status=CaregiverReportStatus.REVIEW_REQUIRED,
        transcript="She said pain is six out of ten this morning and she slept "
        "about five hours. No complaint about food.",
        audio_duration_seconds=23,
        ai_generated=True,
        provider="local",
        model="local-rules-v1",
        model_version="v1",
        confidence=0.9,
        extraction={
            "observations": [
                {
                    "type": "PAIN",
                    "value": "6",
                    "unit": "scale 0-10",
                    "confidence": 0.9,
                    "note": "Pain level reported as a number.",
                },
                {
                    "type": "SLEEP",
                    "value": "5",
                    "unit": "hours",
                    "confidence": 0.9,
                    "note": "Sleep duration reported in hours.",
                },
            ],
            "not_mentioned": ["MOBILITY", "MOOD", "BREATHING", "ENERGY", "OTHER"],
            "summary": "Update mentions: PAIN, SLEEP.",
        },
    )
    db.add(voice)

    db.commit()
    print(f"Seeded Phase 3 caregiver reports for '{org.name}'.")


def seed(db: Session) -> None:
    for org_spec in (ORG_A, ORG_B):
        existing = db.scalar(select(Organization).where(Organization.name == org_spec["name"]))
        if existing is not None:
            print(f"Organization already seeded '{org_spec['name']}'; skipping.")
            continue

        org, users = _organizations_and_users(org_spec)
        db.add(org)
        db.flush()

        if org_spec["name"] == ORG_A["name"]:
            patients = _patients_maple_grove(org)
        else:
            patients = _patients_willow_creek(org)
        db.add_all(patients)
        db.flush()

        # The PATIENT account is linked to the first patient record.
        users["patient"].patient_id = patients[0].id

        _add_bundles(db, org, users, patients)
        db.commit()

        print(
            f"Seeded '{org_spec['name']}' with {len(patients)} patients and "
            f"{len(users)} user accounts (password: {DEMO_PASSWORD})."
        )

    # Phase 3 data is added for both fresh and already-seeded organizations.
    for org_spec in (ORG_A, ORG_B):
        org = db.scalar(select(Organization).where(Organization.name == org_spec["name"]))
        if org is not None:
            _seed_caregiver_reports(db, org)


def main() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
