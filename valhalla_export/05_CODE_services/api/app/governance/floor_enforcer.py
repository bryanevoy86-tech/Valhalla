"""Floor control enforcement - ensure values don't fall below thresholds."""


def enforce_floor(actual: float, target: float, name: str = "Value") -> dict:
    """
    Enforce a floor/threshold.
    
    Args:
        actual: The actual value
        target: The minimum acceptable value
        name: Name of the value being checked (for logging)
    
    Returns:
        dict with enforcement decision and metadata
    """
    if actual < target:
        return {
            "decision": "BLOCK",
            "reason": f"{name} {actual} is below floor {target}",
            "shortfall": target - actual,
            "severity": "high" if actual < target * 0.5 else "medium"
        }
    
    return {
        "decision": "ALLOW",
        "reason": f"{name} {actual} meets floor {target}",
        "buffer": actual - target,
        "buffer_percent": ((actual - target) / target * 100) if target > 0 else 0
    }


def check_multiple_floors(values: dict, floors: dict) -> dict:
    """
    Check multiple values against their floors.
    
    Args:
        values: dict of {name: value}
        floors: dict of {name: floor_value}
    
    Returns:
        dict with overall decision and per-item results
    """
    results = {}
    all_pass = True
    
    for name, floor_value in floors.items():
        actual = values.get(name, 0)
        result = enforce_floor(actual, floor_value, name)
        results[name] = result
        
        if result["decision"] == "BLOCK":
            all_pass = False
    
    return {
        "decision": "ALLOW" if all_pass else "BLOCK",
        "all_pass": all_pass,
        "checks": results
    }


def get_buffer_percent(actual: float, target: float) -> float:
    """Get the buffer as a percentage above the floor."""
    if target <= 0:
        return 0
    return max(0, (actual - target) / target * 100)
