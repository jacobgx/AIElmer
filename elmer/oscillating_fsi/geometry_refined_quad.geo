// Turek-Hron FSI3 / COMSOL oscillating_fsi geometry, SI units.
SetFactory("OpenCASCADE");

L = 2.5;
H = 0.41;
cx = 0.20;
cy = 0.20;
R = 0.05;
beamEnd = 0.60;
beamHalfHeight = 0.01;

Rectangle(1) = {0, 0, 0, L, H};
Disk(2) = {cx, cy, 0, R, R};
Rectangle(3) = {cx, cy-beamHalfHeight, 0, beamEnd-cx, 2*beamHalfHeight};
channel = 1;
cylinder = 2;
beamRect = 3;

// The COMSOL solid is Rectangle 2 minus Circle 1. Keep the circle as the
// fixed obstacle and subtract both circle and beam from the fluid channel.
beam() = BooleanDifference{ Surface{beamRect}; Delete; }{ Surface{cylinder}; };
fluid() = BooleanDifference{ Surface{channel}; Delete; }{ Surface{cylinder, beam()}; };
Coherence;

eps = 1e-5;
inlet[] = Curve In BoundingBox{-eps, -eps, -eps, eps, H+eps, eps};
outlet[] = Curve In BoundingBox{L-eps, -eps, -eps, L+eps, H+eps, eps};
walls[] = Curve In BoundingBox{-eps, -eps, -eps, L+eps, eps, eps};
wallsTop[] = Curve In BoundingBox{-eps, H-eps, -eps, L+eps, H+eps, eps};

beamTop[] = Curve In BoundingBox{cx+R-0.002, cy+beamHalfHeight-eps, -eps,
                                 beamEnd+eps, cy+beamHalfHeight+eps, eps};
beamBottom[] = Curve In BoundingBox{cx+R-0.002, cy-beamHalfHeight-eps, -eps,
                                    beamEnd+eps, cy-beamHalfHeight+eps, eps};
beamTip[] = Curve In BoundingBox{beamEnd-eps, cy-beamHalfHeight-eps, -eps,
                                 beamEnd+eps, cy+beamHalfHeight+eps, eps};
beamRoot[] = Curve In BoundingBox{cx+R-0.002, cy-beamHalfHeight-eps, -eps,
                                  cx+R+eps, cy+beamHalfHeight+eps, eps};

// Remaining circle boundary. Curves that are not adjacent to the fluid are
// harmless for the flow solver; the structural root gets its own fixed group.
cylinderWall[] = Curve In BoundingBox{cx-R-eps, cy-R-eps, -eps,
                                      cx+R+eps, cy+R+eps, eps};

Physical Surface("fluid", 1) = {fluid()};
Physical Surface("solid", 2) = {beam()};
Physical Curve("inlet", 1) = {inlet[]};
Physical Curve("outlet", 2) = {outlet[]};
Physical Curve("walls", 3) = {walls[], wallsTop[]};
Physical Curve("cylinder_fixed", 4) = {cylinderWall[]};
Physical Curve("fsi_interface", 5) = {beamTop[], beamBottom[]};
Physical Curve("solid_root", 6) = {beamRoot[]};
Physical Curve("beam_tip", 7) = {beamTip[]};

// MVP mesh. The beam receives about eight cells through its thickness and the
// fluid is refined around the cylinder/interface and through the near wake.
hFar = 0.025;
hNear = 0.0022;
hWake = 0.0055;

Field[1] = Distance;
Field[1].EdgesList = {cylinderWall[], beamTop[], beamBottom[], beamTip[]};
Field[1].NNodesByEdge = 220;
Field[2] = Threshold;
Field[2].IField = 1;
Field[2].LcMin = hNear;
Field[2].LcMax = hFar;
Field[2].DistMin = 0.016;
Field[2].DistMax = 0.32;

Field[3] = Box;
Field[3].VIn = hWake;
Field[3].VOut = hFar;
Field[3].XMin = 0.15;
Field[3].XMax = 1.60;
Field[3].YMin = 0.08;
Field[3].YMax = 0.32;

Field[4] = Min;
Field[4].FieldsList = {2, 3};
Background Field = 4;

Mesh.Algorithm = 6;
Mesh.Optimize = 1;
Mesh.MshFileVersion = 2.2;

Mesh.ElementOrder = 2;
