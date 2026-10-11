from app.core_flags.flags import is_enabled

LAUNCH_ROUTER_NAMES = ["auth", "users", "leads", "deals", "offers", "buyers", "contracts", "health", "audit"]

# Legacy-compatible aliases retained for existing import contracts.
LAUNCH_ROUTERS = LAUNCH_ROUTER_NAMES
ALWAYS_ALLOW_PATH_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
)
LAUNCH_ALLOW_PATH_FRAGMENTS = (
    "health",
)
FEATURE_LOCKS = {}

def get_active_routers():
    return sorted(LAUNCH_ROUTER_NAMES)

def route_allowed(route):
    if route.name in LAUNCH_ROUTER_NAMES:
        return True
    return False


def classify_route(path: str) -> str:
    lower_path = (path or "").lower()
    if lower_path.startswith(ALWAYS_ALLOW_PATH_PREFIXES):
        return "always_allow"
    if any(fragment in lower_path for fragment in LAUNCH_ALLOW_PATH_FRAGMENTS):
        return "allow_fragment"
    return "managed"
