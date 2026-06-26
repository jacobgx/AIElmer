"""Generate Gmsh mesh variants for fixed-flow order/refinement screening."""

from __future__ import annotations

import argparse
from pathlib import Path

import gmsh


BASE_REPLACEMENTS = {
    "hFar = 0.030;": "hFar = 0.025;",
    "hNear = 0.0030;": "hNear = 0.0022;",
    "hWake = 0.0075;": "hWake = 0.0055;",
    "Field[1].NNodesByEdge = 160;": "Field[1].NNodesByEdge = 220;",
    "Field[2].DistMin = 0.012;": "Field[2].DistMin = 0.016;",
    "Field[2].DistMax = 0.25;": "Field[2].DistMax = 0.32;",
    "Field[3].XMax = 1.40;": "Field[3].XMax = 1.60;",
    "Field[3].YMin = 0.10;": "Field[3].YMin = 0.08;",
    "Field[3].YMax = 0.30;": "Field[3].YMax = 0.32;",
}


def write_refined_geo(base_geo: Path, output_geo: Path, order: int) -> None:
    text = base_geo.read_text(encoding="utf-8")
    for old, new in BASE_REPLACEMENTS.items():
        if old not in text:
            raise ValueError(f"Missing expected geometry line: {old}")
        text = text.replace(old, new)
    text += f"\nMesh.ElementOrder = {order};\n"
    output_geo.write_text(text, encoding="utf-8")


def mesh_geo(geo_path: Path, msh_path: Path) -> None:
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.open(str(geo_path))
        gmsh.model.mesh.generate(2)
        gmsh.write(str(msh_path))
    finally:
        gmsh.finalize()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-geo", type=Path, default=Path("geometry.geo"))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    variants = [
        ("geometry_refined_linear.geo", "geometry_refined_linear.msh", 1),
        ("geometry_refined_quad.geo", "geometry_refined_quad.msh", 2),
    ]
    for geo_name, msh_name, order in variants:
        geo_path = args.out_dir / geo_name
        msh_path = args.out_dir / msh_name
        write_refined_geo(args.base_geo, geo_path, order)
        mesh_geo(geo_path, msh_path)
        print(msh_path)


if __name__ == "__main__":
    main()
