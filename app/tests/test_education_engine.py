"""
PACK AB: Education Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_education.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def client_fixture():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return client


def test_create_course(client_fixture):
    payload = {
        "title": "Intro to Real Estate",
        "subject": "real_estate",
        "level": "beginner",
    }
    res = client_fixture.post("/education/courses", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Intro to Real Estate"
    assert body["subject"] == "real_estate"
    assert body["is_active"] is True


def test_list_courses(client_fixture):
    client_fixture.post(
        "/education/courses",
        json={"title": "Course 1", "subject": "real_estate"},
    )
    client_fixture.post(
        "/education/courses",
        json={"title": "Course 2", "subject": "money"},
    )

    res = client_fixture.get("/education/courses")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_filter_courses_by_subject(client_fixture):
    client_fixture.post(
        "/education/courses",
        json={"title": "RE 101", "subject": "real_estate"},
    )
    client_fixture.post(
        "/education/courses",
        json={"title": "Money 101", "subject": "money"},
    )

    res = client_fixture.get("/education/courses?subject=real_estate")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["subject"] == "real_estate"


def test_get_course(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Test Course"},
    )
    course_id = c_res.json()["id"]

    res = client_fixture.get(f"/education/courses/{course_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == course_id
    assert body["title"] == "Test Course"


def test_update_course(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Original", "level": "beginner"},
    )
    course_id = c_res.json()["id"]

    u_res = client_fixture.patch(
        f"/education/courses/{course_id}",
        json={"level": "intermediate", "is_active": False},
    )
    assert u_res.status_code == 200
    body = u_res.json()
    assert body["level"] == "intermediate"
    assert body["is_active"] is False


def test_create_lesson(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Test Course"},
    )
    course_id = c_res.json()["id"]

    l_res = client_fixture.post(
        "/education/lessons",
        json={
            "course_id": course_id,
            "title": "Lesson 1",
            "summary": "Intro to basics",
            "order_index": 1,
        },
    )
    assert l_res.status_code == 200
    body = l_res.json()
    assert body["title"] == "Lesson 1"
    assert body["order_index"] == 1


def test_list_lessons_for_course(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Test"},
    )
    course_id = c_res.json()["id"]

    client_fixture.post(
        "/education/lessons",
        json={"course_id": course_id, "title": "Lesson 1", "order_index": 1},
    )
    client_fixture.post(
        "/education/lessons",
        json={"course_id": course_id, "title": "Lesson 2", "order_index": 2},
    )

    res = client_fixture.get(f"/education/courses/{course_id}/lessons")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2
    assert body[0]["order_index"] == 1
    assert body[1]["order_index"] == 2


def test_enroll_learner(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Test Course"},
    )
    course_id = c_res.json()["id"]

    e_res = client_fixture.post(
        "/education/enrollments",
        json={"learner_id": 1, "course_id": course_id},
    )
    assert e_res.status_code == 200
    body = e_res.json()
    assert body["learner_id"] == 1
    assert body["course_id"] == course_id
    assert body["lessons_completed"] == 0


def test_update_enrollment_progress(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Mindset 101"},
    )
    course_id = c_res.json()["id"]

    e_res = client_fixture.post(
        "/education/enrollments",
        json={"learner_id": 1, "course_id": course_id},
    )
    enrollment_id = e_res.json()["id"]

    # update progress
    u_res = client_fixture.patch(
        f"/education/enrollments/{enrollment_id}",
        json={"lessons_completed": 3},
    )
    assert u_res.status_code == 200
    assert u_res.json()["lessons_completed"] == 3


def test_list_enrollments_for_learner(client_fixture):
    # enroll in multiple courses
    for i in range(2):
        c_res = client_fixture.post(
            "/education/courses",
            json={"title": f"Course {i}"},
        )
        course_id = c_res.json()["id"]
        client_fixture.post(
            "/education/enrollments",
            json={"learner_id": 1, "course_id": course_id},
        )

    res = client_fixture.get("/education/enrollments/by-learner/1")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_deactivate_enrollment(client_fixture):
    c_res = client_fixture.post(
        "/education/courses",
        json={"title": "Test"},
    )
    course_id = c_res.json()["id"]

    e_res = client_fixture.post(
        "/education/enrollments",
        json={"learner_id": 1, "course_id": course_id},
    )
    enrollment_id = e_res.json()["id"]

    u_res = client_fixture.patch(
        f"/education/enrollments/{enrollment_id}",
        json={"is_active": False},
    )
    assert u_res.status_code == 200
    assert u_res.json()["is_active"] is False


def test_get_nonexistent_course(client_fixture):
    res = client_fixture.get("/education/courses/999")
    assert res.status_code == 404
