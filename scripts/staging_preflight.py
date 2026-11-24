"""Offline checks before opening an isolated Valhalla staging process."""
import argparse
import os
import re
from urllib.parse import urlsplit

PRODUCTION_HOSTS = {"valhalla-api-ha6a.onrender.com"}
STAGING_DATABASE = "valhalla_staging"
STRIPE_SECRETS = ("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", "VALHALLA_STRIPE_READBACK_KEY")
OPERATOR_KEYS = ("VALHALLA_OWNER_MANDATE_KEY", "VALHALLA_PRIME_CONTROL_KEY", "VALHALLA_FACTORY_KEY")
LIVE_SETTINGS = ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "VALHALLA_STRIPE_RECURRING_WRITE_KEY",
                 "VALHALLA_STRIPE_DELIVERY_SCOPE", "VALHALLA_STRIPE_BANK_BOOKING_SCOPE")
KNOWN_EXISTING_DATABASE_HOSTS = {"dpg-d90l1mv7f7vs73cod580-a", "dpg-d9ek3oj7uimc73fooes0-a"}
DISABLED_FLAGS = ("VALHALLA_STRIPE_DELIVERY_ENABLED", "VALHALLA_STRIPE_BANK_BOOKING_ENABLED",
                  "VALHALLA_STRIPE_RECURRING_WORKER_ENABLED", "RESET_OWNER_PASSWORD")
SPECIALISTS = {"odin": "valhalla_stage_odin", "njord": "valhalla_stage_njord"}
SPECIALIST_PRIVATE = "VALHALLA_PANTHEON_WORKER_PRIVATE_KEY"
ENROLLMENT_PRIVATE = "VALHALLA_PANTHEON_ENROLLMENT_PRIVATE_KEY"
ENROLLMENT_PUBLIC = "VALHALLA_PANTHEON_ENROLLMENT_PUBLIC_KEY"


def _https_origin(value):
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname in PRODUCTION_HOSTS:
        return False
    if not re.fullmatch(r"[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?", parsed.hostname):
        return False
    expected = "https://" + parsed.hostname + (f":{port}" if port is not None else "")
    return value == expected


def _matches_database(env):
    try:
        url = urlsplit(env.get("DATABASE_URL", ""))
        port = url.port
    except ValueError:
        return False
    expected_host = env.get("VALHALLA_STAGING_DATABASE_HOST", "")
    return (
        bool(re.fullmatch(r"dpg-[a-z0-9-]+", expected_host))
        and expected_host not in KNOWN_EXISTING_DATABASE_HOSTS
        and url.scheme in {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"}
        and url.hostname == expected_host and port in {None, 5432}
        and url.path == "/" + STAGING_DATABASE and bool(url.username and url.password)
        and not url.query and not url.fragment
    )


def check(env, role):
    failures = []
    if env.get("APP_ENV") != "staging" or env.get("ENV", "staging") != "staging":
        failures.append("stage environment labels must be staging")
    api = env.get("VALHALLA_STAGING_API_ORIGIN", "")
    if not _https_origin(api):
        failures.append("approved staging API origin is invalid")
    if any(env.get(key) for key in LIVE_SETTINGS) or any(
        env.get(key, "").lower() not in {"", "0", "false", "off"} for key in DISABLED_FLAGS
    ):
        failures.append("live effects or startup reset configuration must be absent")
    database_matches = _matches_database(env)
    if role in {"api", "worker", "refund-writer", *SPECIALISTS} and not database_matches:
        failures.append("staging database target does not match the approved private host and database")
    reviewer_key = env.get("VALHALLA_LOKI_REVIEWER_KEY")
    if role == "api":
        keys = [env.get(key) for key in (*OPERATOR_KEYS, "VALHALLA_JWT_SECRET", "VALHALLA_LOKI_REVIEWER_KEY")]
        if not all(keys) or len(set(keys)) != len(keys) or not env.get("VALHALLA_LOKI_REVIEWER_ID", "").strip():
            failures.append("API signing, operator and reviewer keys must be distinct and the reviewer identified")
        preview = env.get("VALHALLA_PREVIEW_ORIGIN", "")
        if not _https_origin(preview) or preview == api or env.get("CORS_ALLOWED_ORIGINS") != preview:
            failures.append("CORS must equal the separate approved browser origin")
        if env.get("VALHALLA_STRIPE_EVENT_MODE") != "test":
            failures.append("Stripe event mode must be test")
        readback = env.get("VALHALLA_STRIPE_READBACK_ENABLED", "")
        if readback not in {"", "0", "1"} or env.get(STRIPE_SECRETS[1], "").startswith(("sk_live_", "rk_live_")):
            failures.append("Stripe readback configuration must be test-only")
        if readback == "1":
            if (not env.get(STRIPE_SECRETS[0], "").startswith("whsec_")
                    or not env.get(STRIPE_SECRETS[1], "").startswith("rk_test_")
                    or not env.get("VALHALLA_STRIPE_ACCOUNT_ID", "").startswith("acct_")):
                failures.append("sandbox signing secret, restricted test key and account identity are required")
    if role != "api" and any(env.get(key) for key in (*STRIPE_SECRETS, "VALHALLA_STRIPE_READBACK_ENABLED",
                                                    "VALHALLA_GMAIL_COMMISSIONING_ACCESS_TOKEN")):
        failures.append("provider credentials and readback settings belong only on the staging API")
    if env.get("VALHALLA_STRIPE_SANDBOX_REFUND_ENABLED") == "1":
        if (role not in {"api", "refund-writer"}
                or not re.fullmatch(r"[0-9a-f]{64}", env.get("VALHALLA_STRIPE_SANDBOX_REFUND_SCOPE", ""))
                or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:\.[a-z]+)?",
                                    env.get("VALHALLA_STRIPE_SANDBOX_REFUND_API_VERSION", ""))):
            failures.append("sandbox refund requires the exact authorized scope and API version")
    if role != "refund-writer" and env.get("VALHALLA_STRIPE_SANDBOX_REFUND_WRITE_KEY"):
        failures.append("the restricted refund writer key belongs only in its isolated process")
    if role == "refund-writer":
        if (not env.get("VALHALLA_STRIPE_SANDBOX_REFUND_WRITE_KEY", "").startswith("rk_test_")
                or env.get("VALHALLA_STRIPE_SANDBOX_REFUND_ENABLED") != "1"
                or env.get("VALHALLA_STRIPE_EVENT_MODE") != "test"
                or not env.get("VALHALLA_STRIPE_ACCOUNT_ID", "").startswith("acct_")
                or reviewer_key or any(env.get(key) for key in (
                    *OPERATOR_KEYS, "PLAID_SECRET", "VALHALLA_PLAID_READ_ACCESS_TOKEN",
                ))):
            failures.append("refund writer requires separate test-only credentials and an approved enablement")
    if role == "worker" and (reviewer_key or any(env.get(key) for key in OPERATOR_KEYS)):
        failures.append("operating worker must have no reviewer, owner, Prime or Factory keys")
    if role in SPECIALISTS:
        if database_matches and urlsplit(env["DATABASE_URL"]).username != SPECIALISTS[role]:
            failures.append("specialist database login must match the exact role")
        if (any(env.get(key) for key in (*OPERATOR_KEYS, "VALHALLA_LOKI_REVIEWER_KEY", ENROLLMENT_PRIVATE,
                                        "VALHALLA_OWNER_PASSWORD", "PLAID_SECRET", "VALHALLA_PLAID_READ_ACCESS_TOKEN",
                                        "VALHALLA_PANTHEON_REGISTRAR_KEY", "VALHALLA_BUILDER_KEY",
                                        "SMTP_PASS", "VALHALLA_STRIPE_SANDBOX_REFUND_ENABLED"))
                or not re.fullmatch(r"[0-9a-f]{64}", env.get(SPECIALIST_PRIVATE, ""))
                or not re.fullmatch(r"[0-9a-f]{64}", env.get(ENROLLMENT_PUBLIC, ""))):
            failures.append("specialist requires its signing key and public enrollment verifier without privileged credentials")
    elif env.get(SPECIALIST_PRIVATE):
        failures.append("specialist signing keys belong only in the corresponding specialist worker")
    if role != "api" and env.get(ENROLLMENT_PRIVATE):
        failures.append("enrollment signing key belongs only on the staging API")
    if role == "reviewer":
        if env.get("VALHALLA_LOKI_QUEUE_URL") != api or not api:
            failures.append("reviewer queue must equal the approved staging API origin")
        if not env.get("VALHALLA_LOKI_REVIEWER_KEY") or not env.get("VALHALLA_LOKI_REVIEWER_ID", "").strip():
            failures.append("independent reviewer key and identity are required")
        if any(env.get(key) for key in (*OPERATOR_KEYS, "DATABASE_URL", "VALHALLA_JWT_SECRET",
                                        "VALHALLA_OWNER_PASSWORD")):
            failures.append("reviewer must have no database, owner, Prime or Factory credentials")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("api", "worker", "reviewer", "refund-writer", *SPECIALISTS))
    args = parser.parse_args()
    failures = check(os.environ, args.role)
    for failure in failures:
        print(f"Staging preflight blocked: {failure}")
    if failures:
        return 2
    print(f"Staging preflight passed for {args.role}. External acceptance and owner approval remain separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
