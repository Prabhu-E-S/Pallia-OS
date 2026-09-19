"""Development / demo seed data.

Creates one organization plus realistic but entirely FICTIONAL patients,
users, care plans, observations, visits and tasks.

This data must never contain real patient information. The script is
idempotent: it skips seeding when the demo organization already exists.

Run with: python -m app.seed
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Caregiver,
    CaregiverRelationship,
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

DEMO_ORG_NAME = "Demo Palliative Care"
DEMO_PASSWORD = "pallia123"


def _utc(hours_offset: float) -> datetime:
    return datetime.now(UTC) + timedelta(hours=hours_offset)


def _organizations_and_users() -> tuple[Organization, list[User]]:
    org = Organization(
        name=DEMO_ORG_NAME,
        type=OrganizationType.HOME_CARE,
        status=OrganizationStatus.ACTIVE,
    )
    admin = User(email="admin@pallia.demo", full_name="Ananya Sharma", role=UserRole.ADMIN)
    coordinator = User(
        email="coordinator@pallia.demo",
        full_name="Ravi Iyer",
        phone="+91 98765 40001",
        role=UserRole.CARE_COORDINATOR,
    )
    nurse = User(
        email="nurse@pallia.demo",
        full_name="Meera Nair",
        phone="+91 98765 40002",
        role=UserRole.NURSE,
    )
    nurse2 = User(
        email="nurse2@pallia.demo",
        full_name="Kiran Menon",
        phone="+91 98765 40003",
        role=UserRole.NURSE,
    )
    doctor = User(
        email="doctor@pallia.demo",
        full_name="Dr. Lakshmi Rao",
        phone="+91 98765 40004",
        role=UserRole.DOCTOR,
    )
    caregiver_user = User(
        email="caregiver@pallia.demo",
        full_name="Priya Verma",
        phone="+91 98765 40005",
        role=UserRole.CAREGIVER,
    )
    users = [admin, coordinator, nurse, nurse2, doctor, caregiver_user]
    for u in users:
        u.organization = org
    return org, users


def _patients(org: Organization) -> list[Patient]:
    patients = [
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
    return patients


def _add_bundles(
    db: Session,
    org: Organization,
    coordinator: User,
    nurse: User,
    nurse2: User,
    doctor: User,
    caregiver_user: User,
    patients: list[Patient],
) -> None:

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

        date = _utc(-index).strftime("%d %b")
        content = f"Caregiver updated family behaviours during visit on {date}."
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
                patient_id=patients[2].id,
                type=AlertType.VISIT,
                severity=AlertSeverity.INFO,
                title="Upcoming review visit",
                description="Care plan review scheduled next week.",
                status=AlertStatus.OPEN,
            ),
        ]
    )


def seed(db: Session) -> None:
    existing = db.scalar(select(Organization).where(Organization.name == DEMO_ORG_NAME))
    if existing is not None:
        print(f"Demo organization already seeded ({DEMO_ORG_NAME}); skipping.")
        return

    org, users = _organizations_and_users()
    db.add(org)
    db.flush()

    _admin, coordinator, nurse, nurse2, doctor, caregiver_user = users

    patients = _patients(org)
    db.add_all(patients)
    db.flush()

    _add_bundles(db, org, coordinator, nurse, nurse2, doctor, caregiver_user, patients)
    db.commit()

    print(f"Seeded demo organization '{DEMO_ORG_NAME}' with {len(patients)} patients.")


def main() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
