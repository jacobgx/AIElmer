"""Analyze solid-only force sweep tip response and dominant frequency."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

from analyze_vtu import nearest, read_elmer_nodes, read_vtu


def local_extrema(times: np.ndarray, values: np.ndarray, kind: str) -> list[tuple[float, float]]:
    extrema = []
    for i in range(1, len(values) - 1):
        if kind == "max" and values[i] >= values[i - 1] and values[i] > values[i + 1]:
            extrema.append((float(times[i]), float(values[i])))
        if kind == "min" and values[i] <= values[i - 1] and values[i] < values[i + 1]:
            extrema.append((float(times[i]), float(values[i])))
    return extrema


def estimate_frequency(times: np.ndarray, values: np.ndarray, start_time: float) -> tuple[float, float, float]:
    mask = times >= start_time
    t = times[mask]
    y = values[mask] - values[mask].mean()
    if len(t) < 8 or np.allclose(y, 0.0):
        return math.nan, math.nan, math.nan

    dt = float(np.median(np.diff(t)))
    spectrum = np.fft.rfft(y * np.hanning(len(y)))
    freq = np.fft.rfftfreq(len(y), dt)
    valid = (freq >= 1.0) & (freq <= 30.0)
    fft_freq = float(freq[valid][np.argmax(np.abs(spectrum[valid]))]) if np.any(valid) else math.nan

    maxima = local_extrema(t, y, "max")
    if len(maxima) >= 3:
        peak_freq = float(1.0 / np.median(np.diff([p[0] for p in maxima])))
    else:
        peak_freq = math.nan

    crossings = []
    for i in range(1, len(y)):
        if y[i - 1] == 0.0:
            crossings.append(float(t[i - 1]))
        elif y[i - 1] * y[i] < 0.0:
            frac = abs(y[i - 1]) / (abs(y[i - 1]) + abs(y[i]))
            crossings.append(float(t[i - 1] + frac * (t[i] - t[i - 1])))
    if len(crossings) >= 5:
        zero_cross_freq = float(0.5 / np.median(np.diff(crossings)))
    else:
        zero_cross_freq = math.nan
    return fft_freq, peak_freq, zero_cross_freq


def analyze_case(case_dir: Path, force_n: float, dt_output: float, csv_dir: Path | None) -> dict[str, float | str]:
    files = sorted(case_dir.glob("*.vtu"))
    if not files:
        raise ValueError(f"No VTU files in {case_dir}")

    first_points, _ = read_vtu(files[0])
    case_root = case_dir.parents[1]
    mesh_nodes = case_root / "mesh" / "mesh.nodes"
    reference_points = read_elmer_nodes(mesh_nodes) if mesh_nodes.exists() else first_points
    tip_id = nearest(reference_points, (0.6, 0.2))

    rows = []
    for step, file in enumerate(files, start=1):
        _, fields = read_vtu(file)
        displacement = fields.get("displacement")
        if displacement is None:
            raise ValueError(f"No displacement field in {file}")
        rows.append(
            {
                "time": step * dt_output,
                "tip_ux": float(displacement[tip_id, 0]),
                "tip_uy": float(displacement[tip_id, 1]),
            }
        )

    if csv_dir is not None:
        csv_dir.mkdir(parents=True, exist_ok=True)
        out_csv = csv_dir / f"{case_dir.name}_tip.csv"
        with out_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["time", "tip_ux", "tip_uy"])
            writer.writeheader()
            writer.writerows(rows)

    times = np.asarray([r["time"] for r in rows])
    uy = np.asarray([r["tip_uy"] for r in rows])
    ux = np.asarray([r["tip_ux"] for r in rows])
    fft_freq, peak_freq, zero_cross_freq = estimate_frequency(times, uy, start_time=1.65)
    post = uy[times >= 1.65]
    return {
        "case": case_dir.name,
        "force_N": force_n,
        "tip_ux_min_mm": float(1000.0 * ux.min()),
        "tip_ux_max_mm": float(1000.0 * ux.max()),
        "tip_uy_min_mm": float(1000.0 * uy.min()),
        "tip_uy_max_mm": float(1000.0 * uy.max()),
        "tip_uy_peak_abs_mm": float(1000.0 * np.max(np.abs(uy))),
        "post_pulse_amp_half_range_mm": float(500.0 * (post.max() - post.min())) if len(post) else math.nan,
        "uy_fft_freq_Hz": fft_freq,
        "uy_peak_spacing_freq_Hz": peak_freq,
        "uy_zero_crossing_freq_Hz": zero_cross_freq,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.01)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--tip-csv-dir", type=Path)
    args = parser.parse_args()

    cases = [
        ("solid_force_0p1N", 0.1),
        ("solid_force_1N", 1.0),
        ("solid_force_10N", 10.0),
        ("solid_force_100N", 100.0),
    ]
    rows = [
        analyze_case(args.case_root / "results_raw" / case, force, args.dt_output, args.tip_csv_dir)
        for case, force in cases
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
