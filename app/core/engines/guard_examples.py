from app.core.engines.actions import OUTREACH, COMPUTE
from app.core.engines.guard_runtime import enforce_engine


def example_compute():
    enforce_engine("wholesaling", COMPUTE)
    return "computed safely"


def example_outreach():
    enforce_engine("wholesaling", OUTREACH)
    return "outreach allowed only if ACTIVE"
