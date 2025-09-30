"""FastAPI application entry point."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .routers import clock

_logger = logging.getLogger("terminal_api")
if not _logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
_logger.setLevel(logging.INFO)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request_id to each incoming request and log request details."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id

        log_payload = {
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time": process_time,
        }
        _logger.info(json.dumps(log_payload))

        return response


def create_app() -> FastAPI:
    """Application factory."""

    application = FastAPI()
    application.add_middleware(RequestIdMiddleware)
    application.include_router(clock.router)
    return application


app = create_app()
