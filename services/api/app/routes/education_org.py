"""PACK 77: Education SaaS - Org Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.education_org import SchoolOut, SchoolCreate, ClassroomOut, ClassroomCreate, TeacherOut, TeacherCreate
from app.services.education_org_service import (
    create_school, list_schools, get_school, update_school, delete_school,
    create_classroom, list_classrooms_by_school, get_classroom, update_classroom, delete_classroom,
    create_teacher, list_teachers_by_school, get_teacher, update_teacher, delete_teacher
)

router = APIRouter(prefix="/education/org", tags=["education_org"])


# School endpoints
@router.post("/school", response_model=SchoolOut)
def post_school(school: SchoolCreate, db: Session = Depends(get_db)):
    return create_school(db, school)


@router.get("/schools", response_model=list[SchoolOut])
def get_schools(db: Session = Depends(get_db)):
    return list_schools(db)


@router.get("/school/{school_id}", response_model=SchoolOut)
def get_school_endpoint(school_id: int, db: Session = Depends(get_db)):
    return get_school(db, school_id)


@router.put("/school/{school_id}", response_model=SchoolOut)
def put_school(school_id: int, school: SchoolCreate, db: Session = Depends(get_db)):
    return update_school(db, school_id, school)


@router.delete("/school/{school_id}")
def delete_school_endpoint(school_id: int, db: Session = Depends(get_db)):
    return delete_school(db, school_id)


# Classroom endpoints
@router.post("/classroom", response_model=ClassroomOut)
def post_classroom(classroom: ClassroomCreate, db: Session = Depends(get_db)):
    return create_classroom(db, classroom)


@router.get("/classrooms/{school_id}", response_model=list[ClassroomOut])
def get_classrooms(school_id: int, db: Session = Depends(get_db)):
    return list_classrooms_by_school(db, school_id)


@router.get("/classroom/{classroom_id}", response_model=ClassroomOut)
def get_classroom_endpoint(classroom_id: int, db: Session = Depends(get_db)):
    return get_classroom(db, classroom_id)


@router.put("/classroom/{classroom_id}", response_model=ClassroomOut)
def put_classroom(classroom_id: int, classroom: ClassroomCreate, db: Session = Depends(get_db)):
    return update_classroom(db, classroom_id, classroom)


@router.delete("/classroom/{classroom_id}")
def delete_classroom_endpoint(classroom_id: int, db: Session = Depends(get_db)):
    return delete_classroom(db, classroom_id)


# Teacher endpoints
@router.post("/teacher", response_model=TeacherOut)
def post_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    return create_teacher(db, teacher)


@router.get("/teachers/{school_id}", response_model=list[TeacherOut])
def get_teachers(school_id: int, db: Session = Depends(get_db)):
    return list_teachers_by_school(db, school_id)


@router.get("/teacher/{teacher_id}", response_model=TeacherOut)
def get_teacher_endpoint(teacher_id: int, db: Session = Depends(get_db)):
    return get_teacher(db, teacher_id)


@router.put("/teacher/{teacher_id}", response_model=TeacherOut)
def put_teacher(teacher_id: int, teacher: TeacherCreate, db: Session = Depends(get_db)):
    return update_teacher(db, teacher_id, teacher)


@router.delete("/teacher/{teacher_id}")
def delete_teacher_endpoint(teacher_id: int, db: Session = Depends(get_db)):
    return delete_teacher(db, teacher_id)
