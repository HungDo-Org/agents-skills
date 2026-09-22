# REST API Design Guide

## Resource and command boundaries

Use resource endpoints for ordinary create/read/update operations. Use explicit subresources or commands for important state changes and immutable corrections, for example:

```text
POST /orders/:id/status-transitions
POST /reports/:id/finalize
POST /diagnoses/:id/amendments
```

Avoid paths that expose table names or implementation-only relationships.

## Lean response rule

For every response field ask: what will the client do with it immediately?

Keep fields needed to:

- identify the new resource;
- render the requested view;
- show workflow status;
- obtain the next page;
- recover from an actionable error.

Omit fields that merely echo the request, represent internal foreign keys, expose authorization decisions, duplicate audit data, or reveal persistence/concurrency internals.

Typical write responses:

```http
201 Created
Location: /api/v1/resources/abc
ETag: "opaque-tag"

{
  "resourceId": "abc",
  "status": "draft"
}
```

Use `204 No Content` when the frontend only needs confirmation of success.

## Concurrency

For high-value mutable records, return an opaque `ETag` and require `If-Match` on updates. Reject stale edits with `412 Precondition Failed`. Keep internal revision counters out of JSON unless the client genuinely displays or reasons about them.

Database row locks protect only the short transaction. Conditional updates protect against a user saving a form loaded before another user's completed update.

## Idempotency

Require `Idempotency-Key` for commands where a retry could create a duplicate or repeat a financial/clinical effect. Persist the key with a request fingerprint and result for a bounded period. Reject reuse with a different request.

Do not require idempotency keys for naturally idempotent reads.

State the idempotency and concurrency requirement on each endpoint's own contract (e.g. "Requires Idempotency-Key" or "Requires If-Match"), not only in one blanket policy paragraph at the top of the API document. A reader must be able to tell whether a retry is safe from that endpoint's definition alone; a general statement that "retry-sensitive POST operations require it" leaves every individual create endpoint to guess whether it counts.

## Pagination

Use cursor pagination for large, chronological, or actively changing collections. Build a stable ordering with a unique tie-breaker, such as `(created_at, id)`.

Offset pagination is acceptable for small, mostly static lists or screens requiring direct page numbers.

## Errors

Use a stable machine code, a safe human message, and only actionable details. Never expose stack traces, SQL, secrets, tokens, or sensitive records. Request-correlation identifiers are optional during early exercises and useful during production hardening.

## Authorization

Document both coarse role requirements and fine-grained resource checks. A valid role alone does not necessarily authorize access to every tenant, patient, account, or project.
