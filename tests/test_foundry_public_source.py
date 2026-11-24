import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.foundry_public_source import DATASETS, LIMIT, fetch, snapshot


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 24, tzinfo=timezone.utc)
        self.payload = {"success": True, "result": {
            "id": DATASETS["awards"], "state": "active", "license_id": "ca-ogl-lgo",
            "metadata_modified": "2026-11-23T10:00:00", "contact": "excluded from output",
        }}

    def test_snapshot_is_attributed_context_only(self):
        raw = json.dumps(self.payload).encode()
        result = snapshot("awards", raw, self.now)
        self.assertIn("Open Government Licence", result["attribution"])
        self.assertFalse(result["verified_customer_demand"])
        self.assertFalse(result["source_enrolled"])
        self.assertFalse(result["external_action_authorized"])
        self.assertNotIn("contact", result)

    def test_rejects_unexpected_identity_licence_date_and_size(self):
        for key, value in (("id", "another-id"), ("state", "deleted"), ("license_id", None),
                           ("metadata_modified", "2026-11-25T00:00:00Z")):
            with self.subTest(key=key):
                data = {**self.payload, "result": {**self.payload["result"], key: value}}
                with self.assertRaises(ValueError):
                    snapshot("awards", json.dumps(data).encode(), self.now)
        with self.assertRaises(ValueError):
            snapshot("awards", b" " * (LIMIT + 1), self.now)

    @patch("scripts.foundry_public_source.build_opener")
    def test_fetch_requests_only_pinned_origin_and_rejects_other_response_urls(self, opener):
        response = opener.return_value.open.return_value.__enter__.return_value
        response.headers.get_content_type.return_value = "application/json"
        response.geturl.return_value = "https://example.invalid/replaced"
        with self.assertRaises(ValueError):
            fetch("awards")
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, (
            "https://open.canada.ca/data/en/api/3/action/package_show?id=" + DATASETS["awards"]
        ))
        response.read.assert_not_called()
