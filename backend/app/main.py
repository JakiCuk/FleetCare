"""FleetCare FastAPI application entrypoint.

Wires up routers (all under ``/api``), CORS, slowapi rate limiting on auth
endpoints, structlog, and consistent ``{"detail": ...}`` error responses.
Importable as ``app.main:app``.
"""

from __future__ import annotations

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401  # register all ORM mappers before any query
from app.config import settings
from app.ratelimit import limiter
from app.routers import (
    auth,
    cars,
    dashboard,
    documents,
    expenses,
    fuel,
    health,
    notifications,
    odometer,
    services,
    settings as settings_router,
    tires,
    users,
)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


_configure_logging()
log = structlog.get_logger("fleetcare")

app = FastAPI(
    title="FleetCare API",
    version=health.VERSION,
    description="Home car-fleet management API (in development).",
)
# slowapi: register the shared limiter + its middleware. The per-route
# @limiter.limit decorators on /api/auth/login and /api/auth/refresh do the work.
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers (uniform {"detail": ...}) ────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422, content={"detail": jsonable_encoder(exc.errors())}
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={"detail": "Rate limit exceeded. Try again later."}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=str(request.url.path), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routers (all under /api) ────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(cars.router, prefix="/api")
app.include_router(odometer.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(tires.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(fuel.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
