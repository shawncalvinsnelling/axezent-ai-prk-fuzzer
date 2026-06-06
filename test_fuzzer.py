from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import prk_fuzzer
import prk_oracle_checker

ROOT = Path(__file__).resolve().parent


def test_generated_valid_receipt_accepts():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    report = prk_oracle_checker.verify_receipt(receipt)
    assert report.result == "ACCEPT", report.errors


def test_bad_edge_rejects():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    bad = prk_fuzzer.mutate_bad_edge(receipt)
    report = prk_oracle_checker.verify_receipt(bad)
    assert report.result == "REJECT"
    assert any("edge set mismatch" in err for err in report.errors)


def test_bad_k_rejects():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    bad = prk_fuzzer.mutate_bad_k(receipt)
    report = prk_oracle_checker.verify_receipt(bad)
    assert report.result == "REJECT"
    assert any("k must equal" in err for err in report.errors)


def test_bad_assignment_rejects():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    bad = prk_fuzzer.mutate_bad_assignment(receipt)
    report = prk_oracle_checker.verify_receipt(bad)
    assert report.result == "REJECT"
    assert any("false under assignment" in err or "does not satisfy clause" in err for err in report.errors)


def test_illegal_extra_edge_rejects():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    bad = prk_fuzzer.mutate_illegal_extra_edge(receipt)
    report = prk_oracle_checker.verify_receipt(bad)
    assert report.result == "REJECT"
    assert any("edge set mismatch" in err for err in report.errors)


def test_bad_clique_duplicate_rejects():
    receipt = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=123)
    bad = prk_fuzzer.mutate_bad_clique_duplicate(receipt)
    report = prk_oracle_checker.verify_receipt(bad)
    assert report.result == "REJECT"
    assert any("duplicate" in err or "one vertex from each clause" in err for err in report.errors)


def test_generation_is_reproducible():
    a = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=999)
    b = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=999)
    c = prk_fuzzer.make_receipt(variable_count=4, clause_count=6, seed=1000)
    assert a == b
    assert a != c
    assert a["receipt_sha256"] == b["receipt_sha256"]


def test_batch_generation_and_oracle_agreement(tmp_path):
    class Args:
        count = 3
        variables = 4
        clauses = 5
        seed = 42
        out_dir = str(tmp_path / "batch")

    assert prk_fuzzer.cmd_batch(Args()) == 0
    files = sorted((tmp_path / "batch").glob("*.json"))
    assert len(files) == 18
    for path in files:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        report = prk_oracle_checker.verify_receipt(receipt)
        assert report.result == receipt["checker_expectation"]["expected_result"], (path.name, report.errors)


def test_cli_generate_and_verify(tmp_path):
    out = tmp_path / "generated_valid.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "prk_fuzzer.py"), "generate-valid", "--variables", "4", "--clauses", "5", "--seed", "42", "--out", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "WROTE" in proc.stdout
    proc2 = subprocess.run(
        [sys.executable, str(ROOT / "prk_oracle_checker.py"), "verify", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ACCEPT" in proc2.stdout


def test_benchmark_zero_mismatch():
    class Args:
        count = 10
        variables = 4
        clauses = 5
        seed = 42

    assert prk_fuzzer.cmd_benchmark(Args()) == 0
