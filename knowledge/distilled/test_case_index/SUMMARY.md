# Official Elmer fem/tests Index

- Generated UTC: `2026-06-26T10:42:06.895286+00:00`
- Repository: `https://github.com/ElmerCSC/elmerfem.git`
- Branch: `devel`
- Commit: `4a05b99b2cf548198eae1140973bf33ccf630229`
- Case directories: `971`
- SIF files: `1130`

## Main Outputs

- `cases.jsonl`: complete machine-readable SIF index.
- `cases.csv`: compact spreadsheet-friendly index.
- `by_physics/`: case lists grouped by inferred physics.
- `by_solver/`: case lists grouped by `module/procedure`.
- `by_equation/`: case lists grouped by equation labels.

## Inferred Tag Counts

- `postprocessing`: 600
- `heat`: 330
- `electromagnetics`: 210
- `elasticity`: 173
- `navier_stokes`: 132
- `beam_shell_plate`: 108
- `other`: 75
- `electrostatics_current`: 70
- `acoustics_wave`: 65
- `linear_solver_benchmark`: 53
- `poisson`: 52
- `mesh_partitioning`: 51
- `contact`: 31
- `optimization_control`: 28
- `fsi`: 24
- `radiation`: 20
- `levelset_free_surface`: 19
- `particles`: 18
- `advection_diffusion`: 9
- `advection_reaction`: 7
- `phase_change`: 5
- `porous_richards`: 4
- `battery_electrochemistry`: 2

## Top Solver Procedures

- `SaveData/SaveScalars`: 441
- `ResultOutputSolve/ResultOutputSolver`: 266
- `HeatSolve/HeatSolver`: 177
- `MagnetoDynamics/MagnetoDynamicsCalcFields`: 113
- `StressSolve/StressSolver`: 101
- `SaveData/SaveLine`: 100
- `RigidMeshMapper/RigidMeshMapper`: 69
- `MagnetoDynamics/WhitneyAVSolver`: 68
- `ElasticSolve/ElasticSolver`: 61
- `ShellSolver/ShellSolver`: 44
- `FlowSolve/FlowSolver`: 39
- `HeatSolveVec/HeatSolver`: 32
- `CircuitsAndDynamics/CircuitsOutput`: 32
- `FluxSolver/FluxSolver`: 31
- `VectorHelmholtz/VectorHelmholtzSolver`: 27
- `VectorHelmholtz/VectorHelmholtzCalcFields`: 27
- `StatCurrentSolve/StatCurrentSolver`: 25
- `StatElecSolve/StatElecSolver`: 24
- `MagnetoDynamics/WhitneyAVHarmonicSolver`: 24
- `ModelPDE/AdvDiffSolver`: 21
- `Poisson/PoissonSolver`: 20
- `CircuitsAndDynamics/CircuitsAndDynamicsHarmonic`: 20
- `MagnetoDynamics2D/MagnetoDynamics2DHarmonic`: 20
- `StructuredMeshMapper/StructuredMeshMapper`: 20
- `SaveData/SaveMaterials`: 19
- `MagnetoDynamics2D/MagnetoDynamics2D`: 18
- `MagnetoDynamics2D/bSolver`: 15
- `CoilSolver/CoilSolver`: 15
- `DirectionSolver/DirectionSolver`: 13
- `WPotentialSolver/Wsolve`: 13

## Top Equation Labels

- `SaveScalars`: 278
- `Heat Equation`: 217
- `ResultOutput`: 116
- `result output`: 110
- `MGDynamicsCalc`: 88
- `Navier-Stokes`: 86
- `SaveLine`: 79
- `MGDynamics`: 77
- `MeshDeform`: 69
- `Shell equations`: 42
- `HeatSolver`: 39
- `calcfields`: 35
- `Linear elasticity`: 34
- `Circuits`: 32
- `Circuits Output`: 32
- `sv`: 31
- `Mag`: 30
- `ComputeFlux`: 30
- `VtuOutput`: 29
- `VectorHelmholtz`: 26
- `Poisson`: 23
- `ModelPDE`: 21
- `Save Scalars`: 20
- `Stress Analysis`: 19
- `Mesh Update`: 19
- `HeatEq`: 18
- `save scalars`: 17
- `SaveMaterial`: 17
- `save line`: 16
- `Elasticity Solver`: 15
