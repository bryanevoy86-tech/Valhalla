"""Keep legacy admin and session-token routes fail closed by default."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test-only")

from fastapi import HTTPException  # noqa: E402
from app.core.dependencies import require_auth, require_builder_key, require_prime_control_key  # noqa: E402
from app.core.settings import settings  # noqa: E402


class AuthBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.old_session = settings.SESSION_TOKEN_DEV
        self.old_builder = settings.BUILDER_KEY
        self.old_env = settings.env

    def tearDown(self):
        settings.SESSION_TOKEN_DEV = self.old_session
        settings.BUILDER_KEY = self.old_builder
        settings.env = self.old_env

    def test_missing_session_secret_is_not_public_api(self):
        settings.SESSION_TOKEN_DEV = None
        settings.env = "dev"
        with patch.dict(os.environ, {"VALHALLA_ALLOW_UNAUTH_DEV": ""}):
            with self.assertRaises(HTTPException) as ctx:
                require_auth(x_session_token=None)
            self.assertEqual(ctx.exception.status_code, 503)

    def test_explicit_development_override_never_applies_to_production(self):
        settings.SESSION_TOKEN_DEV = None
        with patch.dict(os.environ, {"VALHALLA_ALLOW_UNAUTH_DEV": "true"}):
            settings.env = "dev"
            self.assertTrue(require_auth(x_session_token=None))
            settings.env = "production"
            with self.assertRaises(HTTPException) as ctx:
                require_auth(x_session_token=None)
            self.assertEqual(ctx.exception.status_code, 503)

    def test_constant_time_session_guard(self):
        settings.SESSION_TOKEN_DEV = "test-session-secret"
        self.assertTrue(require_auth(x_session_token="test-session-secret"))
        with self.assertRaises(HTTPException) as ctx:
            require_auth(x_session_token="wrong")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_builder_key_must_exist_and_match(self):
        settings.BUILDER_KEY = ""
        with self.assertRaises(HTTPException) as ctx:
            require_builder_key(x_api_key=None)
        self.assertEqual(ctx.exception.status_code, 503)
        settings.BUILDER_KEY = "test-builder-secret"
        with self.assertRaises(HTTPException) as ctx:
            require_builder_key(x_api_key="wrong")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertTrue(require_builder_key(x_api_key="test-builder-secret"))


    def test_prime_credentials_must_be_distinct(self):
        settings.BUILDER_KEY = "builder-test-key"
        settings.SESSION_TOKEN_DEV = "session-test-key"
        with patch.dict(os.environ, {
            "VALHALLA_FACTORY_KEY": "factory-test-key",
            "VALHALLA_OWNER_MANDATE_KEY": "mandate-test-key",
        }):
            for secret in (settings.BUILDER_KEY, settings.SESSION_TOKEN_DEV,
                           settings.jwt_secret, "factory-test-key", "mandate-test-key"):
                with self.subTest(secret_role=secret != settings.jwt_secret):
                    with patch.dict(os.environ, {"VALHALLA_PRIME_CONTROL_KEY": secret}):
                        with self.assertRaises(HTTPException) as ctx:
                            require_prime_control_key(x_prime_control_key=secret)
                        self.assertEqual(ctx.exception.status_code, 503)
            with patch.dict(os.environ, {"VALHALLA_PRIME_CONTROL_KEY": "independent-prime-test"}):
                self.assertTrue(require_prime_control_key(x_prime_control_key="independent-prime-test"))

    def test_non_ascii_wrong_credentials_are_denied_not_server_errors(self):
        settings.BUILDER_KEY = "builder-test-key"
        settings.SESSION_TOKEN_DEV = "session-test-key"
        for guard, kwargs in (
            (require_builder_key, {"x_api_key": "é"}),
            (require_auth, {"x_session_token": "é"}),
        ):
            with self.subTest(guard=guard.__name__):
                with self.assertRaises(HTTPException) as ctx:
                    guard(**kwargs)
                self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
