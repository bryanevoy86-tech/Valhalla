import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize(
    ("role", "trial_flag", "database_login", "mimir_lane", "accepted"),
    [
        ("MIMIR", "1", "stage", "MIMIR", True),
        ("MIMIR", "0", "stage", "MIMIR", False),
        ("MIMIR", "1", "stage", "ODIN", False),
        ("THOR", "1", "stage", "MIMIR", False),
        ("ODIN", "1", "valhalla_stage_odin", "", True),
        ("ODIN", "1", "valhalla_stage_njord", "", False),
        ("NJORD", "1", "valhalla_stage_njord", "", True),
        ("NJORD", "", "valhalla_stage_njord", "", False),
    ],
)
def test_staging_worker_reaches_poll_only_under_approved_role_configuration(
    monkeypatch, role, trial_flag, database_login, mimir_lane, accepted
):
    cron = Path(__file__).resolve().parents[1] / "tools/cron"
    monkeypatch.syspath_prepend(str(cron))
    spec = importlib.util.spec_from_file_location("test_pantheon_worker", cron / "pantheon_worker.py")
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)

    monkeypatch.delenv("VALHALLA_OWNER_PASSWORD", raising=False)
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("VALHALLA_STAGING_API_ORIGIN", "https://staging-api.example.invalid")
    monkeypatch.setenv("VALHALLA_STAGING_DATABASE_HOST", "dpg-stage-a")
    monkeypatch.setenv("DATABASE_URL", f"postgresql://{database_login}:synthetic@dpg-stage-a/valhalla_staging")
    monkeypatch.setenv("VALHALLA_PANTHEON_WORKER_ENABLED", "1")
    monkeypatch.setenv("VALHALLA_STAGING_TRIAL_ENABLED", trial_flag)
    monkeypatch.setenv("VALHALLA_STAGING_PANTHEON_ROLE", mimir_lane)
    if role in {"ODIN", "NJORD"}:
        monkeypatch.setenv("VALHALLA_PANTHEON_WORKER_PRIVATE_KEY", "a" * 64)
        monkeypatch.setenv("VALHALLA_PANTHEON_ENROLLMENT_PUBLIC_KEY", "b" * 64)

    monkeypatch.setattr(sys, "argv", ["pantheon_worker.py", "--role", role, "--once"])
    monkeypatch.setattr(worker.signal, "signal", Mock())
    mocked_poll = Mock(return_value=0)
    monkeypatch.setattr(worker, "poll", mocked_poll)
    if accepted:
        assert worker.main() == 0
        mocked_poll.assert_called_once()
    else:
        with pytest.raises(SystemExit) as error:
            worker.main()
        assert error.value.code == 2
        mocked_poll.assert_not_called()
