"""PACK 92: HR Engine - Routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.hr import EmployeeCreate, EmployeeOut, PerformanceLogCreate, PerformanceLogOut, OnboardingDocumentCreate, OnboardingDocumentOut
from app.services import hr_service

router = APIRouter(
    prefix="/hr",
    tags=["hr"]
)


# Employee endpoints
@router.post("/employee", response_model=EmployeeOut)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    return hr_service.create_employee(db, employee)


@router.get("/employee/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return hr_service.get_employee(db, employee_id)


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return hr_service.list_employees(db)


@router.put("/employee/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, employee: EmployeeCreate, db: Session = Depends(get_db)):
    return hr_service.update_employee(db, employee_id, employee)


@router.delete("/employee/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    success = hr_service.delete_employee(db, employee_id)
    return {"deleted": success}


# Performance log endpoints
@router.post("/performance", response_model=PerformanceLogOut)
def create_performance(perf: PerformanceLogCreate, db: Session = Depends(get_db)):
    return hr_service.create_performance_log(db, perf)


@router.get("/performance/{log_id}", response_model=PerformanceLogOut)
def get_performance(log_id: int, db: Session = Depends(get_db)):
    return hr_service.get_performance_log(db, log_id)


@router.get("/performance", response_model=list[PerformanceLogOut])
def list_performance(employee_id: int | None = None, db: Session = Depends(get_db)):
    return hr_service.list_performance_logs(db, employee_id)


@router.delete("/performance/{log_id}")
def delete_performance(log_id: int, db: Session = Depends(get_db)):
    success = hr_service.delete_performance_log(db, log_id)
    return {"deleted": success}


# Onboarding document endpoints
@router.post("/document", response_model=OnboardingDocumentOut)
def create_document(doc: OnboardingDocumentCreate, db: Session = Depends(get_db)):
    return hr_service.create_onboarding_document(db, doc)


@router.get("/document/{doc_id}", response_model=OnboardingDocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return hr_service.get_onboarding_document(db, doc_id)


@router.get("/documents", response_model=list[OnboardingDocumentOut])
def list_documents(employee_id: int | None = None, db: Session = Depends(get_db)):
    return hr_service.list_onboarding_documents(db, employee_id)


@router.delete("/document/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    success = hr_service.delete_onboarding_document(db, doc_id)
    return {"deleted": success}
