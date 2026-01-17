"""
Pack 51: Legal Document Engine - Pydantic schemas
"""
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Optional, Dict, List


class TemplateIn(BaseModel):
    name: str
    jurisdiction: Optional[str] = None
    kind: str
    active: bool = True


class TemplateOut(TemplateIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class VersionIn(BaseModel):
    template_id: int
    body: str
    version: int


class ClauseIn(BaseModel):
    name: str
    jurisdiction: Optional[str] = None
    body: str


class ClauseOut(ClauseIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class VariableIn(BaseModel):
    key: str
    desc: Optional[str] = None
    required: bool = True
    example: Optional[str] = None


class VariableOut(VariableIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RenderReq(BaseModel):
    template_id: int
    version: int
    variables: Dict[str, str]


class RenderOut(BaseModel):
    rendered: str


class GenerateReq(RenderReq):
    pass


class DocOut(BaseModel):
    id: int
    status: str


class SignReq(BaseModel):
    document_id: int
    signer_name: str
    signer_email: str
