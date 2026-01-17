"""
PACK AB: Education Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.education_engine import Course, Lesson, Enrollment
from app.schemas.education_engine import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    EnrollmentCreate,
    EnrollmentUpdate,
)


# Courses

def create_course(db: Session, payload: CourseCreate) -> Course:
    obj = Course(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_course(
    db: Session,
    course_id: int,
    payload: CourseUpdate,
) -> Optional[Course]:
    obj = db.query(Course).filter(Course.id == course_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_courses(db: Session, subject: Optional[str] = None) -> List[Course]:
    q = db.query(Course).filter(Course.is_active.is_(True))
    if subject:
        q = q.filter(Course.subject == subject)
    return q.order_by(Course.created_at.desc()).all()


def get_course(db: Session, course_id: int) -> Optional[Course]:
    return db.query(Course).filter(Course.id == course_id).first()


# Lessons

def create_lesson(db: Session, payload: LessonCreate) -> Lesson:
    obj = Lesson(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_lessons_for_course(db: Session, course_id: int) -> List[Lesson]:
    return (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.order_index.asc())
        .all()
    )


# Enrollments

def enroll(db: Session, payload: EnrollmentCreate) -> Enrollment:
    obj = Enrollment(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_enrollment(
    db: Session,
    enrollment_id: int,
    payload: EnrollmentUpdate,
) -> Optional[Enrollment]:
    obj = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_enrollments_for_learner(
    db: Session,
    learner_id: int,
) -> List[Enrollment]:
    return (
        db.query(Enrollment)
        .filter(Enrollment.learner_id == learner_id)
        .order_by(Enrollment.created_at.desc())
        .all()
    )
