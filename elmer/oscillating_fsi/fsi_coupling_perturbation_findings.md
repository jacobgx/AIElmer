# FSI Coupling and Perturbation Findings

Date: 2026-06-23

## Remote Runs

Heavy runs were executed on a remote host using:

```text
<case-directory>
```

Two short 0-2 s screening cases were added:

| Case | Change | Status |
| --- | --- | --- |
| `fsi_relax_0p3_2s` | Structural nonlinear relaxation raised from `0.2` to `0.3` | Failed early with degenerate solid elements and segfault. |
| `fsi_inlet_vpulse_2s` | Baseline FSI plus small inlet y-velocity pulse, peak `0.04 m/s` near `t=1.0 s` | Completed on a remote host, 40 VTU outputs. |

The earlier `fsi_relax_0p5_2s` failure is therefore not an isolated threshold: even `0.3` is unstable for this coupled setup.

## Inlet Perturbation Metrics

Corrected loads use sign-flipped `cylinder_beam_all`, consistent with the previous load split.

| Case | Window | tip_y amp (mm) | drag mean (N) | drag amp (N) | lift mean (N) | lift amp (N) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `fsi_tip_fsi_trigger_2s` | 1.5-2.0 s | 0.315 | 433.600 | 0.632 | 11.581 | 11.322 |
| `fsi_tip_trigger_only_2s` | 1.5-2.0 s | 1.785 | 429.530 | 0.672 | 7.659 | 16.619 |
| `fsi_inlet_vpulse_2s` | 1.5-2.0 s | 0.481 | 433.607 | 0.623 | 12.202 | 10.784 |

`fsi_inlet_vpulse_2s` completed without `ERROR`, `Degenerate`, or `Failed convergence tolerances` matches, but it did produce 29 `WARNING` matches. The warning count reflects difficult coupled iterations rather than a failed solve.

## Interpretation

The small asymmetric inlet seed does not produce COMSOL-scale response. In the 1.5-2.0 s comparison window, it only raises tip-y amplitude from `0.315 mm` to `0.481 mm` relative to the FSI-tip baseline, and lift amplitude remains near `11 N`.

This weak response means the main mismatch is unlikely to be caused only by a missing symmetry-breaking seed. The next higher-value direction is numerical dissipation/discretization:

- COMSOL uses fluid shape order `4` and solid displacement order `2`.
- The current Elmer FSI cases use linear triangles with stabilization.
- Fixed-flow and seeded-FSI responses both remain too weak compared with COMSOL lift amplitude `149.78 N`.

## Next Step

Prioritize a remote screening of higher-order/refined flow discretization before changing physical material parameters:

1. Test a short FSI case on remote `mesh_quad` if runtime is acceptable.
2. If quadratic FSI is too expensive or unstable, run a fixed-obstacle quadratic/refined flow case and compare corrected lift growth.
3. Review Elmer stabilization options against COMSOL's exported `CrosswindDiffusion=false` and high-order fluid discretization.
