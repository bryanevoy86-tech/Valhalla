"""Backend Deal model - canonical for Heimdall operations."""

from datetime import datetime
from typing import ClassVar

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {"extend_existing": True}
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_ts = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_ts = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    # Core deal information
    title = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False)  # pipeline stage
    status = Column(String(50), nullable=False, default="active")  # active, closed, dead, etc.

    # Financial metrics (stored as DECIMAL in DB, Numeric in SQLAlchemy)
    arv = Column(Numeric(15, 2), nullable=True)  # After Repair Value
    estimated_repair_cost = Column(Numeric(15, 2), nullable=True)
    max_allowable_offer = Column(Numeric(15, 2), nullable=True)
    target_assignment_fee = Column(Numeric(15, 2), nullable=True)
    score = Column(Numeric(8, 2), nullable=True)  # Heimdall score

    # Metadata
    notes = Column(Text, nullable=True)
    disposition_status = Column(String(50), nullable=True)

    # Relationships
    lead = relationship("Lead", foreign_keys=[lead_id]) if "Lead" in locals() else None

    # Non-persistent compatibility fields expected by some legacy tests/routes.
    _compat_org_id: ClassVar[int | None] = None
    _compat_legacy_id: ClassVar[str | None] = None
    _compat_city: ClassVar[str | None] = None
    _compat_state: ClassVar[str | None] = None
    _compat_price: ClassVar[float | None] = None
    _compat_offer: ClassVar[float | None] = None
    _compat_address: ClassVar[str | None] = None
    _compat_region: ClassVar[str | None] = None
    _compat_property_type: ClassVar[str | None] = None
    _compat_beds: ClassVar[int | None] = None
    _compat_baths: ClassVar[int | None] = None

    @property
    def repairs(self):
        return self.estimated_repair_cost

    @repairs.setter
    def repairs(self, value):
        self.estimated_repair_cost = value

    @property
    def mao(self):
        return self.max_allowable_offer

    @mao.setter
    def mao(self, value):
        self.max_allowable_offer = value

    @property
    def roi_note(self):
        return self.notes

    @roi_note.setter
    def roi_note(self, value):
        self.notes = value

    @property
    def org_id(self):
        return self._compat_org_id

    @org_id.setter
    def org_id(self, value):
        self._compat_org_id = value

    @property
    def legacy_id(self):
        return self._compat_legacy_id

    @legacy_id.setter
    def legacy_id(self, value):
        self._compat_legacy_id = value

    @property
    def city(self):
        return self._compat_city

    @city.setter
    def city(self, value):
        self._compat_city = value

    @property
    def state(self):
        return self._compat_state

    @state.setter
    def state(self, value):
        self._compat_state = value

    @property
    def price(self):
        return self._compat_price

    @price.setter
    def price(self, value):
        self._compat_price = value

    @property
    def offer(self):
        return self._compat_offer

    @offer.setter
    def offer(self, value):
        self._compat_offer = value

    @property
    def purchase_price(self):
        return self.price

    @purchase_price.setter
    def purchase_price(self, value):
        self.price = value

    @property
    def address(self):
        return self._compat_address

    @address.setter
    def address(self, value):
        self._compat_address = value

    @property
    def region(self):
        return self._compat_region

    @region.setter
    def region(self, value):
        self._compat_region = value

    @property
    def property_type(self):
        return self._compat_property_type

    @property_type.setter
    def property_type(self, value):
        self._compat_property_type = value

    @property
    def beds(self):
        return self._compat_beds

    @beds.setter
    def beds(self, value):
        self._compat_beds = value

    @property
    def baths(self):
        return self._compat_baths

    @baths.setter
    def baths(self, value):
        self._compat_baths = value

    def __init__(self, **kwargs):
        # Keep old field names alive while mapping to canonical fields.
        if kwargs.get("estimated_repair_cost") is None and kwargs.get("repairs") is not None:
            kwargs["estimated_repair_cost"] = kwargs.get("repairs")
        if kwargs.get("max_allowable_offer") is None and kwargs.get("mao") is not None:
            kwargs["max_allowable_offer"] = kwargs.get("mao")
        if kwargs.get("price") is None and kwargs.get("purchase_price") is not None:
            kwargs["price"] = kwargs.get("purchase_price")
        if kwargs.get("created_ts") is None and kwargs.get("created_at") is not None:
            kwargs["created_ts"] = kwargs.get("created_at")
        if kwargs.get("updated_ts") is None and kwargs.get("updated_at") is not None:
            kwargs["updated_ts"] = kwargs.get("updated_at")
        if kwargs.get("title") is None and kwargs.get("headline") is not None:
            kwargs["title"] = kwargs.get("headline")

        compat_keys = [
            "org_id",
            "legacy_id",
            "city",
            "state",
            "price",
            "offer",
            "address",
            "region",
            "property_type",
            "beds",
            "baths",
            "headline",
            "purchase_price",
            "created_at",
            "updated_at",
        ]
        compat_values = {k: kwargs.pop(k, None) for k in compat_keys}
        roi_note = kwargs.pop("roi_note", None)
        if kwargs.get("title") is None:
            legacy_id = compat_values.get("legacy_id")
            kwargs["title"] = f"Deal {legacy_id}" if legacy_id else "Untitled Deal"
        if kwargs.get("stage") is None:
            kwargs["stage"] = "lead_received"
        super().__init__(**kwargs)
        self.org_id = compat_values["org_id"]
        self.legacy_id = compat_values["legacy_id"]
        self.city = compat_values["city"]
        self.state = compat_values["state"]
        self.price = compat_values["price"]
        self.offer = compat_values["offer"]
        self.address = compat_values["address"]
        self.region = compat_values["region"]
        self.property_type = compat_values["property_type"]
        self.beds = compat_values["beds"]
        self.baths = compat_values["baths"]
        if roi_note is not None and self.notes is None:
            self.roi_note = roi_note
