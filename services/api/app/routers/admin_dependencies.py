# services/api/app/routers/admin_dependencies.py

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(
    prefix="/admin/deps",
    tags=["Admin", "Dependencies"],
)


@dataclass
class DependencySpec:
    name: str
    import_name: str
    optional: bool
    used_for: str
    recommendation: str


# These are the "nice to have / strongly recommended" dependencies
# that various routers may rely on. You can extend this list as needed.
RECOMMENDED_DEPS: List[DependencySpec] = [
    DependencySpec(
        name="beautifulsoup4",
        import_name="bs4",
        optional=False,
        used_for="HTML parsing / scraping (research, ingest, parsing email/content).",
        recommendation="pip install beautifulsoup4",
    ),
    DependencySpec(
        name="cryptography",
        import_name="cryptography",
        optional=False,
        used_for="Encryption helpers, secure tokens, key management.",
        recommendation="pip install cryptography",
    ),
    DependencySpec(
        name="rapidfuzz",
        import_name="rapidfuzz",
        optional=True,
        used_for="Fast fuzzy matching for matching leads/buyers, names, etc.",
        recommendation="pip install rapidfuzz",
    ),
    DependencySpec(
        name="reportlab",
        import_name="reportlab",
        optional=True,
        used_for="PDF generation for agreements, exports, reports.",
        recommendation="pip install reportlab",
    ),
    DependencySpec(
        name="email-validator",
        import_name="email_validator",
        optional=True,
        used_for="Strict email validation in user / lead forms.",
        recommendation="pip install email-validator",
    ),
    DependencySpec(
        name="python-multipart",
        import_name="multipart",
        optional=False,
        used_for="File uploads via FastAPI (agreements, docs, uploads).",
        recommendation="pip install python-multipart",
    ),
    DependencySpec(
        name="uvloop",
        import_name="uvloop",
        optional=True,
        used_for="High-performance event loop in production.",
        recommendation="pip install uvloop",
    ),
]


def _probe_import(import_name: str) -> bool:
    """
    Return True if the module `import_name` can be imported.
    """
    spec = importlib.util.find_spec(import_name)
    return spec is not None


def _build_dep_status(dep: DependencySpec) -> Dict:
    installed = _probe_import(dep.import_name)
    return {
        "name": dep.name,
        "import_name": dep.import_name,
        "installed": installed,
        "optional": dep.optional,
        "used_for": dep.used_for,
        "recommendation": dep.recommendation,
    }


@router.get(
    "/summary",
    summary="Dependency summary",
    description=(
        "Summary view of important optional/required dependencies and whether "
        "they are installed in the current environment."
    ),
)
async def get_dependency_summary() -> Dict[str, object]:
    deps = [_build_dep_status(dep) for dep in RECOMMENDED_DEPS]

    installed = [d for d in deps if d["installed"]]
    missing_required = [d for d in deps if not d["installed"] and not d["optional"]]
    missing_optional = [d for d in deps if not d["installed"] and d["optional"]]

    # Build suggested pip commands
    required_cmd = None
    optional_cmd = None
    if missing_required:
        required_pkgs = " ".join(d["name"] for d in missing_required)
        required_cmd = f"pip install {required_pkgs}"
    if missing_optional:
        optional_pkgs = " ".join(d["name"] for d in missing_optional)
        optional_cmd = f"pip install {optional_pkgs}"

    return {
        "all": deps,
        "installed": installed,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "suggested_commands": {
            "required": required_cmd,
            "optional": optional_cmd,
        },
    }


@router.get(
    "/check",
    summary="Check a single dependency",
    description=(
        "Check whether a single logical dependency (by name or import_name) is installed."
    ),
)
async def check_single_dependency(
    name: str = Query(
        ...,
        description="Package name or import_name, e.g. 'beautifulsoup4' or 'bs4'.",
    ),
) -> Dict[str, object]:
    normalized = name.strip().lower()

    # Try to match against our known deps
    for dep in RECOMMENDED_DEPS:
        if dep.name.lower() == normalized or dep.import_name.lower() == normalized:
            status_dict = _build_dep_status(dep)
            return {
                "dependency": status_dict,
                "suggested_command": status_dict["recommendation"]
                if not status_dict["installed"]
                else None,
            }

    # If not in our curated list, fall back to a generic import probe
    installed = _probe_import(normalized)
    if installed:
        return {
            "dependency": {
                "name": normalized,
                "import_name": normalized,
                "installed": True,
                "optional": True,
                "used_for": "Unknown (not in curated list).",
                "recommendation": f"pip install {normalized}",
            },
            "suggested_command": None,
        }

    # Not installed and not in curated list
    return {
        "dependency": {
            "name": normalized,
            "import_name": normalized,
            "installed": False,
            "optional": True,
            "used_for": "Unknown (not in curated list).",
            "recommendation": f"pip install {normalized}",
        },
        "suggested_command": f"pip install {normalized}",
    }


@router.get(
    "/missing",
    summary="List missing dependencies only",
    description="Convenience endpoint: just show missing deps and pip commands.",
)
async def get_missing_dependencies() -> Dict[str, object]:
    deps = [_build_dep_status(dep) for dep in RECOMMENDED_DEPS]

    missing_required = [d for d in deps if not d["installed"] and not d["optional"]]
    missing_optional = [d for d in deps if not d["installed"] and d["optional"]]

    required_cmd = None
    optional_cmd = None
    if missing_required:
        required_pkgs = " ".join(d["name"] for d in missing_required)
        required_cmd = f"pip install {required_pkgs}"
    if missing_optional:
        optional_pkgs = " ".join(d["name"] for d in missing_optional)
        optional_cmd = f"pip install {optional_pkgs}"

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "suggested_commands": {
            "required": required_cmd,
            "optional": optional_cmd,
        },
    }
