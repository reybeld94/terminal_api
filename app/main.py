import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import pymssql
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import require_jwt
from .database import get_db_connection
from .schemas import (
    ClockInRequest,
    ClockInResponse,
    ClockOutRequest,
    ClockOutResponse,
)


logger = logging.getLogger("terminal_api")
logging.basicConfig(level=logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        log_payload: Dict[str, Any] = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "request_id": request_id,
        }
        logger.info(json.dumps(log_payload))
        response.headers["X-Request-ID"] = request_id
        return response


def get_connection_dependency():
    with get_db_connection() as connection:
        yield connection


def create_app() -> FastAPI:
    application = FastAPI(title="MIE Trak Terminal API", version="1.0.0")
    application.add_middleware(RequestLoggingMiddleware)

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(  # type: ignore
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": "INVALID_PAYLOAD", "errors": exc.errors()},
        )

    @application.post("/clock-in", response_model=ClockInResponse)
    async def clock_in(
        payload: ClockInRequest,
        _: Dict[str, Any] = Depends(require_jwt),
        connection: pymssql.Connection = Depends(get_connection_dependency),
    ) -> ClockInResponse:
        device_date = payload.deviceDate or datetime.now(timezone.utc)
        if device_date.tzinfo is not None:
            device_date = device_date.astimezone(timezone.utc).replace(tzinfo=None)
        try:
            with connection.cursor(as_dict=True) as cursor:
                cursor.callproc(
                    "dbo.usp_mie_api_ClockInWorkOrderAssembly",
                    (
                        payload.workOrderAssemblyId,
                        payload.userId,
                        payload.divisionFK,
                        device_date,
                    ),
                )
                status = _read_status(cursor)

                work_order_collection_id = _resolve_work_order_collection_id(
                    cursor, payload.workOrderAssemblyId, payload.userId
                )
            connection.commit()
        except pymssql.Error as exc:  # pragma: no cover - requires DB failure
            logger.exception("clock_in_db_error")
            raise HTTPException(status_code=500, detail="DB_ERROR") from exc

        return ClockInResponse(status=status, workOrderCollectionId=work_order_collection_id)

    @application.post("/clock-out", response_model=ClockOutResponse)
    async def clock_out(
        payload: ClockOutRequest,
        _: Dict[str, Any] = Depends(require_jwt),
        connection: pymssql.Connection = Depends(get_connection_dependency),
    ) -> ClockOutResponse:
        device_time_value: Optional[str]
        if payload.deviceTime is not None:
            device_time = payload.deviceTime
            if device_time.tzinfo is None:
                device_time = device_time.replace(tzinfo=timezone.utc)
            else:
                device_time = device_time.astimezone(timezone.utc)
            device_time_value = device_time.isoformat()
        else:
            device_time_value = None

        try:
            with connection.cursor(as_dict=True) as cursor:
                cursor.callproc(
                    "dbo.usp_mie_api_ClockOutWorkOrderCollection",
                    (
                        payload.workOrderCollectionId,
                        float(payload.quantity),
                        float(payload.quantityScrapped),
                        payload.scrapReasonPK,
                        int(payload.complete),
                        payload.comment,
                        device_time_value,
                        payload.divisionFK,
                    ),
                )
                status = _read_status(cursor)
            connection.commit()
        except pymssql.Error as exc:  # pragma: no cover - requires DB failure
            logger.exception("clock_out_db_error")
            raise HTTPException(status_code=500, detail="DB_ERROR") from exc

        return ClockOutResponse(status=status)

    return application


def _read_status(cursor: pymssql.Cursor) -> str:
    status: Optional[str] = None
    row = cursor.fetchone()
    if row and "Status" in row:
        status = row["Status"]

    while cursor.nextset():
        next_row = cursor.fetchone()
        if next_row and "Status" in next_row:
            status = next_row["Status"]

    return status or "UNKNOWN"


def _resolve_work_order_collection_id(
    cursor: pymssql.Cursor, work_order_assembly_id: int, user_id: int
) -> Optional[int]:
    cursor.nextset()
    cursor.execute(
        """
        SELECT TOP 1 woc.WorkOrderCollectionPK
        FROM WorkOrderCollection AS woc
        INNER JOIN WorkOrderAssembly AS wa ON woc.WorkOrderAssemblyFK = wa.WorkOrderAssemblyPK
        WHERE woc.EmployeeFK = %s AND wa.WorkOrderAssemblyPK = %s
        ORDER BY woc.WorkOrderCollectionPK DESC
        """,
        (user_id, work_order_assembly_id),
    )
    row = cursor.fetchone()
    return row["WorkOrderCollectionPK"] if row else None


app = create_app()
