import json
from pathlib import Path

# Import the adapter function from replay harness (or move it to a shared module)
from services.api.tools.public_training.replay_wholesaling import run_wholesaling_pipeline

def test_golden_cases():
    cases_path = Path("tests/golden/wholesaling_cases.json")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    for c in cases:
        pred = run_wholesaling_pipeline(c["lead"])
        exp = c["expect"]

        for k, v in exp.items():
            assert pred.get(k) == v, f"{c['name']} failed: expected {k}={v}, got {pred.get(k)}"
