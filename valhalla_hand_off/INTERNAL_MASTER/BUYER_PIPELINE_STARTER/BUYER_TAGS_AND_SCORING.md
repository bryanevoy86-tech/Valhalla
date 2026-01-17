# Buyer Tags & Reliability Scoring (v1)

## Tags (use consistently)
- buy_type: wholesale | wholetail | flip | hold | brrr | land | multifamily
- cash_or_finance: cash | finance | mixed
- close_speed_days: target close speed (e.g., 7, 14, 30)
- preferred_areas: semicolon-separated areas
- price_min / price_max: realistic band

## Reliability Score (0–100)
Start new buyers at 50. Adjust with behavior:

### Positive
- Responds within 24h: +5
- Provides proof of funds / pre-approval: +10
- Closes as agreed: +15
- No retrade attempts: +5

### Negative
- Ghosts after receiving packet: -10
- Retrade request: -15
- Cancels late: -20
- Repeated lowball / time-waste: -10

## Rule
High reliability buyers see deals first.
Low reliability buyers are deprioritized, not deleted.
