"""PACK 83: Industry Engine - Cost Model Service"""

from sqlalchemy.orm import Session

from app.models.cost_model import CostModel
from app.schemas.cost_model import CostModelCreate


def create_cost_model(db: Session, cost_model: CostModelCreate) -> CostModel:
    db_cost_model = CostModel(
        product_line_id=cost_model.product_line_id,
        labor_cost=cost_model.labor_cost,
        material_cost=cost_model.material_cost,
        overhead_cost=cost_model.overhead_cost,
        supply_chain_payload=cost_model.supply_chain_payload
    )
    db.add(db_cost_model)
    db.commit()
    db.refresh(db_cost_model)
    return db_cost_model


def list_cost_models(db: Session, product_line_id: int | None = None) -> list[CostModel]:
    q = db.query(CostModel)
    if product_line_id:
        q = q.filter(CostModel.product_line_id == product_line_id)
    return q.order_by(CostModel.id.desc()).all()


def get_cost_model(db: Session, cost_model_id: int) -> CostModel | None:
    return db.query(CostModel).filter(CostModel.id == cost_model_id).first()


def update_cost_model(db: Session, cost_model_id: int, cost_model: CostModelCreate) -> CostModel | None:
    db_cost_model = get_cost_model(db, cost_model_id)
    if not db_cost_model:
        return None
    db_cost_model.product_line_id = cost_model.product_line_id
    db_cost_model.labor_cost = cost_model.labor_cost
    db_cost_model.material_cost = cost_model.material_cost
    db_cost_model.overhead_cost = cost_model.overhead_cost
    db_cost_model.supply_chain_payload = cost_model.supply_chain_payload
    db.commit()
    db.refresh(db_cost_model)
    return db_cost_model


def delete_cost_model(db: Session, cost_model_id: int) -> bool:
    db_cost_model = get_cost_model(db, cost_model_id)
    if not db_cost_model:
        return False
    db.delete(db_cost_model)
    db.commit()
    return True
