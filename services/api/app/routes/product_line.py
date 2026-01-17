"""PACK 82: Industry Engine - Product Line Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.product_line import ProductLineOut, ProductLineCreate
from app.services.product_line_service import (
    create_product_line, list_product_lines, get_product_line, update_product_line, delete_product_line
)

router = APIRouter(prefix="/industry/product", tags=["product_line"])


@router.post("/", response_model=ProductLineOut)
def post_product_line(product: ProductLineCreate, db: Session = Depends(get_db)):
    return create_product_line(db, product)


@router.get("/", response_model=list[ProductLineOut])
def get_products(industry_id: int | None = None, db: Session = Depends(get_db)):
    return list_product_lines(db, industry_id)


@router.get("/{product_id}", response_model=ProductLineOut)
def get_product_line_endpoint(product_id: int, db: Session = Depends(get_db)):
    return get_product_line(db, product_id)


@router.put("/{product_id}", response_model=ProductLineOut)
def put_product_line(product_id: int, product: ProductLineCreate, db: Session = Depends(get_db)):
    return update_product_line(db, product_id, product)


@router.delete("/{product_id}")
def delete_product_line_endpoint(product_id: int, db: Session = Depends(get_db)):
    return delete_product_line(db, product_id)
