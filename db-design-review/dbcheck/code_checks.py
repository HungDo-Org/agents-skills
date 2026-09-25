"""Deterministic checks: everything that can be decided from the spec without a model."""

from __future__ import annotations

import re
from collections import defaultdict

from .findings import FAIL, PASS, WARN, Finding
from .spec import Spec, Table

REPEATING_GROUP = re.compile(r"^(.*?)(_?\d+)$")
VALID_REL_TYPES = {"1:1", "1:N", "M:N"}
VALID_DELETE_RULES = {"restrict", "cascade", "set null", "set default", "no action"}
VALID_PARTICIPATION = {"mandatory", "optional"}


def _fk_between(child: Table, parent: str) -> list[str]:
    return [f.name for f in child.foreign_keys() if f.ref_table == parent]


def run(spec: Spec) -> list[Finding]:
    out: list[Finding] = []
    add = lambda check, status, target, msg: out.append(Finding(check, status, target, msg))  # noqa: E731
    conv = spec.conventions
    audit = conv["audit_fields"]

    # --- Tables -----------------------------------------------------------
    related = {t for r in spec.relationships for t in r.between} | {r.via for r in spec.relationships if r.via}
    related |= {f.ref_table for t in spec.tables.values() for f in t.foreign_keys()}
    related |= {t.name for t in spec.tables.values() if t.foreign_keys()}

    for t in spec.tables.values():
        add("T1", PASS if t.description else FAIL, t.name,
            "has a description" if t.description else "table has no description")
        if t.type not in conv["table_types"]:
            add("T5", WARN, t.name, f"table type `{t.type}` should be one of {', '.join(conv['table_types'])}")
        else:
            add("T5", PASS, t.name, f"type: {t.type}")
        add("T6", PASS if t.name in related else WARN, t.name,
            "is related to other tables" if t.name in related else "table is not in any relationship (orphan)")

        # --- Keys ---------------------------------------------------------
        if not t.primary_key:
            add("K1", FAIL, t.name, "no primary key")
        else:
            add("K1", PASS, t.name, f"primary key ({', '.join(t.primary_key)})")
            missing = [k for k in t.primary_key if k not in t.fields]
            nullable = [k for k in t.primary_key if k in t.fields and t.fields[k].nullable]
            if missing:
                add("K2", FAIL, t.name, f"primary key field(s) not defined: {', '.join(missing)}")
            elif nullable:
                add("K2", FAIL, t.name, f"primary key field(s) marked nullable: {', '.join(nullable)}")
            else:
                add("K2", PASS, t.name, "PK fields exist and are NOT NULL")

        for f in t.foreign_keys():
            target = f"{t.name}.{f.name}"
            ref_t = spec.tables.get(f.ref_table or "")
            if ref_t is None:
                add("K4", FAIL, target, f"references missing table `{f.ref_table}`")
                continue
            ref_col = f.ref_field or (ref_t.primary_key[0] if len(ref_t.primary_key) == 1 else None)
            if ref_col is None or ref_col not in ref_t.fields:
                add("K4", FAIL, target, f"references missing field `{f.references}`")
                continue
            if not ref_t.is_unique([ref_col]):
                add("K4", FAIL, target, f"references `{ref_t.name}.{ref_col}`, which is neither the PK nor unique")
            else:
                add("K4", PASS, target, f"→ {ref_t.name}.{ref_col}")
            ref_type = ref_t.fields[ref_col].type
            if f.type and ref_type and f.type.lower() != ref_type.lower():
                add("K5", FAIL, target, f"type `{f.type}` ≠ referenced `{ref_t.name}.{ref_col}` type `{ref_type}`")
            elif f.type and ref_type:
                add("K5", PASS, target, f"type `{f.type}` matches")

        # --- Fields -------------------------------------------------------
        groups: dict[str, list[str]] = defaultdict(list)
        for fname, f in t.fields.items():
            m = REPEATING_GROUP.match(fname)
            if m and m.group(1):
                groups[m.group(1).rstrip("_")].append(fname)
            if not f.type:
                add("F9", WARN, f"{t.name}.{fname}", "field has no type (physical domain)")
        for base, names in groups.items():
            if len(names) > 1 or base + "s" in t.fields or base in t.fields:
                add("F1", FAIL, t.name, f"repeating group: {', '.join(sorted(names))} — move `{base}` to its own table")

        if audit and not conv["audit_fields_implicit"] and t.type != "validation":
            missing = [a for a in audit if a not in t.fields]
            add("F10", WARN if missing else PASS, t.name,
                f"missing audit field(s): {', '.join(missing)}" if missing else "audit fields present")

    # F7: the same non-key, non-FK, non-audit field name in several data tables.
    skip = set(audit) | set(conv["shared_field_names"])
    owners: dict[str, list[str]] = defaultdict(list)
    for t in spec.tables.values():
        keys = set(t.primary_key) | {f.name for f in t.foreign_keys()}
        for fname in t.fields:
            if fname not in keys and fname not in skip:
                owners[fname].append(t.name)
    for fname, tables in owners.items():
        if len(tables) > 1:
            add("F7", WARN, ", ".join(tables),
                f"field `{fname}` appears in {len(tables)} tables — confirm it is not duplicated data "
                "(rename it if it is a different characteristic in each table)")

    # --- Relationships ----------------------------------------------------
    for r in spec.relationships:
        missing = [n for n in r.between if n not in spec.tables]
        if len(r.between) != 2 or missing:
            add("R1", FAIL, r.label, f"relationship must name two existing tables; missing: {', '.join(missing) or '—'}")
            continue
        add("R1", PASS, r.label, "both tables exist")
        a, b = (spec.tables[n] for n in r.between)

        if r.type not in VALID_REL_TYPES:
            add("R2", FAIL, r.label, f"type `{r.type}` must be one of 1:1, 1:N, M:N")
        elif r.type == "M:N":
            link = spec.tables.get(r.via or "")
            if not r.via:
                add("R3", FAIL, r.label, "M:N relationship has no linking table (`via`)")
            elif link is None:
                add("R3", FAIL, r.label, f"linking table `{r.via}` is not defined")
            else:
                gaps = [n for n in r.between if not _fk_between(link, n)]
                add("R3", FAIL if gaps else PASS, r.label,
                    f"linking table `{r.via}` has no FK to: {', '.join(gaps)}" if gaps else f"resolved by `{r.via}`")
        else:
            fk_b, fk_a = _fk_between(b, a.name), _fk_between(a, b.name)
            if not fk_b and not fk_a:
                add("K4", FAIL, r.label, f"no foreign key implements this {r.type} relationship")
            if r.type == "1:1" and (fk_a or fk_b):
                child, cols = (b, fk_b) if fk_b else (a, fk_a)
                ok = any(child.is_unique([c]) for c in cols)
                add("R4", PASS if ok else FAIL, r.label,
                    f"`{child.name}.{cols[0]}` is unique" if ok else f"`{child.name}.{cols[0]}` must be UNIQUE to enforce 1:1")

        if not r.on_delete:
            add("R5", WARN, r.label, "no deletion rule (restrict / cascade / set null / set default)")
        elif r.on_delete.lower() not in VALID_DELETE_RULES:
            add("R5", WARN, r.label, f"unknown deletion rule `{r.on_delete}`")
        else:
            add("R5", PASS, r.label, f"on delete {r.on_delete}")

        bad = [n for n in r.between if r.participation.get(n) not in VALID_PARTICIPATION]
        add("R6", WARN if bad else PASS, r.label,
            f"participation (mandatory/optional) not declared for: {', '.join(bad)}" if bad else "participation declared")

    # --- Business rules ---------------------------------------------------
    for rule in spec.rules:
        missing = [n for n in rule.tables if n not in spec.tables]
        if missing:
            add("B1", FAIL, rule.id, f"references unknown table(s): {', '.join(missing)}")

    return out
