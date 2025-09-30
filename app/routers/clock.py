"""Clock related endpoints router (currently empty)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..security import require_bearer

router = APIRouter(prefix="", tags=["clock"], dependencies=[Depends(require_bearer)])
