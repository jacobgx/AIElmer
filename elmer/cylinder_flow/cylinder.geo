// COMSOL cylinder-flow benchmark geometry, expressed in metres.
L = 2.2;
H = 0.41;
R = 0.05;
cx = 0.20;
cy = 0.20;
// Refined production mesh: sized to be comparable with the COMSOL reference.
lcFar = 0.015;
lcCylinder = 0.003;

Point(1) = {0, 0, 0, lcFar};
Point(2) = {L, 0, 0, lcFar};
Point(3) = {L, H, 0, lcFar};
Point(4) = {0, H, 0, lcFar};
Line(1) = {1, 2};              // bottom wall
Line(2) = {2, 3};              // outlet
Line(3) = {3, 4};              // top wall
Line(4) = {4, 1};              // inlet
Line Loop(1) = {1, 2, 3, 4};

Point(5) = {cx, cy, 0, lcCylinder};
Point(6) = {cx + R, cy, 0, lcCylinder};
Point(7) = {cx, cy + R, 0, lcCylinder};
Point(8) = {cx - R, cy, 0, lcCylinder};
Point(9) = {cx, cy - R, 0, lcCylinder};
Circle(5) = {6, 5, 7};
Circle(6) = {7, 5, 8};
Circle(7) = {8, 5, 9};
Circle(8) = {9, 5, 6};
Line Loop(2) = {5, 6, 7, 8};

Plane Surface(1) = {1, 2};

Physical Surface("fluid", 1) = {1};
Physical Line("inlet", 1) = {4};
Physical Line("outlet", 2) = {2};
Physical Line("walls", 3) = {1, 3};
Physical Line("cylinder", 4) = {5, 6, 7, 8};

Field[1] = Distance;
Field[1].EdgesList = {5, 6, 7, 8};
Field[1].NNodesByEdge = 80;
Field[2] = Threshold;
Field[2].IField = 1;
Field[2].LcMin = lcCylinder;
Field[2].LcMax = lcFar;
Field[2].DistMin = 0.025;
Field[2].DistMax = 0.35;
Background Field = 2;
Mesh.Algorithm = 6;
Mesh.MshFileVersion = 2.2;
