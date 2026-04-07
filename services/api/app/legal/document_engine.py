"""
Document Engine - Template Loading and Variable Substitution
Loads JSON templates and renders them with provided data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
GENERATED_DIR = BASE_DIR / "generated"


@dataclass
class GeneratedDocument:
    template_key: str
    title: str
    subject: str
    output_path: str
    missing_fields: list[str]
    generated_at: str


class TemplateNotFoundError(Exception):
    pass


def _load_template(template_key: str) -> dict[str, Any]:
    """Load template JSON by key."""
    path = TEMPLATES_DIR / f"{template_key}.json"
    if not path.exists():
        raise TemplateNotFoundError(f"Template not found: {template_key}")
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_tokens(text: str) -> list[str]:
    """Extract {{variable}} tokens from text."""
    return sorted(set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text)))


def _render_text(text: str, payload: dict[str, Any]) -> str:
    """Replace {{variables}} with values from payload."""
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        value = payload.get(key, "")
        return str(value)
    return re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", replacer, text)


def generate_document(template_key: str, payload: dict[str, Any]) -> GeneratedDocument:
    """
    Generate a document from template with provided data.
    
    Returns GeneratedDocument with rendered output and missing field list.
    """
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    tpl = _load_template(template_key)
    tokens = _extract_tokens(tpl["body_text"]) + _extract_tokens(tpl.get("subject", ""))
    required = sorted(set(tpl.get("required_fields", []) + tokens))
    missing = [k for k in required if payload.get(k, "") in ("", None)]

    rendered_subject = _render_text(tpl.get("subject", tpl["title"]), payload)
    rendered_body = _render_text(tpl["body_text"], payload)

    safe_address = str(payload.get("property_address", "document")).replace("/", "-").replace("\\", "-")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{template_key}__{safe_address[:60]}__{ts}.txt"
    output_path = GENERATED_DIR / filename
    output_path.write_text(rendered_body, encoding="utf-8")

    return GeneratedDocument(
        template_key=template_key,
        title=tpl["title"],
        subject=rendered_subject,
        output_path=str(output_path),
        missing_fields=missing,
        generated_at=ts,
    )


def list_templates() -> list[dict[str, Any]]:
    """Get list of all available templates."""
    templates: list[dict[str, Any]] = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        templates.append(
            {
                "template_key": data["template_key"],
                "title": data["title"],
                "description": data.get("description", ""),
                "required_fields": data.get("required_fields", []),
            }
        )
    return templates
