import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.connection import engine, SessionLocal
from app.database.base import Base
import app.models # Ensure all models are loaded

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.categories import router as categories_router
from app.api.v1.grievances import router as grievances_router
from app.api.v1.comments import router as comments_router
from app.api.v1.attachments import router as attachments_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ai import router as ai_router
from app.api.v1.organizational_units import router as organizational_units_router
from app.api.v1.aicte_cases import router as aicte_cases_router
from app.api.v1.aicte_overlaps import router as aicte_overlaps_router
from app.api.v1.aicte_transfers import router as aicte_transfers_router
from app.api.v1.aicte_analytics import router as aicte_analytics_router
from app.services.scheduler import sla_scheduler
import time
from collections import defaultdict

setup_logging()
logger = logging.getLogger("eduresolve.main")

# Sliding window rate limiter state: {key: [timestamp1, timestamp2, ...]}
_rate_limits = defaultdict(list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing EduResolve AI application...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Check MySQL connectivity on startup (safe, non-destructive, never drops database)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            "MySQL database connection verified: %s on %s:%s",
            settings.MYSQL_DATABASE,
            settings.MYSQL_HOST,
            settings.MYSQL_PORT
        )
    except Exception as e:
        logger.warning(
            "MySQL database is currently unreachable on %s:%s. Ensure XAMPP MySQL service is running. Error: %s",
            settings.MYSQL_HOST,
            settings.MYSQL_PORT,
            str(e)
        )

    # Start background SLA scheduler
    sla_scheduler.start()
        
    yield
    # Shutdown tasks
    logger.info("Shutting down EduResolve AI application...")
    sla_scheduler.stop()
    logger.info("EduResolve AI application stopped cleanly.")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Centralized Student Grievance Redressal and Monitoring Platform",
    version="1.0.0",
    docs_url="/docs" if (settings.DEBUG or settings.APP_ENV == "development") else None,
    redoc_url="/redoc" if (settings.DEBUG or settings.APP_ENV == "development") else None,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers and Request Safeguards Middleware
@app.middleware("http")
async def security_safeguards_middleware(request: Request, call_next):
    # 1. Request payload size limit check
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length_bytes = int(content_length)
            max_bytes = settings.MAX_CONTENT_LENGTH_MB * 1024 * 1024
            if length_bytes > max_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request payload exceeds maximum allowed limit of {settings.MAX_CONTENT_LENGTH_MB}MB."}
                )
        except ValueError:
            pass

    # 2. Rate limiting check for sensitive endpoints
    if settings.RATE_LIMIT_ENABLED:
        client_ip = request.client.host if request.client else "unknown"
        # In automated test suite, only enforce when explicitly testing rate limit via X-Test-Rate-Limit header
        should_check_rate_limit = (client_ip != "testclient") or (request.headers.get("X-Test-Rate-Limit") == "true")

        if should_check_rate_limit:
            path = request.url.path
            now = time.time()
            window_seconds = 60

            rate_limit_map = {
                f"{settings.API_V1_PREFIX}/auth/login": settings.RATE_LIMIT_LOGIN_MAX_REQUESTS,
                f"{settings.API_V1_PREFIX}/auth/register": settings.RATE_LIMIT_REGISTER_MAX_REQUESTS,
                f"{settings.API_V1_PREFIX}/auth/resend-verification": settings.RATE_LIMIT_VERIFY_RESEND_MAX_REQUESTS
            }

            if path in rate_limit_map and request.method == "POST":
                max_allowed = rate_limit_map[path]
                key = f"{client_ip}:{path}"
                # Prune timestamps older than window
                _rate_limits[key] = [t for t in _rate_limits[key] if now - t < window_seconds]
                if len(_rate_limits[key]) >= max_allowed:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests. Please wait a moment before trying again."}
                    )
                _rate_limits[key].append(now)

    response = await call_next(request)

    # 3. Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response

# Global Safe Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later or contact support."}
    )


# Root Endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "online",
        "docs": "/docs" if (settings.DEBUG or settings.APP_ENV == "development") else None,
        "health": "/api/health"
    }

# Health Checks
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }

@app.get("/api/health/db", tags=["Health"])
def db_health_check():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "database": "healthy",
            "driver": "mysql+pymysql",
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "database_name": settings.MYSQL_DATABASE
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "disconnected",
                "database": "unhealthy",
                "detail": "Database is unreachable. Please verify that MySQL service is running in XAMPP."
            }
        )

# Register v1 API Routers
v1_prefix = settings.API_V1_PREFIX
app.add_api_route(f"{v1_prefix}/health", health_check, methods=["GET"], tags=["Health"])
app.add_api_route(f"{v1_prefix}/health/db", db_health_check, methods=["GET"], tags=["Health"])

app.include_router(auth_router, prefix=v1_prefix)
app.include_router(users_router, prefix=v1_prefix)
app.include_router(institutions_router, prefix=v1_prefix)
app.include_router(categories_router, prefix=v1_prefix)
app.include_router(grievances_router, prefix=v1_prefix)
app.include_router(comments_router, prefix=v1_prefix)
app.include_router(attachments_router, prefix=v1_prefix)
app.include_router(feedback_router, prefix=v1_prefix)
app.include_router(notifications_router, prefix=v1_prefix)
app.include_router(analytics_router, prefix=v1_prefix)
app.include_router(ai_router, prefix=v1_prefix)
app.include_router(organizational_units_router, prefix=v1_prefix)
app.include_router(aicte_cases_router, prefix=v1_prefix)
app.include_router(aicte_overlaps_router, prefix=v1_prefix)
app.include_router(aicte_transfers_router, prefix=v1_prefix)
app.include_router(aicte_analytics_router, prefix=v1_prefix)

from app.models.enums import UserRoleEnum
from app.models.user import User
from app.core.permissions import require_roles
from app.database.connection import get_db
from sqlalchemy.orm import Session

# System and Scheduler Status Endpoints
@app.get(f"{v1_prefix}/system/scheduler-status", tags=["System"])
def get_scheduler_status(current_user: User = Depends(require_roles([UserRoleEnum.SUPER_ADMIN]))):
    """Return background SLA scheduler operational telemetry."""
    return sla_scheduler.telemetry

@app.post(f"{v1_prefix}/system/scheduler-run", tags=["System"])
def trigger_scheduler_run(
    current_user: User = Depends(require_roles([UserRoleEnum.SUPER_ADMIN])),
    db: Session = Depends(get_db)
):
    """Synchronously execute an SLA monitoring and outbox dispatch cycle."""
    result = sla_scheduler.run_cycle_sync(db)
    return {"status": "SUCCESS", "result": result, "telemetry": sla_scheduler.telemetry}

