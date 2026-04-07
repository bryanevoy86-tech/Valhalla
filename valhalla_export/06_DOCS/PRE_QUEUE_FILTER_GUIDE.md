# SANDBOX Learning - Pre-Queue Filter Implementation Guide

## Goal
Add a pre-queue filter that blocks low-quality items BEFORE they enter approvals.

**Expected Result**: Approval rate jumps from 60% to 75%+, while reducing noise.

---

## Change Location
File: `services/api/app/routers/notify.py`

In the `queue_email()` function, where we catch the SANDBOX block (line ~87-102):

### Current Code (lines 87-102):
```python
        if e.status_code == 409 and isinstance(e.detail, dict) and "EngineBlocked" in str(e.detail.get("title", "")):
            # Create a pending action (preview only, not sent yet)
            pa = PendingAction(
                engine_name="wholesaling",
                action_type="OUTREACH_EMAIL",
                status=PendingActionStatus.PENDING.value,
                target=str(payload.to),
                subject=payload.subject,
                preview_text=f"[SANDBOX PREVIEW] To: {payload.to}\nSubject: {payload.subject}\n\n{payload.body_text}",
                payload_json=json.dumps(payload.model_dump()),
                reason=str(e.detail),
            )
            db.add(pa)

            db.add(SandboxEvent(
                engine_name="wholesaling",
                event_type="OUTREACH_BLOCKED_QUEUED",
                payload_json=json.dumps({"action_type": "OUTREACH_EMAIL", "target": str(payload.to), "subject": payload.subject}),
            ))
            db.commit()

            return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
```

---

## The Patch - Add Pre-Queue Filter

Replace that block with:

```python
        if e.status_code == 409 and isinstance(e.detail, dict) and "EngineBlocked" in str(e.detail.get("title", "")):
            
            # PRE-QUEUE FILTER: Only queue if item meets quality thresholds
            # Extract metrics from payload if available (adjust field names to match your schema)
            payload_dict = payload.model_dump() if hasattr(payload, 'model_dump') else {}
            
            profit = payload_dict.get('profit', 0)
            roi = payload_dict.get('roi', 0)
            risk = payload_dict.get('risk', 100)
            
            # Thresholds (tune as needed)
            MIN_PROFIT = 20000
            MIN_ROI = 20
            MAX_RISK = 15
            
            should_queue = (profit >= MIN_PROFIT) and (roi >= MIN_ROI) and (risk <= MAX_RISK)
            
            if should_queue:
                # Item meets quality bar - queue for approval
                pa = PendingAction(
                    engine_name="wholesaling",
                    action_type="OUTREACH_EMAIL",
                    status=PendingActionStatus.PENDING.value,
                    target=str(payload.to),
                    subject=payload.subject,
                    preview_text=f"[SANDBOX PREVIEW] To: {payload.to}\nSubject: {payload.subject}\n\n{payload.body_text}",
                    payload_json=json.dumps(payload_dict),
                    reason=str(e.detail),
                )
                db.add(pa)

                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_QUEUED",
                    payload_json=json.dumps({"action_type": "OUTREACH_EMAIL", "target": str(payload.to), "subject": payload.subject}),
                ))
                db.commit()

                return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
            else:
                # Item does not meet quality bar - log but don't queue
                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_NOT_QUEUED",
                    payload_json=json.dumps({
                        "action_type": "OUTREACH_EMAIL",
                        "target": str(payload.to),
                        "subject": payload.subject,
                        "reason": f"quality_filter: profit={profit} (min {MIN_PROFIT}), roi={roi} (min {MIN_ROI}), risk={risk} (max {MAX_RISK})"
                    }),
                ))
                db.commit()

                return {"ok": True, "queued_for_approval": False, "reason": "Filtered out by quality gate"}
```

---

## Do the Same for Webhooks

In `queue_webhook()` function (around line ~30-50), apply the same logic:

```python
        if e.status_code == 409 and isinstance(e.detail, dict) and "EngineBlocked" in str(e.detail.get("title", "")):
            url = payload.url or settings.DEFAULT_WEBHOOK_URL
            if not url:
                raise HTTPException(status_code=400, detail="no webhook url provided or configured")
            
            # PRE-QUEUE FILTER
            payload_dict = payload.payload if hasattr(payload, 'payload') else {}
            profit = payload_dict.get('profit', 0)
            roi = payload_dict.get('roi', 0)
            risk = payload_dict.get('risk', 100)
            
            MIN_PROFIT = 20000
            MIN_ROI = 20
            MAX_RISK = 15
            
            should_queue = (profit >= MIN_PROFIT) and (roi >= MIN_ROI) and (risk <= MAX_RISK)
            
            if should_queue:
                pa = PendingAction(
                    engine_name="wholesaling",
                    action_type="OUTREACH_WEBHOOK",
                    status=PendingActionStatus.PENDING.value,
                    target=url,
                    preview_text=f"[SANDBOX PREVIEW] Webhook to: {url}\n\nPayload: {json.dumps(payload_dict, indent=2)}",
                    payload_json=json.dumps(payload.model_dump()),
                    reason=str(e.detail),
                )
                db.add(pa)

                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_QUEUED",
                    payload_json=json.dumps({"action_type": "OUTREACH_WEBHOOK", "target": url}),
                ))
                db.commit()

                return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
            else:
                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_NOT_QUEUED",
                    payload_json=json.dumps({
                        "action_type": "OUTREACH_WEBHOOK",
                        "target": url,
                        "reason": f"quality_filter: profit={profit} (min {MIN_PROFIT}), roi={roi} (min {MIN_ROI}), risk={risk} (max {MAX_RISK})"
                    }),
                ))
                db.commit()

                return {"ok": True, "queued_for_approval": False, "reason": "Filtered out by quality gate"}
```

---

## What This Does

**Before** (current):
- SANDBOX blocks → Always queue for approval
- Result: All items reach you; 40% decline rate

**After** (with pre-queue filter):
- SANDBOX blocks → Check profit/roi/risk
- If profit >= 20k AND roi >= 20 AND risk <= 15: Queue for approval
- Otherwise: Log "NOT_QUEUED" event, don't bother you

**Expected improvements:**
- Approval rate: 60% → 80%+ (fewer low-quality items)
- Your review time: saved (fewer items to review)
- FP rate: 40% → <10% (the items you see are better)

---

## Tuning the Thresholds

Start conservative:
```
MIN_PROFIT = 20000
MIN_ROI = 20
MAX_RISK = 15
```

After 1 week of data, adjust:
- If still too many declines in queue: Raise MIN_PROFIT or MIN_ROI
- If queue is too empty: Lower thresholds
- If risk-related declines: Lower MAX_RISK

Use the learning report (`/api/sandbox/learning/report`) to track changes.

---

## Testing

After deploying:

1. Queue a test email:
   ```
   POST /api/notify/email
   {"to":"test@example.com", "subject":"test", "body_html":"test", "body_text":"test", "profit": 25000, "roi": 22, "risk": 10}
   ```
   Expected: `{"ok": true, "queued_for_approval": true}`

2. Queue a low-quality email:
   ```
   POST /api/notify/email
   {"to":"test@example.com", "subject":"test", "body_html":"test", "body_text":"test", "profit": 5000, "roi": 5, "risk": 40}
   ```
   Expected: `{"ok": true, "queued_for_approval": false}`

3. Check learning report:
   ```
   GET /api/sandbox/learning/report
   ```
   Should now show:
   - OUTREACH_BLOCKED_NOT_QUEUED events in event breakdown
   - Fewer items in pending queue
   - Better approval rate (fewer low-quality items)

---

## After Deploy: Label 18 More Items Strategically

Once this filter is live, label items using the 4-category plan:
- 5 clearly good (high profit, low risk, high roi) → APPROVE
- 5 clearly bad (low profit, high risk, low roi) → REJECT
- 5 borderline (medium across all metrics) → NEEDS_INFO
- 5 risky-but-profitable (high profit but high risk) → Your call

This trains the system on your actual strategy, not on random items.

---

## Expected Timeline

- **Hour 1**: Deploy filter
- **Day 1**: Queue should drop 30-50%, approval rate jump to 75%+
- **Week 1**: Collect 20 structured labels
- **Week 2**: Retrain gates based on label patterns
- **Week 3+**: System learns and improves automatically

---

This is the engineering approach: measure, filter, label, repeat.
