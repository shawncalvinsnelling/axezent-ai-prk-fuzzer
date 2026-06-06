# Tested Status

Local package tests run before release packaging:

- valid generated receipt accepts
- bad-edge receipt rejects
- bad-k receipt rejects
- bad-assignment receipt rejects
- illegal-extra-edge receipt rejects
- duplicate-clique receipt rejects
- batch generation agrees with oracle checker
- benchmark returns zero mismatches
- Python pytest suite passes
- source audit passes
- workflow YAML included

Rust scaffold is included and intended to be tested in GitHub Actions using the hosted Rust toolchain.
