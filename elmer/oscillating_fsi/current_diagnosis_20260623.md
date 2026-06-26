# Current Diagnosis

Date: 2026-06-23

## Remote Execution

Heavy runs are now running on a remote host, not locally. Since remote host did not provide Elmer in PATH, a user-local Elmer 26.2 runtime was staged at:

```text
<elmer-runtime-path>
```

The runtime uses remote host OpenMPI from `<openmpi-install-path>`. Solid-only runs completed successfully on a remote host.

## Dry Solid Frequency Reinterpretation

The previous suspicion that Elmer dry-solid frequency is wrong because it is near 2 Hz is likely incorrect.

For a cantilever with:

- `E = 5.6 MPa`
- `rho = 1000 kg/m3`
- height `h = 0.02 m`
- free length `L = 0.35 m`

the Euler-Bernoulli first bending estimate is about `1.97 Hz`, matching the Elmer dry-solid result (`~1.99 Hz`). A 5.3 Hz dry-solid frequency would correspond to an effective free length of about `0.214 m`, which is not the modeled beam length.

Therefore, the COMSOL `5.3 Hz` y-displacement target should be treated as a full FSI/vortex response frequency, not as a dry-solid natural frequency target.

## Completed Solid Diagnostics

| Case | zero-crossing freq (Hz) | Main conclusion |
| --- | ---: | --- |
| `solid_force_1N_no_plane_stress` | 2.194 | Removing `Plane Stress = True` does not recover 5.3 Hz. |
| `solid_force_1N_density_142kg` | 5.179 | Artificial mass scaling can hit 5.3 Hz, but is not physically justified. |
| `solid_force_1N_E_39p3MPa` | 5.179 | Artificial stiffness scaling can hit 5.3 Hz, but contradicts COMSOL material input. |
| `solid_force_1N_quadmesh` | 1.877 | Quadratic Elmer mesh does not explain the frequency gap. |

## FSI Dynamics Diagnosis

The corrected fixed-flow load split shows that the fixed obstacle flow remains nearly steady at `t>=4 s`:

- fixed-flow corrected drag amp: about `0.10 N`
- fixed-flow corrected lift amp: about `7.0 N`

The FSI baseline does increase lift response, but still not enough:

- FSI corrected lift amp at `t>=4 s`: about `43.5 N`
- COMSOL lift amp target: about `149.8 N`

This points to the main remaining issue being the growth of unsteady FSI/vortex dynamics, not dry structural frequency.

## Relaxation Screening

A remote host screening run was attempted:

```text
fsi_relax_0p5_2s.sif
```

This only changed the structural nonlinear relaxation factor from `0.2` to `0.5`. It failed before writing VTU output with repeated degenerate element errors and a MUMPS/segfault failure. This means simply increasing structural relaxation is not a stable path in the current configuration.

A less aggressive remote case was also attempted:

```text
fsi_relax_0p3_2s.sif
```

This also failed early with degenerate solid elements near the beam tip and a segfault. The relaxation-increase path should now be deprioritized.

## Asymmetric Seed Screening

A remote host case with a small inlet y-velocity pulse completed:

```text
fsi_inlet_vpulse_2s.sif
```

The pulse used peak `v = 0.04 m/s` near `t = 1.0 s`, about 2% of the inlet mean speed. It completed to 2 s with 40 VTU outputs and no `ERROR`, `Degenerate`, or `Failed convergence tolerances` matches, but with 29 warning matches.

In the 1.5-2.0 s comparison window:

- `tip_uy` amplitude: `0.481 mm`
- corrected drag amplitude: `0.623 N`
- corrected lift amplitude: `10.784 N`

Compared with `fsi_tip_fsi_trigger_2s`, the inlet seed only raises `tip_uy` amplitude from `0.315 mm` to `0.481 mm`; lift amplitude does not improve. The weak response is therefore not explained by a missing tiny asymmetry seed alone.

## Next Recommended Direction

Do not tune dry-solid E or density to force 5.3 Hz. Instead:

1. Investigate why the flow/FSI system is not developing strong unsteady lift.
2. Deprioritize structural relaxation increases: both `0.3` and `0.5` fail with degenerate elements.
3. Deprioritize tiny inlet asymmetry as a standalone fix: the completed vpulse run remains far below COMSOL amplitude.
4. Prioritize numerical-dissipation and discretization screening: COMSOL uses fluid order `4`, while the current Elmer FSI is linear-triangle stabilized.
5. Review Elmer stabilization options against COMSOL's `CrosswindDiffusion=false` and, if feasible, run a short remote higher-order/refined FSI or fixed-flow screen.

## New Fixed-Flow Discretization Screen

The first remote no-stabilization fixed-flow screen completed:

```text
fixed_flow_nostab_2s
```

In the same early `t=1.5..2.0 s` window, the corrected lift amplitude increased from about `22.9 N` in the existing `fixed_flow_long` baseline to about `37.8 N` in `fixed_flow_nostab_2s`. This is a meaningful increase, but it must still be confirmed over the COMSOL comparison window `t=4..5 s`.

A long confirmation case has therefore been prepared:

```text
fixed_flow_nostab_5s
```

The quadratic fixed-flow screen has also completed:

```text
fixed_flow_quad_2s
```

In the same `t=1.5..2.0 s` window, corrected lift amplitude was about `27.2 N`. This is only a modest increase over the old baseline and weaker than the no-stabilization result.

## Direct COMSOL Target Extraction

The original COMSOL 6.3 MPH installed on secondary host was opened read-only with COMSOL `6.3.0.290`. Its table `tbl1` contains 1552 rows of time, drag, lift, tip-x, and tip-y data. Direct `t=4..5 s` metrics from that table are:

- drag mean: `451.48 N/m`, drag amp: `24.83 N/m`
- lift amp: `154.97 N/m`
- tip-y amp: `32.16 mm`

These direct table values should replace earlier approximate plot-read targets.

## Long No-Stabilization Fixed-Flow Confirmation

The promoted remote case completed on a remote host:

```text
fixed_flow_nostab_5s
```

It exited with status `0`. In the COMSOL comparison window `t=4..5 s`, corrected load metrics were:

- drag mean: `430.52 N`, drag amp: `7.26 N`
- lift mean: `-58.25 N`, lift amp: `537.79 N`

This is a decisive clue: the stabilized Elmer fixed-flow baseline is too dissipative for wake/lift dynamics, but the attempted stabilization reduction over-shoots the COMSOL lift amplitude (`154.97 N/m`) by a large factor. The next stage should calibrate stabilization/flow discretization before promoting to FSI.

## FlowSolve Stabilization Audit And Calibration

New source/documentation audit on 2026-06-24 used the remote host Elmer runtime and the official Elmer source tree. The relevant FlowSolve keywords are not a continuous SUPG coefficient. `FlowSolve.F90` exposes these method branches through `Stabilization Method`:

- `stabilized`
- `bubbles`
- `pbubbles`
- `p2/p1` or `p2p1`
- `vms`

It also reads boolean `Div Discretization` and `Gradp Discretization`. `SOLVER.KEYWORDS` registers `Stabilization Method`, `Stabilize`, `Bubbles`, `Div Discretization`, and `Gradp Discretization`, but no scalar stabilization-strength coefficient was found.

Important correction: the existing cases named `fixed_flow_nostab_*` are not truly no-stabilization Galerkin runs. Their logs show:

```text
FlowSolver: Defaulting to "stabilized" method
```

This happens even when the SIF contains `Stabilize = False`, unless a recognized `Stabilization Method` is supplied. Therefore, keep the old case names for file continuity, but interpret them as attempted stabilization-reduction/default-stabilized variants, not clean no-stabilization results.

A fixed-flow calibration batch completed on a remote host:

```text
remote host_run_fixed_flow_stabilization_calibration.sh
```

Remote results in the COMSOL comparison window `t=4..5 s`:

| Case | Exit code | Samples | Drag mean | Drag amp | Lift mean | Lift amp | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `fixed_flow_nostab_dt005_5s` | 0 | 21 | `429.48 N` | `8.97 N` | `1.84 N` | `582.83 N` | Reducing dt from 0.01 to 0.005 does not remove the large over-response. |
| `fixed_flow_nostab_outfine_5s` | 0 | 101 | `430.51 N` | `7.48 N` | `-63.70 N` | `555.17 N` | Output at 0.01 s still shows large continuous oscillation, so 0.05 s sampling is not the cause. |
| `fixed_flow_bubbles_5s` | 0 | 21 | `432.88 N` | `0.34 N` | `-58.38 N` | `51.79 N` | Recognized `bubbles` branch is stable and intermediate, but still well below COMSOL lift amp `154.97 N/m`. |
| `fixed_flow_vms_5s` | 1 | n/a | n/a | n/a | n/a | n/a | Failed around `t=1.15 s` with solution norm blow-up and NaN. |

Time-series spot checks:

- `fixed_flow_nostab_outfine_5s` has no single-step jump larger than half its `t=4..5 s` lift range, so the huge amplitude is not a one-sample spike.
- A simple 1-15 Hz DFT screen over `t=4..5 s` identifies the dominant coarse bin near `4 Hz` for the attempted-reduction cases and for `bubbles`.

Current fixed-flow ladder is therefore:

| Flow setting | `t=4..5 s` corrected lift amp |
| --- | ---: |
| Stabilized baseline `fixed_flow_long` | `6.97 N` |
| `bubbles` | `51.79 N` |
| COMSOL target | `154.97 N/m` |
| attempted reduction/default-stabilized high-response variants | `537.79-582.83 N` |

Decision: do not promote any of these fixed-flow settings directly to FSI yet. `bubbles` is too damped, the attempted-reduction branch is far too energetic, and `vms` is unstable on the current mesh/time-step/solver settings. The next fixed-flow screens should target the gap between `bubbles` and the high-response branch, for example `pbubbles`, `p2p1`/quadratic-compatible variants, and `Div Discretization` / `Gradp Discretization` combinations, before any long FSI run.

## Next Fixed-Flow Screen Preparation And Execution, 2026-06-24

The next fixed-flow calibration batch was first prepared while the remote compute hosts were unreachable:

- `ssh remote host` resolved to the compute node but TCP port `22` timed out repeatedly.
- `Test-NetConnection` to the compute node reported `TcpTestSucceeded: False`.
- The fallback probe through `local workstation` also timed out before reaching remote host.
- Since secondary host must be reached through remote host, secondary host was not usable in this state.

No local heavy Elmer computation was run.

A new remote host batch script was added:

```text
remote host_run_fixed_flow_next_screen.sh
```

It generates and runs these `0..5 s`, `dt=0.01`, output-every-`0.05 s` fixed-flow cases, with per-case logs, stderr, exit codes, corrected `cylinder_beam_all` load summaries, row CSVs, ERROR/NaN/failed-convergence flags, max lift step jump, and a simple `1..15 Hz` DFT frequency screen:

| Case | Intended setting |
| --- | --- |
| `fixed_flow_pbubbles_5s` | `Stabilization Method = pbubbles`, `Stabilize = False`, `Bubbles = False` |
| `fixed_flow_p2p1_5s` | `Stabilization Method = p2p1`, `Stabilize = False`, `Bubbles = False` |
| `fixed_flow_divdisc_5s` | attempted-reduction/default-stabilized branch plus `Div Discretization = True` |
| `fixed_flow_gradpdisc_5s` | attempted-reduction/default-stabilized branch plus `Gradp Discretization = True` |
| `fixed_flow_div_gradp_disc_5s` | attempted-reduction/default-stabilized branch plus both discretization flags |
| `fixed_flow_bubbles_gradpdisc_5s` | `bubbles` branch plus `Gradp Discretization = True` |
| `fixed_flow_bubbles_divdisc_5s` | `bubbles` branch plus `Div Discretization = True` |
| `fixed_flow_pbubbles_gradpdisc_5s` | `pbubbles` branch plus `Gradp Discretization = True` |

remote host connectivity later recovered, and the batch was executed remotely on a remote host from `2026-06-24T14:04:44+08:00` to `2026-06-24T15:26:41+08:00`. All eight cases exited with status `0`; the health scan found no `ERROR`, `NaN`, or `Failed convergence` matches. Local copies of the combined summaries are stored at:

```text
results_raw/remote_next_screen_20260624/fixed_flow_next_screen_t4to5.csv
results_raw/remote_next_screen_20260624/fixed_flow_next_screen_health.csv
logs/fixed_flow_next_screen_driver.log
```

Corrected `cylinder_beam_all` results over `t=4..5 s`:

| Case | Exit | Drag mean | Drag amp | Lift mean | Lift amp | DFT bin | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `fixed_flow_pbubbles_5s` | 0 | `432.88 N` | `0.34 N` | `-58.38 N` | `51.79 N` | `4.25 Hz` | Recognized branch, but numerically identical to `bubbles`; still too damped. |
| `fixed_flow_p2p1_5s` | 0 | `432.88 N` | `0.34 N` | `-58.38 N` | `51.79 N` | `4.25 Hz` | Also identical to `bubbles` on the current linear mesh; not an intermediate response. |
| `fixed_flow_divdisc_5s` | 0 | `430.51 N` | `7.26 N` | `-58.25 N` | `537.79 N` | `4.50 Hz` | Returns to the high-response attempted-reduction/default-stabilized branch. |
| `fixed_flow_gradpdisc_5s` | 0 | `-6.01 N` | `31.31 N` | `28.74 N` | `40.01 N` | `1.00 Hz` | Force scale becomes nonphysical; reject. |
| `fixed_flow_div_gradp_disc_5s` | 0 | `-12.75 N` | `33.94 N` | `27.11 N` | `43.60 N` | `1.00 Hz` | Force scale remains nonphysical; reject. |
| `fixed_flow_bubbles_gradpdisc_5s` | 0 | `-0.55 N` | `0.09 N` | `0.63 N` | `0.27 N` | `1.00 Hz` | Loads collapse almost to zero; reject. |
| `fixed_flow_bubbles_divdisc_5s` | 0 | `432.88 N` | `0.34 N` | `-58.38 N` | `51.79 N` | `4.25 Hz` | Same as `bubbles`; still too damped. |
| `fixed_flow_pbubbles_gradpdisc_5s` | 0 | `-0.55 N` | `0.09 N` | `0.63 N` | `0.27 N` | `1.00 Hz` | Loads collapse almost to zero; reject. |

No screened case landed in the approximate `120..220 N` corrected lift-amplitude range. Therefore no new GIF was generated and no short FSI probe should be started from this batch. The best numerically sane case by closeness to COMSOL `154.97 N/m` is still the weak `bubbles`/`pbubbles`/`p2p1` family at about `51.79 N`, but it is far below target. The next step should not be a long FSI run; it should move to a different fixed-flow axis such as mesh/order refinement, a quadratic-compatible `p2p1` setup, or more COMSOL-like high-order/mapped near-beam discretization.

## Mesh/Order Fixed-Flow Ladder And FSI Probe, 2026-06-24

A mesh/order fixed-flow ladder was run on a remote host:

```text
remote host_run_fixed_flow_mesh_order_ladder.sh
```

New meshes:

- `mesh_refined_linear`: `24452` nodes, `48473` linear triangular bulk elements.
- `mesh_refined_quad`: `97377` nodes, `48473` quadratic triangular bulk elements.

Corrected `cylinder_beam_all` results over `t=4..5 s`:

| Case | Exit | Drag mean | Drag amp | Lift amp | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| `fixed_flow_refined_linear_bubbles_5s` | 0 | `434.84 N` | `1.33 N` | `123.58 N` | First fixed-flow intermediate candidate; in the `120..220 N` target band. |
| `fixed_flow_quad_p2p1_5s` | 0 | `429.03 N` | `3.39 N` | `337.56 N` | True quadratic `p2p1` changes the wake strongly but overshoots the target. |
| `fixed_flow_refined_quad_p2p1_5s` | 0 | `432.16 N` | `3.25 N` | `326.07 N` | Quadratic plus refined mesh remains too energetic. |

The candidate `fixed_flow_refined_linear_bubbles_5s` was rerun with output every `0.01 s`:

| Case | Exit | Samples | Drag mean | Drag amp | Lift amp | DFT bin | Health |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `fixed_flow_refined_linear_bubbles_outfine_5s` | 0 | 101 | `434.86 N` | `1.41 N` | `140.32 N` | `4.50 Hz` | No `ERROR`, `NaN`, `Failed convergence`, or jump-over-half-range flag. |

This confirms the refined-linear `bubbles` fixed-flow candidate is not a coarse-output artifact and is currently the best fixed-flow match to COMSOL lift amplitude `154.97 N/m`.

A conservative short FSI probe was then attempted:

```text
fsi_refined_linear_bubbles_probe_2s
```

It used `mesh_refined_linear`, `Stabilization Method = bubbles`, `Stabilize = False`, `Bubbles = True`, and kept structural relaxation at `0.2`. The run was intentionally terminated after it reached about `t=0.42 s` because it was extremely slow and emitted repeated coupled-system nonconvergence warnings. It exited with status `143` after termination, not a natural solver finish.

Current partial FSI rows through `t=0.40 s` are stored at:

```text
results_raw/fsi_refined_linear_bubbles_probe_20260624/fsi_refined_linear_bubbles_probe_2s_current_t0to0p4.csv
results_raw/fsi_refined_linear_bubbles_probe_20260624/fsi_refined_linear_bubbles_probe_2s_rows_t0to0p4.csv
logs/fsi_refined_linear_bubbles_probe_2s.log
logs/fsi_refined_linear_bubbles_probe_2s_driver.log
```

Partial metrics over `t=0.05..0.40 s`:

- `tip_uy` amplitude: `0.187 mm`
- drag mean: `107.45 N`, drag amp: `88.29 N`
- lift mean: `50.16 N`, lift amp: `216.28 N`
- the final available row at `t=0.40 s` jumps to lift `415.61 N`
- at least `25` repeated `Coupled system did not converge` warnings were present before termination
- no `Degenerate` or `NaN` matches were found before termination

Interpretation: the fixed-flow candidate is valuable, but the direct refined-mesh FSI probe is not yet numerically healthy. Do not treat the partial FSI values as physical validation. Before another FSI attempt, reduce the refined FSI cost and improve coupled convergence, for example by a shorter `0..0.5 s` diagnostic, looser output, smaller/targeted refinement, or modified coupled iteration controls. Do not start a long FSI run from this state.
