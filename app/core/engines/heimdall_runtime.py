from app.core.engines.heimdall_authority import HeimdallEngineAuthority
from app.core.engines.runtime import engine_state_store

heimdall_engine_authority = HeimdallEngineAuthority(store=engine_state_store)
