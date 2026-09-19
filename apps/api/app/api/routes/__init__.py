from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    health,
    observations,
    organizations,
    patients,
    tasks,
    users,
    visits,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(users.router)
api_router.include_router(patients.router)
api_router.include_router(observations.router)
api_router.include_router(visits.router)
api_router.include_router(tasks.router)
api_router.include_router(dashboard.router)


def get_router() -> APIRouter:
    return api_router
