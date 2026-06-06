# Benchmarking

Run:

```bash
python prk_fuzzer.py benchmark --count 1000 --variables 4 --clauses 5 --seed 42
```

The benchmark generates six receipts per seed:

- one valid receipt
- one missing-edge receipt
- one bad-k receipt
- one bad-assignment receipt
- one illegal-extra-edge receipt
- one duplicate-clique receipt

The benchmark immediately verifies each generated receipt with the included oracle checker and reports mismatches.

A mismatch means the fuzzer's expected result disagreed with the deterministic checker result.
