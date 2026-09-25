from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

PASS, FAIL, WARN, REVIEW = "PASS", "FAIL", "WARN", "REVIEW"

# Checklist metadata: id -> (phase, short title, normal forms it protects).
CHECKS: dict[str, tuple[str, str, str]] = {
    "M1": ("Mission", "Mission statement states purpose succinctly, no tasks", ""),
    "M2": ("Mission", "Objective is one declarative sentence, one general task", ""),
    "M3": ("Mission", "Objective is supported by a table", ""),
    "T1": ("Tables", "Table has a description", ""),
    "T2": ("Tables", "Table represents exactly one subject", "2NF/3NF/4NF"),
    "T3": ("Tables", "Table description follows the guidelines", ""),
    "T4": ("Tables", "Table name is plural, no acronyms, one subject", ""),
    "T5": ("Tables", "Table type declared", ""),
    "T6": ("Tables", "Table takes part in a relationship", ""),
    "F1": ("Fields", "No repeating groups", "1NF"),
    "F2": ("Fields", "No multivalued fields", "1NF"),
    "F3": ("Fields", "No multipart fields", "1NF"),
    "F4": ("Fields", "No calculated fields", "2NF/3NF"),
    "F5": ("Fields", "Field describes the table's own subject", "3NF"),
    "F6": ("Fields", "Depends on the whole composite key", "2NF"),
    "F7": ("Fields", "No unnecessary duplicate fields", "3NF"),
    "F8": ("Fields", "Field name is clear and singular", ""),
    "F9": ("Fields", "Field has a type", "DK/NF"),
    "F10": ("Fields", "Audit fields present", ""),
    "K1": ("Keys", "Exactly one primary key", "1NF"),
    "K2": ("Keys", "PK fields exist and are NOT NULL", "1NF"),
    "K3": ("Keys", "PK is stable and not private data", "BCNF"),
    "K4": ("Keys", "FK points to an existing PK/unique key", "RI"),
    "K5": ("Keys", "FK type matches referenced key", "RI"),
    "K6": ("Keys", "Natural identifiers declared unique", "BCNF"),
    "R1": ("Relationships", "Both tables exist", ""),
    "R2": ("Relationships", "Declared type matches description", ""),
    "R3": ("Relationships", "M:N resolved by a linking table", "1NF/4NF"),
    "R4": ("Relationships", "1:1 enforced by a unique FK", ""),
    "R5": ("Relationships", "Deletion rule declared", "RI"),
    "R6": ("Relationships", "Participation declared", ""),
    "R7": ("Relationships", "No independent multi-valued facts in one linking table", "4NF"),
    "B1": ("Business rules", "Rule references existing tables", ""),
    "B3": ("Business rules", "Declared enforcement is plausible", "DK/NF"),
}

PHASES = ["Mission", "Tables", "Fields", "Keys", "Relationships", "Business rules"]

# Checks that need a human; listed in every report as a to-do.
HUMAN_CHECKS = [
    ("M4", "Mission statement and objectives reviewed with users and management"),
    ("K7", "BCNF: every field that determines other fields is itself a candidate key"),
    ("R8", "5NF: no 3+-way linking table can be rebuilt by joining its 2-way projections"),
    ("R9", "Relationships verified with users and management"),
    ("B2", "Each business rule is categorized (field-specific vs relationship-specific) on a Business Rule Specifications sheet"),
    ("B4", "Validation (lookup) tables back rules that restrict a field to a fixed list"),
    ("V1", "Required views identified from reports, data-entry samples, and business rules"),
    ("I4", "Soft-deleted rows use partial unique indexes where value reuse is allowed"),
]


@dataclass
class Finding:
    check: str
    status: str
    target: str
    message: str
    source: str = "code"  # code | jev
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def phase(self) -> str:
        return CHECKS.get(self.check, ("Other", "", ""))[0]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "phase": self.phase}
