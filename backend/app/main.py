import logging
from contextlib import asynccontextmanager

from app.api.routes import calendar, evaluation, health, history, plans, tasks
from app.api.routes import settings as settings_routes
from app.core.config import settings
from app.db.init_db import init_db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aura")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AURA Backend Engine (Environment: %s)...", settings.ENVIRONMENT)
    await init_db()
    logger.info("AURA Database & Services ready.")
    yield
    logger.info("AURA Backend Engine shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Adaptive Utility-Aware AI Assistant for Real-Time Task Planning and Execution",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Safe diagnostic logged without exposing secrets."},
    )

# Include API Routers under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(calendar.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(settings_routes.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")

# Also include health check at root /api/health and /health
app.include_router(health.router, prefix="/api")
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "name": "AURA API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
