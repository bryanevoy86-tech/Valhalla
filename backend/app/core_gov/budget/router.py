from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import BucketCreate, BucketListResponse, MonthSnapshotResponse
from . import service
from . import calendar as cal_service

router = APIRouter(prefix="/core/budget", tags=["core-budget"])


@router.post("/buckets")
def create_bucket(payload: BucketCreate):
    try:
        return service.create_bucket(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/buckets", response_model=BucketListResponse)
def list_buckets(status: Optional[str] = None, bucket_type: Optional[str] = None):
    return {"items": service.list_buckets(status=status, bucket_type=bucket_type)}


@router.get("/buckets/{bucket_id}")
def get_bucket(bucket_id: str):
    b = service.get_bucket(bucket_id)
    if not b:
        raise HTTPException(status_code=404, detail="bucket not found")
    return b


@router.patch("/buckets/{bucket_id}")
def patch_bucket(bucket_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_bucket(bucket_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="bucket not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/months/{month}/allocate/{bucket_id}")
def allocate(month: str, bucket_id: str, allocated: float):
    try:
        return service.set_allocation(month=month, bucket_id=bucket_id, allocated=allocated)
    except KeyError:
        raise HTTPException(status_code=404, detail="bucket not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/months", response_model=MonthSnapshotResponse)
def month(month: Optional[str] = None):
    try:
        return {"items": service.get_month(month=month)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bill_calendar")
def bill_calendar(start: str, end: str):
    return cal_service.bill_calendar(start, end)


@router.get("/bill_calendar_next_30")
def bill_calendar_next_30():
    return cal_service.next_30_days_calendar()

