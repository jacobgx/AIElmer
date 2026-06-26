# FSI Tip Boundary A/B Findings

Date: 2026-06-23

## Purpose

Compare two 0-2 s FSI variants to test whether applying the FSI velocity/ALE mesh constraint on the beam tip suppresses the trigger response.

- A: `fsi_tip_fsi_trigger_2s.sif`
  - Tip boundary has `FSI BC = True`, mesh update equals displacement, velocity equals mesh velocity, and the Gaussian trigger traction.
- B: `fsi_tip_trigger_only_2s.sif`
  - Tip boundary keeps only the Gaussian trigger traction; no tip FSI velocity or mesh constraint.

Both runs use independent result directories and do not overwrite the 0-5 s baseline.

## Outputs

- A result directory: `results_raw/fsi_tip_fsi_trigger_2s`
- B result directory: `results_raw/fsi_tip_trigger_only_2s`
- A tip probe CSV: `results_raw/fsi_tip_fsi_trigger_2s_summary.csv`
- B tip probe CSV: `results_raw/fsi_tip_trigger_only_2s_summary.csv`
- A corrected loads CSV: `results_raw/fsi_tip_fsi_trigger_2s_loads_by_boundary.csv`
- B corrected loads CSV: `results_raw/fsi_tip_trigger_only_2s_loads_by_boundary.csv`
- A/B combined metrics CSV: `results_raw/fsi_tip_ab_combined_metrics.csv`
- A/B trigger-window metrics CSV: `results_raw/fsi_tip_ab_combined_metrics_t1p5to2.csv`

Corrected loads below use sign-flipped `cylinder_beam_all` from `postprocess/analyze_load_boundaries.py`.

## Run Health

| Case | ALL DONE | VTU files | Real time | Coupled non-convergence warnings | Degenerate/Inverted/NaN |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: tip FSI + trigger | yes | 40 | 2262.40 s | 11 | 0 |
| B: trigger only | yes | 40 | 2684.62 s | 34 | 0 |

B did not improve coupled convergence. Its warnings appeared later than A, but the final count was higher.

## Full 0-2 s Metrics

| Case | tip_y mean (mm) | tip_y amp (mm) | drag mean (N) | drag amp (N) | lift mean (N) | lift amp (N) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A: tip FSI + trigger | 0.636 | 1.302 | 354.021 | 221.338 | 5.829 | 13.398 |
| B: trigger only | 1.431 | 3.621 | 397.032 | 260.192 | -1.424 | 38.352 |

The full-window drag amplitude is dominated by inlet ramp-up and is not a steady oscillation metric.

## Trigger Window Metrics, 1.5-2.0 s

| Case | tip_y mean (mm) | tip_y amp (mm) | drag mean (N) | drag amp (N) | lift mean (N) | lift amp (N) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A: tip FSI + trigger | 1.638 | 0.315 | 433.600 | 0.632 | 11.581 | 11.322 |
| B: trigger only | 1.297 | 1.785 | 429.530 | 0.672 | 7.659 | 16.619 |

COMSOL reference amplitudes from the current comparison set are:

- tip_y amp: 34.38 mm
- drag amp: 22.66 N
- lift amp: 149.78 N

B increases the trigger-window tip_y amplitude by about 5.7x relative to A, but it is still only about 5.2% of the COMSOL tip_y amplitude. B also increases lift amplitude modestly, but only to about 11.1% of the COMSOL lift amplitude. Drag mean remains close to the previous corrected-load baseline, while trigger-window drag amplitude remains much too small in both variants.

## Interpretation

Removing the tip FSI velocity/ALE constraint has a measurable effect on dynamic response, so the tip boundary treatment is not completely neutral. However, it does not recover COMSOL-scale motion and it worsens coupled convergence in this 2 s test.

This points back to the larger structural/dynamic mismatch rather than the tip FSI boundary being the sole cause. The dry solid frequency discrepancy remains the higher-value next target.

## Next Recommended Step

Run focused solid-only structural variants before more FSI sweeps:

1. Plane strain / no `Plane Stress` variant.
2. Thickness or density scaling checks.
3. Fixed-root boundary variant against COMSOL selections 19 and 20.
4. If practical, test a higher-order displacement discretization or a mesh/order setting closer to COMSOL's displacement order 2.

Keep these as independent SIF/result directories and compare dry-solid frequency and tip_y response before returning to relaxation sweeps.
