"""FastAPI application entry point."""

from __future__ import annotations

import json
import os
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .routers import clock
from .security import issue_token


def _now_iso() -> str:
    """Return the current UTC time formatted in ISO 8601."""

    return datetime.now(tz=timezone.utc).isoformat()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request_id to each incoming request and log request details."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:  # pragma: no cover - defensive guard
            response = JSONResponse(
                {"detail": "Internal Server Error"}, status_code=500
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            log_payload = {
                "time": _now_iso(),
                "level": "ERROR",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "error": traceback.format_exc(limit=3).strip(),
            }
            print(json.dumps(log_payload), flush=True)
            response.headers["X-Request-ID"] = request_id
            return response

        latency_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id

        log_payload = {
            "time": _now_iso(),
            "level": "INFO",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        print(json.dumps(log_payload), flush=True)

        return response


def create_app() -> FastAPI:
    """Application factory."""

    application = FastAPI()
    application.add_middleware(RequestIdMiddleware)
    application.include_router(clock.router)

    if os.getenv("ENV") == "dev":

        @application.get("/dev/token")
        def dev_token() -> dict[str, str]:
            """Return a short-lived development token."""

            return {"token": issue_token("dev-user")}

    return application


app = create_app()
