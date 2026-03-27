from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...crud import user as crud_user
from ...schemas.user import UserCreate, UserOut
from ..deps import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return crud_user.create(db, data)
