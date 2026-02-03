import sys
from pathlib import Path
import json

# Set up path for app module imports
_services_api = Path(__file__).parent.parent / "services" / "api"
if str(_services_api) not in sys.path:
    sys.path.insert(0, str(_services_api))

# Import the adapter function from replay harness
from services.api.tools.public_training.replay_wholesaling import run_wholesaling_pipeline

def test_golden_cases():
    cases_path = Path("tests/golden/wholesaling_cases.json")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    for c in cases:
        pred = run_wholesaling_pipeline(c["lead"])
        exp = c["expect"]

        for k, v in exp.items():
            assert pred.get(k) == v, f"{c['name']} failed: expected {k}={v}, got {pred.get(k)}"
