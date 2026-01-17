from pydantic import BaseModel


class EnqueueOut(BaseModel):
    job_id: str


class JobStatusOut(BaseModel):
    id: str
    status: str
    result: dict | None = None
