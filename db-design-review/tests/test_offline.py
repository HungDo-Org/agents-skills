"""Offline tests: code checks on the example spec, and Jev interpretation with simulated answers."""

import random
from pathlib import Path

from dbcheck import __main__ as cli, code_checks, jev_checks, spec
from dbcheck.jev import JevClient

EXAMPLE = Path(__file__).parent.parent / "examples" / "clinic.yaml"


def fake_answer(q: dict) -> dict:
    if q["type"] == "noul":
        return {"type": "noul", "noul": random.choice([0.02, 0.5, 0.97])}
    opts = list(q["criteria"]) if q["type"] == "choice" else [str(i) for i in range(len(q["criteria"]))]
    pick = random.choice(opts)
    probs = {o: (1.0 if o == pick else 0.0) for o in opts}
    base = {"type": q["type"], "probabilities": probs, "confidence": random.choice([0.3, 0.9])}
    if q["type"] == "choice":
        return {**base, "choice": pick}
    return {**base, "score": float(pick), "legend": {str(i): c for i, c in enumerate(q["criteria"])}}


def test_code_checks_find_missing_linking_tables():
    findings = code_checks.run(spec.load(EXAMPLE))
    fails = {(f.check, f.target) for f in findings if f.status == "FAIL"}
    assert ("R3", "doctors ↔ titles") in fails
    assert ("R3", "doctors ↔ departments") in fails
    assert ("B1", "DEP-3") in fails


def test_full_run_with_simulated_jev(monkeypatch, tmp_path):
    random.seed(1)
    monkeypatch.setattr(JevClient, "ask", lambda self, state, qs: {k: fake_answer(q) for k, q in qs.items()})
    out = tmp_path / "r.md"
    code = cli.main([str(EXAMPLE), "-o", str(out), "--no-cache"])
    text = out.read_text()
    assert code == 1  # the example has real FAILs
    assert "(jev)" not in text and "| jev |" in text
    assert "REVIEW" in out.with_suffix(".json").read_text()


def test_every_question_has_an_interpreter():
    for b in jev_checks.build_batches(spec.load(EXAMPLE)):
        assert b.questions.keys() == b.interpret.keys()
        for q in b.questions.values():
            assert q["type"] in {"noul", "choice", "score"}
            if q["type"] == "choice":
                assert len(q["criteria"]) <= 255
            if q["type"] == "score":
                assert 2 <= len(q["criteria"]) <= 10
