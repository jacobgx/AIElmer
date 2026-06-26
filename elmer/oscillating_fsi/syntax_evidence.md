# Elmer syntax evidence

Installed solver: Elmer 26.2, compiled 2026-06-21 with MUMPS and HYPRE.

- Transient strong FSI, full-domain mesh update and interface kinematics:
  `/opt/src/elmerfem/fem/tests/fsi_box/box.sif`.
- Direct FSI load transfer and alternative explicit nodal load mapping:
  `/opt/src/elmerfem/fem/tests/fsi_beam/fsi.sif` and
  `/opt/src/elmerfem/fem/tests/fsi_beam_nodalforce/fsi.sif`.
- `FSI BC` implementation and the default availability of large deflection:
  `/opt/src/elmerfem/fem/src/modules/ElasticSolve.F90`.
- ALE flow and load calculation on a moving mesh:
  `/opt/src/elmerfem/fem/tests/RotatingBeamFlow/case.sif`.

The first executable checks use only syntax demonstrated by these installed
version-matched cases.
