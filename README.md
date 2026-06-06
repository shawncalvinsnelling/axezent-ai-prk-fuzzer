# Axezent AI PRK-Fuzzer & Receipt Generator

**Axezent AI PRK-Fuzzer** is a structure-aware open-source fuzzer and receipt generator for finite complexity-reduction verification workflows.

The launch pack generates valid and invalid receipts for one classical reduction:

```text
3SAT → CLIQUE
```

The core principle is simple:

```text
No claim without a receipt.
```

An external checker is only as trustworthy as the stress tests around it. PRK-Fuzzer generates lawful finite reduction objects first, then injects controlled mathematical defects one at a time.

```text
valid 3SAT formula
        ↓
textbook 3SAT → CLIQUE graph
        ↓
valid witness clique
        ↓
controlled mutation
        ↓
ACCEPT / REJECT benchmark receipt
```

## Truth Boundary

Axezent AI PRK-Fuzzer does **not** claim to resolve P vs NP, prove global solver correctness, optimize every reduction, or automate all of complexity theory.

It verifies a narrower and stronger engineering claim:

> Given a seed and configuration, PRK-Fuzzer generates reproducible valid and invalid finite 3SAT-to-CLIQUE receipts for stress-testing deterministic reduction checkers.

## Why This Is Structure-Aware

Random fuzzing often fails at syntax. PRK-Fuzzer instead works at the mathematical structure layer:

- generate a satisfying assignment first;
- generate 3-literal clauses satisfied by that assignment;
- build exactly `3k` graph vertices for `k` clauses;
- compute the exact expected edge set from the textbook reduction rule;
- choose one true literal per clause as the witness clique;
- then inject isolated defects with predictable rejection outcomes.

This creates semantic tests instead of random broken files.

## Quick Start

Generate one valid receipt:

```bash
python prk_fuzzer.py generate-valid --variables 4 --clauses 5 --seed 42 --out generated_valid.json
```

Verify it with the included oracle checker:

```bash
python prk_oracle_checker.py verify generated_valid.json
```

Expected result:

```text
ACCEPT
```

Generate controlled invalid receipts:

```bash
python prk_fuzzer.py mutate-bad-edge generated_valid.json --out generated_bad_edge.json
python prk_fuzzer.py mutate-bad-k generated_valid.json --out generated_bad_k.json
python prk_fuzzer.py mutate-bad-assignment generated_valid.json --out generated_bad_assignment.json
python prk_fuzzer.py mutate-illegal-extra-edge generated_valid.json --out generated_illegal_extra_edge.json
python prk_fuzzer.py mutate-bad-clique-duplicate generated_valid.json --out generated_bad_clique_duplicate.json
```

Verify an invalid receipt:

```bash
python prk_oracle_checker.py verify generated_bad_edge.json
```

Expected result:

```text
REJECT
```

Generate a batch:

```bash
python prk_fuzzer.py batch --count 100 --variables 4 --clauses 5 --seed 42 --out-dir generated_batch
```

Run benchmark smoke test:

```bash
python prk_fuzzer.py benchmark --count 100 --variables 4 --clauses 5 --seed 42
```

Run tests:

```bash
python -m pytest test_fuzzer.py
```

Run Rust scaffold tests:

```bash
cargo test
cargo run
```

## Mutation Taxonomy

| Mutation | What it does | Expected result |
|---|---|---:|
| `bad_edge_missing_required_edge` | removes one required edge from the generated graph | `REJECT` |
| `bad_k_parameter_mismatch` | changes `k` away from the clause count | `REJECT` |
| `bad_assignment_flip_clique_variable` | flips a variable used by the witness clique | `REJECT` |
| `illegal_extra_same_clause_edge` | adds an edge inside one clause | `REJECT` |
| `bad_clique_duplicate_vertex` | duplicates a clique vertex | `REJECT` |
| `none` | no mutation; lawful generated receipt | `ACCEPT` |

## Included Files

```text
prk_fuzzer.py                              structure-aware fuzzer and receipt generator
prk_oracle_checker.py                      deterministic finite receipt checker
test_fuzzer.py                             Python test suite
axezent_ai_prk_receipt_v1.schema.json  JSON schema for generated receipts
generated_valid_receipt.json                generated valid example
generated_bad_edge_receipt.json             controlled missing-edge example
generated_bad_k_receipt.json                controlled bad-k example
generated_bad_assignment_receipt.json       controlled bad-assignment example
generated_illegal_extra_edge_receipt.json   controlled illegal-extra-edge example
generated_bad_clique_duplicate_receipt.json controlled bad-clique example
Cargo.toml, lib.rs, main.rs                Rust runtime scaffold
GITHUB_WORKFLOW_MAIN.yml                   visible backup workflow
```

## Browser Upload Edition

This package is intentionally flat at the repository root so GitHub browser upload does not lose folder structure.

The intended workflow file is:

```text
.github/workflows/main.yml
```

If your operating system hides `.github`, create that file manually in GitHub and paste the contents of `GITHUB_WORKFLOW_MAIN.yml`.

## Donations

Optional donations support open-source development and maintenance.

Cash App:

```text
$Axezent
```

Donations are voluntary support. They do not create equity, tokens, investment rights, ownership rights, or guaranteed support obligations.

## Commercial / Enterprise Direction

The open-source fuzzer provides reproducible test data for finite reduction receipt checkers.

Commercial layers can include:

- signed benchmark certificates;
- hosted verification dashboards;
- private reduction-fuzzer packs;
- educational complexity-theory tooling;
- high-volume fuzzing infrastructure;
- enterprise proof-artifact storage.

Contact: axezentai@Gmail.com

## License

MIT License. See `LICENSE`.
