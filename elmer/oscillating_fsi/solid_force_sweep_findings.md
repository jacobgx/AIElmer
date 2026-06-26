# Solid-only force sweep findings

Date: 2026-06-23

Purpose: check whether the Gaussian trigger force and solid-only structural
response are plausible before changing the mesh.

Cases:

- `solid_force_0p1N.sif`: peak tip traction 5 N/m, integrated peak force about 0.1 N.
- `solid_force_1N.sif`: peak tip traction 50 N/m, integrated peak force about 1 N.
- `solid_force_10N.sif`: peak tip traction 500 N/m, integrated peak force about 10 N.
- `solid_force_100N.sif`: peak tip traction 5000 N/m, integrated peak force about 100 N.

All cases use the same mesh and material model as `solid_only.sif`, run from
0 to 3 s with `dt = 0.01 s`, output every timestep, and keep results in separate
directories under `results_raw/solid_force_*`.

Summary from `results_raw/solid_force_sweep_summary.csv`:

| case | force N | tip ux min/max mm | tip uy min/max mm | abs tip uy peak mm | post-pulse half-range mm | uy freq Hz |
|---|---:|---:|---:|---:|---:|---:|
| `solid_force_0p1N` | 0.1 | -0.00298 / 0.00225 | -0.46673 / 0.46719 | 0.46719 | 0.46680 | 1.99 |
| `solid_force_1N` | 1.0 | -0.06245 / 0.00476 | -4.66727 / 4.67141 | 4.67141 | 4.66769 | 1.99 |
| `solid_force_10N` | 10.0 | -3.86123 / 0.01122 | -46.40364 / 46.40743 | 46.40743 | 46.38568 | 1.99 |
| `solid_force_100N` | 100.0 | -222.51711 / 0.29575 | -286.24971 / 284.25795 | 286.24971 | 285.11020 | 2.09 |

Log scan:

- No `warning`, `error`, `degenerate`, `inverted`, or `nan` matches were found
  in `logs/solid_force_*.log` or `logs/solid_force_*.wsl.log`.
- All four Elmer runs ended with `ALL DONE`.

Interpretation:

- The 0.1, 1, and 10 N responses are almost perfectly linear in `tip_uy`, so
  the current Elmer `Surface Traction 2 = force / 0.02 m` convention is behaving
  consistently for small and moderate deflections.
- A 1 N Gaussian pulse produces about 4.67 mm peak `tip_uy` in the dry structural
  model. Reaching the COMSOL reference y amplitude of about 34.38 mm by the
  trigger alone would require roughly 7.4 N in this linear range.
- The dry structural frequency is about 2.0 Hz from zero crossings. This is far
  below the COMSOL y reference frequency of about 5.3 Hz, so the structural
  stiffness/mass/boundary/thickness convention still needs review.
- The 10 N dry response already reaches the COMSOL-scale displacement amplitude,
  while the coupled 0-5 s baseline has much lower drag and a much smaller tip
  oscillation. This points to an additional FSI/load-transfer or flow-load
  magnitude issue beyond the trigger force equivalence.
