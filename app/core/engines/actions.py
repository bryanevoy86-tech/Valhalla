from dataclasses import dataclass


@dataclass(frozen=True)
class EngineAction:
    """
    An EngineAction describes what the engine is attempting to do.
    'real_world_effect' means irreversible external side-effects:
      - outreach (sms/email/calls)
      - sending deals to buyers
      - contract signing flows
      - payment or money movement
      - broker execution (trading)
    """
    name: str
    real_world_effect: bool = False


# Common actions
READ_ONLY = EngineAction(name="READ_ONLY", real_world_effect=False)
COMPUTE = EngineAction(name="COMPUTE", real_world_effect=False)

OUTREACH = EngineAction(name="OUTREACH", real_world_effect=True)
DISPOSITION_SEND = EngineAction(name="DISPOSITION_SEND", real_world_effect=True)
CONTRACT_SEND = EngineAction(name="CONTRACT_SEND", real_world_effect=True)

TRADING_SIGNAL = EngineAction(name="TRADING_SIGNAL", real_world_effect=False)  # advisory ok
TRADING_EXECUTE = EngineAction(name="TRADING_EXECUTE", real_world_effect=True)  # never in sandbox
