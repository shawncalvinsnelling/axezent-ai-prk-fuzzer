#!/usr/bin/env python3
"""Axezent AI Poly-Reduce Kernel reference checker.

Launch scope: finite 3SAT -> CLIQUE reduction receipts.
Truth boundary: this checks a submitted finite receipt. It does not prove P=NP,
global solver correctness, reduction optimality, or any asymptotic complexity claim.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

ACCEPT = "ACCEPT"
REJECT = "REJECT"
INCOMPLETE = "INCOMPLETE"

VAR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
LIT_RE = re.compile(r"^(~|¬|-)?([A-Za-z][A-Za-z0-9_]*)$")


@dataclass(frozen=True)
class Report:
    result: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    facts: dict[str, Any]

    def exit_code(self) -> int:
        return {ACCEPT: 0, REJECT: 1, INCOMPLETE: 2}.get(self.result, 2)


def canonical_edge(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))  # type: ignore[return-value]


def parse_literal(lit: str) -> tuple[str, bool]:
    if not isinstance(lit, str):
        raise ValueError(f"literal is not a string: {lit!r}")
    m = LIT_RE.match(lit.strip())
    if not m:
        raise ValueError(f"invalid literal syntax: {lit!r}")
    neg = bool(m.group(1))
    var = m.group(2)
    return var, neg


def literal_id(lit: str) -> str:
    var, neg = parse_literal(lit)
    return f"not_{var}" if neg else var


def vertex_id(clause_index: int, literal_index: int, lit: str) -> str:
    return f"c{clause_index}_l{literal_index}_{literal_id(lit)}"


def contradictory(a: str, b: str) -> bool:
    va, na = parse_literal(a)
    vb, nb = parse_literal(b)
    return va == vb and na != nb


def literal_value(lit: str, assignment: dict[str, bool]) -> bool:
    var, neg = parse_literal(lit)
    if var not in assignment:
        raise KeyError(f"assignment missing variable {var}")
    value = bool(assignment[var])
    return (not value) if neg else value


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require_keys(obj: dict[str, Any], keys: Iterable[str], where: str, errors: list[str]) -> None:
    for key in keys:
        if key not in obj:
            errors.append(f"missing required key {where}.{key}")


def expected_graph_from_formula(variables: list[str], clauses: list[list[str]]) -> tuple[list[str], set[tuple[str, str]], dict[str, tuple[int, int, str]]]:
    vertices: list[str] = []
    vertex_meta: dict[str, tuple[int, int, str]] = {}
    for ci, clause in enumerate(clauses):
        for li, lit in enumerate(clause):
            v = vertex_id(ci, li, lit)
            vertices.append(v)
            vertex_meta[v] = (ci, li, lit)

    edge_set: set[tuple[str, str]] = set()
    for a, b in itertools.combinations(vertices, 2):
        ca, _la, lita = vertex_meta[a]
        cb, _lb, litb = vertex_meta[b]
        if ca != cb and not contradictory(lita, litb):
            edge_set.add(canonical_edge(a, b))
    return vertices, edge_set, vertex_meta


def verify_3sat_to_clique(receipt: dict[str, Any]) -> Report:
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, Any] = {}

    require_keys(
        receipt,
        ["schema", "truth_label", "reduction", "input_instance", "target_instance", "witness"],
        "receipt",
        errors,
    )
    if errors:
        return Report(INCOMPLETE, tuple(errors), tuple(warnings), facts)

    if receipt.get("schema") != "AXEZENT-AI-PRK-RECEIPT-v1":
        errors.append("schema must be AXEZENT-AI-PRK-RECEIPT-v1")
    if receipt.get("truth_label") != "BOUNDED_FINITE_REDUCTION_CHECK":
        errors.append("truth_label must be BOUNDED_FINITE_REDUCTION_CHECK")

    reduction = receipt.get("reduction", {})
    if reduction.get("name") != "3SAT_TO_CLIQUE":
        errors.append("only reduction.name=3SAT_TO_CLIQUE is supported in v1.0.0")

    inst = receipt.get("input_instance", {})
    target = receipt.get("target_instance", {})
    witness = receipt.get("witness", {})
    require_keys(inst, ["variables", "clauses"], "input_instance", errors)
    require_keys(target, ["vertices", "edges", "k"], "target_instance", errors)
    require_keys(witness, ["assignment", "claimed_clique"], "witness", errors)
    if errors:
        return Report(INCOMPLETE, tuple(errors), tuple(warnings), facts)

    variables = inst["variables"]
    clauses = inst["clauses"]
    if not isinstance(variables, list) or not all(isinstance(v, str) for v in variables):
        errors.append("input_instance.variables must be a list of strings")
        variables = []
    if len(set(variables)) != len(variables):
        errors.append("input_instance.variables contains duplicates")
    for v in variables:
        if not VAR_RE.match(v):
            errors.append(f"invalid variable name: {v!r}")

    if not isinstance(clauses, list) or not all(isinstance(c, list) for c in clauses):
        errors.append("input_instance.clauses must be a list of clauses")
        clauses = []
    for ci, clause in enumerate(clauses):
        if len(clause) != 3:
            errors.append(f"clause {ci} is not a 3-literal clause")
        for lit in clause:
            try:
                var, _neg = parse_literal(lit)
                if var not in variables:
                    errors.append(f"literal {lit!r} uses undeclared variable {var!r}")
            except ValueError as exc:
                errors.append(str(exc))

    if errors:
        return Report(REJECT, tuple(errors), tuple(warnings), facts)

    expected_vertices, expected_edges, vertex_meta = expected_graph_from_formula(variables, clauses)
    claimed_vertices = target["vertices"]
    claimed_edges_raw = target["edges"]
    claimed_k = target["k"]

    if sorted(claimed_vertices) != sorted(expected_vertices):
        missing = sorted(set(expected_vertices) - set(claimed_vertices))
        extra = sorted(set(claimed_vertices) - set(expected_vertices))
        errors.append(f"target vertices mismatch; missing={missing}; extra={extra}")

    claimed_edges: set[tuple[str, str]] = set()
    if not isinstance(claimed_edges_raw, list):
        errors.append("target_instance.edges must be a list")
    else:
        for edge in claimed_edges_raw:
            if not isinstance(edge, list) or len(edge) != 2:
                errors.append(f"invalid edge shape: {edge!r}")
                continue
            a, b = edge
            if a == b:
                errors.append(f"self-loop edge is invalid: {edge!r}")
            if a not in expected_vertices or b not in expected_vertices:
                errors.append(f"edge references unknown vertex: {edge!r}")
            claimed_edges.add(canonical_edge(str(a), str(b)))

    if claimed_edges != expected_edges:
        missing = sorted(expected_edges - claimed_edges)
        extra = sorted(claimed_edges - expected_edges)
        errors.append(
            f"edge set mismatch; missing_count={len(missing)}; extra_count={len(extra)}; "
            f"first_missing={missing[:3]}; first_extra={extra[:3]}"
        )

    if claimed_k != len(clauses):
        errors.append(f"k must equal number of clauses ({len(clauses)}), got {claimed_k!r}")

    assignment = witness["assignment"]
    if not isinstance(assignment, dict):
        errors.append("witness.assignment must be an object")
        assignment = {}
    for var in variables:
        if var not in assignment:
            errors.append(f"assignment missing variable {var}")
        elif not isinstance(assignment[var], bool):
            errors.append(f"assignment value for {var} must be boolean")

    claimed_clique = witness["claimed_clique"]
    if not isinstance(claimed_clique, list):
        errors.append("witness.claimed_clique must be a list")
        claimed_clique = []
    if len(claimed_clique) != len(clauses):
        errors.append(f"claimed clique size must equal k={len(clauses)}, got {len(claimed_clique)}")
    if len(set(claimed_clique)) != len(claimed_clique):
        errors.append("claimed clique contains duplicate vertices")

    clause_hits: set[int] = set()
    for v in claimed_clique:
        if v not in vertex_meta:
            errors.append(f"claimed clique vertex not in constructed graph: {v!r}")
            continue
        ci, _li, lit = vertex_meta[v]
        clause_hits.add(ci)
        try:
            if not literal_value(lit, assignment):
                errors.append(f"claimed clique vertex {v} is not true under assignment")
        except KeyError as exc:
            errors.append(str(exc))
    if clause_hits != set(range(len(clauses))):
        errors.append(f"claimed clique must choose exactly one vertex per clause; got clauses {sorted(clause_hits)}")

    for a, b in itertools.combinations(claimed_clique, 2):
        if canonical_edge(a, b) not in claimed_edges:
            errors.append(f"claimed clique pair is not an edge: {a}, {b}")

    for ci, clause in enumerate(clauses):
        if not any(literal_value(lit, assignment) for lit in clause):
            errors.append(f"assignment does not satisfy clause {ci}")

    facts.update(
        {
            "variables": len(variables),
            "clauses": len(clauses),
            "expected_vertices": len(expected_vertices),
            "expected_edges": len(expected_edges),
            "claimed_edges": len(claimed_edges),
            "claimed_k": claimed_k,
        }
    )

    return Report(REJECT if errors else ACCEPT, tuple(errors), tuple(warnings), facts)


def verify_receipt(receipt: dict[str, Any]) -> Report:
    reduction = receipt.get("reduction", {}) if isinstance(receipt, dict) else {}
    if reduction.get("name") == "3SAT_TO_CLIQUE":
        return verify_3sat_to_clique(receipt)
    return Report(INCOMPLETE, ("unsupported or missing reduction.name",), (), {})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Axezent AI Poly-Reduce Kernel receipt checker")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="verify a finite reduction receipt")
    verify.add_argument("receipt", help="path to receipt JSON")
    verify.add_argument("--json", action="store_true", help="print full JSON report")
    args = parser.parse_args(argv)

    if args.command == "verify":
        receipt = load_json(args.receipt)
        report = verify_receipt(receipt)
        if args.json:
            print(json.dumps(asdict(report), indent=2, sort_keys=True))
        else:
            print(report.result)
            for err in report.errors:
                print(f"ERROR: {err}")
            for warn in report.warnings:
                print(f"WARNING: {warn}")
        return report.exit_code()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
