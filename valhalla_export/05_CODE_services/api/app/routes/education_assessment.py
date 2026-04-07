"""PACK 80: Education SaaS - Assessment Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.education_assessment import AssignmentOut, AssignmentCreate, SubmissionOut, SubmissionCreate, GradeOut, GradeCreate
from app.services.education_assessment_service import (
    create_assignment, list_assignments, get_assignment, update_assignment, delete_assignment,
    create_submission, list_submissions, get_submission, update_submission, delete_submission,
    create_grade, list_grades, get_grade, update_grade, delete_grade
)

router = APIRouter(prefix="/education/assess", tags=["education_assessment"])


# Assignment endpoints
@router.post("/assignment", response_model=AssignmentOut)
def post_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    return create_assignment(db, assignment)


@router.get("/assignments", response_model=list[AssignmentOut])
def get_assignments_all(classroom_id: int | None = None, db: Session = Depends(get_db)):
    return list_assignments(db, classroom_id)


@router.get("/assignment/{assignment_id}", response_model=AssignmentOut)
def get_assignment_endpoint(assignment_id: int, db: Session = Depends(get_db)):
    return get_assignment(db, assignment_id)


@router.put("/assignment/{assignment_id}", response_model=AssignmentOut)
def put_assignment(assignment_id: int, assignment: AssignmentCreate, db: Session = Depends(get_db)):
    return update_assignment(db, assignment_id, assignment)


@router.delete("/assignment/{assignment_id}")
def delete_assignment_endpoint(assignment_id: int, db: Session = Depends(get_db)):
    return delete_assignment(db, assignment_id)


# Submission endpoints
@router.post("/submission", response_model=SubmissionOut)
def post_submission(submission: SubmissionCreate, db: Session = Depends(get_db)):
    return create_submission(db, submission)


@router.get("/submissions", response_model=list[SubmissionOut])
def get_submissions_all(assignment_id: int | None = None, db: Session = Depends(get_db)):
    return list_submissions(db, assignment_id)


@router.get("/submission/{submission_id}", response_model=SubmissionOut)
def get_submission_endpoint(submission_id: int, db: Session = Depends(get_db)):
    return get_submission(db, submission_id)


@router.put("/submission/{submission_id}", response_model=SubmissionOut)
def put_submission(submission_id: int, submission: SubmissionCreate, db: Session = Depends(get_db)):
    return update_submission(db, submission_id, submission)


@router.delete("/submission/{submission_id}")
def delete_submission_endpoint(submission_id: int, db: Session = Depends(get_db)):
    return delete_submission(db, submission_id)


# Grade endpoints
@router.post("/grade", response_model=GradeOut)
def post_grade(grade: GradeCreate, db: Session = Depends(get_db)):
    return create_grade(db, grade)


@router.get("/grades", response_model=list[GradeOut])
def get_grades_all(submission_id: int | None = None, db: Session = Depends(get_db)):
    return list_grades(db, submission_id)


@router.get("/grade/{grade_id}", response_model=GradeOut)
def get_grade_endpoint(grade_id: int, db: Session = Depends(get_db)):
    return get_grade(db, grade_id)


@router.put("/grade/{grade_id}", response_model=GradeOut)
def put_grade(grade_id: int, grade: GradeCreate, db: Session = Depends(get_db)):
    return update_grade(db, grade_id, grade)


@router.delete("/grade/{grade_id}")
def delete_grade_endpoint(grade_id: int, db: Session = Depends(get_db)):
    return delete_grade(db, grade_id)
