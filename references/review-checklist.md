# Cross-Section Review Checklist

## Scope and terminology

- Does the artifact open with a short overview paragraph (what the system does, what the document covers, what it excludes) before the mission statement and detailed sections?
- Are mission statement, mission objectives, in-scope, not-in-scope, actors (primary/supporting/domain subject/external), use cases, functional requirements, and every non-functional-requirement category (performance, availability, scalability, data integrity, security, auditability, backup and recovery, maintainability) all present as their own labeled subsections — not merged together or silently dropped?
- Do all later sections use the same actors, domain terms, and exclusions?
- Trace each concept named in the requirements or use cases forward into the domain model, architecture, and API — flag any that were silently renamed, merged, or dropped without an explicit note (e.g. an "episode of care" from requirements reappearing only as "medical record" everywhere else).
- Did a format-only reference accidentally introduce unrelated features?
- Are assumptions clearly separated from validated requirements?

## Requirements to architecture

- Does each major component satisfy a stated requirement?
- Are caches, queues, replicas, and service splits justified?
- Is there exactly one authoritative source for each important datum?
- Are degraded modes and dependency failures described?
- Does every capacity line item from estimation (database, cache, object storage, queue) have a matching component in the architecture, and does every such component have a matching estimate? A sized attachment/media total with no object-storage component (or vice versa) is a contradiction, not a style gap.

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
- Are idempotency and `If-Match` used only where justified, and is that requirement stated on each affected endpoint itself rather than only in a general policy paragraph?
- Is pagination stable under concurrent inserts?
- Do status codes and state transitions agree?

## Operations and security

- Are sensitive values excluded from logs and errors?
- Are backup, restore, RPO, and RTO consistent?
- Are metrics and alerts tied to critical workflows?
- Are audit events append-only and access-controlled where required?

## Final handoff

- Confirm the artifact contains an actual written wrap-up section — not just a mental summary — listing unresolved assumptions and stakeholder validations.
- State the current bottleneck and the trigger for the next scaling step.
- Confirm every decision record has an "alternatives considered" and a "revisit when" field filled in, not just decision/rationale/trade-offs.
- Preserve the source document's formatting and verify generated artifacts with the relevant document workflow.
