from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/family_payroll", tags=["core-family-payroll"])

@router.post("/people")
def add_person(name: str, role: str = "child", status: str = "active", notes: str = ""):
    try:
        return service.add_person(name=name, role=role, status=status, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/people")
def list_people(status: str = ""):
    return {"items": service.list_people(status=status)}

@router.post("/entries")
def add_entry(person_id: str, entry_type: str, date: str, amount: float = 0.0, description: str = "", deduction_type: str = "", meal_log: str = ""):
    try:
        return service.add_entry(person_id=person_id, entry_type=entry_type, date=date, amount=amount, description=description, deduction_type=deduction_type, meal_log=meal_log)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/entries")
def list_entries(person_id: str = "", entry_type: str = "", date_from: str = "", date_to: str = ""):
    return {"items": service.list_entries(person_id=person_id, entry_type=entry_type, date_from=date_from, date_to=date_to)}

@router.get("/cra_warnings")
def cra_warnings(person_id: str = "", year: int = 0):
    return service.cra_warnings_stub(person_id=person_id, year=year)
