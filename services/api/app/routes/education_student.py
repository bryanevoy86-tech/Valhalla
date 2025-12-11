"""PACK 78: Education SaaS - Student Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.education_student import StudentOut, StudentCreate, ParentAccountOut, ParentAccountCreate
from app.services.education_student_service import (
    create_student, list_students_by_classroom, get_student, update_student, delete_student,
    create_parent_account, list_parent_accounts_by_student, get_parent_account, update_parent_account, delete_parent_account
)

router = APIRouter(prefix="/education/student", tags=["education_student"])


# Student endpoints
@router.post("/student", response_model=StudentOut)
def post_student(student: StudentCreate, db: Session = Depends(get_db)):
    return create_student(db, student)


@router.get("/students/{classroom_id}", response_model=list[StudentOut])
def get_students(classroom_id: int, db: Session = Depends(get_db)):
    return list_students_by_classroom(db, classroom_id)


@router.get("/student/{student_id}", response_model=StudentOut)
def get_student_endpoint(student_id: int, db: Session = Depends(get_db)):
    return get_student(db, student_id)


@router.put("/student/{student_id}", response_model=StudentOut)
def put_student(student_id: int, student: StudentCreate, db: Session = Depends(get_db)):
    return update_student(db, student_id, student)


@router.delete("/student/{student_id}")
def delete_student_endpoint(student_id: int, db: Session = Depends(get_db)):
    return delete_student(db, student_id)


# Parent account endpoints
@router.post("/parent", response_model=ParentAccountOut)
def post_parent_account(parent: ParentAccountCreate, db: Session = Depends(get_db)):
    return create_parent_account(db, parent)


@router.get("/parents/{student_id}", response_model=list[ParentAccountOut])
def get_parent_accounts(student_id: int, db: Session = Depends(get_db)):
    return list_parent_accounts_by_student(db, student_id)


@router.get("/parent/{parent_id}", response_model=ParentAccountOut)
def get_parent_account_endpoint(parent_id: int, db: Session = Depends(get_db)):
    return get_parent_account(db, parent_id)


@router.put("/parent/{parent_id}", response_model=ParentAccountOut)
def put_parent_account(parent_id: int, parent: ParentAccountCreate, db: Session = Depends(get_db)):
    return update_parent_account(db, parent_id, parent)


@router.delete("/parent/{parent_id}")
def delete_parent_account_endpoint(parent_id: int, db: Session = Depends(get_db)):
    return delete_parent_account(db, parent_id)
