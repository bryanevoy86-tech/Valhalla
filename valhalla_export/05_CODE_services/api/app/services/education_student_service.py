"""PACK 78: Education SaaS - Student Service"""

from sqlalchemy.orm import Session

from app.models.education_student import Student, ParentAccount
from app.schemas.education_student import StudentCreate, ParentAccountCreate


# Student operations
def create_student(db: Session, student: StudentCreate) -> Student:
    db_student = Student(
        classroom_id=student.classroom_id,
        name=student.name,
        age=student.age,
        notes=student.notes
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def list_students_by_classroom(db: Session, classroom_id: int) -> list[Student]:
    return db.query(Student).filter(Student.classroom_id == classroom_id).all()


def get_student(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()


def update_student(db: Session, student_id: int, student: StudentCreate) -> Student | None:
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    db_student.classroom_id = student.classroom_id
    db_student.name = student.name
    db_student.age = student.age
    db_student.notes = student.notes
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: int) -> bool:
    db_student = get_student(db, student_id)
    if not db_student:
        return False
    db.delete(db_student)
    db.commit()
    return True


# Parent account operations
def create_parent_account(db: Session, parent: ParentAccountCreate) -> ParentAccount:
    db_parent = ParentAccount(
        student_id=parent.student_id,
        parent_name=parent.parent_name,
        contact_email=parent.contact_email
    )
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    return db_parent


def list_parent_accounts_by_student(db: Session, student_id: int) -> list[ParentAccount]:
    return db.query(ParentAccount).filter(ParentAccount.student_id == student_id).all()


def get_parent_account(db: Session, parent_id: int) -> ParentAccount | None:
    return db.query(ParentAccount).filter(ParentAccount.id == parent_id).first()


def update_parent_account(db: Session, parent_id: int, parent: ParentAccountCreate) -> ParentAccount | None:
    db_parent = get_parent_account(db, parent_id)
    if not db_parent:
        return None
    db_parent.student_id = parent.student_id
    db_parent.parent_name = parent.parent_name
    db_parent.contact_email = parent.contact_email
    db.commit()
    db.refresh(db_parent)
    return db_parent


def delete_parent_account(db: Session, parent_id: int) -> bool:
    db_parent = get_parent_account(db, parent_id)
    if not db_parent:
        return False
    db.delete(db_parent)
    db.commit()
    return True
