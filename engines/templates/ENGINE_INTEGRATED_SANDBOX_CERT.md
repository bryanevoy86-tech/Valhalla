# INTEGRATED SANDBOX CERTIFICATION

Engine is tested alongside other engines to prove it plays well in the system.

## Engine Information

**Engine Name:**  
**Date Tested:**  
**Tester:**  
**Coexisting Engines:** (What else is running?)  

## Integration Test Setup

**Duration:** (How long was the integration test?)  
**Environment:**
- DRY_RUN=1 (simulation mode)
- OUTBOUND_DISABLED=1 (no external calls)
- Multi-engine sandbox
- Real resource contention (CPU, memory, I/O)

**Coexisting Engines:**
1. Valhalla Core (primary)
2. (Other engines being tested together)

## Results

### Resource Impact
- **Memory Usage:** (Isolated vs. Integrated)
- **CPU Impact:** (Does it steal resources?)
- **I/O Contention:** (Disk conflicts?)
- **Network Contention:** (If applicable)

### Dominance Risk
- **Does this engine overwhelm others?** (Yes / No / Sometimes)
- **Does this engine starve under load?** (Yes / No / Sometimes)
- **Priority handling:** (How does scheduling work?)
- **Fairness:** (Is resource allocation balanced?)

### System Health
- **System stability during integration:** (1-10 rating)
- **Unexpected interactions discovered:**
- **Failure modes in integration:**
- **Recovery behavior under contention:**

### Net Contribution
- **Does this engine add value?** (Yes / No / Conditional)
- **Does it break anything else?** (Yes / No / Minor)
- **Reversibility:** (Can we turn it off cleanly?)
- **Overall assessment:** (Worth keeping?)

## Verdict

- [ ] **PASS** — Integrates cleanly, ready for STAGE 3 (Ready Cert)
- [ ] **PASS with Throttle** — Passes but needs resource limits applied
- [ ] **FAIL** — Conflicts with other engines; needs redesign
- [ ] **ARCHIVE** — Too risky for integration

### Throttle Constraints (if applicable)

(What limits must be enforced if this passes with throttle?)

- Max CPU usage: ____%
- Max memory usage: _____ MB
- Max concurrent executions: _____
- Quiet hours: _____

## Integration Issues

| Issue | Severity | Impact | Resolution | Status |
|-------|----------|--------|-----------|--------|
| | | | | |

## Recommendation

(Does this belong in production? Under what constraints?)

---

**Tester Signature:**  
**Date Completed:**  
**Status:** STAGE 2 COMPLETE

**Next Step:** ENGINE_READY_CERT.md (if PASS)

---

*Integration testing is the real proof. Solo stability means nothing if the engine breaks the system.*
