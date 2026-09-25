"""Load a design spec (YAML/JSON) and normalize it into plain dicts the checks can rely on."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONVENTIONS = {
    "audit_fields": [],
    # True = audit fields are assumed on every table and need not be listed per table.
    "audit_fields_implicit": False,
    "surrogate_pk_types": ["uuid", "serial", "bigserial", "int", "integer", "bigint", "identity"],
    # Generic names allowed in many tables without an F7 duplicate-field warning.
    "shared_field_names": ["id", "name", "description", "notes", "status", "code",
                           "started_at", "ended_at"],
    "table_types": ["data", "linking", "subset", "validation"],
}


@dataclass
class Field:
    name: str
    type: str | None = None
    description: str = ""
    nullable: bool = True
    unique: bool = False
    references: str | None = None  # "table.field"

    @property
    def ref_table(self) -> str | None:
        return self.references.split(".")[0] if self.references else None

    @property
    def ref_field(self) -> str | None:
        return self.references.split(".")[1] if self.references and "." in self.references else None


@dataclass
class Table:
    name: str
    type: str | None
    description: str
    primary_key: list[str]
    fields: dict[str, Field]
    unique: list[list[str]] = field(default_factory=list)

    def is_unique(self, cols: list[str]) -> bool:
        if sorted(cols) == sorted(self.primary_key):
            return True
        if len(cols) == 1 and cols[0] in self.fields and self.fields[cols[0]].unique:
            return True
        return any(sorted(u) == sorted(cols) for u in self.unique)

    def foreign_keys(self) -> list[Field]:
        return [f for f in self.fields.values() if f.references]


@dataclass
class Relationship:
    index: int
    between: list[str]
    type: str | None
    description: str
    via: str | None
    on_delete: str | None
    participation: dict[str, str]

    @property
    def label(self) -> str:
        return f"{self.between[0]} ↔ {self.between[1]}" if len(self.between) == 2 else f"relationship #{self.index}"


@dataclass
class Rule:
    id: str
    text: str
    tables: list[str]
    enforcement: str | None


@dataclass
class Spec:
    name: str
    mission_statement: str
    mission_objectives: list[str]
    tables: dict[str, Table]
    relationships: list[Relationship]
    rules: list[Rule]
    conventions: dict[str, Any]


def _as_list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _parse_field(name: str, raw: Any) -> Field:
    if raw is None:
        return Field(name=name)
    if isinstance(raw, str):
        return Field(name=name, type=raw)
    return Field(
        name=name,
        type=raw.get("type"),
        description=raw.get("description", "") or "",
        nullable=raw.get("nullable", True),
        unique=bool(raw.get("unique", False)),
        references=raw.get("references"),
    )


def load(path: str | Path) -> Spec:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        import yaml

        raw = yaml.safe_load(text)

    conventions = {**DEFAULT_CONVENTIONS, **(raw.get("conventions") or {})}
    mission = raw.get("mission") or {}

    tables: dict[str, Table] = {}
    for tname, t in (raw.get("tables") or {}).items():
        t = t or {}
        fields = {fname: _parse_field(fname, f) for fname, f in (t.get("fields") or {}).items()}
        pk = _as_list(t.get("primary_key"))
        # Primary key fields are never nullable (Elements of a Primary Key).
        for k in pk:
            if k in fields and "nullable" not in ((t.get("fields") or {}).get(k) or {}):
                fields[k].nullable = False
        tables[tname] = Table(
            name=tname,
            type=t.get("type"),
            description=(t.get("description") or "").strip(),
            primary_key=pk,
            fields=fields,
            unique=[_as_list(u) for u in _as_list(t.get("unique"))],
        )

    relationships = [
        Relationship(
            index=i,
            between=_as_list(r.get("between")),
            type=r.get("type"),
            description=(r.get("description") or "").strip(),
            via=r.get("via"),
            on_delete=r.get("on_delete"),
            participation=r.get("participation") or {},
        )
        for i, r in enumerate(raw.get("relationships") or [])
    ]

    rules = [
        Rule(
            id=str(r.get("id") or f"BR{i + 1}"),
            text=(r.get("text") or "").strip(),
            tables=_as_list(r.get("tables")),
            enforcement=r.get("enforcement"),
        )
        for i, r in enumerate(raw.get("business_rules") or [])
    ]

    return Spec(
        name=raw.get("name") or path.stem,
        mission_statement=(mission.get("statement") or "").strip(),
        mission_objectives=[o.strip() for o in _as_list(mission.get("objectives"))],
        tables=tables,
        relationships=relationships,
        rules=rules,
        conventions=conventions,
    )
