from __future__ import annotations

from collections import Counter

from .findings import CHECKS, FAIL, HUMAN_CHECKS, PASS, PHASES, REVIEW, WARN, Finding

ICON = {FAIL: "❌", WARN: "⚠️", REVIEW: "🔍", PASS: "✅"}
ORDER = {FAIL: 0, REVIEW: 1, WARN: 2, PASS: 3}


def summary(findings: list[Finding]) -> Counter:
    return Counter(f.status for f in findings)


def markdown(spec_name: str, findings: list[Finding], skipped_jev: int = 0, usage: dict | None = None) -> str:
    c = summary(findings)
    lines = [
        f"# Database design review — {spec_name}",
        "",
        f"**{c[FAIL]} fail · {c[REVIEW]} review · {c[WARN]} warn · {c[PASS]} pass**",
        "",
        "Checklist IDs refer to `CHECKLIST.md`. 🔍 REVIEW = Jev was not confident; decide yourself.",
    ]
    if skipped_jev:
        lines += ["", f"> Dry run: {skipped_jev} Jev questions were not sent. Only deterministic checks ran."]
    if usage:
        lines += ["", f"> Jev: {usage['requests']} requests ({usage['cached']} cached), "
                      f"{usage['input_tokens']} input / {usage['output_tokens']} output tokens."]

    # Normal-form scorecard: an NF is clean when none of its checks failed.
    nf_fail: Counter = Counter()
    for f in findings:
        if f.status in (FAIL, WARN, REVIEW):
            for nf in CHECKS.get(f.check, ("", "", ""))[2].split("/"):
                if nf:
                    nf_fail[(nf, f.status)] += 1
    lines += ["", "## Normal forms", "", "| NF | Fail | Review | Warn |", "|----|-----:|-------:|-----:|"]
    for nf in ["1NF", "2NF", "3NF", "BCNF", "4NF", "DK/NF", "RI"]:
        lines.append(f"| {nf} | {nf_fail[(nf, FAIL)]} | {nf_fail[(nf, REVIEW)]} | {nf_fail[(nf, WARN)]} |")

    for phase in PHASES:
        issues = sorted((f for f in findings if f.phase == phase and f.status != PASS),
                        key=lambda f: (ORDER[f.status], f.check, f.target))
        passed = sum(1 for f in findings if f.phase == phase and f.status == PASS)
        lines += ["", f"## {phase}", ""]
        if not issues:
            lines.append(f"All {passed} checks passed." if passed else "No checks ran.")
            continue
        lines += ["| | Check | Target | Finding | Source |", "|---|---|---|---|---|"]
        for f in issues:
            title = CHECKS.get(f.check, ("", f.check, ""))[1]
            lines.append(f"| {ICON[f.status]} | **{f.check}** {title} | `{f.target}` | {f.message} | {f.source} |")
        if passed:
            lines.append(f"\n{passed} other checks passed.")

    lines += ["", "## Human checks (tick these yourself)", ""]
    lines += [f"- [ ] **{cid}** {text}" for cid, text in HUMAN_CHECKS]
    return "\n".join(lines) + "\n"
