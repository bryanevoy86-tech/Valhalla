"""PACK 89: Household OS - Service"""

from sqlalchemy.orm import Session

from app.models.household import HouseholdTask, HomeInventoryItem
from app.schemas.household import HouseholdTaskCreate, HomeInventoryCreate


# Household task operations
def create_task(db: Session, task: HouseholdTaskCreate) -> HouseholdTask:
    db_task = HouseholdTask(
        name=task.name,
        frequency=task.frequency,
        assigned_to=task.assigned_to,
        notes=task.notes,
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def list_tasks(db: Session) -> list[HouseholdTask]:
    return db.query(HouseholdTask).order_by(HouseholdTask.id.desc()).all()


def get_task(db: Session, task_id: int) -> HouseholdTask | None:
    return db.query(HouseholdTask).filter(HouseholdTask.id == task_id).first()


def update_task(db: Session, task_id: int, task: HouseholdTaskCreate) -> HouseholdTask | None:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    db_task.name = task.name
    db_task.frequency = task.frequency
    db_task.assigned_to = task.assigned_to
    db_task.notes = task.notes
    db_task.completed = task.completed
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True


# Home inventory operations
def create_inventory_item(db: Session, item: HomeInventoryCreate) -> HomeInventoryItem:
    db_item = HomeInventoryItem(
        item_name=item.item_name,
        quantity=item.quantity,
        min_required=item.min_required,
        notes=item.notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def list_inventory(db: Session) -> list[HomeInventoryItem]:
    return db.query(HomeInventoryItem).order_by(HomeInventoryItem.id.desc()).all()


def get_inventory_item(db: Session, item_id: int) -> HomeInventoryItem | None:
    return db.query(HomeInventoryItem).filter(HomeInventoryItem.id == item_id).first()


def update_inventory_item(db: Session, item_id: int, item: HomeInventoryCreate) -> HomeInventoryItem | None:
    db_item = get_inventory_item(db, item_id)
    if not db_item:
        return None
    db_item.item_name = item.item_name
    db_item.quantity = item.quantity
    db_item.min_required = item.min_required
    db_item.notes = item.notes
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_inventory_item(db: Session, item_id: int) -> bool:
    db_item = get_inventory_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True
