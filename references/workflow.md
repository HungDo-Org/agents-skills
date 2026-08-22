# System Design Workflow

Use the lightest sequence that fits the task. If the artifact already completed a stage, validate it briefly and continue from the first incomplete stage.

## 1. Frame the system

- Mission statement and business outcome
- In-scope and out-of-scope capabilities
- Actors, external systems, and trust boundaries
- Primary use cases and critical workflows
- Explicit assumptions and constraints

Do not treat a domain subject as a direct actor unless it actually interacts with the system.

## 2. Define requirements

Functional requirements should describe observable capabilities and lifecycle transitions. Non-functional requirements should include measurable targets where possible:

- latency and throughput;
- availability and reliability;
- consistency and data integrity;
- security, privacy, and authorization;
- auditability and retention;
- recovery point and recovery time;
- maintainability and observability.

Separate stakeholder-validated facts from planning assumptions.

## 3. Estimate capacity

Estimate traffic, peak concentration, concurrency, storage growth, attachments or media, replication, backup, and retention. Show formulas and connect the rounded targets to architecture decisions.

## 4. Model the domain and data

Define aggregate boundaries, identifiers, relationships, cardinality, lifecycle states, invariants, and deletion/amendment rules. Choose storage from access patterns and consistency needs, not popularity.

## 5. Create the high-level design

Show clients, edge/gateway, application boundaries, authoritative stores, caches, queues, object storage, identity, audit, monitoring, and external dependencies that are actually in scope. Explain the main read and write flows.

## 6. Deep dive into critical paths

Prioritize the flows with the greatest correctness or scale risk. Define transaction boundaries, failure behavior, retries, deduplication, concurrency, state transitions, security checks, and recovery.

## 7. Record design decisions

For each non-obvious choice include:

- context;
- decision;
- rationale;
- alternatives considered;
- trade-offs;
- failure/degraded behavior;
- condition that would trigger reconsideration.

## 8. Design implementation-facing APIs

Map endpoints to domain capabilities, not database tables. Define method, path, authorization, description, request fields, lean response fields, error behavior, idempotency, concurrency, pagination, and state-transition rules.

## 9. Wrap up

Summarize risks, bottlenecks, unresolved assumptions, validation needed from stakeholders, and the next growth step. Avoid adding future-scale machinery without a stated trigger.
