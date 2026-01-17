from typing import List, Dict
from sqlalchemy.orm import Session

from .schemas import Language, TranslationOut


class LanguageService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def get_languages() -> List[Language]:
        # Static list for this pack; replace with DB-backed later if needed
        return [
            Language(code="en", name="English"),
            Language(code="es", name="Spanish"),
            Language(code="fr", name="French"),
        ]

    @staticmethod
    def translate_content(content_id: str, lang_code: str) -> TranslationOut:
        # Simple demo translations; replace with DB or i18n backend later
        translations: Dict[str, Dict[str, str]] = {
            "content_001": {
                "en": "Welcome to Valhalla",
                "es": "Bienvenido a Valhalla",
                "fr": "Bienvenue à Valhalla",
            },
            "content_002": {
                "en": "Security settings updated",
                "es": "Configuración de seguridad actualizada",
                "fr": "Paramètres de sécurité mis à jour",
            },
        }
        table = translations.get(content_id, {})
        text = table.get(lang_code, table.get("en", ""))
        return TranslationOut(content_id=content_id, language=lang_code, text=text)
