from app.core.db import SessionLocal
from app.models.file_asset import FileAsset


def test_file_asset_model():
    db = SessionLocal()
    try:
        f = FileAsset(
            key="uploads/primary/test.txt",
            filename="test.txt",
            content_type="text/plain",
            size=5,
            legacy_id="primary",
            created_by=1,
        )
        db.add(f)
        db.commit()
        db.refresh(f)
        assert f.id > 0
    finally:
        db.close()
