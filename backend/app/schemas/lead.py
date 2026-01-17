from pydantic import BaseModel


class LeadBase(BaseModel):
    name: str
    phone: str | None = ""
    email: str | None = ""
    address: str | None = ""
    status: str | None = "new"
    tags: str | None = ""
    notes: str | None = ""
    legacy_id: str | None = "primary"


class LeadCreate(LeadBase):
    pass


class LeadOut(LeadBase):
    id: int

    class Config:
        from_attributes = True
