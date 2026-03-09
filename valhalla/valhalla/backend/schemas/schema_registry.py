from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft7Validator, Draft202012Validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _choose_validator(meta: Dict[str, Any]):
    uri = meta.get("$schema", "")
    if "draft-07" in uri:
        return Draft7Validator
    return Draft202012Validator


async def fetch_active_version(session: AsyncSession, job_type: str) -> Optional[dict]:
    row = (
        (
            await session.execute(
                text(
                    """
      SELECT version, schema
      FROM export_schema_versions
      WHERE job_type=:jt AND is_active=TRUE
      ORDER BY version DESC
      LIMIT 1
    """
                ),
                {"jt": job_type},
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


async def fetch_schema(session: AsyncSession, job_type: str, version: int) -> Optional[dict]:
    row = (
        (
            await session.execute(
                text(
                    """
      SELECT version, schema
      FROM export_schema_versions
      WHERE job_type=:jt AND version=:v
      LIMIT 1
    """
                ),
                {"jt": job_type, "v": version},
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def validate_params(params: dict, schema: dict) -> Tuple[bool, List[dict]]:
    Validator = _choose_validator(schema)
    v = Validator(schema)
    errors = []
    for e in sorted(v.iter_errors(params), key=lambda x: x.path):
        errors.append(
            {
                "path": list(e.path),
                "message": e.message,
                "validator": e.validator,
                "schema_path": list(e.schema_path),
            }
        )
    return (len(errors) == 0, errors)
