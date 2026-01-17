"""
PACK AB: Education Engine Router
Prefix: /education
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.education_engine import (
    CourseCreate,
    CourseUpdate,
    CourseOut,
    LessonCreate,
    LessonOut,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentOut,
)
from app.services.education_engine import (
    create_course,
    update_course,
    list_courses,
    get_course,
    create_lesson,
    list_lessons_for_course,
    enroll,
    update_enrollment,
    list_enrollments_for_learner,
)

router = APIRouter(prefix="/education", tags=["Education"])


@router.post("/courses", response_model=CourseOut)
def create_course_endpoint(
    payload: CourseCreate,
    db: Session = Depends(get_db),
):
    """Create a new course."""
    return create_course(db, payload)


@router.get("/courses", response_model=List[CourseOut])
def list_courses_endpoint(
    subject: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List courses with optional filtering by subject."""
    return list_courses(db, subject=subject)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific course by ID."""
    obj = get_course(db, course_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    return obj


@router.patch("/courses/{course_id}", response_model=CourseOut)
def update_course_endpoint(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
):
    """Update a course."""
    obj = update_course(db, course_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Course not found")
    return obj


@router.post("/lessons", response_model=LessonOut)
def create_lesson_endpoint(
    payload: LessonCreate,
    db: Session = Depends(get_db),
):
    """Create a new lesson in a course."""
    return create_lesson(db, payload)


@router.get("/courses/{course_id}/lessons", response_model=List[LessonOut])
def list_lessons_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
):
    """List all lessons in a course (ordered by index)."""
    return list_lessons_for_course(db, course_id)


@router.post("/enrollments", response_model=EnrollmentOut)
def enroll_endpoint(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
):
    """Enroll a learner in a course."""
    return enroll(db, payload)


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentOut)
def update_enrollment_endpoint(
    enrollment_id: int,
    payload: EnrollmentUpdate,
    db: Session = Depends(get_db),
):
    """Update enrollment (progress, status)."""
    obj = update_enrollment(db, enrollment_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return obj


@router.get("/enrollments/by-learner/{learner_id}", response_model=List[EnrollmentOut])
def list_enrollments_for_learner_endpoint(
    learner_id: int,
    db: Session = Depends(get_db),
):
    """List all course enrollments for a specific learner."""
    return list_enrollments_for_learner(db, learner_id)
