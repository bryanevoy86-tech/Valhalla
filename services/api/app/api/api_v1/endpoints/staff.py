from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.staff import StaffCreate, StaffUpdate, StaffOut
from app.models.staff import Staff

router = APIRouter()

@router.post("/", response_model=StaffOut)
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    staff = Staff(**payload.dict())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

@router.get("/", response_model=list[StaffOut])
def get_all_staff(db: Session = Depends(get_db)):
    return db.query(Staff).all()

@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(staff_id: int, payload: StaffUpdate, db: Session = Depends(get_db)):
    staff = db.query(Staff).get(staff_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(staff, k, v)
    db.commit()
    db.refresh(staff)
    return staff
