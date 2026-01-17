"""
Diagnostic: Check for duplicate mapped class names in SQLAlchemy registry.
This detects the ChildProfile collision issue before it crashes.

Run from services/api/:
    python scripts/diag_registry_check.py
"""
from app.core.db import Base


def main():
    # Touch mappers and print all mapped class names
    mapped = []
    for m in Base.registry.mappers:
        cls = m.class_
        mapped.append(f"{cls.__module__}.{cls.__name__}")

    # quick check for duplicates by class name
    by_name = {}
    for m in Base.registry.mappers:
        n = m.class_.__name__
        by_name.setdefault(n, 0)
        by_name[n] += 1

    dupes = {k: v for k, v in by_name.items() if v > 1}

    print("MAPPED CLASSES:", len(mapped))
    if dupes:
        print("DUPLICATE CLASS NAMES FOUND:")
        for name, count in sorted(dupes.items()):
            print(f"  - {name} ({count} times)")
        raise SystemExit(2)
    else:
        print("✓ OK: No duplicate mapped class names.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
