# Intervention Threshold Rules (INTERNAL)

## Rule
I do not intervene unless the system violates clear thresholds.
This prevents emotional overrides and premature tuning.

## Default thresholds (sandbox)
- Export cadence deviates by >20% for >5 cycles
- Duplicate artifacts detected >0
- Error rate >2% sustained over 20 cycles
- Memory increases monotonically over 60 minutes (creep)
- Guard violation attempt (immediate stop)

## Override protocol
If I override a system decision:
1) I write why
2) I log the metric that triggered it
3) I wait 12–24 hours before irreversible changes (unless safety)
