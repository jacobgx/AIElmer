# Structural Variant Diagnostics

Date: 2026-06-23

## Purpose

These diagnostic SIF variants were created to investigate why the dry-solid natural frequency was near 2 Hz instead of the expected COMSOL y-direction target near 5.3 Hz.

## Prepared Independent SIF Variants

| Case | Purpose |
| --- | --- |
| `solid_force_1N_no_plane_stress.sif` | Remove `Plane Stress = True` and test Elmer default 2D elasticity behavior. |
| `solid_force_1N_density_142kg.sif` | Lower density to 142.4 kg/m³, approximately the mass scaling needed to move 2.0 Hz toward 5.3 Hz. Tests whether an effective thickness/mass convention could explain the mismatch. |
| `solid_force_1N_E_39p3MPa.sif` | Increase Young's modulus to 39.3 MPa, approximately the stiffness scaling needed to move 2.0 Hz toward 5.3 Hz. Diagnostic only, not a proposed physical fix. |

Run locally with:

```powershell
.\scripts\run_elmer_oscillating_fsi.ps1 -Case solid_force_1N_no_plane_stress
.\scripts\run_elmer_oscillating_fsi.ps1 -Case solid_force_1N_density_142kg
.\scripts\run_elmer_oscillating_fsi.ps1 -Case solid_force_1N_E_39p3MPa
```

## Results Summary

| Case | zero-crossing freq (Hz) | Main conclusion |
| --- | ---: | --- |
| `solid_force_1N_no_plane_stress` | 2.194 | Removing `Plane Stress = True` does not recover 5.3 Hz. |
| `solid_force_1N_density_142kg` | 5.179 | Artificial mass scaling can hit 5.3 Hz, but is not physically justified. |
| `solid_force_1N_E_39p3MPa` | 5.179 | Artificial stiffness scaling can hit 5.3 Hz, but contradicts COMSOL material input. |
| `solid_force_1N_quadmesh` | 1.877 | Quadratic Elmer mesh does not explain the frequency gap. |

Postprocessing:

```bash
python3 postprocess/analyze_solid_variants_pure.py . \
  --case solid_force_1N_no_plane_stress \
  --case solid_force_1N_density_142kg \
  --case solid_force_1N_E_39p3MPa \
  --summary-csv results_raw/solid_variant_summary.csv \
  --tip-csv-dir results_raw/solid_variant_tip_csv
```

The `_pure.py` postprocessing variant avoids numpy dependency for minimal-environment execution.

## Decision Logic

- If `no_plane_stress` moves frequency materially toward 5.3 Hz, focus on Elmer 2D solid formulation.
- If density scaling lands near 5.3 Hz, investigate COMSOL/Elmer mass-per-thickness conventions.
- If only high stiffness lands near 5.3 Hz, the frequency extractor and mesh can reproduce the target scale, but the physical stiffness/geometry mapping remains wrong.
- If none of these materially move the frequency, inspect root boundary constraints and displacement element order next.
