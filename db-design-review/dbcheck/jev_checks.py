"""Semantic checks answered by Jev.

Following TypeSafe's guidance, each question is atomic and literal, the state holds only what that
question needs (one table, one relationship list, ...), and all arithmetic and comparisons stay in
code. Answers are gated: a Noul between the yes/no thresholds, or a Choice/Score below the
confidence floor, becomes REVIEW instead of PASS/FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .findings import FAIL, PASS, REVIEW, WARN, Finding
from .spec import Spec, Table


@dataclass
class Thresholds:
    yes: float = 0.7
    no: float = 0.3
    min_confidence: float = 0.6


Interpret = Callable[[dict, Thresholds], Finding]


@dataclass
class Batch:
    name: str
    state: Any
    questions: dict[str, dict] = field(default_factory=dict)
    interpret: dict[str, Interpret] = field(default_factory=dict)

    def add(self, key: str, question: dict, interpret: Interpret) -> None:
        self.questions[key] = question
        self.interpret[key] = interpret


# --- question helpers -------------------------------------------------------

def noul(instructions: str, true: str | None = None, false: str | None = None) -> dict:
    q: dict[str, Any] = {"type": "noul", "instructions": instructions}
    if true or false:
        q["criteria"] = {"true": true or "", "false": false or ""}
    return q


def choice(instructions: str, criteria: dict[str, str | None]) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def score(instructions: str, levels: list[str]) -> dict:
    return {"type": "score", "instructions": instructions, "criteria": levels}


def on_noul(check: str, target: str, bad_if: str, bad_msg: str, ok_msg: str, severity: str = FAIL) -> Interpret:
    def f(ans: dict, th: Thresholds) -> Finding:
        p = float(ans["noul"])
        ev = {"noul": round(p, 3)}
        if th.no < p < th.yes:
            return Finding(check, REVIEW, target, f"uncertain (p={p:.2f}): {bad_msg}", "jev", ev)
        is_bad = (p >= th.yes) if bad_if == "yes" else (p <= th.no)
        return Finding(check, severity if is_bad else PASS, target, bad_msg if is_bad else ok_msg, "jev", ev)
    return f


def on_score(check: str, target: str, fail_below: float, warn_below: float, msg: str) -> Interpret:
    def f(ans: dict, th: Thresholds) -> Finding:
        s, conf = float(ans["score"]), float(ans.get("confidence", 1))
        ev = {"score": round(s, 2), "confidence": round(conf, 2), "legend": ans.get("legend")}
        level = ans.get("legend", {}).get(str(round(s)), "")
        if conf < th.min_confidence:
            return Finding(check, REVIEW, target, f"low confidence — {msg}: {level}", "jev", ev)
        status = FAIL if s < fail_below else WARN if s < warn_below else PASS
        return Finding(check, status, target, f"{msg}: {level}", "jev", ev)
    return f


def on_choice(check: str, target: str, judge: Callable[[str], tuple[str, str]]) -> Interpret:
    def f(ans: dict, th: Thresholds) -> Finding:
        pick, conf = ans["choice"], float(ans.get("confidence", 1))
        ev = {"choice": pick, "confidence": round(conf, 2), "probabilities": ans.get("probabilities")}
        status, msg = judge(pick)
        if conf < th.min_confidence and status != PASS:
            return Finding(check, REVIEW, target, f"low confidence — {msg}", "jev", ev)
        return Finding(check, status, target, msg, "jev", ev)
    return f


# --- batches ----------------------------------------------------------------

def _mission_batch(spec: Spec) -> Batch | None:
    if not spec.mission_statement and not spec.mission_objectives:
        return None
    options: dict[str, str | None] = {n: t.description or None for n, t in spec.tables.items()}
    options["none_of_these"] = "No table in the design stores the data this objective needs"
    b = Batch("mission", {
        "mission_statement": spec.mission_statement,
        "mission_objectives": spec.mission_objectives,
    })
    if spec.mission_statement:
        b.add("M1", score(
            "Rate `mission_statement` as the mission statement of a database. A good one states the "
            "database's purpose in one or two succinct sentences and does not list specific tasks.",
            ["Does not state a purpose, or is mostly a list of specific tasks",
             "States a purpose but includes specific tasks or unnecessary detail",
             "Succinctly states the purpose with no specific tasks"],
        ), on_score("M1", "mission statement", 0.75, 1.5, "mission statement"))
    for i, obj in enumerate(spec.mission_objectives):
        tgt = f"objective {i + 1}: {obj[:60]}"
        b.add(f"M2_{i}", noul(
            f"Is `mission_objectives[{i}]` a single declarative sentence that describes one general task, "
            "without implementation details?"),
            on_noul("M2", tgt, "no", "objective is not one clear, general task", "well-formed objective", WARN))
        b.add(f"M3_{i}", {
            **choice(f"Which table primarily stores the data needed to meet `mission_objectives[{i}]`?", options),
        }, on_choice("M3", tgt, lambda pick: (FAIL, "no table supports this objective") if pick == "none_of_these"
                     else (PASS, f"supported by `{pick}`")))
    return b


def _table_state(t: Table) -> dict:
    return {"table": {
        "name": t.name,
        "type": t.type,
        "description": t.description,
        "primary_key": t.primary_key,
        "fields": {n: {k: v for k, v in {"type": f.type, "description": f.description,
                                         "references": f.references}.items() if v}
                   for n, f in t.fields.items()},
    }}


def _table_batch(spec: Spec, t: Table) -> Batch:
    b = Batch(f"table:{t.name}", _table_state(t))
    audit = set(spec.conventions["audit_fields"])
    fks = {f.name for f in t.foreign_keys()}

    if t.type != "linking":
        b.add("T2", noul(
            "Does `table` store exactly one subject — one kind of thing or one kind of event — "
            "with every field describing that one subject?"),
            on_noul("T2", t.name, "no", "table mixes more than one subject — split it", "single subject"))
    if t.description:
        b.add("T3", score(
            "Rate `table.description`. A good table description defines the table, explains why it matters "
            "to the organization, and contains no implementation details and no examples.",
            ["Does not define the table",
             "Defines the table but does not say why it matters, or contains implementation details or examples",
             "Defines the table and why it matters, with no implementation details or examples"],
        ), on_score("T3", t.name, 0.75, 1.5, "table description"))
    b.add("T4", noul(
        "Is `table.name` a plural noun phrase, without acronyms, that names a single subject?"),
        on_noul("T4", t.name, "no", "rename: table names should be plural, no acronyms, one subject", "good name", WARN))

    surrogate = set(spec.conventions["surrogate_pk_types"])
    pk_types = [(t.fields[k].type or "").lower() for k in t.primary_key if k in t.fields]
    if t.primary_key and not fks.issuperset(t.primary_key) and not all(x in surrogate for x in pk_types):
        b.add("K3", noul(
            "Is any field in `table.primary_key` a value that can change over time or that is private, "
            "such as a name, email address, phone number, or national ID?"),
            on_noul("K3", t.name, "yes", "primary key is unstable or private — use a surrogate key", "stable key"))

    composite = len(t.primary_key) > 1
    for fname, f in t.fields.items():
        if fname in t.primary_key or fname in fks or fname in audit:
            continue
        ref = f"`table.fields.{fname}`"
        tgt = f"{t.name}.{fname}"
        b.add(f"F2__{fname}", noul(
            f"Can the field {ref} hold more than one value for a single record, such as a list or a "
            "comma-separated set of values?"),
            on_noul("F2", tgt, "yes", "multivalued field — move the values to their own table", "single-valued"))
        b.add(f"F3__{fname}", noul(
            f"Does the field {ref} combine several distinct items of data that could be stored separately, "
            "like a full address (street, city, postal code) or a full name (given name and family name)?"),
            on_noul("F3", tgt, "yes", "multipart field — split it into separate fields", "atomic", WARN))
        b.add(f"F4__{fname}", noul(
            f"Is the field {ref} a value calculated or derived from other stored data, such as an age, "
            "a total, an average, or a count?"),
            on_noul("F4", tgt, "yes", "calculated field — compute it in a query or view instead", "not calculated"))
        b.add(f"F5__{fname}", noul(
            f"Does the field {ref} describe a characteristic of the subject of `table` itself, and not a "
            "characteristic of some other subject?"),
            on_noul("F5", tgt, "no", "describes another subject (transitive dependency) — move it to that subject's table",
                    "describes this table's subject"))
        b.add(f"F8__{fname}", noul(
            f"Is `{fname}` a clear, singular field name for exactly one characteristic, without acronyms?"),
            on_noul("F8", tgt, "no", "unclear or plural field name", "good name", WARN))
        if not f.unique and not t.is_unique([fname]):
            b.add(f"K6__{fname}", noul(
                f"Would the value of {ref} be different for every record, because it is an identifier "
                "such as a license number, account number, email address, or code?"),
                on_noul("K6", tgt, "yes", "looks like a natural identifier — declare it UNIQUE (alternate key)",
                        "not an identifier", WARN))
        if composite:
            for k in t.primary_key:
                b.add(f"F6__{fname}__{k}", noul(
                    f"Can the value of {ref} be known from `table.fields.{k}` alone, without the other "
                    "primary key fields?"),
                    on_noul("F6", tgt, "yes", f"depends only on `{k}` (partial dependency) — move it to that table",
                            "depends on the whole key"))

    if t.type == "linking" and len(t.primary_key) >= 3:
        b.add("R7", noul(
            "Does `table` combine two facts that are independent of each other, so that its rows could be "
            "stored in two separate two-column tables without losing information?"),
            on_noul("R7", t.name, "yes", "independent multi-valued facts (4NF) — split the linking table", "one fact"))
    return b


REL_TYPES = {
    "1:1": "Each record on either side relates to at most one record on the other side",
    "1:N": "One record on one side relates to many records on the other side, and each of those relates to only one",
    "M:N": "Records on each side can relate to many records on the other side",
}


def _relationship_batch(spec: Spec) -> Batch | None:
    rels = [r for r in spec.relationships if r.description and r.type in REL_TYPES]
    if not rels:
        return None
    b = Batch("relationships", {"relationships": [{"tables": r.between, "description": r.description} for r in rels]})
    for i, r in enumerate(rels):
        b.add(f"R2_{r.index}", choice(
            f"Which kind of relationship does `relationships[{i}].description` describe?", dict(REL_TYPES)),
            on_choice("R2", r.label, lambda pick, r=r: (PASS, f"description matches {r.type}") if pick == r.type
                      else (FAIL, f"declared {r.type}, but the description reads as {pick}")))
    return b


ENFORCEMENT = {
    "database": "A column type, NOT NULL, CHECK, UNIQUE, or foreign-key constraint on a single table can enforce it",
    "application": "It needs data from several tables, a status workflow, or who-did-what checks, "
                   "so application code or a trigger must enforce it",
}


def _rules_batch(spec: Spec) -> Batch | None:
    rules = [r for r in spec.rules if r.enforcement in ENFORCEMENT]
    if not rules:
        return None
    b = Batch("business_rules", {"rules": [r.text for r in rules]})
    for i, r in enumerate(rules):
        b.add(f"B3_{i}", choice(f"How can `rules[{i}]` be enforced?", dict(ENFORCEMENT)),
              on_choice("B3", f"{r.id}: {r.text[:60]}", lambda pick, r=r: (PASS, f"{r.enforcement} enforcement fits")
                        if pick == r.enforcement else (WARN, f"declared {r.enforcement}, but reads as {pick}-enforced")))
    return b


def build_batches(spec: Spec) -> list[Batch]:
    batches = [_mission_batch(spec), *(_table_batch(spec, t) for t in spec.tables.values()),
               _relationship_batch(spec), _rules_batch(spec)]
    return [b for b in batches if b and b.questions]


def interpret(batch: Batch, answers: dict[str, dict], th: Thresholds) -> list[Finding]:
    out = []
    for key, fn in batch.interpret.items():
        ans = answers.get(key)
        if ans is None:
            out.append(Finding(key.split("__")[0].split("_")[0], REVIEW, batch.name, f"no answer for `{key}`", "jev"))
        else:
            out.append(fn(ans, th))
    return out
