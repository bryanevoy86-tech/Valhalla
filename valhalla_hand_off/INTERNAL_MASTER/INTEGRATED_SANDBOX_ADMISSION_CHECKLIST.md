# Integrated Sandbox Admission Checklist (INTERNAL)

Rule: NO ENGINE enters integrated sandbox until it passes SOLO sandbox.

## SOLO PASS REQUIREMENTS (must be true)
- Guard enforcement proven (DRY-RUN must be ON; outbound must be OFF)
- Ingest works with real-ish data formats
- Score distribution sane (not pinned)
- Edge-cases do not crash the system
- Stable run time threshold met (minimum agreed duration)
- Outputs are artifacts only (no external actions)

## INTEGRATED ENTRY RULES
- Add engines one at a time (A+B, then A+B+C)
- No direct cross-engine mutation (engines don't write into each other's state)
- Interactions allowed only via:
  - shared scheduler budgets
  - simulated capital pool
  - global caps
  - priority arbitration

## INTEGRATED PASS REQUIREMENTS
- No cadence drift
- No resource creep (memory/cpu stable)
- No export collisions
- Clear attribution in reports (which engine consumed what)
- No guard violations under load
