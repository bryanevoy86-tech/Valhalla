from pydantic import BaseModel, EmailStr


class BuyerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = ""
    legacy_id: str | None = "primary"
    markets: str | None = ""
    zips: str | None = ""
    price_min: float | None = 0.0
    price_max: float | None = 9e12
    beds_min: float | None = 0.0
    baths_min: float | None = 0.0
    property_types: str | None = ""
    tags: str | None = ""
    active: bool | None = True


class BuyerCreate(BuyerBase):
    pass


class BuyerOut(BuyerBase):
    id: int

    class Config:
        from_attributes = True
