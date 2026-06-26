# Assumptions and risks

- CONFIRMED: geometry, material values, inlet, trigger, time range and target
  observables were extracted from the COMSOL 6.3 MPH and its PDF.
- CONFIRMED: COMSOL uses P2+P2 flow discretization, plane 2D solid mechanics,
  fully coupled time integration and Yeoh smoothing for the fluid mesh.
- ASSUMED: Elmer's large-deflection plane-stress ElasticSolver is the closest
  available constitutive implementation for the COMSOL linear-elastic solid.
- ASSUMED: strong partitioned Elmer FSI is acceptable although it is not
  algebraically identical to COMSOL's monolithic fully coupled solve.
- RISK: default Elmer mesh smoothing may be less robust than COMSOL Yeoh
  smoothing at the roughly 35 mm transverse beam displacement.
- RISK: added-mass coupling is strong because fluid and solid densities match;
  relaxation or artificial-compressibility scaling may be needed for stability.
