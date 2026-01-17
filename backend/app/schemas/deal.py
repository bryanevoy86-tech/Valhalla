from pydantic import BaseModel


class DealBase(BaseModel):
    lead_id: int
    arv: float = 0.0
    repairs: float = 0.0
    offer: float = 0.0
    mao: float = 0.0
    roi_note: str | None = ""
    legacy_id: str | None = "primary"


class DealCreate(DealBase):
    pass


class DealOut(DealBase):
    id: int

    class Config:
        from_attributes = True
