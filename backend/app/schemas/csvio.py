from pydantic import BaseModel


class ImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: int
    message: str | None = None
