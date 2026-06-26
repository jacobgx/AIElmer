# Elmer official elstat reproduction report

Generated: 2026-06-26 17:43:14 +08:00

## Summary

Status: success.

The official `elstat` test case was copied and run locally in the requested working copy. The original files under `tmp/elmerfem_remote_tree` were not modified. The copied `elstatics.sif` and `elmesh.grd` match the official originals by SHA256.

This is a steady-state electrostatics case. The rotation GIF generated here is a visualization-only camera rotation of one steady-state solution; it is not a physical transient animation.

## Paths

- Official source: `tmp\elmerfem_remote_tree\fem\tests\elstat`
- Run copy: `elmer\official_runs\elstat`
- WSL run path: `elmer/official_runs/elstat`
- Official SIF in copy: `elmer\official_runs\elstat\elstatics.sif`
- Visualization SIF: `elmer\official_runs\elstat\elstatics_viz.sif`

## Environment

Commands were run in WSL with an ElmerFEM 26.2 installation.

- `ElmerSolver --version`: `26.2-unknown`, compiled `2026-06-21`
- `ElmerGrid --version`: `26.2`
- Full version log: `elmer\official_runs\elstat\env_versions.log`

Note: the WSL launcher printed a localhost/NAT warning into the captured logs. The Elmer commands themselves completed successfully; see the explicit exit-code lines in the logs.

## Commands

Version record:

```bash
bash run_versions.sh > env_versions.log 2>&1
```

Official run:

```bash
cd elmer/official_runs/elstat
ElmerGrid 1 2 elmesh
ElmerSolver
```

Captured by:

```bash
bash run_official.sh > run.log 2>&1
```

Visualization run:

```bash
cd elmer/official_runs/elstat
ElmerSolver elstatics_viz.sif
```

Captured by:

```bash
bash run_viz.sh > run_viz.log 2>&1
```

Postprocessing:

```powershell
python elmer\official_runs\elstat\postprocess_elstat.py `
  > elmer\official_runs\elstat\postprocess.log 2>&1
```

## Official Run Result

Official run succeeded.

Key log lines from `run.log`:

- `ElmerGrid exit code: 0`
- `CompareToReferenceSolution: PASSED all 1 tests!`
- `MAIN: *** Elmer Solver: ALL DONE ***`
- `ElmerSolver exit code: 0`

Key computed values:

- Potential difference: `1000.0000000000000`
- Result norm: `584.15909814698102`
- Electric energy: `1.0671584813416691E-010`
- Capacitance: `2.1343169626833383E-016`

## Visualization SIF Changes

`elstatics_viz.sif` was created in the copied run directory. The official `elstatics.sif` was not edited.

Physical settings were kept the same:

- Solver: `StatElecSolve` / `StatElecSolver`
- Variable: `Potential`
- Mesh DB: `"." "elmesh"`
- Boundary condition 1: `Target Boundaries = 4`, `Potential = 0.0`
- Boundary condition 2: `Target Boundaries = 3`, `Potential = 1.0e3`
- Simulation type: `Steady State`

Minimal visualization changes:

- `Active Solvers(2) = 1 2` changed to `Active Solvers(4) = 1 2 3 4`
- `Calculate Electric Field = False` changed to `True`
- `Calculate Electric Flux = False` changed to `True`
- Added `ResultOutputSolver` as Solver 4 with VTU output:
  - `Output File Name = elstatics`
  - `Vtu Format = Logical True`
  - `Save Geometry Ids = Logical True`

Visualization run succeeded. `run_viz.log` confirms VTU output and vector fields:

- `CreateListForSaving: Scalar Field 1: potential`
- `CreateListForSaving: Vector Field 1: electric field`
- `CreateListForSaving: Vector Field 2: electric flux`
- `VtuOutputSolver: Writing the vtu file: elmesh/elstatics_t0001.vtu`
- `CompareToReferenceSolution: PASSED all 1 tests!`
- `ElmerSolver exit code: 0`

## Generated Files

Mesh files:

- `elmer\official_runs\elstat\elmesh\mesh.header`
- `elmer\official_runs\elstat\elmesh\mesh.nodes`
- `elmer\official_runs\elstat\elmesh\mesh.elements`
- `elmer\official_runs\elstat\elmesh\mesh.boundary`

VTU:

- `elmer\official_runs\elstat\elmesh\elstatics_t0001.vtu`

DAT:

- No `.dat` file was generated. The official SIF has `Filename = "scalars.dat"` commented out, so `SaveScalars` reported values in the solver log rather than writing a scalar data file.

Logs and scripts:

- `elmer\official_runs\elstat\env_versions.log`
- `elmer\official_runs\elstat\run.log`
- `elmer\official_runs\elstat\run_viz.log`
- `elmer\official_runs\elstat\postprocess.log`
- `elmer\official_runs\elstat\run_versions.sh`
- `elmer\official_runs\elstat\run_official.sh`
- `elmer\official_runs\elstat\run_viz.sh`
- `elmer\official_runs\elstat\postprocess_elstat.py`

Visualizations:

- `elmer\official_runs\elstat\visualizations\potential_slice.png`
- `elmer\official_runs\elstat\visualizations\potential_isosurface.png`
- `elmer\official_runs\elstat\visualizations\electric_field.png`
- `elmer\official_runs\elstat\visualizations\potential_rotation.gif`
- `elmer\official_runs\elstat\visualizations\postprocess_summary.txt`

## Postprocessing Notes

`pyvista`, `meshio`, `matplotlib`, and `imageio` were not available in the checked Python environments. The fallback postprocessor uses `numpy` and `Pillow`, parses the appended-binary VTU directly, and renders:

- `potential_slice.png`: potential on a mid-plane node slice.
- `potential_isosurface.png`: boundary-surface point rendering colored by potential. This is a surface rendering, not a marching-cubes isosurface.
- `electric_field.png`: log-scaled electric-field magnitude on the same slice, with in-slice vector arrows.
- `potential_rotation.gif`: camera rotation around the same steady-state boundary-surface rendering.

Postprocess statistics:

- Nodes: `32296`
- Boundary nodes rendered: `7376`
- Potential min/max: `0`, `1000`
- Electric field magnitude min/max: `1683.30054163`, `1552206736.4`
