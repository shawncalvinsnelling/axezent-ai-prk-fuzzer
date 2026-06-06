#!/usr/bin/env python3
"""Axezent AI PRK Fuzzer & Receipt Generator.

Structure-aware generator for finite 3SAT -> CLIQUE reduction receipts.
It builds lawful mathematical objects first, then injects isolated defects.

Truth boundary:
This tool generates finite test receipts. It does not prove P=NP, global solver
correctness, reduction optimality, or any asymptotic complexity claim.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import time
from itertools import combinations
from pathlib import Path
from typing import Any

SCHEMA = "AXEZENT-AI-PRK-RECEIPT-v1"
TRUTH_LABEL = "BOUNDED_FINITE_REDUCTION_CHECK"


def literal_id(lit: str) -> str:
    if lit.startswith("~"):
        return "not_" + lit[1:]
    return lit


def parse_literal(lit: str) -> tuple[str, bool]:
    if lit.startswith("~"):
        return lit[1:], True
    return lit, False


def is_complement(a: str, b: str) -> bool:
    va, na = parse_literal(a)
    vb, nb = parse_literal(b)
    return va == vb and na != nb


def literal_value(lit: str, assignment: dict[str, bool]) -> bool:
    var, neg = parse_literal(lit)
    val = assignment[var]
    return (not val) if neg else val


def vertex_id(clause_index: int, literal_index: int, lit: str) -> str:
    return f"c{clause_index}_l{literal_index}_{literal_id(lit)}"


def canonical_edge(a: str, b: str) -> list[str]:
    if a == b:
        raise ValueError("self-edge is invalid")
    return sorted([a, b])


def edge_key(edge: list[str]) -> tuple[str, str]:
    return tuple(edge)  # edges are already canonicalized before storage


def generate_assignment(variable_count: int, rng: random.Random) -> dict[str, bool]:
    return {f"x{i + 1}": rng.choice([True, False]) for i in range(variable_count)}


def random_literal_for_assignment(
    variables: list[str],
    assignment: dict[str, bool],
    rng: random.Random,
    force_true: bool | None = None,
) -> str:
    var = rng.choice(variables)
    value = assignment[var]
    if force_true is True:
        return var if value else f"~{var}"
    if force_true is False:
        return f"~{var}" if value else var
    return var if rng.choice([True, False]) else f"~{var}"


def generate_satisfied_clause(
    variables: list[str],
    assignment: dict[str, bool],
    rng: random.Random,
) -> list[str]:
    """Generate a 3-literal clause guaranteed to be satisfied."""
    true_slot = rng.randrange(3)
    clause: list[str] = []
    for i in range(3):
        if i == true_slot:
            clause.append(random_literal_for_assignment(variables, assignment, rng, force_true=True))
        else:
            clause.append(random_literal_for_assignment(variables, assignment, rng, force_true=None))
    return clause


def build_vertices(clauses: list[list[str]]) -> tuple[list[str], dict[str, tuple[int, int, str]]]:
    vertices: list[str] = []
    meta: dict[str, tuple[int, int, str]] = {}
    for ci, clause in enumerate(clauses):
        if len(clause) != 3:
            raise ValueError(f"clause {ci} does not have exactly 3 literals")
        for li, lit in enumerate(clause):
            vid = vertex_id(ci, li, lit)
            vertices.append(vid)
            meta[vid] = (ci, li, lit)
    return vertices, meta


def should_connect(a_meta: tuple[int, int, str], b_meta: tuple[int, int, str]) -> bool:
    ca, _la, lita = a_meta
    cb, _lb, litb = b_meta
    return ca != cb and not is_complement(lita, litb)


def build_expected_edges(vertices: list[str], meta: dict[str, tuple[int, int, str]]) -> list[list[str]]:
    edges: list[list[str]] = []
    for a, b in combinations(vertices, 2):
        if should_connect(meta[a], meta[b]):
            edges.append(canonical_edge(a, b))
    return sorted(edges)


def choose_witness_clique(
    clauses: list[list[str]],
    assignment: dict[str, bool],
    rng: random.Random,
) -> list[str]:
    clique: list[str] = []
    for ci, clause in enumerate(clauses):
        true_literal_indices = [li for li, lit in enumerate(clause) if literal_value(lit, assignment)]
        if not true_literal_indices:
            raise ValueError(f"generated unsatisfied clause {ci}")
        li = rng.choice(true_literal_indices)
        clique.append(vertex_id(ci, li, clause[li]))
    return clique


def canonical_json_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(obj: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def make_receipt(variable_count: int, clause_count: int, seed: int) -> dict[str, Any]:
    if variable_count < 1:
        raise ValueError("variable_count must be at least 1")
    if clause_count < 1:
        raise ValueError("clause_count must be at least 1")

    rng = random.Random(seed)
    variables = [f"x{i + 1}" for i in range(variable_count)]
    assignment = generate_assignment(variable_count, rng)
    clauses = [generate_satisfied_clause(variables, assignment, rng) for _ in range(clause_count)]
    vertices, meta = build_vertices(clauses)
    edges = build_expected_edges(vertices, meta)
    clique = choose_witness_clique(clauses, assignment, rng)

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "truth_label": TRUTH_LABEL,
        "reduction": {
            "name": "3SAT_TO_CLIQUE",
            "source_problem": "3SAT",
            "target_problem": "CLIQUE",
            "version": "1.0.0",
        },
        "input_instance": {
            "format": "3CNF",
            "variables": variables,
            "clauses": clauses,
        },
        "target_instance": {
            "format": "GRAPH_WITH_CLIQUE_PARAMETER",
            "vertices": vertices,
            "edges": edges,
            "k": clause_count,
        },
        "witness": {
            "assignment": assignment,
            "claimed_clique": clique,
        },
        "checker_expectation": {"expected_result": "ACCEPT"},
        "claim_boundary": {
            "does_claim": [
                "finite 3SAT-to-CLIQUE receipt generated",
                "constructed graph follows the textbook reduction for this finite instance",
                "claimed witness is generated for this finite instance",
            ],
            "does_not_claim": [
                "P=NP",
                "global solver correctness",
                "optimality of reductions",
                "broad NP-complete claims",
            ],
        },
        "fuzzer_metadata": {
            "generator": "Axezent AI PRK Fuzzer",
            "seed": seed,
            "variable_count": variable_count,
            "clause_count": clause_count,
            "mutation": "none",
        },
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def mark_mutation(out: dict[str, Any], mutation: str) -> dict[str, Any]:
    out["checker_expectation"]["expected_result"] = "REJECT"
    out["fuzzer_metadata"]["mutation"] = mutation
    out.pop("receipt_sha256", None)
    out["receipt_sha256"] = sha256_json(out)
    return out


def mutate_bad_edge(receipt: dict[str, Any]) -> dict[str, Any]:
    """Remove one edge that should exist."""
    out = copy.deepcopy(receipt)
    edges = out["target_instance"]["edges"]
    if not edges:
        raise ValueError("cannot remove an edge from an empty edge set")
    removed = edges.pop(0)
    out["fuzzer_metadata"]["removed_edge"] = removed
    return mark_mutation(out, "bad_edge_missing_required_edge")


def mutate_bad_k(receipt: dict[str, Any]) -> dict[str, Any]:
    """Change k away from the number of clauses."""
    out = copy.deepcopy(receipt)
    out["target_instance"]["k"] = out["target_instance"]["k"] + 1
    return mark_mutation(out, "bad_k_parameter_mismatch")


def mutate_bad_assignment(receipt: dict[str, Any]) -> dict[str, Any]:
    """Flip the variable used by the first claimed clique literal."""
    out = copy.deepcopy(receipt)
    clique = out["witness"]["claimed_clique"]
    if not clique:
        raise ValueError("cannot mutate assignment without a claimed clique")
    literal_part = clique[0].split("_", 2)[2]
    var = literal_part[4:] if literal_part.startswith("not_") else literal_part
    assignment = out["witness"]["assignment"]
    if var not in assignment:
        raise ValueError(f"clique variable {var} not in assignment")
    assignment[var] = not assignment[var]
    out["fuzzer_metadata"]["flipped_variable"] = var
    return mark_mutation(out, "bad_assignment_flip_clique_variable")


def mutate_illegal_extra_edge(receipt: dict[str, Any]) -> dict[str, Any]:
    """Add a forbidden same-clause edge."""
    out = copy.deepcopy(receipt)
    vertices = out["target_instance"]["vertices"]
    by_clause: dict[str, list[str]] = {}
    for vertex in vertices:
        clause_key = vertex.split("_", 1)[0]
        by_clause.setdefault(clause_key, []).append(vertex)

    chosen_pair: list[str] | None = None
    for group in by_clause.values():
        if len(group) >= 2:
            chosen_pair = canonical_edge(group[0], group[1])
            break
    if chosen_pair is None:
        raise ValueError("could not find same-clause vertex pair")

    edges = out["target_instance"]["edges"]
    if chosen_pair not in edges:
        edges.append(chosen_pair)
    out["target_instance"]["edges"] = sorted(edges)
    out["fuzzer_metadata"]["added_edge"] = chosen_pair
    return mark_mutation(out, "illegal_extra_same_clause_edge")


def mutate_bad_clique_duplicate(receipt: dict[str, Any]) -> dict[str, Any]:
    """Duplicate one clique vertex, breaking the one-per-clause witness rule."""
    out = copy.deepcopy(receipt)
    clique = out["witness"]["claimed_clique"]
    if len(clique) < 2:
        raise ValueError("need at least two clique vertices to duplicate")
    clique[-1] = clique[0]
    return mark_mutation(out, "bad_clique_duplicate_vertex")


def save_json(path: str | Path, obj: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def cmd_generate_valid(args: argparse.Namespace) -> int:
    receipt = make_receipt(args.variables, args.clauses, args.seed)
    save_json(args.out, receipt)
    print(f"WROTE {args.out}")
    return 0


def cmd_mutate(args: argparse.Namespace, mutation: str) -> int:
    receipt = load_json(args.input)
    mutations = {
        "bad-edge": mutate_bad_edge,
        "bad-k": mutate_bad_k,
        "bad-assignment": mutate_bad_assignment,
        "illegal-extra-edge": mutate_illegal_extra_edge,
        "bad-clique-duplicate": mutate_bad_clique_duplicate,
    }
    out = mutations[mutation](receipt)
    save_json(args.out, out)
    print(f"WROTE {args.out}")
    return 0


def generate_family(variable_count: int, clause_count: int, seed: int) -> dict[str, dict[str, Any]]:
    base = make_receipt(variable_count, clause_count, seed)
    return {
        "valid": base,
        "bad_edge": mutate_bad_edge(base),
        "bad_k": mutate_bad_k(base),
        "bad_assignment": mutate_bad_assignment(base),
        "illegal_extra_edge": mutate_illegal_extra_edge(base),
        "bad_clique_duplicate": mutate_bad_clique_duplicate(base),
    }


def cmd_batch(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for i in range(args.count):
        seed = args.seed + i
        family = generate_family(args.variables, args.clauses, seed)
        for label, receipt in family.items():
            save_json(out_dir / f"{i:05d}_{label}.json", receipt)
            total += 1
    print(f"GENERATED {total} receipts in {out_dir}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    import prk_oracle_checker

    start = time.perf_counter()
    accept = reject = mismatch = 0
    for i in range(args.count):
        family = generate_family(args.variables, args.clauses, args.seed + i)
        for receipt in family.values():
            report = prk_oracle_checker.verify_receipt(receipt)
            expected = receipt["checker_expectation"]["expected_result"]
            if report.result == "ACCEPT":
                accept += 1
            elif report.result == "REJECT":
                reject += 1
            if report.result != expected:
                mismatch += 1
    elapsed = time.perf_counter() - start
    result = {
        "generated_receipts": args.count * 6,
        "accept": accept,
        "reject": reject,
        "mismatch": mismatch,
        "elapsed_seconds": round(elapsed, 6),
        "receipts_per_second": round((args.count * 6) / elapsed, 2) if elapsed else None,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if mismatch == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Axezent AI PRK fuzzer and receipt generator")
    sub = parser.add_subparsers(dest="command", required=True)

    valid = sub.add_parser("generate-valid", help="generate one valid 3SAT-to-CLIQUE receipt")
    valid.add_argument("--variables", type=int, default=4)
    valid.add_argument("--clauses", type=int, default=5)
    valid.add_argument("--seed", type=int, default=42)
    valid.add_argument("--out", required=True)
    valid.set_defaults(func=cmd_generate_valid)

    for name, help_text in [
        ("mutate-bad-edge", "remove one required edge"),
        ("mutate-bad-k", "change k to the wrong value"),
        ("mutate-bad-assignment", "flip one witness variable"),
        ("mutate-illegal-extra-edge", "add a forbidden same-clause edge"),
        ("mutate-bad-clique-duplicate", "duplicate a clique vertex"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("input")
        p.add_argument("--out", required=True)
        mutation_key = name.replace("mutate-", "")
        p.set_defaults(func=lambda args, m=mutation_key: cmd_mutate(args, m))

    batch = sub.add_parser("batch", help="generate valid and invalid receipt batches")
    batch.add_argument("--count", type=int, default=100)
    batch.add_argument("--variables", type=int, default=4)
    batch.add_argument("--clauses", type=int, default=5)
    batch.add_argument("--seed", type=int, default=42)
    batch.add_argument("--out-dir", required=True)
    batch.set_defaults(func=cmd_batch)

    bench = sub.add_parser("benchmark", help="generate and immediately verify a benchmark batch")
    bench.add_argument("--count", type=int, default=100)
    bench.add_argument("--variables", type=int, default=4)
    bench.add_argument("--clauses", type=int, default=5)
    bench.add_argument("--seed", type=int, default=42)
    bench.set_defaults(func=cmd_benchmark)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "variables") and args.variables < 1:
        parser.error("--variables must be at least 1")
    if hasattr(args, "clauses") and args.clauses < 1:
        parser.error("--clauses must be at least 1")
    if hasattr(args, "count") and args.count < 1:
        parser.error("--count must be at least 1")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
