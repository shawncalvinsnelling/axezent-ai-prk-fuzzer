# Threat Model

Axezent AI PRK-Fuzzer is designed to generate finite receipts for deterministic reduction checkers.

## In scope

- malformed generated receipts
- missing-edge mutations
- illegal-extra-edge mutations
- incorrect `k` mutations
- incorrect witness assignment mutations
- duplicate clique-witness mutations
- reproducibility from seed
- verifier agreement between generated expectation and checker result

## Out of scope

- arbitrary malicious code execution outside normal Python file handling
- global solver correctness
- asymptotic complexity claims
- proving P vs NP
- checking reductions not implemented by the declared receipt schema
