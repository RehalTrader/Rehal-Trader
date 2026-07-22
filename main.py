import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router, ws_router
from app.cache.redis_client import redis_client
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up trading signal API...")
    if not await redis_client.ping():
        logger.warning("Redis is not reachable at startup — cache features degraded.")
    yield
    logger.info("Shutting down trading signal API...")


app = FastAPI(
    title="AI Trading Signal Platform API",
    version="1.0.0",
    description="REST + WebSocket API serving AI-generated trading signals.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    # In production, restrict this to settings.FRONTEND_URL rather than "*".
    allow_origins=["*"] if not settings.is_production else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["system"])
async def health_check():
    redis_ok = await redis_client.ping()
    return {"status": "ok", "redis": redis_ok}


app.include_router(api_router)
app.include_router(ws_router)
