# Solid Structural Variant Findings

Date: 2026-06-23

## Purpose

The dry solid 1 N baseline has a y-direction frequency near 2.0 Hz, while the current COMSOL comparison target is about 5.3 Hz. These solid-only variants test whether the mismatch is caused by Elmer's 2D formulation, an effective mass/thickness convention, or a stiffness scale.

Heavy runs were executed on a remote host using the user-local Elmer 26.2 runtime at:

```text
<elmer-runtime-path>
```

The remote case directory was:

```text
<case-directory>
```

Only small postprocessed CSV/log files were copied back locally.

## Run Health

| Case | ALL DONE | warnings/errors/NaN |
| --- | ---: | ---: |
| `solid_force_1N_no_plane_stress` | yes | 0 |
| `solid_force_1N_density_142kg` | yes | 0 |
| `solid_force_1N_E_39p3MPa` | yes | 0 |
| `solid_force_1N_quadmesh` | yes | 0 |

## Metrics

Reference baseline from the earlier sweep:

| Case | tip_y peak abs (mm) | post-pulse amp half-range (mm) | zero-crossing freq (Hz) |
| --- | ---: | ---: | ---: |
| `solid_force_1N` | 4.671 | 4.668 | 1.988 |

New variants:

| Case | tip_y peak abs (mm) | post-pulse amp half-range (mm) | peak-spacing freq (Hz) | zero-crossing freq (Hz) | error vs 5.3 Hz |
| --- | ---: | ---: | ---: | ---: | ---: |
| `solid_force_1N_no_plane_stress` | 4.119 | 4.096 | 2.174 | 2.194 | -58.6% |
| `solid_force_1N_density_142kg` | 5.642 | 3.796 | 5.263 | 5.179 | -2.3% |
| `solid_force_1N_E_39p3MPa` | 0.804 | 0.541 | 5.263 | 5.179 | -2.3% |
| `solid_force_1N_quadmesh` | 4.767 | 4.758 | n/a | 1.877 | -64.6% |

## Interpretation

Removing `Plane Stress = True` does not solve the frequency discrepancy. The frequency remains near 2.2 Hz, only slightly above the 1.99 Hz baseline.

Increasing the Elmer mesh from linear to quadratic elements also does not solve the discrepancy. The dry-solid frequency decreases to about 1.88 Hz while the displacement amplitude remains close to the baseline. This rules out the COMSOL displacement order 2 versus Elmer linear-triangle order as the main reason for the missing 5.3 Hz frequency.

Both the low-density variant and the high-stiffness variant move the dry-solid frequency to about 5.18 Hz, close to the 5.3 Hz COMSOL target. That confirms the frequency extraction is capable of seeing the target band and that the current model is mainly off by an effective stiffness-to-mass ratio of about `(5.3 / 2.0)^2 ~= 7`.

The two matching-frequency diagnostics are physically different:

- Lowering density to 142.4 kg/m3 keeps 1 N displacement scale similar or slightly larger than baseline.
- Raising Young's modulus to 39.3 MPa makes the beam much stiffer and cuts the displacement amplitude to about 0.54 mm post-pulse.

Because COMSOL Java records `E=5.6 MPa`, `rho=1000`, and no obvious thickness override, the low-density result should not be treated as a fix. It is a strong clue that a mass/thickness/2D-depth convention or structural domain interpretation is still mismatched.

## Next Step

Prioritize mass/thickness and geometry interpretation before more FSI sweeps:

1. Inspect COMSOL export more deeply for out-of-plane thickness, density scaling, or mass matrix settings.
2. Test Elmer solid-only variants that explicitly set or emulate thickness/depth if supported.
3. Recheck whether the Elmer solid body includes the same effective structure as COMSOL's rectangle-minus-circle solid.
4. Since quadratic Elmer elements did not increase the frequency, deprioritize element order as the primary explanation.
5. Only after resolving dry-solid frequency should FSI relaxation sweeps resume.
