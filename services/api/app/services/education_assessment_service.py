"""PACK 80: Education SaaS - Assessment Service"""

from sqlalchemy.orm import Session

from app.models.education_assessment import Assignment, Submission, Grade
from app.schemas.education_assessment import AssignmentCreate, SubmissionCreate, GradeCreate


# Assignment operations
def create_assignment(db: Session, assignment: AssignmentCreate) -> Assignment:
    db_assignment = Assignment(
        classroom_id=assignment.classroom_id,
        title=assignment.title,
        instructions=assignment.instructions,
        due_date=assignment.due_date
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def list_assignments(db: Session, classroom_id: int | None = None) -> list[Assignment]:
    q = db.query(Assignment)
    if classroom_id:
        q = q.filter(Assignment.classroom_id == classroom_id)
    return q.order_by(Assignment.id.desc()).all()


def get_assignment(db: Session, assignment_id: int) -> Assignment | None:
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()


def update_assignment(db: Session, assignment_id: int, assignment: AssignmentCreate) -> Assignment | None:
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        return None
    db_assignment.classroom_id = assignment.classroom_id
    db_assignment.title = assignment.title
    db_assignment.instructions = assignment.instructions
    db_assignment.due_date = assignment.due_date
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def delete_assignment(db: Session, assignment_id: int) -> bool:
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        return False
    db.delete(db_assignment)
    db.commit()
    return True


# Submission operations
def create_submission(db: Session, submission: SubmissionCreate) -> Submission:
    db_submission = Submission(
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        content_payload=submission.content_payload
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


def list_submissions(db: Session, assignment_id: int | None = None) -> list[Submission]:
    q = db.query(Submission)
    if assignment_id:
        q = q.filter(Submission.assignment_id == assignment_id)
    return q.order_by(Submission.id.desc()).all()


def get_submission(db: Session, submission_id: int) -> Submission | None:
    return db.query(Submission).filter(Submission.id == submission_id).first()


def update_submission(db: Session, submission_id: int, submission: SubmissionCreate) -> Submission | None:
    db_submission = get_submission(db, submission_id)
    if not db_submission:
        return None
    db_submission.assignment_id = submission.assignment_id
    db_submission.student_id = submission.student_id
    db_submission.content_payload = submission.content_payload
    db.commit()
    db.refresh(db_submission)
    return db_submission


def delete_submission(db: Session, submission_id: int) -> bool:
    db_submission = get_submission(db, submission_id)
    if not db_submission:
        return False
    db.delete(db_submission)
    db.commit()
    return True


# Grade operations
def create_grade(db: Session, grade: GradeCreate) -> Grade:
    db_grade = Grade(
        submission_id=grade.submission_id,
        score=grade.score,
        feedback=grade.feedback
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade


def list_grades(db: Session, submission_id: int | None = None) -> list[Grade]:
    q = db.query(Grade)
    if submission_id:
        q = q.filter(Grade.submission_id == submission_id)
    return q.order_by(Grade.id.desc()).all()


def get_grade(db: Session, grade_id: int) -> Grade | None:
    return db.query(Grade).filter(Grade.id == grade_id).first()


def update_grade(db: Session, grade_id: int, grade: GradeCreate) -> Grade | None:
    db_grade = get_grade(db, grade_id)
    if not db_grade:
        return None
    db_grade.submission_id = grade.submission_id
    db_grade.score = grade.score
    db_grade.feedback = grade.feedback
    db.commit()
    db.refresh(db_grade)
    return db_grade


def delete_grade(db: Session, grade_id: int) -> bool:
    db_grade = get_grade(db, grade_id)
    if not db_grade:
        return False
    db.delete(db_grade)
    db.commit()
    return True
