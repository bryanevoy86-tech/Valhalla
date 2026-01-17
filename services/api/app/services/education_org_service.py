"""PACK 77: Education SaaS - Org Service"""

from sqlalchemy.orm import Session

from app.models.education_org import School, Classroom, Teacher
from app.schemas.education_org import SchoolCreate, ClassroomCreate, TeacherCreate


# School operations
def create_school(db: Session, school: SchoolCreate) -> School:
    db_school = School(
        name=school.name,
        district=school.district,
        notes=school.notes
    )
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def list_schools(db: Session) -> list[School]:
    return db.query(School).all()


def get_school(db: Session, school_id: int) -> School | None:
    return db.query(School).filter(School.id == school_id).first()


def update_school(db: Session, school_id: int, school: SchoolCreate) -> School | None:
    db_school = get_school(db, school_id)
    if not db_school:
        return None
    db_school.name = school.name
    db_school.district = school.district
    db_school.notes = school.notes
    db.commit()
    db.refresh(db_school)
    return db_school


def delete_school(db: Session, school_id: int) -> bool:
    db_school = get_school(db, school_id)
    if not db_school:
        return False
    db.delete(db_school)
    db.commit()
    return True


# Classroom operations
def create_classroom(db: Session, classroom: ClassroomCreate) -> Classroom:
    db_classroom = Classroom(
        school_id=classroom.school_id,
        name=classroom.name,
        grade_level=classroom.grade_level
    )
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom


def list_classrooms_by_school(db: Session, school_id: int) -> list[Classroom]:
    return db.query(Classroom).filter(Classroom.school_id == school_id).all()


def get_classroom(db: Session, classroom_id: int) -> Classroom | None:
    return db.query(Classroom).filter(Classroom.id == classroom_id).first()


def update_classroom(db: Session, classroom_id: int, classroom: ClassroomCreate) -> Classroom | None:
    db_classroom = get_classroom(db, classroom_id)
    if not db_classroom:
        return None
    db_classroom.school_id = classroom.school_id
    db_classroom.name = classroom.name
    db_classroom.grade_level = classroom.grade_level
    db.commit()
    db.refresh(db_classroom)
    return db_classroom


def delete_classroom(db: Session, classroom_id: int) -> bool:
    db_classroom = get_classroom(db, classroom_id)
    if not db_classroom:
        return False
    db.delete(db_classroom)
    db.commit()
    return True


# Teacher operations
def create_teacher(db: Session, teacher: TeacherCreate) -> Teacher:
    db_teacher = Teacher(
        school_id=teacher.school_id,
        name=teacher.name,
        subject=teacher.subject
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def list_teachers_by_school(db: Session, school_id: int) -> list[Teacher]:
    return db.query(Teacher).filter(Teacher.school_id == school_id).all()


def get_teacher(db: Session, teacher_id: int) -> Teacher | None:
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


def update_teacher(db: Session, teacher_id: int, teacher: TeacherCreate) -> Teacher | None:
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    db_teacher.school_id = teacher.school_id
    db_teacher.name = teacher.name
    db_teacher.subject = teacher.subject
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def delete_teacher(db: Session, teacher_id: int) -> bool:
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return False
    db.delete(db_teacher)
    db.commit()
    return True
