from fastapi import APIRouter
from pydantic import BaseModel

from financial_platform import __version__
from financial_platform.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """GET /health - Returns operational status of the service."""
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.APP_ENV,
    )
