# Fuzzing Specification

The fuzzer is structure-aware.

## Valid generation

1. Choose a deterministic random seed.
2. Generate a Boolean assignment over variables `x1 ... xn`.
3. Generate each 3-literal clause so that at least one literal is true under the assignment.
4. Build one vertex for each literal occurrence.
5. Build graph edges using the 3SAT-to-CLIQUE rule:
   - connect vertices from different clauses;
   - do not connect complementary literals.
6. Choose one true literal per clause as the witness clique.
7. Emit `expected_result = ACCEPT`.

## Controlled mutations

Each invalid receipt begins as a valid receipt and then receives exactly one logical defect.

This creates predictable, isolated rejection behavior instead of random syntax failures.
