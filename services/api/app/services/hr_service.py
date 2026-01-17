"""PACK 92: HR Engine - Service"""

from sqlalchemy.orm import Session

from app.models.hr import Employee, PerformanceLog, OnboardingDocument
from app.schemas.hr import EmployeeCreate, PerformanceLogCreate, OnboardingDocumentCreate


# Employee operations
def create_employee(db: Session, employee: EmployeeCreate) -> Employee:
    db_employee = Employee(
        name=employee.name,
        role=employee.role,
        email=employee.email,
        status=employee.status
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def list_employees(db: Session) -> list[Employee]:
    return db.query(Employee).order_by(Employee.id.desc()).all()


def get_employee(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def update_employee(db: Session, employee_id: int, employee: EmployeeCreate) -> Employee | None:
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None
    db_employee.name = employee.name
    db_employee.role = employee.role
    db_employee.email = employee.email
    db_employee.status = employee.status
    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, employee_id: int) -> bool:
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return False
    db.delete(db_employee)
    db.commit()
    return True


# Performance log operations
def create_performance_log(db: Session, perf: PerformanceLogCreate) -> PerformanceLog:
    db_perf = PerformanceLog(
        employee_id=perf.employee_id,
        score=perf.score,
        notes=perf.notes
    )
    db.add(db_perf)
    db.commit()
    db.refresh(db_perf)
    return db_perf


def list_performance_logs(db: Session, employee_id: int | None = None) -> list[PerformanceLog]:
    q = db.query(PerformanceLog)
    if employee_id:
        q = q.filter(PerformanceLog.employee_id == employee_id)
    return q.order_by(PerformanceLog.id.desc()).all()


def get_performance_log(db: Session, log_id: int) -> PerformanceLog | None:
    return db.query(PerformanceLog).filter(PerformanceLog.id == log_id).first()


def delete_performance_log(db: Session, log_id: int) -> bool:
    db_perf = get_performance_log(db, log_id)
    if not db_perf:
        return False
    db.delete(db_perf)
    db.commit()
    return True


# Onboarding document operations
def create_onboarding_document(db: Session, doc: OnboardingDocumentCreate) -> OnboardingDocument:
    db_doc = OnboardingDocument(
        employee_id=doc.employee_id,
        doc_type=doc.doc_type,
        doc_payload=doc.doc_payload
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


def list_onboarding_documents(db: Session, employee_id: int | None = None) -> list[OnboardingDocument]:
    q = db.query(OnboardingDocument)
    if employee_id:
        q = q.filter(OnboardingDocument.employee_id == employee_id)
    return q.order_by(OnboardingDocument.id.desc()).all()


def get_onboarding_document(db: Session, doc_id: int) -> OnboardingDocument | None:
    return db.query(OnboardingDocument).filter(OnboardingDocument.id == doc_id).first()


def delete_onboarding_document(db: Session, doc_id: int) -> bool:
    db_doc = get_onboarding_document(db, doc_id)
    if not db_doc:
        return False
    db.delete(db_doc)
    db.commit()
    return True
