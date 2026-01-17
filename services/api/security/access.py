from fastapi import Header, HTTPException


def require_level(level: int):
    """
    Level 1: Password OR Fingerprint
    Level 2: Password + Fingerprint + Token
    Level 2.5: Password + Fingerprint
    Level 3: Password + Fingerprint + Retina + Token
    """

    def checker(
        password: str | None = Header(default=None, alias="X-Password"),
        fingerprint: str | None = Header(default=None, alias="X-Fingerprint"),
        retina: str | None = Header(default=None, alias="X-Retina"),
        token: str | None = Header(default=None, alias="X-Token"),
    ):
        ok = lambda x: x is not None and len(x) >= 6
        if level == 1:
            if not (ok(password) or ok(fingerprint)):
                raise HTTPException(401, "Level1 requires Password OR Fingerprint")
        elif level == 2:
            if not (ok(password) and ok(fingerprint) and ok(token)):
                raise HTTPException(401, "Level2 requires Password + Fingerprint + Token")
        elif level == 25:
            if not (ok(password) and ok(fingerprint)):
                raise HTTPException(401, "Level2.5 requires Password + Fingerprint")
        elif level == 3:
            if not (ok(password) and ok(fingerprint) and ok(retina) and ok(token)):
                raise HTTPException(401, "Level3 requires Password + Fingerprint + Retina + Token")
        else:
            raise HTTPException(403, "Unknown access level")

    return checker
