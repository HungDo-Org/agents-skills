# db-design-validator

Checks a relational database design against *Database Design for Mere Mortals* (Hernandez) and the
normal forms (1NF–5NF, BCNF), using three kinds of checker:

| Checker | Handles | Examples |
|---------|---------|----------|
| **Code** (`dbcheck/code_checks.py`) | Anything decidable from the structure | missing PK, FK to a missing table, M:N with no linking table, 1:1 without UNIQUE, repeating groups |
| **Jev** (`dbcheck/jev_checks.py`) | Narrow semantic judgments, one atomic question each | "Does this table store one subject?", "Is `address` multipart?", "Does `department_name` describe another subject?" |
| **Human / Claude** (`skills/db-design-review`) | Business knowledge and review | BCNF determinants, 5NF, verifying with users, views |

This split follows TypeSafe's guidance for Jev: keep questions literal and atomic, send only the state
each question needs (one table per request), keep comparisons in code, and use confidence to route
uncertain answers to a human (**REVIEW**) instead of guessing.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export TYPESAFE_API_KEY=...   # https://console.typesafe.ai/keys
```

## Run

```bash
.venv/bin/python -m dbcheck examples/clinic.yaml             # full run
.venv/bin/python -m dbcheck examples/clinic.yaml --dry-run   # no API calls; writes the Jev payloads
```

Output: `clinic.report.md` (readable) and `clinic.report.json` (for tooling). The command exits with code 1 when
there is a FAIL (add `--strict` to also fail on REVIEW), so it can run in CI.

Tuning: `--yes 0.7 --no 0.3` set the Noul thresholds (between them → REVIEW), and `--min-confidence 0.6`
sets the Choice/Score confidence floor.

## Spec format

See `examples/clinic.yaml` (transcribed from the Community Health Clinic practice doc). Top-level keys:
`name`, `mission {statement, objectives}`, `conventions`, `tables`, `relationships`, `business_rules`.

## Install as a Claude Code skill

```bash
git clone https://github.com/HungDo-Org/agents-skills.git
cp -R agents-skills/db-design-review ~/.claude/skills/
```

Then ask Claude something like *"review the database design in my Google Doc X"*, or run
`/db-design-review <doc>`. It transcribes the doc into a spec, runs `scripts/dbcheck` (which creates its own
venv on first run), and explains the findings. Put `export TYPESAFE_API_KEY=...` in your shell profile to
enable the Jev checks; without it the skill falls back to `--dry-run`.

## Tests

```bash
.venv/bin/pip install pytest && .venv/bin/python -m pytest -q tests
```

The tests use simulated Jev answers, so they need no API key.
