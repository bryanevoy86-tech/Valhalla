# Phase 4 Approval Gates Map (INTERNAL)

## Principle
Phase 4 is not "turn it on." Phase 4 is "turn on ONE safe thing at a time."

## Categories
A) Irreversible actions (ALWAYS require explicit approval)
- Any real money movement
- Signing/issuing contracts
- Sending outbound communications (unless explicitly whitelisted)
- Committing to vendors/services
- Changing DRY-RUN or outbound disable flags

B) Legal required checkpoints
- New contract templates
- Unusual structures or jurisdictions
- Any disputes, liens, or title irregularities

C) Accounting checkpoints
- Category setup + monthly review
- Transaction logging completeness
- Tax-sensitive decisions

## Default Phase 4 Flow
1) Draft actions only
2) Queue for approval
3) Approve one-by-one
4) Log approvals
5) Execute only after approval
6) Post-action audit log entry

## Emergency Stop Conditions (instant rollback)
- Any unexpected outbound attempt
- Any DRY-RUN bypass
- Duplicate transaction intent
- Resource creep indicating leak
- Error storm / repeated failure
