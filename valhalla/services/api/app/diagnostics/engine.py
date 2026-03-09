# app/diagnostics/engine.py
from pydantic import BaseModel
from typing import List
import importlib

class DiagnosticCheck(BaseModel):
    name: str
    ok: bool
    detail: str | None = None

class DiagnosticSummary(BaseModel):
    overall_ok: bool
    checks: List[DiagnosticCheck]

class DiagnosticsEngine:
    @staticmethod
    async def run():
        checks: List[DiagnosticCheck] = []

        # Check 1: main imports
        try:
            importlib.import_module("app.main")
            checks.append(DiagnosticCheck(name="main_import", ok=True))
        except Exception as e:
            checks.append(DiagnosticCheck(name="main_import", ok=False, detail=str(e)))

        # Check 2: router integrity
        try:
            importlib.import_module("app.api.v1.root")
            checks.append(DiagnosticCheck(name="router_root", ok=True))
        except Exception as e:
            checks.append(DiagnosticCheck(name="router_root", ok=False, detail=str(e)))

        # Check 3: telemetry exists
        try:
            importlib.import_module("app.telemetry.feed")
            checks.append(DiagnosticCheck(name="telemetry_feed", ok=True))
        except Exception as e:
            checks.append(DiagnosticCheck(name="telemetry_feed", ok=False, detail=str(e)))

        # Pass/fail
        overall_ok = all(c.ok for c in checks)
        return DiagnosticSummary(overall_ok=overall_ok, checks=checks)
