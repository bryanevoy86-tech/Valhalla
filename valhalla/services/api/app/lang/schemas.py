from typing import List
from pydantic import BaseModel


class Language(BaseModel):
    code: str  # e.g., 'en', 'es', 'fr'
    name: str  # e.g., 'English', 'Spanish'


class TranslationOut(BaseModel):
    content_id: str
    language: str
    text: str
