from app.core_flags.flags import is_enabled

LAUNCH_ROUTERS = ["auth", "users", "leads", "deals", "offers", "buyers", "contracts", "health", "audit"]

def get_active_routers():
    return sorted(LAUNCH_ROUTERS)

def route_allowed(route):
    if route.name in LAUNCH_ROUTERS:
        return True
    return False
