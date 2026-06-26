"""Split Elmer Flow Solution Loads by geometric boundary groups."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

from analyze_vtu import read_elmer_nodes, read_vtu


CX = 0.20
CY = 0.20
R = 0.05
L = 2.5
H = 0.41
BEAM_X0 = CX + R
BEAM_X1 = 0.60
BEAM_Y0 = CY - 0.01
BEAM_Y1 = CY + 0.01
TOL = 2.0e-3


GROUPS = (
    "inlet",
    "outlet",
    "walls",
    "cylinder",
    "beam_top",
    "beam_bottom",
    "beam_tip",
    "beam_root",
)


def classify_midpoint(x: float, y: float) -> str | None:
    if abs(x) < TOL:
        return "inlet"
    if abs(x - L) < TOL:
        return "outlet"
    if abs(y) < TOL or abs(y - H) < TOL:
        return "walls"
    if abs(x - BEAM_X1) < TOL and BEAM_Y0 - TOL <= y <= BEAM_Y1 + TOL:
        return "beam_tip"
    if abs(x - BEAM_X0) < 5 * TOL and BEAM_Y0 - TOL <= y <= BEAM_Y1 + TOL:
        return "beam_root"
    if BEAM_X0 - TOL <= x <= BEAM_X1 + TOL and abs(y - BEAM_Y1) < TOL:
        return "beam_top"
    if BEAM_X0 - TOL <= x <= BEAM_X1 + TOL and abs(y - BEAM_Y0) < TOL:
        return "beam_bottom"
    if abs(math.hypot(x - CX, y - CY) - R) < 3 * TOL:
        return "cylinder"
    return None


def boundary_nodes(fields: dict[str, np.ndarray], reference_points: np.ndarray) -> dict[str, set[int]]:
    nodes = {name: set() for name in GROUPS}
    geometry_ids = fields.get("geometryids")
    connectivity = fields.get("connectivity")
    offsets = fields.get("offsets")
    cell_types = fields.get("types")
    if any(value is None for value in (geometry_ids, connectivity, offsets, cell_types)):
        raise ValueError("VTU does not contain geometryids/connectivity/offsets/types")

    begin = 0
    for end, cell_type in zip(offsets, cell_types):
        cell = np.asarray(connectivity[begin:int(end)], dtype=int)
        begin = int(end)
        if int(cell_type) != 3 or len(cell) != 2:
            continue
        midpoint = reference_points[cell, :2].mean(axis=0)
        group = classify_midpoint(float(midpoint[0]), float(midpoint[1]))
        if group is not None:
            nodes[group].update(int(node) for node in cell)
    return nodes


def load_sum(loads: np.ndarray, node_ids: set[int]) -> tuple[float, float]:
    if not node_ids:
        return 0.0, 0.0
    ids = np.asarray(sorted(node_ids), dtype=int)
    summed = loads[ids, :2].sum(axis=0)
    return float(summed[0]), float(summed[1])


def summarize(rows: list[dict[str, float]]) -> dict[str, tuple[float, float]]:
    summary = {}
    keys = [key[:-7] for key in rows[0] if key.endswith("_drag_N")]
    for key in keys:
        drag = [row[f"{key}_drag_N"] for row in rows]
        lift = [row[f"{key}_lift_N"] for row in rows]
        summary[f"{key}_drag_N"] = (min(drag), max(drag))
        summary[f"{key}_lift_N"] = (min(lift), max(lift))
    return summary


def analyze_directory(directory: Path, dt_output: float, time_offset: float) -> list[dict[str, float]]:
    files = sorted(directory.glob("*.vtu"))
    if not files:
        raise FileNotFoundError(f"No VTU files in {directory}")

    first_points, first_fields = read_vtu(files[0])
    mesh_nodes = directory.parents[1] / "mesh" / "mesh.nodes"
    reference_points = read_elmer_nodes(mesh_nodes) if mesh_nodes.exists() else first_points
    node_groups = boundary_nodes(first_fields, reference_points)
    combined = {
        "beam_sides": node_groups["beam_top"] | node_groups["beam_bottom"],
        "beam_all": node_groups["beam_top"] | node_groups["beam_bottom"] | node_groups["beam_tip"],
        "cylinder_beam_sides": node_groups["cylinder"] | node_groups["beam_top"] | node_groups["beam_bottom"],
        "cylinder_beam_all": node_groups["cylinder"] | node_groups["beam_top"] | node_groups["beam_bottom"] | node_groups["beam_tip"],
    }

    rows = []
    for step, file in enumerate(files, start=1):
        _, fields = read_vtu(file)
        loads = fields.get("flow solution loads")
        if loads is None:
            raise ValueError(f"No Flow Solution Loads in {file}")
        row: dict[str, float] = {"time": time_offset + step * dt_output}
        for name, ids in {**node_groups, **combined}.items():
            drag, lift = load_sum(loads, ids)
            row[f"{name}_drag_N"] = drag
            row[f"{name}_lift_N"] = lift
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.05)
    parser.add_argument("--time-offset", type=float, default=0.0)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    rows = analyze_directory(args.directory, args.dt_output, args.time_offset)
    if args.csv:
        write_csv(args.csv, rows)

    print(f"files={len(rows)}")
    print(f"last={rows[-1]}")
    for key, value in summarize(rows).items():
        print(f"{key}_range={value[0]:.9g},{value[1]:.9g}")


if __name__ == "__main__":
    main()
