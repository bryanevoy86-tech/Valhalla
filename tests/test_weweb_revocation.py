"""Real SQLAlchemy storage and WeWeb session tests after process-style restart.

Uses disposable SQLite, not a live user table or real credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "CI-only-not-production")

models_package = types.ModuleType("app.models")
models_package.__path__ = [str(ROOT / "services/api/app/models")]
sys.modules["app.models"] = models_package

from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from app.models.auth_revocations import RevokedAccessToken  # noqa: E402
from app.security.token_revocation import (  # noqa: E402
    is_access_token_revoked,
    revoke_access_token,
)
from app.routers import auth_weweb  # noqa: E402


class PersistentWeWebRevocationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        RevokedAccessToken.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.payload = {
            "user_id": 4,
            "jti": "test-session-randomized-id-1234",
            "exp": int(time.time()) + 3600,
            "sub": "user@example.invalid",
        }
        self.mock_auth = types.SimpleNamespace(
            jwt_decode=lambda token, secret: dict(self.payload),
            SETTINGS=types.SimpleNamespace(jwt_secret="CI-only-not-production"),
        )

    def tearDown(self):
        self.engine.dispose()

    def test_logout_persists_revocation_across_fresh_sessions(self):
        session_a = self.sessions()
        try:
            with patch.object(auth_weweb, "_auth_runtime", return_value=self.mock_auth):
                current = auth_weweb.get_current_user(token="test-token", db=session_a)
                self.assertEqual(current["user_id"], 4)
                result = auth_weweb.logout(current_user=current, db=session_a)
                self.assertTrue(result["ok"])
        finally:
            session_a.close()

        # A second session simulates a fresh worker/process talking to the DB.
        session_b = self.sessions()
        try:
            with patch.object(auth_weweb, "_auth_runtime", return_value=self.mock_auth):
                with self.assertRaises(HTTPException) as caught:
                    auth_weweb.get_current_user(token="test-token", db=session_b)
                self.assertEqual(caught.exception.status_code, 401)
            stored = session_b.query(RevokedAccessToken).all()
            self.assertEqual(len(stored), 1)
            self.assertNotEqual(stored[0].jti_sha256, self.payload["jti"])
            self.assertEqual(len(stored[0].jti_sha256), 64)
        finally:
            session_b.close()

    def test_duplicate_revocation_does_not_duplicate_table_row(self):
        db = self.sessions()
        try:
            self.assertTrue(revoke_access_token(db, self.payload))
            db.commit()
            self.assertFalse(revoke_access_token(db, self.payload))
            db.commit()
            self.assertTrue(is_access_token_revoked(db, self.payload))
            self.assertEqual(db.query(RevokedAccessToken).count(), 1)
        finally:
            db.close()

    def test_missing_table_blocks_access_instead_of_reviving_token(self):
        RevokedAccessToken.__table__.drop(self.engine)
        db = self.sessions()
        try:
            with patch.object(auth_weweb, "_auth_runtime", return_value=self.mock_auth):
                with self.assertRaises(HTTPException) as caught:
                    auth_weweb.get_current_user(token="test-token", db=db)
                self.assertEqual(caught.exception.status_code, 503)
        finally:
            db.close()

    def test_malformed_token_identifiers_are_rejected(self):
        db = self.sessions()
        try:
            for changed in ({"jti": ""}, {"exp": 0}, {"user_id": "4"}):
                payload = dict(self.payload, **changed)
                with self.subTest(changed=changed):
                    with self.assertRaises(ValueError):
                        is_access_token_revoked(db, payload)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
