"""Pure-Python fallback analyzer for remote solid-only VTU results."""

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
    "UInt8": ("B", 1),
}


def read_nodes(path: Path) -> list[tuple[float, float, float]]:
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


def displacement_at(path: Path, point_id: int) -> tuple[float, float]:
    raw = path.read_bytes()
    marker = b'<AppendedData encoding="raw">'
    start = raw.index(marker) + len(marker)
    underscore = raw.index(b"_", start)
    appended = raw[underscore + 1 :]
    header = raw[:start].decode("utf-8", errors="ignore")

    for line in header.splitlines():
        if "<DataArray" not in line or 'format="appended"' not in line:
            continue
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', line))
        if attrs.get("Name", "").lower() != "displacement":
            continue
        offset = int(attrs["offset"])
        nbytes = struct.unpack_from("<I", appended, offset)[0]
        code, itemsize = DTYPES[attrs["type"]]
        components = int(attrs.get("NumberOfComponents", "1"))
        data = array(code)
        data.frombytes(appended[offset + 4 : offset + 4 + nbytes])
        if struct.pack("=H", 1) != struct.pack("<H", 1):
            data.byteswap()
        base = point_id * components
        return float(data[base]), float(data[base + 1])
    raise ValueError(f"No displacement field in {path}")


def local_extrema(times: list[float], values: list[float], kind: str) -> list[tuple[float, float]]:
    extrema = []
    for i in range(1, len(values) - 1):
        if kind == "max" and values[i] >= values[i - 1] and values[i] > values[i + 1]:
            extrema.append((times[i], values[i]))
        if kind == "min" and values[i] <= values[i - 1] and values[i] < values[i + 1]:
            extrema.append((times[i], values[i]))
    return extrema


def zero_crossing_frequency(times: list[float], values: list[float], start_time: float) -> float:
    selected = [(t, y) for t, y in zip(times, values) if t >= start_time]
    if len(selected) < 8:
        return math.nan
    mean = sum(y for _, y in selected) / len(selected)
    t = [row[0] for row in selected]
    y = [row[1] - mean for row in selected]
    crossings = []
    for i in range(1, len(y)):
        if y[i - 1] == 0.0:
            crossings.append(t[i - 1])
        elif y[i - 1] * y[i] < 0.0:
            frac = abs(y[i - 1]) / (abs(y[i - 1]) + abs(y[i]))
            crossings.append(t[i - 1] + frac * (t[i] - t[i - 1]))
    if len(crossings) < 5:
        return math.nan
    intervals = sorted(crossings[i] - crossings[i - 1] for i in range(1, len(crossings)))
    median = intervals[len(intervals) // 2]
    return 0.5 / median


def peak_spacing_frequency(times: list[float], values: list[float], start_time: float) -> float:
    selected = [(t, y) for t, y in zip(times, values) if t >= start_time]
    if len(selected) < 8:
        return math.nan
    mean = sum(y for _, y in selected) / len(selected)
    t = [row[0] for row in selected]
    y = [row[1] - mean for row in selected]
    peaks = local_extrema(t, y, "max")
    if len(peaks) < 3:
        return math.nan
    intervals = sorted(peaks[i][0] - peaks[i - 1][0] for i in range(1, len(peaks)))
    return 1.0 / intervals[len(intervals) // 2]


def analyze_case(
    case_root: Path,
    case: str,
    force_n: float,
    dt_output: float,
    tip_csv_dir: Path | None,
    mesh_dir: str,
) -> dict[str, float | str]:
    directory = case_root / "results_raw" / case
    files = sorted(directory.glob("*.vtu"))
    if not files:
        raise FileNotFoundError(directory)
    points = read_nodes(case_root / mesh_dir / "mesh.nodes")
    tip_id = nearest(points, (0.6, 0.2))

    rows = []
    for step, file in enumerate(files, start=1):
        ux, uy = displacement_at(file, tip_id)
        rows.append({"time": step * dt_output, "tip_ux": ux, "tip_uy": uy})

    if tip_csv_dir is not None:
        tip_csv_dir.mkdir(parents=True, exist_ok=True)
        with (tip_csv_dir / f"{case}_tip.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["time", "tip_ux", "tip_uy"])
            writer.writeheader()
            writer.writerows(rows)

    times = [row["time"] for row in rows]
    ux = [row["tip_ux"] for row in rows]
    uy = [row["tip_uy"] for row in rows]
    post = [row["tip_uy"] for row in rows if row["time"] >= 1.65]
    zero_freq = zero_crossing_frequency(times, uy, 1.65)
    peak_freq = peak_spacing_frequency(times, uy, 1.65)
    return {
        "case": case,
        "force_N": force_n,
        "tip_ux_min_mm": 1000.0 * min(ux),
        "tip_ux_max_mm": 1000.0 * max(ux),
        "tip_uy_min_mm": 1000.0 * min(uy),
        "tip_uy_max_mm": 1000.0 * max(uy),
        "tip_uy_peak_abs_mm": 1000.0 * max(abs(v) for v in uy),
        "post_pulse_amp_half_range_mm": 500.0 * (max(post) - min(post)) if post else math.nan,
        "uy_peak_spacing_freq_Hz": peak_freq,
        "uy_zero_crossing_freq_Hz": zero_freq,
        "freq_error_pct_vs_comsol": 100.0 * (zero_freq - 5.3) / 5.3 if zero_freq == zero_freq else math.nan,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.01)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--tip-csv-dir", type=Path)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--mesh-dir", default="mesh")
    args = parser.parse_args()

    cases = args.cases or [
        "solid_force_1N",
        "solid_force_1N_no_plane_stress",
        "solid_force_1N_density_142kg",
        "solid_force_1N_E_39p3MPa",
    ]
    rows = [analyze_case(args.case_root, case, 1.0, args.dt_output, args.tip_csv_dir, args.mesh_dir) for case in cases]
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
