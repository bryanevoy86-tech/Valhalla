#!/usr/bin/env python3
"""Read CanadaBuys catalogue metadata for Foundry research without enrolling a source."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

PORTAL = "https://open.canada.ca/data/en"
LICENCE = "https://open.canada.ca/en/open-government-licence-canada/"
DATASETS = {
    "awards": "a1acb126-9ce8-40a9-b889-5da2b1dd20cb",
    "contract-history": "4fe645a1-ffcd-40c1-9385-2c771be956a4",
}
LIMIT = 1_048_576


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def snapshot(name, raw, observed_at):
    if len(raw) > LIMIT:
        raise ValueError("Catalogue response exceeds the size limit")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ValueError("Catalogue did not return successful metadata")
    data = payload.get("result")
    if not isinstance(data, dict) or data.get("id") != DATASETS[name] or data.get("state") != "active":
        raise ValueError("Catalogue dataset identity or current state is unverified")
    if data.get("license_id") != "ca-ogl-lgo":
        raise ValueError("Catalogue did not confirm the expected Open Government Licence")
    updated = data.get("metadata_modified")
    if not isinstance(updated, str):
        raise ValueError("Catalogue modification time is unavailable")
    modified = datetime.fromisoformat(updated)
    if modified.tzinfo is None:
        modified = modified.replace(tzinfo=timezone.utc)
    if modified > observed_at:
        raise ValueError("Catalogue modification time is future-dated")
    return {
        "basis": "OFFICIAL_PUBLIC_CATALOGUE_METADATA",
        "dataset": name, "dataset_id": DATASETS[name],
        "citation": f"{PORTAL}/dataset/{DATASETS[name]}",
        "attribution": "Contains information licensed under the Open Government Licence – Canada.",
        "licence": LICENCE, "retrieved_at": observed_at.isoformat(),
        "metadata_modified": modified.isoformat(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_customer_demand": False, "source_enrolled": False,
        "external_action_authorized": False,
    }


def fetch(name):
    url = f"{PORTAL}/api/3/action/package_show?id={DATASETS[name]}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Valhalla-Foundry-Research/1.0"})
    with build_opener(ProxyHandler({}), NoRedirects()).open(request, timeout=8) as response:
        if response.geturl() != url or response.headers.get_content_type() != "application/json":
            raise ValueError("Unverified catalogue response content or origin")
        return snapshot(name, response.read(LIMIT + 1), datetime.now(timezone.utc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=DATASETS)
    args = parser.parse_args()
    try:
        result = fetch(args.dataset)
    except (OSError, URLError, ValueError) as exc:
        parser.exit(2, f"Research snapshot unavailable: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
