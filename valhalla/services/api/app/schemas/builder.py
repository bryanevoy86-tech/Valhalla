from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class RegisterIn(BaseModel):
    agent_name: str = Field(..., max_length=64)
    version: Optional[str] = None

class RegisterOut(BaseModel):
    ok: bool
    message: str

class TaskIn(BaseModel):
    title: str
    scope: str
    plan: Optional[str] = None

class FileSpec(BaseModel):
    path: str               # relative to repo root
    content: str            # utf-8 text
    mode: str = "add"       # add|replace

class DraftOut(BaseModel):
    task_id: int
    files: List[FileSpec]
    diff_summary: str

class TaskOut(BaseModel):
    id: int
    title: str
    scope: str
    status: str
    diff_summary: Optional[str] = None

class TelemetryIn(BaseModel):
    kind: str
    msg: Optional[str] = None
    meta_json: Optional[str] = None

class ApplyIn(BaseModel):
    task_id: int
    approve: bool = True
