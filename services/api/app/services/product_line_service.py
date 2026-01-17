"""PACK 82: Industry Engine - Product Line Service"""

from sqlalchemy.orm import Session

from app.models.product_line import ProductLine
from app.schemas.product_line import ProductLineCreate


def create_product_line(db: Session, product: ProductLineCreate) -> ProductLine:
    db_product = ProductLine(
        industry_id=product.industry_id,
        name=product.name,
        description=product.description,
        cost_structure=product.cost_structure,
        retail_price=product.retail_price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def list_product_lines(db: Session, industry_id: int | None = None) -> list[ProductLine]:
    q = db.query(ProductLine)
    if industry_id:
        q = q.filter(ProductLine.industry_id == industry_id)
    return q.order_by(ProductLine.id.desc()).all()


def get_product_line(db: Session, product_id: int) -> ProductLine | None:
    return db.query(ProductLine).filter(ProductLine.id == product_id).first()


def update_product_line(db: Session, product_id: int, product: ProductLineCreate) -> ProductLine | None:
    db_product = get_product_line(db, product_id)
    if not db_product:
        return None
    db_product.industry_id = product.industry_id
    db_product.name = product.name
    db_product.description = product.description
    db_product.cost_structure = product.cost_structure
    db_product.retail_price = product.retail_price
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product_line(db: Session, product_id: int) -> bool:
    db_product = get_product_line(db, product_id)
    if not db_product:
        return False
    db.delete(db_product)
    db.commit()
    return True
