import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from financial_platform import __version__
from financial_platform.api.routes import health
from financial_platform.core.config import settings
from financial_platform.core.logging import setup_logging

logger = logging.getLogger("financial_platform.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager initializing logging and system setup."""
    setup_logging(log_level=settings.LOG_LEVEL, app_env=settings.APP_ENV)
    logger.info(f"Starting {settings.APP_NAME} v{__version__} [{settings.APP_ENV}]")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Register routers
    application.include_router(health.router)

    return application


app = create_app()
