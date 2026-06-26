# Official Elmer Case Workflow

Official Elmer test cases are excellent syntax evidence, but they should be distilled before being used as AI defaults.

## Source

Preferred source:

```text
ElmerCSC/elmerfem/fem/tests/
```

Use either:

- the installed local source tree matching the runtime version, or
- a GitHub snapshot with a recorded commit ID.

## Distillation Steps

1. Copy the official case into a local run directory.
2. Preserve the original SIF unchanged.
3. Run the original case and save logs.
4. If visualization requires extra output, create a separate `*_viz.sif`.
5. Extract metadata:
   - equations
   - solver procedures
   - variables and DOFs
   - materials
   - boundary conditions
   - mesh source
   - output files
6. Create or update a physics card in `knowledge/distilled/physics_cards/`.
7. Mark the template state:
   - `RAW`
   - `INDEXED`
   - `EVIDENCED`
   - `RUNNABLE`
   - `VALIDATED_TEMPLATE`

## First Recommended Cases

- `CavityLid`: Navier-Stokes
- `heateq`: heat equation
- `adv_diff1` through `adv_diff4`: advection-diffusion
- `elasticity` or `stress`: linear elasticity
- `fsi_beam`: fluid-structure interaction
- `EMWaveBoxHexas`: electromagnetic wave
- `elstat`: electrostatics

## Current Index

After downloading or updating `ElmerCSC/elmerfem/fem/tests`, rebuild the searchable index:

```powershell
python .\scripts\distill_sif_tests.py
```

Main outputs:

- `knowledge/distilled/test_case_index/SUMMARY.md`
- `knowledge/distilled/test_case_index/cases.jsonl`
- `knowledge/distilled/test_case_index/cases.csv`
- `knowledge/distilled/test_case_index/by_physics/`
- `knowledge/distilled/test_case_index/by_solver/`
- `knowledge/distilled/test_case_index/by_equation/`

## Rule

Do not copy the entire official Elmer source tree into this repository. Store distilled metadata, small templates, and source references instead.
