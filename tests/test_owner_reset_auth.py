"""Owner recovery route must NEVER become public when setup key is absent.

These tests import the real route code with inert model/db stubs, and do not
perform any account modification or use real credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "services/api/app/routers/auth_weweb.py"


def _stub(name: str, **attributes):
    mod = types.ModuleType(name)
    for field, value in attributes.items():
        setattr(mod, field, value)
    return mod


class OwnerResetGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = _stub("app")
        app.__path__ = []
        core = _stub("app.core")
        core.__path__ = []
        db = _stub("app.core.db", get_db=lambda: None)
        users = _stub("app.users")
        users.__path__ = []
        models = _stub(
            "app.users.models",
            UserProfile=type("UserProfile", (), {}),
            AccountSettings=type("AccountSettings", (), {}),
        )
        with patch.dict(sys.modules, {
            "app": app,
            "app.core": core,
            "app.core.db": db,
            "app.users": users,
            "app.users.models": models,
        }):
            cls.fn = staticmethod(runpy.run_path(str(MODULE))["admin_reset_password"])

    @staticmethod
    def _request(token: str = ""):
        return types.SimpleNamespace(headers={"X-Setup-Token": token} if token else {})

    def test_reset_disabled_even_when_secret_exists(self):
        with patch.dict(os.environ, {
            "RESET_OWNER_PASSWORD": "false",
            "VALHALLA_SETUP_TOKEN": "secret-set",
        }):
            with self.assertRaises(HTTPException) as caught:
                self.fn(self._request("secret-set"), db=None)
            self.assertEqual(caught.exception.status_code, 403)

    def test_missing_setup_secret_fails_closed_when_reset_enabled(self):
        with patch.dict(os.environ, {
            "RESET_OWNER_PASSWORD": "true",
            "VALHALLA_SETUP_TOKEN": "",
        }):
            with self.assertRaises(HTTPException) as caught:
                self.fn(self._request(), db=None)
            self.assertEqual(caught.exception.status_code, 503)

    def test_missing_or_wrong_token_denied(self):
        with patch.dict(os.environ, {
            "RESET_OWNER_PASSWORD": "true",
            "VALHALLA_SETUP_TOKEN": "secret-set",
        }):
            for request in (self._request(), self._request("not-the-secret")):
                with self.assertRaises(HTTPException) as caught:
                    self.fn(request, db=None)
                self.assertEqual(caught.exception.status_code, 401)

    def test_valid_setup_token_still_requires_owner_config(self):
        with patch.dict(os.environ, {
            "RESET_OWNER_PASSWORD": "true",
            "VALHALLA_SETUP_TOKEN": "secret-set",
            "VALHALLA_OWNER_EMAIL": "",
            "VALHALLA_OWNER_PASSWORD": "",
        }):
            with self.assertRaises(HTTPException) as caught:
                self.fn(self._request("secret-set"), db=None)
            self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
