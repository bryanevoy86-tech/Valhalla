"""PACK 89: Household OS - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.household import HouseholdTaskOut, HouseholdTaskCreate, HomeInventoryOut, HomeInventoryCreate
from app.services.household_service import (
    create_task, list_tasks, get_task, update_task, delete_task,
    create_inventory_item, list_inventory, get_inventory_item, update_inventory_item, delete_inventory_item
)

router = APIRouter(prefix="/household", tags=["household"])


# Household task endpoints
@router.post("/task", response_model=HouseholdTaskOut)
def post_task(task: HouseholdTaskCreate, db: Session = Depends(get_db)):
    return create_task(db, task)


@router.get("/tasks", response_model=list[HouseholdTaskOut])
def get_tasks_endpoint(db: Session = Depends(get_db)):
    return list_tasks(db)


@router.get("/task/{task_id}", response_model=HouseholdTaskOut)
def get_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    return get_task(db, task_id)


@router.put("/task/{task_id}", response_model=HouseholdTaskOut)
def put_task(task_id: int, task: HouseholdTaskCreate, db: Session = Depends(get_db)):
    return update_task(db, task_id, task)


@router.delete("/task/{task_id}")
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    return delete_task(db, task_id)


# Home inventory endpoints
@router.post("/inventory", response_model=HomeInventoryOut)
def post_inventory_item(item: HomeInventoryCreate, db: Session = Depends(get_db)):
    return create_inventory_item(db, item)


@router.get("/inventory", response_model=list[HomeInventoryOut])
def get_inventory_endpoint(db: Session = Depends(get_db)):
    return list_inventory(db)


@router.get("/inventory/{item_id}", response_model=HomeInventoryOut)
def get_inventory_item_endpoint(item_id: int, db: Session = Depends(get_db)):
    return get_inventory_item(db, item_id)


@router.put("/inventory/{item_id}", response_model=HomeInventoryOut)
def put_inventory_item(item_id: int, item: HomeInventoryCreate, db: Session = Depends(get_db)):
    return update_inventory_item(db, item_id, item)


@router.delete("/inventory/{item_id}")
def delete_inventory_item_endpoint(item_id: int, db: Session = Depends(get_db)):
    return delete_inventory_item(db, item_id)
