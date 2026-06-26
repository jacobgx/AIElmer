"""Minimal raw-appended VTU reader and oscillating-FSI probe extractor."""

from __future__ import annotations

import argparse
import csv
import re
import struct
from pathlib import Path

import numpy as np


DTYPES = {"Float64": "<f8", "Float32": "<f4", "Int32": "<i4", "UInt8": "u1"}


def read_vtu(path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    raw = path.read_bytes()
    marker = b'<AppendedData encoding="raw">'
    start = raw.index(marker) + len(marker)
    underscore = raw.index(b"_", start)
    appended = raw[underscore + 1 :]
    header = raw[:start].decode("utf-8", errors="ignore")
    npoints = int(re.search(r'NumberOfPoints="(\d+)"', header).group(1))

    arrays: dict[str, np.ndarray] = {}
    points: np.ndarray | None = None
    in_points = False
    for line in header.splitlines():
        if "<Points>" in line:
            in_points = True
            continue
        if "</Points>" in line:
            in_points = False
        if "<DataArray" not in line or 'format="appended"' not in line:
            continue
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', line))
        offset = int(attrs["offset"])
        nbytes = struct.unpack_from("<I", appended, offset)[0]
        dtype = np.dtype(DTYPES[attrs["type"]])
        data = np.frombuffer(appended, dtype=dtype, count=nbytes // dtype.itemsize, offset=offset + 4).copy()
        components = int(attrs.get("NumberOfComponents", "1"))
        if components > 1:
            data = data.reshape((-1, components))
        if in_points:
            points = data[:npoints]
        elif "Name" in attrs:
            arrays[attrs["Name"].lower()] = data
    if points is None:
        raise ValueError(f"No point coordinates found in {path}")
    return points, arrays


def nearest(points: np.ndarray, xy: tuple[float, float]) -> int:
    return int(np.argmin((points[:, 0] - xy[0]) ** 2 + (points[:, 1] - xy[1]) ** 2))


def read_elmer_nodes(path: Path) -> np.ndarray:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        rows.append((int(parts[0]), float(parts[2]), float(parts[3]), float(parts[4])))
    rows.sort()
    return np.asarray([(x, y, z) for _, x, y, z in rows])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.05)
    parser.add_argument(
        "--time-offset",
        type=float,
        default=0.0,
        help="Absolute time before the first exported VTU segment, useful for restart runs.",
    )
    parser.add_argument("--csv", type=Path, help="Optional CSV output path for all extracted rows.")
    args = parser.parse_args()

    files = sorted(args.directory.glob("*.vtu"))
    if not files:
        raise SystemExit(f"No VTU files in {args.directory}")

    first_points, _ = read_vtu(files[0])
    mesh_nodes = args.directory.parents[1] / "mesh" / "mesh.nodes"
    reference_points = read_elmer_nodes(mesh_nodes) if mesh_nodes.exists() else first_points
    probe_ids = {
        "tip": nearest(reference_points, (0.6, 0.2)),
        "near_interface": nearest(reference_points, (0.65, 0.2)),
        "mid_fluid": nearest(reference_points, (1.0, 0.25)),
        "far_fluid": nearest(reference_points, (1.5, 0.30)),
    }

    rows = []
    for step, file in enumerate(files, start=1):
        points, fields = read_vtu(file)
        displacement = fields.get("displacement")
        row = {"time": args.time_offset + step * args.dt_output}
        if displacement is not None:
            row["tip_ux"] = float(displacement[probe_ids["tip"], 0])
            row["tip_uy"] = float(displacement[probe_ids["tip"], 1])
        loads = fields.get("flow solution loads")
        geometry_ids = fields.get("geometryids")
        connectivity = fields.get("connectivity")
        offsets = fields.get("offsets")
        cell_types = fields.get("types")
        if all(value is not None for value in (loads, geometry_ids, connectivity, offsets, cell_types)):
            interface_nodes: set[int] = set()
            begin = 0
            for geometry_id, end, cell_type in zip(geometry_ids, offsets, cell_types):
                if int(cell_type) == 3 and int(geometry_id) in (105, 107):
                    interface_nodes.update(int(node) for node in connectivity[begin:int(end)])
                begin = int(end)
            ids = np.asarray(sorted(interface_nodes), dtype=int)
            if ids.size:
                total_load = loads[ids].sum(axis=0)
                row["drag_N"] = float(total_load[0])
                row["lift_N"] = float(total_load[1])
        for name, index in probe_ids.items():
            delta = points[index, :2] - reference_points[index, :2]
            row[f"{name}_coordinate_change"] = float(np.linalg.norm(delta))
        rows.append(row)

    if args.csv:
        keys = sorted({key for row in rows for key in row})
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)

    print(f"files={len(files)}")
    print("probe_ids=" + repr(probe_ids))
    print("last=" + repr(rows[-1]))
    if "tip_uy" in rows[-1]:
        print(f"tip_uy_range_m={min(r['tip_uy'] for r in rows):.9g},{max(r['tip_uy'] for r in rows):.9g}")
        print(f"tip_ux_range_m={min(r['tip_ux'] for r in rows):.9g},{max(r['tip_ux'] for r in rows):.9g}")
    if "drag_N" in rows[-1]:
        print(f"drag_range_N={min(r['drag_N'] for r in rows):.9g},{max(r['drag_N'] for r in rows):.9g}")
        print(f"lift_range_N={min(r['lift_N'] for r in rows):.9g},{max(r['lift_N'] for r in rows):.9g}")


if __name__ == "__main__":
    main()
