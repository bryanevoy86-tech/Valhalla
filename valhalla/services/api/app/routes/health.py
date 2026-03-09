"""PACK 90: Health & Fitness - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.health import HealthMetricOut, HealthMetricCreate, WorkoutSessionOut, WorkoutSessionCreate
from app.services.health_service import (
    create_metric, list_metrics, get_metric, update_metric, delete_metric,
    create_workout, list_workouts, get_workout, update_workout, delete_workout
)

router = APIRouter(prefix="/health", tags=["health"])


# Health metric endpoints
@router.post("/metric", response_model=HealthMetricOut)
def post_metric(metric: HealthMetricCreate, db: Session = Depends(get_db)):
    return create_metric(db, metric)


@router.get("/metrics", response_model=list[HealthMetricOut])
def get_metrics_endpoint(metric_name: str | None = None, db: Session = Depends(get_db)):
    return list_metrics(db, metric_name)


@router.get("/metric/{metric_id}", response_model=HealthMetricOut)
def get_metric_endpoint(metric_id: int, db: Session = Depends(get_db)):
    return get_metric(db, metric_id)


@router.put("/metric/{metric_id}", response_model=HealthMetricOut)
def put_metric(metric_id: int, metric: HealthMetricCreate, db: Session = Depends(get_db)):
    return update_metric(db, metric_id, metric)


@router.delete("/metric/{metric_id}")
def delete_metric_endpoint(metric_id: int, db: Session = Depends(get_db)):
    return delete_metric(db, metric_id)


# Workout session endpoints
@router.post("/workout", response_model=WorkoutSessionOut)
def post_workout(workout: WorkoutSessionCreate, db: Session = Depends(get_db)):
    return create_workout(db, workout)


@router.get("/workouts", response_model=list[WorkoutSessionOut])
def get_workouts_endpoint(workout_type: str | None = None, db: Session = Depends(get_db)):
    return list_workouts(db, workout_type)


@router.get("/workout/{workout_id}", response_model=WorkoutSessionOut)
def get_workout_endpoint(workout_id: int, db: Session = Depends(get_db)):
    return get_workout(db, workout_id)


@router.put("/workout/{workout_id}", response_model=WorkoutSessionOut)
def put_workout(workout_id: int, workout: WorkoutSessionCreate, db: Session = Depends(get_db)):
    return update_workout(db, workout_id, workout)


@router.delete("/workout/{workout_id}")
def delete_workout_endpoint(workout_id: int, db: Session = Depends(get_db)):
    return delete_workout(db, workout_id)
