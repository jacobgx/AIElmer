# Formulation

The fluid uses transient incompressible Navier-Stokes in an ALE frame. The
solid uses transient plane-stress elasticity with inertia and large deflection.
The fluid mesh displacement is solved throughout the complete fluid domain.

At the FSI interface, fluid traction loads the solid, the fluid velocity equals
the interface mesh velocity, and mesh displacement equals solid displacement.
The channel boundary and fixed cylinder have zero mesh displacement.

The inlet profile is

`u_x = 1.5 * 2 m/s * y * (0.41 m-y)/(0.205 m)^2 * ramp(t)` and `u_y=0`.

The time-localized perturbation is a 1 N Gaussian y-load centred at 1.5 s with
sigma 0.05 s, matching the COMSOL model definition.

Coupling is strongly partitioned within each physical timestep:

1. FlowSolver computes ALE flow and interface loads.
2. ElasticSolver updates the dynamic structural displacement.
3. Mesh Update propagates interface motion through the whole fluid mesh.
4. The outer steady-state iteration repeats until all fields converge.

All values use SI units. Reynolds number based on cylinder diameter is 200.
