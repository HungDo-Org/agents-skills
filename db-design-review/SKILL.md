---
name: db-design-review
description: Review a relational database design against "Database Design for Mere Mortals" (Hernandez) and 1NF–5NF/BCNF, using the dbcheck validator (deterministic checks + TypeSafe Jev semantic checks). Use when the user asks to review, validate, check, or grade a database design, ERD, schema, table list, or a "Database Design Practice" doc, or asks whether a design is normalized.
---

# Database design review

You review a database design the way Hernandez's method does: mission → tables → fields → keys →
relationships → business rules → views, with normalization built into every step. The validator
`dbcheck` does the mechanical and semantic checks; your job is to transcribe the design faithfully,
run it, interpret the result, and cover what it cannot.

This skill lives in `~/.claude/skills/db-design-review/`. The checklist is `CHECKLIST.md` there; every
finding ID (T2, F5, R3…) refers to it. Read it before your first review in a session.

## 1. Get the design

Accept any source: a Google Doc (read it with the Drive tools), a Notion page, Markdown, an ERD
description, SQL DDL, or a Prisma/TypeORM schema. Read all of it before you start.

## 2. Transcribe it into a spec — faithfully

Write `<name>.yaml` in the user's current project (or the scratch/working directory), in the format of
`~/.claude/skills/db-design-review/examples/clinic.yaml`. Rules:

- **Do not fix anything while transcribing.** If the doc names a linking table it never defines, keep
  the relationship's `via:` pointing at the missing table. If a field is "phone number and address",
  transcribe what the doc says. The validator must see the real design, flaws included.
- Use the doc's own descriptions verbatim for `description:` on tables and relationships — T3 and R2
  grade them.
- Field shorthand: `name: text` means type only. Use the long form for `nullable`, `unique`,
  `references: table.field`, `description`.
- Only set `on_delete` and `participation` if the doc states them. Missing ones are real findings (R5, R6).
- Table `type`: `data`, `linking` (resolves M:N), `subset` (subtype sharing the parent's PK), or
  `validation` (lookup/catalog).
- Business rules: copy each rule's text; set `enforcement: database | application` only when the doc says so.
- If the doc says audit columns exist on every table, set `conventions.audit_fields_implicit: true`.

Tell the user what you could not map (e.g. an attribute with no clear type) instead of guessing silently.

## 3. Run the validator

```bash
~/.claude/skills/db-design-review/scripts/dbcheck <name>.yaml            # needs TYPESAFE_API_KEY
~/.claude/skills/db-design-review/scripts/dbcheck <name>.yaml --dry-run  # no key: code checks only
```

The script creates its own venv on first run. Exit code 1 means there is at least one FAIL; exit
code 2 means setup or the API failed (e.g. no key — then fall back to `--dry-run` and say so). Answers are cached in `.dbcheck-cache/`, so reruns
after an edit only pay for questions that changed.

## 4. Interpret the report (`<name>.report.md`)

- **FAIL (code)** — deterministic; trust it.
- **FAIL / WARN (jev)** — a calibrated judgment, not a proof. Read the field or table yourself before
  repeating it. Say "Jev flagged…" and give your own view.
- **REVIEW** — Jev was uncertain. Decide each one yourself and say what you decided and why.
- Group what you tell the user by root cause, not by check ID. Five F5 hits on `patients` usually
  mean one missing table (e.g. `emergency_contacts`).

For each real problem give: what is wrong, which guideline or normal form it breaks, and the concrete
fix (new table, moved field, added UNIQUE, deletion rule…).

## 5. Cover the human checks

The report ends with checks no tool can settle (M4, K7 BCNF, R8 5NF, R9, B2, B4, V1, I4). For each,
give your own assessment from the design, clearly labelled as your judgment, or say what you would
need to ask the business.

## 6. Do not edit the user's source doc

Suggest changes in chat or in a separate file. Only edit their Google Doc or Notion page if they ask.
