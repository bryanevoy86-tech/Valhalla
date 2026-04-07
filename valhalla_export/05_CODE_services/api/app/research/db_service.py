from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.research import ResearchSource, ResearchPlaybook
from .schemas import Source, Playbook, UpsertPlaybook
import json

class ResearchDB:
    def __init__(self, db: Session):
        self.db = db

    # Sources
    def list_sources(self) -> List[Source]:
        rows = self.db.execute(select(ResearchSource).order_by(ResearchSource.id.desc())).scalars().all()
        out: List[Source] = []
        for r in rows:
            tags = [t for t in (r.tags or '').split(',') if t]
            out.append(Source(name=r.name, url=r.url, type=(r.kind or 'doc'), tags=tags))
        return out

    def add_source(self, src: Source) -> None:
        tags_csv = ','.join(src.tags or [])
        # upsert by url
        row = self.db.execute(select(ResearchSource).where(ResearchSource.url == str(src.url))).scalar_one_or_none()
        if row:
            row.name = src.name
            row.kind = src.type
            row.tags = tags_csv
        else:
            row = ResearchSource(name=src.name, url=str(src.url), kind=src.type, tags=tags_csv)
            self.db.add(row)
        self.db.commit()

    # Playbooks
    def upsert_playbook(self, key: str, body: UpsertPlaybook) -> Playbook:
        tags_csv = ','.join(body.tags or [])
        steps_text = json.dumps(body.steps)
        meta_text = json.dumps(body.meta or {})
        row = self.db.execute(select(ResearchPlaybook).where(ResearchPlaybook.key == key)).scalar_one_or_none()
        if row:
            row.title = body.title
            row.steps = steps_text
            row.tags = tags_csv
            row.meta = meta_text
        else:
            row = ResearchPlaybook(key=key, title=body.title, steps=steps_text, tags=tags_csv, meta=meta_text)
            self.db.add(row)
        self.db.commit()
        return self._to_playbook(row)

    def get_playbook(self, key: str) -> Optional[Playbook]:
        row = self.db.execute(select(ResearchPlaybook).where(ResearchPlaybook.key == key)).scalar_one_or_none()
        if not row:
            return None
        return self._to_playbook(row)

    def list_playbooks(self) -> List[Playbook]:
        rows = self.db.execute(select(ResearchPlaybook).order_by(ResearchPlaybook.id.desc())).scalars().all()
        return [self._to_playbook(r) for r in rows]

    def _to_playbook(self, r: ResearchPlaybook) -> Playbook:
        steps = json.loads(r.steps) if r.steps else []
        tags = [t for t in (r.tags or '').split(',') if t]
        meta = json.loads(r.meta) if r.meta else {}
        return Playbook(key=r.key, title=r.title, steps=steps, tags=tags, meta=meta)
