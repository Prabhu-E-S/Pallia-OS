"""Test fixtures.

Tests run against an in-memory SQLite database so they work anywhere without
a running PostgreSQL. Models only use portable types; migration correctness
is exercised separately against PostgreSQL (docker compose).

The database is seeded with two organizations:

  * Org A ("Alpha Care")  - admin, caregiver, patient accounts + two patients
  * Org B ("Beta Care")   - nurse + caregiver users (different tenant)

This is enough to exercise health, CRUD, authentication, authorization,
organization isolation and permission checks.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Caregiver,
    CaregiverRelationship,
    Organization,
    OrganizationStatus,
    OrganizationType,
    Patient,
    PatientCaregiver,
    PatientStatus,
    User,
    UserRole,
    UserStatus,
)

engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def db() -> Session:
    from contextlib import contextmanager

    @contextmanager
    def _session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    with _session() as session:
        yield session


def _user(
    org_id: uuid.UUID,
    *,
    email: str,
    full_name: str,
    role: UserRole,
    password: str | None = None,
    status: UserStatus = UserStatus.ACTIVE,
    patient_id: uuid.UUID | None = None,
) -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=org_id,
        email=email,
        full_name=full_name,
        role=role,
        status=status,
        password_hash=hash_password(password) if password else None,
        patient_id=patient_id,
    )


@pytest.fixture(scope="session")
def tenants(db: Session) -> dict[str, dict]:
    """Creates two organizations with staff, caregivers and patients."""

    org_a = Organization(
        id=uuid.uuid4(),
        name="Alpha Care",
        type=OrganizationType.HOME_CARE,
        status=OrganizationStatus.ACTIVE,
    )
    org_b = Organization(
        id=uuid.uuid4(),
        name="Beta Care",
        type=OrganizationType.HOSPICE,
        status=OrganizationStatus.ACTIVE,
    )
    db.add_all([org_a, org_b])
    db.flush()

    admin_a = _user(
        org_a.id, email="admin@alpha.pallia.dev", full_name="Alpha Admin", role=UserRole.ADMIN
    )
    nurse_b = _user(
        org_b.id, email="nurse@beta.pallia.dev", full_name="Beta Nurse", role=UserRole.NURSE
    )

    patient_a = Patient(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        full_name="Test Patient One",
        status=PatientStatus.ACTIVE,
    )
    patient_a2 = Patient(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        full_name="Test Patient Two (unlinked)",
        status=PatientStatus.ACTIVE,
    )
    patient_b = Patient(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        full_name="Beta Patient",
        status=PatientStatus.ACTIVE,
    )
    db.add_all([patient_a, patient_a2, patient_b])
    db.flush()

    caregiver_a = _user(
        org_a.id,
        email="caregiver@alpha.pallia.dev",
        full_name="Alpha Caregiver",
        role=UserRole.CAREGIVER,
    )
    caregiver_b = _user(
        org_b.id,
        email="caregiver@beta.pallia.dev",
        full_name="Beta Caregiver",
        role=UserRole.CAREGIVER,
    )
    patient_role = _user(
        org_a.id,
        email="patient@alpha.pallia.dev",
        full_name="A Patient",
        role=UserRole.PATIENT,
        patient_id=patient_a.id,
    )
    db.add_all([admin_a, nurse_b, caregiver_a, caregiver_b, patient_role])
    db.flush()

    caregiver_a_row = Caregiver(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        user_id=caregiver_a.id,
        relationship_type=CaregiverRelationship.FAMILY,
    )
    caregiver_b_row = Caregiver(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        user_id=caregiver_b.id,
        relationship_type=CaregiverRelationship.PROFESSIONAL,
    )
    db.add_all([caregiver_a_row, caregiver_b_row])
    db.flush()
    db.add_all(
        [
            PatientCaregiver(
                patient_id=patient_a.id,
                caregiver_id=caregiver_a_row.id,
                is_primary=True,
            ),
            PatientCaregiver(
                patient_id=patient_b.id,
                caregiver_id=caregiver_b_row.id,
                is_primary=True,
            ),
        ]
    )

    login_users = [
        _user(
            org_a.id,
            email="login@alpha.pallia.dev",
            full_name="Login Admin",
            role=UserRole.ADMIN,
            password="c0rrect-h0rse",
        ),
        _user(
            org_a.id,
            email="inactive@alpha.pallia.dev",
            full_name="Inactive User",
            role=UserRole.NURSE,
            password="c0rrect-h0rse",
            status=UserStatus.INACTIVE,
        ),
        _user(
            org_a.id,
            email="suspended@alpha.pallia.dev",
            full_name="Suspended User",
            role=UserRole.NURSE,
            password="c0rrect-h0rse",
            status=UserStatus.SUSPENDED,
        ),
        _user(
            org_a.id,
            email="ratelimit@alpha.pallia.dev",
            full_name="Rate Limit Target",
            role=UserRole.NURSE,
            password="c0rrect-h0rse",
        ),
    ]
    db.add_all(login_users)
    db.commit()

    return {
        "org_a": {"id": str(org_a.id), "id_raw": org_a.id},
        "org_b": {"id": str(org_b.id), "id_raw": org_b.id},
        "admin_a": {"user": admin_a, "id": str(admin_a.id)},
        "nurse_b": {"user": nurse_b, "id": str(nurse_b.id)},
        "caregiver_a": {"user": caregiver_a, "id": str(caregiver_a.id)},
        "caregiver_b": {"user": caregiver_b, "id": str(caregiver_b.id)},
        "patient_role": {
            "user": patient_role,
            "id": str(patient_role.id),
            "patient_id": str(patient_a.id),
        },
        "patient_a": {"user": patient_a, "id": str(patient_a.id)},
        "patient_a2": {"user": patient_a2, "id": str(patient_a2.id)},
        "patient_b": {"user": patient_b, "id": str(patient_b.id)},
        "login_admin": {"user": login_users[0], "id": str(login_users[0].id)},
        "inactive_user": {"user": login_users[1], "id": str(login_users[1].id)},
        "suspended_user": {"user": login_users[2], "id": str(login_users[2].id)},
        "rate_limit_user": {"user": login_users[3], "id": str(login_users[3].id)},
    }


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def token_for(user: User) -> str:
    return create_access_token(str(user.id))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def alpha_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["admin_a"]["user"]))


@pytest.fixture
def beta_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["nurse_b"]["user"]))


@pytest.fixture
def caregiver_a_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["caregiver_a"]["user"]))


@pytest.fixture
def caregiver_b_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["caregiver_b"]["user"]))


@pytest.fixture
def patient_role_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["patient_role"]["user"]))
