"""PACK 90: Health & Fitness - Service"""

from sqlalchemy.orm import Session

from app.models.health import HealthMetric, WorkoutSession
from app.schemas.health import HealthMetricCreate, WorkoutSessionCreate


# Health metric operations
def create_metric(db: Session, metric: HealthMetricCreate) -> HealthMetric:
    db_metric = HealthMetric(
        metric_name=metric.metric_name,
        value=metric.value,
        notes=metric.notes
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def list_metrics(db: Session, metric_name: str | None = None) -> list[HealthMetric]:
    q = db.query(HealthMetric)
    if metric_name:
        q = q.filter(HealthMetric.metric_name == metric_name)
    return q.order_by(HealthMetric.id.desc()).all()


def get_metric(db: Session, metric_id: int) -> HealthMetric | None:
    return db.query(HealthMetric).filter(HealthMetric.id == metric_id).first()


def update_metric(db: Session, metric_id: int, metric: HealthMetricCreate) -> HealthMetric | None:
    db_metric = get_metric(db, metric_id)
    if not db_metric:
        return None
    db_metric.metric_name = metric.metric_name
    db_metric.value = metric.value
    db_metric.notes = metric.notes
    db.commit()
    db.refresh(db_metric)
    return db_metric


def delete_metric(db: Session, metric_id: int) -> bool:
    db_metric = get_metric(db, metric_id)
    if not db_metric:
        return False
    db.delete(db_metric)
    db.commit()
    return True


# Workout session operations
def create_workout(db: Session, workout: WorkoutSessionCreate) -> WorkoutSession:
    db_workout = WorkoutSession(
        workout_type=workout.workout_type,
        duration_minutes=workout.duration_minutes,
        intensity=workout.intensity,
        notes=workout.notes
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout


def list_workouts(db: Session, workout_type: str | None = None) -> list[WorkoutSession]:
    q = db.query(WorkoutSession)
    if workout_type:
        q = q.filter(WorkoutSession.workout_type == workout_type)
    return q.order_by(WorkoutSession.id.desc()).all()


def get_workout(db: Session, workout_id: int) -> WorkoutSession | None:
    return db.query(WorkoutSession).filter(WorkoutSession.id == workout_id).first()


def update_workout(db: Session, workout_id: int, workout: WorkoutSessionCreate) -> WorkoutSession | None:
    db_workout = get_workout(db, workout_id)
    if not db_workout:
        return None
    db_workout.workout_type = workout.workout_type
    db_workout.duration_minutes = workout.duration_minutes
    db_workout.intensity = workout.intensity
    db_workout.notes = workout.notes
    db.commit()
    db.refresh(db_workout)
    return db_workout


def delete_workout(db: Session, workout_id: int) -> bool:
    db_workout = get_workout(db, workout_id)
    if not db_workout:
        return False
    db.delete(db_workout)
    db.commit()
    return True
