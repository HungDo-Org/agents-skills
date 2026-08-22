# Cross-Section Review Checklist

## Scope and terminology

- Do all later sections use the same actors, domain terms, and exclusions?
- Did a format-only reference accidentally introduce unrelated features?
- Are assumptions clearly separated from validated requirements?

## Requirements to architecture

- Does each major component satisfy a stated requirement?
- Are caches, queues, replicas, and service splits justified?
- Is there exactly one authoritative source for each important datum?
- Are degraded modes and dependency failures described?

## Data and consistency

- Do relationships and state transitions match the workflows?
- Are transaction boundaries explicit for multi-record invariants?
- Are duplicate requests and concurrent updates handled?
- Are finalized or immutable records corrected through traceable mechanisms?
- Do deletion and retention rules match audit and regulatory needs?

## Estimation

- Are units, formulas, peak windows, growth, retention, and replication visible?
- Do estimates support the chosen architecture rather than merely accompany it?
- Are structured data and large objects estimated separately?
- Is the load-test target connected to calculated demand?

## API contracts

- Does every endpoint map to a real use case?
- Are authorization rules consistent with the actors and assignments?
- Are response payloads limited to frontend needs?
- Are internal counters and persistence fields excluded from JSON?
- Are idempotency and `If-Match` used only where justified?
- Is pagination stable under concurrent inserts?
- Do status codes and state transitions agree?

## Operations and security

- Are sensitive values excluded from logs and errors?
- Are backup, restore, RPO, and RTO consistent?
- Are metrics and alerts tied to critical workflows?
- Are audit events append-only and access-controlled where required?

## Final handoff

- List unresolved assumptions and stakeholder validations.
- State the current bottleneck and the trigger for the next scaling step.
- Preserve the source document's formatting and verify generated artifacts with the relevant document workflow.
