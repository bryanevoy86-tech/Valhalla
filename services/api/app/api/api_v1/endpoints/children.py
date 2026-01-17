from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.child import Child, Chore, CoinLedger
from app.schemas.children import (
    ChildCreate,
    ChildUpdate,
    ChildOut,
    ChoreCreate,
    ChoreUpdate,
    ChoreOut,
    CoinLedgerCreate,
    CoinLedgerOut,
)

router = APIRouter()

# Children
@router.post("/profiles", response_model=ChildOut)
def create_child(payload: ChildCreate, db: Session = Depends(get_db)):
    obj = Child(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/profiles", response_model=list[ChildOut])
def list_children(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Child)
    if status:
        query = query.filter(Child.status == status)
    return query.all()

@router.put("/profiles/{child_id}", response_model=ChildOut)
def update_child(child_id: int, payload: ChildUpdate, db: Session = Depends(get_db)):
    obj = db.query(Child).get(child_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

# Chores
@router.post("/chores", response_model=ChoreOut)
def create_chore(payload: ChoreCreate, db: Session = Depends(get_db)):
    obj = Chore(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/chores", response_model=list[ChoreOut])
def list_chores(child_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Chore)
    if child_id is not None:
        query = query.filter(Chore.child_id == child_id)
    return query.all()

@router.put("/chores/{chore_id}", response_model=ChoreOut)
def update_chore(chore_id: int, payload: ChoreUpdate, db: Session = Depends(get_db)):
    obj = db.query(Chore).get(chore_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

# Coin Ledger
@router.post("/coins", response_model=CoinLedgerOut)
def add_coin_entry(payload: CoinLedgerCreate, db: Session = Depends(get_db)):
    obj = CoinLedger(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/coins", response_model=list[CoinLedgerOut])
def list_coin_entries(child_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(CoinLedger)
    if child_id is not None:
        query = query.filter(CoinLedger.child_id == child_id)
    return query.all()
