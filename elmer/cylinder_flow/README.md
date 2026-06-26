# ElmerFEM cylinder-flow benchmark

This is a classic 2-D cylinder-flow benchmark. The reference parameters are taken from standard benchmark definitions; Gmsh, ElmerGrid and ElmerSolver perform all simulations.

## Reference parameters

- Channel: `2.2 m × 0.41 m`.
- Cylinder: radius `0.05 m`, centre `(0.20, 0.20) m`.
- Fluid: density `1 kg/m³`, dynamic viscosity `1e-3 Pa·s`.
- Inlet: parabolic profile with mean velocity `1 m/s`, smoothly ramped from rest.
- Reynolds number based on cylinder diameter: `100`.
- Transient integration: BDF2, `dt = 0.02 s`, `350` steps, final time `7 s`.
- Thermal case: initial/inlet `25 °C`, cylinder `100 °C`, `Cp = 1000 J/(kg·K)`, `k = 0.6 W/(m·K)`.
- Constant properties and zero gravity keep temperature passive, matching the intended forced-convection extension.

## Files and verified boundary IDs

- `cylinder.geo`: geometry and locally refined Gmsh mesh.
- `baseline.sif`: Elmer Navier–Stokes case.
- `thermal.sif`: Elmer Navier–Stokes + Heat Equation case.
- `species.sif`: Elmer Navier–Stokes + Fickian advection-diffusion case.
- Boundary `1`: inlet; `2`: outlet; `3`: upper/lower walls; `4`: cylinder.
- Refined converted mesh: 11,409 nodes and 22,298 triangular bulk elements (comparable to the COMSOL reference's 26,410 elements).

## Run and postprocess

```powershell
.\scripts\run_elmer_cylinder.ps1 -Case baseline
.\scripts\run_elmer_cylinder.ps1 -Case thermal
.\scripts\run_elmer_cylinder.ps1 -Case species
python .\scripts\postprocess_elmer_cylinder.py
```

## Fickian dilute-species case

- Elmer module: `AdvectionDiffusionSolver`, variable `Concentration` in `mol/m³`.
- Diffusivity: `1e-3 m²/s` (parameter selected because no species-specific value was supplied; diameter-based `Pe ≈ 100`).
- Inlet and initial concentration: `0 mol/m³`.
- Cylinder source: `Concentration Flux = 100 mol/(m²·s)` into the fluid.
- Channel walls: impermeable; outlet: natural convective outflow.
- For a unit out-of-plane depth, the prescribed source rate is `31.4159 mol/(m·s)`.

Raw Elmer VTU/PVD files and solver logs remain in this directory. Reviewed plots and numerical summaries are under `results/elmer/` at the workspace root.
