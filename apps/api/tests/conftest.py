"""Test fixtures.

Tests run against an in-memory SQLite database so they work anywhere without
a running PostgreSQL. Models only use portable types; migration correctness
is exercised separately against PostgreSQL (docker compose).

The database is seeded with two organizations:

  * Org A ("Alpha Care")  - admin user + a patient
  * Org B ("Beta Care")   - a nurse user (different tenant)

This is enough to exercise health, CRUD, organization isolation and
permission checks.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import (
    Organization,
    OrganizationStatus,
    OrganizationType,
    Patient,
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


@pytest.fixture(scope="session")
def tenants(db: Session) -> dict[str, dict]:
    """Creates two organizations with one user each and one patient in Org A."""

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

    admin_a = User(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        email="admin@alpha.pallia.dev",
        full_name="Alpha Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    nurse_b = User(
        id=uuid.uuid4(),
        organization_id=org_b.id,
        email="nurse@beta.pallia.dev",
        full_name="Beta Nurse",
        role=UserRole.NURSE,
        status=UserStatus.ACTIVE,
    )
    patient_role = User(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        email="patient@alpha.pallia.dev",
        full_name="A Patient",
        role=UserRole.PATIENT,
        status=UserStatus.ACTIVE,
    )
    db.add_all([admin_a, nurse_b, patient_role])
    db.flush()

    patient = Patient(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        full_name="Test Patient One",
        status=PatientStatus.ACTIVE,
    )
    db.add(patient)
    db.commit()

    return {
        "org_a": {"id": str(org_a.id), "id_raw": org_a.id},
        "org_b": {"id": str(org_b.id), "id_raw": org_b.id},
        "admin_a": {"user": admin_a, "id": str(admin_a.id)},
        "nurse_b": {"user": nurse_b, "id": str(nurse_b.id)},
        "patient_role": {"user": patient_role, "id": str(patient_role.id)},
        "patient_a": {"user": patient, "id": str(patient.id)},
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
def patient_role_headers(tenants) -> dict[str, str]:
    return auth_headers(token_for(tenants["patient_role"]["user"]))
