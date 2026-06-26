"""Pure-Python corrected load metrics for remote Elmer VTU results."""

from __future__ import annotations

import argparse
import csv
import math
import re
import struct
from array import array
from pathlib import Path


DTYPES = {
    "Float64": ("d", 8),
    "Float32": ("f", 4),
    "Int32": ("i", 4),
    "UInt32": ("I", 4),
    "Int64": ("q", 8),
    "UInt64": ("Q", 8),
    "UInt8": ("B", 1),
}

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


def read_nodes(path: Path) -> list[tuple[float, float, float]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        rows.append((int(parts[0]), float(parts[2]), float(parts[3]), float(parts[4])))
    rows.sort()
    return [(x, y, z) for _, x, y, z in rows]


def raw_array(appended: bytes, attrs: dict[str, str]) -> list:
    offset = int(attrs["offset"])
    nbytes = struct.unpack_from("<I", appended, offset)[0]
    code, _ = DTYPES[attrs["type"]]
    data = array(code)
    data.frombytes(appended[offset + 4 : offset + 4 + nbytes])
    if struct.pack("=H", 1) != struct.pack("<H", 1):
        data.byteswap()
    components = int(attrs.get("NumberOfComponents", "1"))
    if components <= 1:
        return list(data)
    return [tuple(data[i : i + components]) for i in range(0, len(data), components)]


def read_vtu(path: Path) -> tuple[list[tuple[float, float, float]], dict[str, list]]:
    raw = path.read_bytes()
    marker = b'<AppendedData encoding="raw">'
    start = raw.index(marker) + len(marker)
    underscore = raw.index(b"_", start)
    appended = raw[underscore + 1 :]
    header = raw[:start].decode("utf-8", errors="ignore")

    points = None
    arrays: dict[str, list] = {}
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
        values = raw_array(appended, attrs)
        if in_points:
            points = values
        elif "Name" in attrs:
            arrays[attrs["Name"].lower()] = values
    if points is None:
        raise ValueError(f"No point coordinates in {path}")
    return points, arrays


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


def boundary_nodes(fields: dict[str, list], reference_points: list[tuple[float, float, float]]) -> dict[str, set[int]]:
    groups = ("inlet", "outlet", "walls", "cylinder", "beam_top", "beam_bottom", "beam_tip", "beam_root")
    nodes = {name: set() for name in groups}
    connectivity = fields["connectivity"]
    offsets = fields["offsets"]
    cell_types = fields["types"]
    begin = 0
    for end, cell_type in zip(offsets, cell_types):
        cell = [int(node) for node in connectivity[begin : int(end)]]
        begin = int(end)
        if int(cell_type) not in (3, 21) or len(cell) < 2:
            continue
        x = sum(reference_points[node][0] for node in cell) / len(cell)
        y = sum(reference_points[node][1] for node in cell) / len(cell)
        group = classify_midpoint(x, y)
        if group is not None:
            nodes[group].update(cell)
    return nodes


def load_sum(loads: list[tuple[float, ...]], node_ids: set[int]) -> tuple[float, float]:
    drag = 0.0
    lift = 0.0
    for node in node_ids:
        drag += float(loads[node][0])
        lift += float(loads[node][1])
    return drag, lift


def signal_metrics(times: list[float], values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "amp": 0.5 * (max(values) - min(values)),
    }


def analyze_case(
    case_root: Path,
    case: str,
    mesh_dir: str,
    dt_output: float,
    window_start: float,
    rows_dir: Path | None,
) -> dict[str, float | str]:
    directory = case_root / "results_raw" / case
    files = sorted(directory.glob("*.vtu"))
    if not files:
        raise FileNotFoundError(directory)
    _, first_fields = read_vtu(files[0])
    reference_points = read_nodes(case_root / mesh_dir / "mesh.nodes")
    groups = boundary_nodes(first_fields, reference_points)
    corrected = groups["cylinder"] | groups["beam_top"] | groups["beam_bottom"] | groups["beam_tip"]

    rows = []
    for step, file in enumerate(files, start=1):
        _, fields = read_vtu(file)
        drag, lift = load_sum(fields["flow solution loads"], corrected)
        rows.append({"time": step * dt_output, "drag_N": -drag, "lift_N": -lift})

    if rows_dir is not None:
        rows_dir.mkdir(parents=True, exist_ok=True)
        with (rows_dir / f"{case}_loads.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    selected = [row for row in rows if row["time"] >= window_start]
    times = [row["time"] for row in selected]
    summary: dict[str, float | str] = {
        "case": case,
        "mesh_dir": mesh_dir,
        "time_start": times[0],
        "time_end": times[-1],
        "samples": len(selected),
    }
    for signal in ("drag_N", "lift_N"):
        values = [row[signal] for row in selected]
        for key, value in signal_metrics(times, values).items():
            summary[f"{signal}_{key}"] = value
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--case", action="append", required=True)
    parser.add_argument("--mesh-dir", action="append", dest="mesh_dirs")
    parser.add_argument("--dt-output", type=float, default=0.05)
    parser.add_argument("--window-start", type=float, default=0.0)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--rows-dir", type=Path)
    args = parser.parse_args()

    mesh_dirs = args.mesh_dirs or ["mesh"] * len(args.case)
    if len(mesh_dirs) != len(args.case):
        raise SystemExit("--mesh-dir count must match --case count")
    rows = [
        analyze_case(args.case_root, case, mesh_dir, args.dt_output, args.window_start, args.rows_dir)
        for case, mesh_dir in zip(args.case, mesh_dirs)
    ]
    keys = list(rows[0].keys())
    if args.summary_csv:
        args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    print(",".join(keys))
    for row in rows:
        print(",".join(str(row[key]) for key in keys))


if __name__ == "__main__":
    main()
