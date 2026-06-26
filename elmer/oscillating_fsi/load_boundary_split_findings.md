# Load boundary split findings

Date: 2026-06-23

Purpose: check whether the previous drag/lift mismatch came from the flow
solution itself or from postprocessing/integration boundaries.

New tools and cases:

- `postprocess/analyze_load_boundaries.py` classifies boundary line cells by
  geometry and sums `Flow Solution Loads` on:
  - cylinder
  - beam top
  - beam bottom
  - beam tip
  - beam top+bottom
  - beam all
  - cylinder+beam top/bottom
  - cylinder+beam all
- `fixed_flow_long.sif` is a corrected fixed-geometry flow case with no-slip
  on boundaries `4 5 7`, i.e. cylinder, beam sides, and beam tip.
- `fsi_tip_fsi_trigger_2s.sif` and `fsi_tip_trigger_only_2s.sif` are prepared
  for the next tip-boundary comparison, but were not run in this batch.

COMSOL audit:

- COMSOL defines drag/lift as `-intop1(spf.T_stressx)` and
  `-intop1(spf.T_stressy)`.
- `intop1` is a boundary integration operator on selected boundaries
  `8, 9, 10, 15, 16, 17, 18`, which correspond to the cylinder/beam obstacle
  boundaries, not only the beam FSI side walls.
- Therefore the closest Elmer comparison is the sign-flipped
  `cylinder_beam_all` group, not the old hard-coded geometry-id subset in
  `analyze_vtu.py`.

Existing FSI split-load result:

| segment | `cylinder_beam_all` drag range, Elmer sign N | sign-flipped drag range N | `cylinder_beam_all` lift range, Elmer sign N |
|---|---:|---:|---:|
| `fsi_pilot_1s` | -464.79 / -22.12 | 22.12 / 464.79 | -15.26 / 3.43 |
| `fsi_1to2` | -434.28 / -428.28 | 428.28 / 434.28 | -21.17 / -0.96 |
| `fsi_2to5` | -436.74 / -434.28 | 434.28 / 436.74 | -127.80 / -11.37 |

Combined CSV:

- `results_raw/fsi_0to5_loads_by_boundary.csv`

Interpretation:

- The previous `drag: 17.46 to 99.12 N` and `lift: -90.18 to 3.10 N` values
  from `analyze_vtu.py` are not valid for COMSOL comparison; they came from a
  too-narrow/hard-coded load integration subset.
- The corrected sign-flipped 2-5 s drag is about `434-437 N`, much closer to
  the COMSOL drag mean `457.3 N`.
- The corrected lift amplitude in 2-5 s is about half-range `58 N`, still below
  the COMSOL lift amplitude `149.78 N`, but it is no longer the same failure
  mode as the earlier drag mismatch.
- This shifts the main unresolved mismatch away from "fluid force magnitude is
  globally wrong" and toward structure/FSI response, lift oscillation amplitude,
  and tip displacement amplitude.

Corrected fixed-flow long run:

- `fixed_flow_long.sif` completed normally from 0 to 5 s.
- Log scan found no `warning`, `error`, `degenerate`, `inverted`, or `nan`
  matches.
- `results_raw/fixed_flow_long_loads_by_boundary.csv` contains the split-load
  output.
- For `t >= 4 s`:
  - `cylinder_beam_all_drag_N`: mean `-437.07 N`, half-range `0.10 N`.
  - Sign-flipped drag comparison value: mean `437.07 N`.
  - `cylinder_beam_all_lift_N`: mean `54.84 N`, half-range `6.97 N`.
- For the existing FSI combined split-load result at `t >= 4 s`:
  - `cylinder_beam_all_drag_N`: mean `-436.38 N`, half-range `0.44 N`.
  - Sign-flipped drag comparison value: mean `436.38 N`.
  - `cylinder_beam_all_lift_N`: mean `-74.76 N`, half-range `43.46 N`.

Fixed-flow interpretation:

- Corrected fixed-flow drag and FSI drag are mutually consistent after 4 s.
- Both are within about `4-5%` of the COMSOL drag mean `457.3 N`.
- The fixed-flow lift is not expected to match the oscillatory FSI lift, but it
  confirms that the corrected obstacle integration is producing plausible force
  magnitudes.
- The remaining quantitative mismatch is now concentrated in dynamic lift
  amplitude and beam-tip motion rather than steady drag scale.

Notes:

- `fixed_flow.sif` and `fixed_flow_mvp.sif` only constrain boundaries `4 5`
  for the fixed obstacle. They do not include `beam_tip` boundary `7`, so the
  older fixed-flow cases are not ideal for validation.
- `fixed_flow_long.sif` corrects that by applying no-slip to `4 5 7`.
