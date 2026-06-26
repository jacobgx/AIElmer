# Test Case Index

This directory stores structured metadata for official and local Elmer examples.

Recommended files:

- `cases.jsonl`: one JSON object per SIF file.
- `by_solver/`: filtered lists by solver procedure.
- `by_physics/`: filtered lists by physical model.
- `minimal_templates/`: small, runnable, curated templates.

Do not store full upstream source trees here. Keep source paths and commit IDs instead.

## Current Official Index

The official `ElmerCSC/elmerfem/fem/tests` snapshot has been indexed from:

```text
tmp/elmerfem_remote_tree/fem/tests
```

Generated outputs:

- `SUMMARY.md`: human-readable summary.
- `metadata.json`: source snapshot and aggregate counts.
- `cases.jsonl`: complete machine-readable index.
- `cases.csv`: spreadsheet-friendly index.
- `by_physics/`: inferred tag lists.
- `by_solver/`: solver procedure lists.
- `by_equation/`: equation label lists.

Rebuild with:

```powershell
python .\scripts\distill_sif_tests.py
```
