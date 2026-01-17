from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.lang.service import LanguageService
from app.lang.schemas import Language, TranslationOut
from app.core.db import get_db


router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("/languages", response_model=List[Language])
async def get_languages(db: Session = Depends(get_db)):
    return LanguageService(db).get_languages()


@router.get("/translate/{content_id}/{lang_code}", response_model=TranslationOut)
async def translate_content(content_id: str, lang_code: str, db: Session = Depends(get_db)):
    return LanguageService(db).translate_content(content_id, lang_code)
