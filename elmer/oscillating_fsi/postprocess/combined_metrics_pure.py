"""Pure-Python FSI tip-displacement and corrected-load metrics.

This minimal-dependency fallback avoids numpy for environments without PyPI access.
"""

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

COMSOL_TARGETS = {
    "tip_ux_mm_mean": -2.69,
    "tip_ux_mm_amp": 2.53,
    "tip_uy_mm_mean": 1.48,
    "tip_uy_mm_amp": 34.38,
    "drag_N_mean": 457.3,
    "drag_N_amp": 22.66,
    "lift_N_mean": 2.22,
    "lift_N_amp": 149.78,
}


def read_elmer_nodes(path: Path) -> list[tuple[float, float, float]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        rows.append((int(parts[0]), float(parts[2]), float(parts[3]), float(parts[4])))
    rows.sort()
    return [(x, y, z) for _, x, y, z in rows]


def nearest(points: list[tuple[float, float, float]], xy: tuple[float, float]) -> int:
    best_i = 0
    best_d = float("inf")
    for i, (x, y, _) in enumerate(points):
        d = (x - xy[0]) ** 2 + (y - xy[1]) ** 2
        if d < best_d:
            best_i = i
            best_d = d
    return best_i


def raw_array(appended: bytes, attrs: dict[str, str]) -> list[float | int] | list[tuple[float, ...]]:
    offset = int(attrs["offset"])
    nbytes = struct.unpack_from("<I", appended, offset)[0]
    code, itemsize = DTYPES[attrs["type"]]
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
        raise ValueError(f"No point coordinates found in {path}")
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
    names = ("inlet", "outlet", "walls", "cylinder", "beam_top", "beam_bottom", "beam_tip", "beam_root")
    nodes = {name: set() for name in names}
    connectivity = fields["connectivity"]
    offsets = fields["offsets"]
    cell_types = fields["types"]
    begin = 0
    for end, cell_type in zip(offsets, cell_types):
        cell = [int(node) for node in connectivity[begin : int(end)]]
        begin = int(end)
        if int(cell_type) != 3 or len(cell) != 2:
            continue
        x = 0.5 * (reference_points[cell[0]][0] + reference_points[cell[1]][0])
        y = 0.5 * (reference_points[cell[0]][1] + reference_points[cell[1]][1])
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


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def zero_crossing_frequency(times: list[float], values: list[float]) -> float:
    if len(values) < 8:
        return math.nan
    avg = mean(values)
    y = [value - avg for value in values]
    crossings = []
    for i in range(1, len(y)):
        if y[i - 1] == 0.0:
            crossings.append(times[i - 1])
        elif y[i - 1] * y[i] < 0.0:
            frac = abs(y[i - 1]) / (abs(y[i - 1]) + abs(y[i]))
            crossings.append(times[i - 1] + frac * (times[i] - times[i - 1]))
    if len(crossings) < 3:
        return math.nan
    intervals = sorted(crossings[i] - crossings[i - 1] for i in range(1, len(crossings)))
    return 0.5 / intervals[len(intervals) // 2]


def signal_metrics(times: list[float], values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "amp": 0.5 * (max(values) - min(values)),
        "freq_Hz": zero_crossing_frequency(times, values),
    }


def target_error(metric: str, value: float) -> float:
    target = COMSOL_TARGETS.get(metric)
    if target is None or target == 0.0 or not math.isfinite(value):
        return math.nan
    return 100.0 * (value - target) / abs(target)


def analyze_case(
    case_root: Path,
    case: str,
    mesh_dir: str,
    dt_output: float,
    time_offset: float,
    window_start: float,
    row_csv_dir: Path | None,
) -> dict[str, float | str]:
    directory = case_root / "results_raw" / case
    files = sorted(directory.glob("*.vtu"))
    if not files:
        raise FileNotFoundError(directory)

    first_points, first_fields = read_vtu(files[0])
    mesh_nodes = case_root / mesh_dir / "mesh.nodes"
    reference_points = read_elmer_nodes(mesh_nodes) if mesh_nodes.exists() else first_points
    tip_id = nearest(reference_points, (0.6, 0.2))
    node_groups = boundary_nodes(first_fields, reference_points)
    force_nodes = (
        node_groups["cylinder"]
        | node_groups["beam_top"]
        | node_groups["beam_bottom"]
        | node_groups["beam_tip"]
    )

    rows = []
    for step, file in enumerate(files, start=1):
        _, fields = read_vtu(file)
        displacement = fields["displacement"]
        loads = fields["flow solution loads"]
        drag, lift = load_sum(loads, force_nodes)
        rows.append(
            {
                "time": time_offset + step * dt_output,
                "tip_ux_mm": 1000.0 * float(displacement[tip_id][0]),
                "tip_uy_mm": 1000.0 * float(displacement[tip_id][1]),
                "drag_N": -drag,
                "lift_N": -lift,
            }
        )

    if row_csv_dir is not None:
        row_csv_dir.mkdir(parents=True, exist_ok=True)
        with (row_csv_dir / f"{case}_rows.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    selected = [row for row in rows if float(row["time"]) >= window_start]
    if not selected:
        raise ValueError(f"No rows at or after window_start={window_start}")
    times = [float(row["time"]) for row in selected]
    summary: dict[str, float | str] = {
        "case": case,
        "time_start": times[0],
        "time_end": times[-1],
        "samples": len(selected),
    }
    for signal in ("tip_ux_mm", "tip_uy_mm", "drag_N", "lift_N"):
        values = [float(row[signal]) for row in selected]
        metrics = signal_metrics(times, values)
        for name, value in metrics.items():
            summary[f"{signal}_{name}"] = value
        for name in ("mean", "amp"):
            key = f"{signal}_{name}"
            summary[f"{key}_target"] = COMSOL_TARGETS.get(key, math.nan)
            summary[f"{key}_error_pct"] = target_error(key, float(summary[key]))
    return summary


def write_summary_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--case", action="append", dest="cases", required=True)
    parser.add_argument("--dt-output", type=float, default=0.05)
    parser.add_argument("--mesh-dir", default="mesh")
    parser.add_argument("--time-offset", type=float, default=0.0)
    parser.add_argument("--window-start", type=float, default=0.0)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--row-csv-dir", type=Path)
    args = parser.parse_args()

    rows = [
        analyze_case(args.case_root, case, args.mesh_dir, args.dt_output, args.time_offset, args.window_start, args.row_csv_dir)
        for case in args.cases
    ]
    if args.summary_csv:
        write_summary_csv(args.summary_csv, rows)
    for row in rows:
        print(f"case={row['case']} window={row['time_start']:.6g}-{row['time_end']:.6g}s samples={row['samples']}")
        for signal in ("tip_ux_mm", "tip_uy_mm", "drag_N", "lift_N"):
            print(
                f"  {signal}: mean={row[f'{signal}_mean']:.6g}, "
                f"amp={row[f'{signal}_amp']:.6g}, freq={row[f'{signal}_freq_Hz']:.6g} Hz, "
                f"range={row[f'{signal}_min']:.6g}..{row[f'{signal}_max']:.6g}"
            )


if __name__ == "__main__":
    main()
