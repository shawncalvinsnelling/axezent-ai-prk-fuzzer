# Receipt Specification

Schema name:

```text
AXEZENT-AI-PRK-RECEIPT-v1
```

Truth label:

```text
BOUNDED_FINITE_REDUCTION_CHECK
```

Launch reduction:

```text
3SAT_TO_CLIQUE
```

Required top-level fields:

- `schema`
- `truth_label`
- `reduction`
- `input_instance`
- `target_instance`
- `witness`
- `checker_expectation`
- `fuzzer_metadata`

The checker verifies semantic cross-field rules that JSON Schema cannot express alone, including `|V| = 3k`, exact edge-set construction, witness-clique validity, and assignment satisfaction.
