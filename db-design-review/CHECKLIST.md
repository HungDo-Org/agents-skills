# Database Design Review Checklist

Based on *Database Design for Mere Mortals* (Hernandez, 25th Anniversary ed.) — Appendix C "Design
Guidelines" and Appendix G "On Normalization" — plus the classic 1NF → 5NF / BCNF normal forms.

Each item has an ID used by the validator report, and says **who checks it**:

- **code** — deterministic; `dbcheck` checks it from the spec with no AI.
- **jev** — a semantic judgment; `dbcheck` asks Jev one narrow question (Noul / Choice / Score) and
  gates on its probability/confidence. Low-confidence answers become **REVIEW**, not PASS/FAIL.
- **human** — needs business knowledge or talking to users; the report lists these for you to tick.

The **NF** column shows which normal form the item protects (Hernandez, Table G.2). You never "run
normalization" as a separate step: if every item below passes, the tables are normalized.

---

## Phase 1 — Mission (Ch. 4–5)

| ID | Check | Who | NF |
|----|-------|-----|----|
| M1 | Mission statement exists, is succinct, and describes purpose — not specific tasks | jev (Score) | — |
| M2 | Each mission objective is one declarative sentence describing one general task | jev (Noul per objective) | — |
| M3 | Every mission objective is supported by at least one table | jev (Choice over tables) | — |
| M4 | Statement and objectives were reviewed with users and management | human | — |

## Phase 2 — Tables (Ch. 7)

| ID | Check | Who | NF |
|----|-------|-----|----|
| T1 | Every table has a description | code | — |
| T2 | The table represents exactly **one subject** (one object or one event) | jev (Noul) | 2NF, 3NF, 4NF |
| T3 | Description defines the table, says why it matters, has no implementation details or examples | jev (Score) | — |
| T4 | Table name is plural, has no acronyms, and names a single subject | jev (Noul) | — |
| T5 | Table type is declared: `data`, `linking`, `subset`, or `validation` | code | — |
| T6 | Table is connected to at least one relationship (no orphans) | code | — |

## Phase 3 — Fields (Ch. 7, 9) — *the Ideal Field*

| ID | Check | Who | NF |
|----|-------|-----|----|
| F1 | No **repeating groups** (`phone1`, `phone2`, `item_3`…) | code | 1NF |
| F2 | No **multivalued** field (a list, a comma-separated set, "tags") | jev (Noul) | 1NF |
| F3 | No **multipart** field (full address, full name, "phone number and address") | jev (Noul) | 1NF |
| F4 | No **calculated / derived** field (age, total, count) | jev (Noul) | 2NF/3NF |
| F5 | Field describes the table's own subject, not another subject (**transitive dependency**) | jev (Noul) | 3NF |
| F6 | In a composite-key table, each non-key field depends on the **whole** key, not part of it | jev (Noul per key part) | 2NF |
| F7 | Non-key fields are not duplicated across tables (unnecessary duplicate fields) | code | 3NF |
| F8 | Field names are singular, unambiguous, one characteristic each | jev (Noul) | — |
| F9 | Every field has a type (physical domain) | code | DK/NF |
| F10 | Required audit fields are present (e.g. `created_at`, `updated_at`, `deleted_at`) | code | — |

## Phase 4 — Keys (Ch. 8) — *Elements of a Primary / Foreign Key*

| ID | Check | Who | NF |
|----|-------|-----|----|
| K1 | Every table has exactly one primary key | code | 1NF |
| K2 | PK fields exist and are NOT NULL | code | 1NF |
| K3 | PK is minimal and never changes (no names, phones, emails as PK) | jev (Noul) | BCNF |
| K4 | Every FK points to an existing table and to that table's PK (or a unique key) | code | RI |
| K5 | FK field type matches the referenced PK type | code | RI |
| K6 | Alternate (candidate) keys are declared `unique` | code | BCNF |
| K7 | Every determinant is a candidate key (no field that determines others without being a key) | human | BCNF |

## Phase 5 — Relationships (Ch. 10)

| ID | Check | Who | NF |
|----|-------|-----|----|
| R1 | Both tables in the relationship exist | code | — |
| R2 | Declared type (1:1, 1:N, M:N) matches its plain-English description | jev (Choice) | — |
| R3 | Every **M:N** is resolved by a linking table that exists and holds FKs to both sides | code | 1NF, 4NF |
| R4 | Every **1:1** is enforced with a unique FK | code | — |
| R5 | Every relationship has a **deletion rule** (restrict / cascade / set null / set default) | code | RI |
| R6 | Every relationship declares **participation** (mandatory / optional) on both sides | code | — |
| R7 | A linking table with 3+ key parts has no independent multi-valued facts (split it) | jev (Noul) | 4NF |
| R8 | A 3+ way linking table cannot be rebuilt by joining its 2-way projections | human | 5NF |
| R9 | Relationships were verified with users and management | human | — |

## Phase 6 — Business rules (Ch. 11)

| ID | Check | Who | NF |
|----|-------|-----|----|
| B1 | Each rule references tables that exist | code | — |
| B2 | Rule category (field-specific vs relationship-specific) is recorded on a Business Rule Specifications sheet | human | — |
| B3 | Declared enforcement (`database` / `application`) is plausible for the rule | jev (Choice) | DK/NF |
| B4 | Validation (lookup) tables back rules that restrict a field to a fixed list | human | DK/NF |

## Phase 7 — Views & integrity (Ch. 12–13)

| ID | Check | Who | NF |
|----|-------|-----|----|
| V1 | Required views are identified from reports, data-entry samples, and business rules | human | — |
| I1 | Table-level integrity: no duplicate records, PK unique and not null | code (K1, K2) | — |
| I2 | Field-level integrity: field specs are consistent across the database | code (K5, F9) | — |
| I3 | Relationship-level integrity: inserts and deletes make sense (R3–R6) | code | — |
| I4 | Soft-deleted rows are excluded from uniqueness via partial unique indexes where reuse is allowed | human | — |

---

## Normal forms at a glance

| NF | Plain-English test | Items |
|----|--------------------|-------|
| 1NF | One value per cell; no repeating groups; a primary key exists | F1, F2, F3, K1, K2 |
| 2NF | Non-key fields depend on the **whole** composite key | F6, T2 |
| 3NF | Non-key fields depend on **nothing but** the key (no transitive dependency) | F4, F5, F7, T2 |
| BCNF | Every determinant is a candidate key | K3, K6, K7 |
| 4NF | No two independent multi-valued facts in one table | R3, R7, T2 |
| 5NF | No table that can be losslessly split into smaller ones and re-joined | R8 |
| DK/NF | All constraints follow from domains and keys | F9, B3, B4 |
