# Oscillating FSI reproduction

ElmerFEM reproduction of the COMSOL 6.3 `oscillating_fsi` verification model
(Turek-Hron FSI3 configuration).

Current status: Elmer baseline implemented and run through 0-5 s.

The case is numerically runnable, but it is not yet quantitatively matched to
the COMSOL reference amplitudes. The present Elmer baseline gives a much smaller
beam-tip oscillation than the COMSOL report, so the next task is calibration
and convergence study rather than basic implementation.

Planned cases:

- `fixed_flow.sif`: rigid cylinder and beam, transient Re=200 flow.
- `solid_only.sif`: dynamic elastic beam with the Gaussian trigger load.
- `fsi_mvp.sif`: short coarse-mesh ALE-FSI verification.
- `fsi.sif`: production 0-5 s coupled simulation, dt=0.01 s.

Completed checks:

- Mesh generation: 10878 nodes, 21434 triangular elements.
- `fixed_flow_mvp.sif`: completed.
- `solid_only.sif`: completed, bounded pulse response.
- `fsi_mvp.sif`: completed, confirms whole-fluid ALE mesh motion.
- Full coupled baseline: completed as restart segments 0-1, 1-2, and 2-5 s.

Baseline result files:

- Combined probe/load CSV: `results_raw/fsi_0to5_summary.csv`
- Archived 0-1 s VTU: `results_raw/fsi_pilot_1s/`
- 1-2 s VTU: `results_raw/fsi_1to2/`
- 2-5 s VTU: `results_raw/fsi_2to5/`

Observed 0-5 s baseline ranges from the combined CSV:

- Tip `ux`: -0.132 to -0.033 mm
- Tip `uy`: -0.561 to 3.311 mm
- Drag: 17.46 to 99.12 N
- Lift: -90.18 to 3.10 N

COMSOL reference ranges from the PDF/Java audit are much larger for the beam-tip
motion and drag level, so the current case should be treated as a stable
first implementation, not a validated reproduction.

The original MPH and PDF are never modified. The audited COMSOL Java export is
stored under `tmp/comsol_extract/oscillating_fsi.java`.
