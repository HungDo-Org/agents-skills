# System Design Workflow

Use the lightest sequence that fits the task. If the artifact already completed a stage, validate it briefly and continue from the first incomplete stage.

## 1. Frame the system

Open the artifact with a short overview paragraph — what the system does, what this document covers, and what it explicitly excludes — before the mission statement and the rest of the detail below. A reader should get the shape of the whole design from this paragraph alone; write or update it last if it's easier, but the artifact needs it as its lead-in, not just as an implied summary of the sections that follow.

Produce these as distinct, explicitly labeled subsections — don't fold them into one paragraph or skip one because it feels redundant with another:

- **Mission statement** — one paragraph: who the system serves and the core outcome it exists to deliver.
- **Mission objectives** — a bulleted list of the concrete capabilities that fulfill the mission statement. This is more granular than the mission statement and more outcome-oriented than the functional requirements that follow in stage 2.
- **Scope**
  - **In scope** — bulleted list of the capabilities this design covers.
  - **Not in scope** — bulleted list of capabilities explicitly excluded, with a note that they may return as a future design once their own requirements are introduced.
- **Actors** — group them, don't list them flat:
  - **Primary actors** — who directly perform the system's core work.
  - **Supporting actor(s)** — who administer or operate the system without performing its core work (e.g. a system administrator).
  - **Domain subject** — the entity the system is about but that does not itself use the system, if one exists (e.g. a patient, a customer's asset). Omit this category outright if every relevant party is a direct actor.
  - **External actors** — external systems or organizations that interact with the system, or an explicit statement that none exist in the current scope.
- **Use cases** — grouped per actor, as short capability statements ("Review X", "Record Y"), not one undifferentiated list.

Do not treat a domain subject as a direct actor unless it actually interacts with the system.

Keep a running glossary of domain concepts as you name them here (one canonical name per concept). A concept named in a use case or requirement (for example, an "episode of care") must reappear under that exact name in the domain model, architecture, and API stages. If a later stage needs to rename, merge, or split a concept, update the glossary and the earlier section that introduced it — don't let a second name for the same idea stand uncorrected. This is the most common source of cross-section contradiction and is easy to miss because each stage reads consistently in isolation.

## 2. Define requirements

**Functional requirements** describe observable capabilities and lifecycle transitions, grouped by the domain workflow they belong to (not one flat list) — e.g. one group per major entity or process stage.

**Non-functional requirements** need measurable targets where possible, as explicitly labeled subsections, one per category — don't compress these into a single paragraph:

- **Performance** — latency/throughput targets, typically per-operation-class with a percentile.
- **Availability and reliability** — an uptime target and what "not silently losing confirmed data" means for this domain.
- **Scalability** — expected growth and the peak-multiple the design must absorb without a rearchitecture.
- **Data integrity** — rules against silent overwrite/deletion, concurrent-update handling, and transactional consistency for multi-record changes.
- **Security and privacy** — encryption in transit/at rest, role-based access, least privilege, session/credential handling.
- **Auditability** — what must be recorded, what fields each audit event needs, and who can read/search it.
- **Backup and recovery** — recovery point objective (RPO), recovery time objective (RTO), backup encryption, and restore testing.
- **Maintainability and observability** — logging, metrics, alerting, schema versioning, and safe rollback.

Close stage 1 and 2 with **assumptions and constraints** as their own explicitly labeled subsections — separate stakeholder-validated facts (constraints) from planning assumptions the design depends on until validated.

## 3. Estimate capacity

Estimate traffic, peak concentration, concurrency, storage growth, attachments or media, replication, backup, and retention. Show formulas and connect the rounded targets to architecture decisions.

## 4. Model the domain and data

Define aggregate boundaries, identifiers, relationships, cardinality, lifecycle states, invariants, and deletion/amendment rules. Choose storage from access patterns and consistency needs, not popularity.

## 5. Create the high-level design

Show clients, edge/gateway, application boundaries, authoritative stores, caches, queues, object storage, identity, audit, monitoring, and external dependencies that are actually in scope. Explain the main read and write flows.

Cross-check this against the capacity estimates: every storage, cache, or object-storage line item estimated in stage 3 needs a matching component here, and every persistent component here needs a matching estimate. A large or growing capacity figure with nowhere to live in the architecture (or a component with no sized workload behind it) is a contradiction to resolve now, not a detail to defer.

## 6. Deep dive into critical paths

Prioritize the flows with the greatest correctness or scale risk. Define transaction boundaries, failure behavior, retries, deduplication, concurrency, state transitions, security checks, and recovery.

## 7. Record design decisions

For each non-obvious choice, fill in every field below — a decision record with the trade-offs field missing is incomplete, not merely terse. "Alternatives considered" and "revisit when" are the two fields most often dropped when this is written as free-form prose instead of filled in as a template; keep them mandatory.

```
Decision: <the choice made>
Context: <the forces and constraints that made this a decision>
Rationale: <why this choice satisfies those forces>
Alternatives considered: <at least one rejected option and why it was rejected>
Trade-offs: <what is given up by choosing this>
Failure/degraded behavior: <what happens when this component or dependency fails>
Revisit when: <the specific condition — a metric, scale threshold, or new requirement — that would trigger reconsidering this decision>
```

## 8. Design implementation-facing APIs

Map endpoints to domain capabilities, not database tables. Define method, path, authorization, description, request fields, lean response fields, error behavior, idempotency, concurrency, pagination, and state-transition rules.

## 9. Wrap up

Write this as an actual closing section in the artifact, not just a mental check before delivery — a design with 9 detailed stages and no written wrap-up is missing this stage, regardless of how thorough the rest is. Summarize risks, bottlenecks, unresolved assumptions, validation needed from stakeholders, and the next growth step. Avoid adding future-scale machinery without a stated trigger.
