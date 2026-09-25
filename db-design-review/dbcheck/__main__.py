"""dbcheck — validate a database design spec against the Mere Mortals checklist.

    python -m dbcheck design.yaml                 # code checks + Jev checks
    python -m dbcheck design.yaml --dry-run       # code checks only; writes Jev payloads for inspection
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import code_checks, jev_checks, report, spec as spec_mod
from .findings import FAIL, REVIEW, Finding
from .jev import JevClient, JevError


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dbcheck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="design spec (.yaml / .yml / .json)")
    ap.add_argument("-o", "--out", default=None, help="report path (default: <spec>.report.md; JSON beside it)")
    ap.add_argument("--dry-run", action="store_true", help="skip Jev; write request payloads to <spec>.jev-requests.json")
    ap.add_argument("--model", default="jev-latest")
    ap.add_argument("--yes", type=float, default=0.7, help="Noul probability at or above which the answer is yes")
    ap.add_argument("--no", type=float, default=0.3, help="Noul probability at or below which the answer is no")
    ap.add_argument("--min-confidence", type=float, default=0.6, help="Choice/Score confidence below this → REVIEW")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 on REVIEW as well as FAIL")
    args = ap.parse_args(argv)

    spec_path = Path(args.spec)
    spec = spec_mod.load(spec_path)
    out = Path(args.out) if args.out else spec_path.with_suffix(".report.md")

    findings: list[Finding] = code_checks.run(spec)
    batches = jev_checks.build_batches(spec)
    n_questions = sum(len(b.questions) for b in batches)
    usage = None

    if args.dry_run:
        dump = spec_path.with_suffix(".jev-requests.json")
        dump.write_text(json.dumps([{"name": b.name, "state": b.state, "model": args.model, "questions": b.questions}
                                    for b in batches], indent=2, ensure_ascii=False))
        print(f"dry run: {len(batches)} requests / {n_questions} Jev questions written to {dump}", file=sys.stderr)
    else:
        client = JevClient(model=args.model, cache_dir=None if args.no_cache else spec_path.parent / ".dbcheck-cache")
        th = jev_checks.Thresholds(args.yes, args.no, args.min_confidence)
        print(f"asking Jev {n_questions} questions in {len(batches)} requests…", file=sys.stderr)
        try:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                results = list(pool.map(lambda b: client.ask(b.state, b.questions), batches))
        except JevError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        for b, answers in zip(batches, results):
            findings += jev_checks.interpret(b, answers, th)
        usage = client.usage

    md = report.markdown(spec.name, findings, skipped_jev=n_questions if args.dry_run else 0, usage=usage)
    out.write_text(md, encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps([f.to_dict() for f in findings], indent=2, ensure_ascii=False))

    c = report.summary(findings)
    print(f"{c[FAIL]} fail · {c[REVIEW]} review · {c['WARN']} warn · {c['PASS']} pass → {out}", file=sys.stderr)
    return 1 if c[FAIL] or (args.strict and c[REVIEW]) else 0


if __name__ == "__main__":
    sys.exit(main())
