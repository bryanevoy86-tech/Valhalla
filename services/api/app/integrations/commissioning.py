"""Shared transport and narrowly selected Google Workspace metadata commissioning."""
from contextlib import contextmanager
from hashlib import sha256
import os
import re

import httpx
from fastapi import HTTPException


@contextmanager
def approved_reader(provider, origin, *config_suffixes, transport=None):
    # All destinations are fixed at call sites. Callers can never supply a host or credential.
    prefix = f"VALHALLA_{provider}_COMMISSIONING_"
    token = os.getenv(prefix + "ACCESS_TOKEN", "")
    settings = tuple(os.getenv(prefix + suffix, "") for suffix in config_suffixes)
    if (os.getenv(prefix + "ENABLED") != "1" or not re.fullmatch(r"[\x21-\x7e]{12,4096}", token)
            or not all(settings)):
        raise HTTPException(503, "Provider commissioning readback is disabled or unconfigured")
    with httpx.Client(base_url=origin, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                      timeout=5.0, follow_redirects=False, trust_env=False, transport=transport) as client:
        yield client, settings


def read_json(client, path, **query):
    try:
        response = client.get(path, params=query)
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {401, 403}:
            raise HTTPException(409, "Provider credential or consent rejected") from None
        if error.response.status_code == 404:
            raise HTTPException(409, "Configured provider resource was not found") from None
        raise HTTPException(503, "Provider readback unavailable") from None
    except (httpx.RequestError, ValueError):
        raise HTTPException(503, "Provider readback unavailable") from None
    if not isinstance(body, dict):
        raise HTTPException(409, "Provider evidence is not an object")
    return body


def commissioning_receipt(provider, reference, **evidence):
    return {"provider": provider, "resource_sha256": sha256(reference.encode()).hexdigest(), **evidence,
            "basis": "AUTHORIZED_TEST_RESOURCE_READBACK", "write_performed": False,
            "production_verified": False, "external_action_authorized": False}


def read_drive_fixture(*, transport=None):
    with approved_reader("GOOGLE_DRIVE", "https://www.googleapis.com", "FILE_ID", transport=transport) as (client, config):
        file_id, = config
        if not re.fullmatch(r"[A-Za-z0-9_-]{12,160}", file_id):
            raise HTTPException(503, "Exact test file configuration required")
        body = read_json(client, f"/drive/v3/files/{file_id}", fields="id,mimeType,trashed", supportsAllDrives="false")
        mime = body.get("mimeType")
        if body.get("id") != file_id or body.get("trashed") is not False or mime not in {
            "application/vnd.google-apps.document", "application/vnd.google-apps.spreadsheet",
        }:
            raise HTTPException(409, "Test Drive file metadata did not match the configured resource")
    return commissioning_receipt("GOOGLE_DRIVE", file_id, mime_type=mime, content_downloaded=False)
