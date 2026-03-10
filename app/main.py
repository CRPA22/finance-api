import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import router
from app.config import settings
from app.core.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("main")

app = FastAPI()
app.include_router(router, prefix="/api/v1")

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()
        logger.info(
            "%s %s request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )
        response = await call_next(request)
        duration = time.perf_counter() - start
        logger.info(
            "%s %s request_id=%s status=%s duration=%.2fs",
            request.method,
            request.url.path,
            request_id,
            response.status_code,
            duration,
        )
        return response


app.add_middleware(LoggingMiddleware)

