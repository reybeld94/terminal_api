from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ClockInRequest(BaseModel):
    workOrderAssemblyId: int = Field(..., ge=1)
    userId: int = Field(..., ge=1)
    divisionFK: int = Field(..., ge=1)
    deviceDate: Optional[datetime] = None


class ClockInResponse(BaseModel):
    status: str
    workOrderCollectionId: Optional[int] = None


class ClockOutRequest(BaseModel):
    workOrderCollectionId: int = Field(..., ge=1)
    quantity: Decimal
    quantityScrapped: Decimal
    scrapReasonPK: int = Field(..., ge=0)
    complete: bool
    comment: Optional[str] = None
    deviceTime: Optional[datetime] = None
    divisionFK: int = Field(..., ge=1)


class ClockOutResponse(BaseModel):
    status: str
