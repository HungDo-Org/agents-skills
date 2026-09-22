---
name: system-design-practice
description: Continue, create, or review practical backend system designs from requirements through capacity estimates, architecture decisions, data design, and REST API contracts. Use when a user is practicing system design, extending an incomplete design document, checking cross-section consistency, or converting an existing design into implementation-facing documentation. Do not use for low-level code implementation unless the user also requests it.
---

# System Design Practice

Produce a coherent design whose requirements, estimates, architecture, data model, and APIs agree with each other. Continue from the artifact's actual stopping point instead of restarting completed work.

## Start from the available evidence

1. Inspect every source artifact that defines the system.
2. Distinguish content sources from format-only references. Do not copy another product's domain entities merely because its document is the formatting example.
3. Identify completed, incomplete, contradictory, and missing sections.
4. Preserve the user's established terminology, scope, and document style unless asked to change them.
5. State consequential assumptions. Do not invent external integrations, actors, or product features beyond scope.

For the end-to-end design sequence and stopping-point logic, read [references/workflow.md](references/workflow.md).

## Maintain traceability

Every major design element must trace back to a requirement or constraint:

- Actors and use cases define authorization and API consumers.
- Functional requirements define workflows and domain resources.
- Non-functional requirements drive availability, consistency, latency, security, audit, backup, and scaling decisions.
- Capacity assumptions justify infrastructure and storage choices.
- Domain invariants determine transactions, concurrency controls, and lifecycle transitions.
- APIs expose the domain without leaking internal persistence details.

When a new section conflicts with an earlier decision, resolve the conflict or flag it explicitly. Never silently introduce a second source of truth.

Watch specifically for domain terms that quietly change identity between stages — a concept named in the requirements or use cases (e.g. "episode of care") reappearing under a different name in the domain model or API (e.g. "medical record") without an explicit note that they are the same thing, or a deliberate split. Each stage tends to read as internally consistent even when it silently drifted from an earlier one, so this needs an active check, not just proofreading.

## Estimate before scaling

Use labeled units and visible formulas. Separate normal, peak, burst, growth, retention, replication, index, backup, and attachment assumptions. Keep calculated demand distinct from the rounded engineering target.

Read [references/estimation.md](references/estimation.md) when the task includes QPS, bandwidth, storage, cache, availability, or recovery estimates.

## Prefer the simplest adequate architecture

Start with the smallest architecture that satisfies the stated requirements. Add caches, replicas, queues, partitioning, or separate services only when a concrete workload, availability, isolation, or ownership need justifies them.

For authoritative writes, define:

- the source of truth;
- transaction boundaries;
- allowed state transitions;
- idempotency behavior;
- concurrent-update behavior;
- audit and amendment behavior;
- failure and recovery behavior.

Record non-obvious choices as short design-decision records containing context, decision, rationale, alternatives considered, trade-offs, failure behavior, and a trigger for revisiting the choice. Read [references/workflow.md](references/workflow.md) for the fill-in template — writing these as free prose tends to quietly drop the alternatives and the revisit trigger.

## Design lean client-facing APIs

Return only the data the client needs to render the view or continue the workflow. Do not echo complete requests or expose internal database columns, audit payloads, authorization state, or concurrency counters in JSON without a client use case.

Use HTTP semantics deliberately:

- `Location` for a newly created resource when useful.
- `ETag` and `If-Match` for optimistic concurrency on mutable, high-value records.
- `Idempotency-Key` only for retry-sensitive commands.
- Cursor pagination for large or actively changing ordered collections.
- `204 No Content` when the client does not require a response body.
- Consistent error codes and safe error messages without secrets or sensitive domain data.

Operational headers such as request correlation IDs are optional during early practice unless observability is in scope.

Read [references/api-design.md](references/api-design.md) before creating or reviewing endpoint contracts.

## Review before delivery

Run the cross-section review in [references/review-checklist.md](references/review-checklist.md). Prioritize substantive contradictions over cosmetic completeness. If editing an existing artifact, preserve its structure and formatting and verify the final artifact using the applicable document skill.
