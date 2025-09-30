"""Clock related endpoints router."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
import logging
from typing import Optional

import pymssql
from fastapi import APIRouter, Depends, HTTPException, status

from ..db import get_conn
from ..schemas import (
    ClockInRequest,
    ClockInResponse,
    ClockOutRequest,
    ClockOutResponse,
)
from ..security import require_bearer

_logger = logging.getLogger(__name__)


router = APIRouter(prefix="", tags=["clock"], dependencies=[Depends(require_bearer)])


def _extract_status(row: Optional[dict[str, object]]) -> str:
    """Return the status string from a stored procedure SELECT row."""

    if not row:
        return ""
    # Stored procedures return `Status` (capitalized); fall back to lower case if needed.
    return str(row.get("Status") or row.get("status") or "")


@router.post("/clock-in", response_model=ClockInResponse)
def clock_in(payload: ClockInRequest) -> ClockInResponse:
    """Execute the clock-in stored procedure and return the status."""

    device_date = payload.device_date or datetime.utcnow()

    try:
        with closing(get_conn()) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.callproc(
                    "dbo.usp_mie_api_ClockInWorkOrderAssembly",
                    (
                        payload.work_order_assembly_id,
                        payload.user_id,
                        payload.division_fk,
                        device_date,
                    ),
                )
                sp_status = _extract_status(cursor.fetchone())
                # Ensure all result sets are consumed before the next query.
                while cursor.nextset():
                    pass

                cursor.execute(
                    """
                    SELECT TOP 1 WorkOrderCollectionPK
                    FROM WorkOrderCollection
                    WHERE EmployeeFK = %s AND WorkOrderAssemblyNumber = %s
                    ORDER BY WorkOrderCollectionPK DESC
                    """,
                    (payload.user_id, payload.work_order_assembly_id),
                )
                work_order_row = cursor.fetchone()
                work_order_collection_id = (
                    work_order_row.get("WorkOrderCollectionPK") if work_order_row else None
                )

                conn.commit()
    except pymssql.Error as exc:  # pragma: no cover - requires live DB
        _logger.exception("Database error during clock-in")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB_ERROR",
        ) from exc

    return ClockInResponse(
        status=sp_status, work_order_collection_id=work_order_collection_id
    )


@router.post("/clock-out", response_model=ClockOutResponse)
def clock_out(payload: ClockOutRequest) -> ClockOutResponse:
    """Execute the clock-out stored procedure and return the status."""

    device_time_str = (payload.device_time or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")

    try:
        with closing(get_conn()) as conn:
            with conn.cursor(as_dict=True) as cursor:
                cursor.callproc(
                    "dbo.usp_mie_api_ClockOutWorkOrderCollection",
                    (
                        payload.work_order_collection_id,
                        payload.quantity,
                        payload.quantity_scrapped,
                        payload.scrap_reason_pk,
                        int(payload.complete),
                        payload.comment,
                        device_time_str,
                        payload.division_fk,
                    ),
                )
                sp_status = _extract_status(cursor.fetchone())
                while cursor.nextset():
                    pass

                conn.commit()
    except pymssql.Error as exc:  # pragma: no cover - requires live DB
        _logger.exception("Database error during clock-out")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB_ERROR",
        ) from exc

    return ClockOutResponse(status=sp_status)
