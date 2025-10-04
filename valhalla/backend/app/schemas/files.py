from pydantic import BaseModel


class PresignUploadIn(BaseModel):
    filename: str
    content_type: str | None = "application/octet-stream"
    legacy_id: str | None = "primary"
    prefix: str | None = "uploads"  # key prefix/folder


class PresignUploadOut(BaseModel):
    key: str
    url: str


class RegisterUploadIn(BaseModel):
    key: str
    size: int
    filename: str
    content_type: str | None = "application/octet-stream"
    legacy_id: str | None = "primary"


class FileOut(BaseModel):
    id: int
    key: str
    filename: str
    content_type: str
    size: int
    legacy_id: str

    class Config:
        from_attributes = True


class PresignDownloadOut(BaseModel):
    url: str
