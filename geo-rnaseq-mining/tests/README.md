# Tests

- `unit/`: fast contract and schema tests
- `integration/`: future small end-to-end workflow tests
- `fixtures/`: synthetic, non-biological test inputs
- `expected/`: expected outputs for integration tests

`unit/test_bulk_analysis.py` covers the bulk count and design safety contract,
including the rule that outlier flags never remove samples.

Run current tests with:

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
```
