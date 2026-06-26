# Structure model review

Date: 2026-06-23

COMSOL Java audit:

- Geometry:
  - Channel rectangle: `2.5 x 0.41 m`.
  - Cylinder: radius `0.05 m`, center `(0.2, 0.2)`.
  - Solid rectangle before cylinder subtraction: size `"0.35+0.05", "0.02"`,
    centered at `("0.2+0.4/2", "0.2")`, i.e. x-span `0.2-0.6 m`.
  - Solid is rectangle minus circle, so the effective free beam downstream of
    the cylinder is about `0.35 m`.
- Solid mechanics:
  - COMSOL uses `SolidMechanics` on the solid domain.
  - Displacement shape order is set to `2`.
  - Fixed boundaries are COMSOL selections `19, 20`.
  - Trigger is a `PointLoad` on point selection `11` with force
    `{0, 1[N]*gp1(t), 0}`.
- Material:
  - `E = 5.6[MPa]`
  - `nu = 0.4`
  - `density = 1e3`
- No explicit `plane stress`, `plane strain`, or `thickness` override was found
  in the exported Java. That means the COMSOL default 2D Solid Mechanics
  convention still needs a manual GUI/PDF check if frequency remains wrong.

Elmer status:

- Geometry and material values match the Java export at the parameter level.
- The current Elmer trigger is a line traction on the `beam_tip` boundary with
  peak traction `50 N/m`, giving integrated peak force about `1 N` over the
  `0.02 m` tip height.
- Solid-only force sweep showed:
  - 0.1, 1, and 10 N responses are essentially linear.
  - 1 N dry structural tip-y peak is about `4.67 mm`.
  - Dry structural frequency is about `2.0 Hz`, below the COMSOL y-frequency
    reference `5.3 Hz`.

Interpretation:

- Total trigger force scaling appears internally consistent in Elmer.
- The difference between COMSOL point load and Elmer distributed tip traction
  can change local excitation, but it should not alone explain a structural
  frequency shift from about `5.3 Hz` to about `2.0 Hz`.
- The most suspicious remaining structure items are:
  - COMSOL 2D solid default: plane stress vs plane strain and any implicit
    thickness convention.
  - Elmer `Plane Stress = True` effectiveness/location for `ElasticSolver`.
  - Structural boundary selections at the cylinder/beam junction.
  - Element/order difference: COMSOL solid displacement order 2 versus the
    current linear triangular Elmer mesh.
