# Validation plan

1. DONE: Verify physical body and boundary IDs from `mesh.names` and element
   counts.
2. DONE: Run fixed-body transient flow; require clean completion, Re=200 wake
   and no unknown-keyword warnings.
3. DONE: Run solid-only transient pulse response; require finite bounded
   displacement.
4. DONE: Run short ALE-FSI MVP and inspect displacement of interior fluid nodes
   to prove that the whole fluid mesh participates in mesh motion.
5. DONE/PARTIAL: Run 0-5 s baseline with dt=0.01 s and extract tip displacement
   and drag/lift. The run completed, but the resulting amplitudes do not yet
   match the COMSOL reference.
6. TODO: Investigate amplitude mismatch. Candidate causes:
   - Gaussian point-load replacement by a distributed tip traction.
   - Load and force sign/normal convention in Elmer `flow solution loads`.
   - Missing or different COMSOL FSI coupling terms on the solid tip boundary.
   - Mesh/time-step sensitivity and structural damping implied by solver
     relaxation.
7. DONE/PARTIAL: Remote short screens for coupling and symmetry:
   - `fsi_relax_0p3_2s` failed early, confirming relaxation increase is unstable.
   - `fsi_inlet_vpulse_2s` completed but remained far below COMSOL amplitudes.
8. NEXT: Test whether Elmer's linear stabilized flow discretization is damping the wake/FSI response. Prefer remote higher-order/refined FSI or fixed-flow screening before changing physical material parameters.
9. TODO: Repeat with dt=0.005 s after calibration.
10. TODO: Repeat with one refined mesh and dt=0.0025 s.

Acceptance targets after convergence study: frequency error <=5%; displacement
and force amplitude error <=10%; no inverted elements or unexplained failures.

Current baseline status: stable, not accepted.
