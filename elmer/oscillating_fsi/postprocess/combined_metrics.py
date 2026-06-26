"""Combined tip-displacement and corrected load metrics for oscillating FSI."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

from analyze_load_boundaries import analyze_directory
from analyze_vtu import nearest, read_elmer_nodes, read_vtu


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


def signal_metrics(times: np.ndarray, values: np.ndarray) -> dict[str, float]:
    mean = float(np.mean(values))
    amplitude = float(0.5 * (np.max(values) - np.min(values)))
    frequency = float("nan")
    if values.size >= 4 and np.ptp(times) > 0.0:
        detrended = values - mean
        if np.max(np.abs(detrended)) > 0.0:
            dt = float(np.median(np.diff(times)))
            freqs = np.fft.rfftfreq(values.size, d=dt)
            spectrum = np.abs(np.fft.rfft(detrended))
            if freqs.size > 1:
                peak = int(np.argmax(spectrum[1:]) + 1)
                frequency = float(freqs[peak])
    return {"mean": mean, "amp": amplitude, "freq_Hz": frequency}


def read_tip_rows(directory: Path, dt_output: float, time_offset: float) -> list[dict[str, float]]:
    files = sorted(directory.glob("*.vtu"))
    if not files:
        raise FileNotFoundError(f"No VTU files in {directory}")

    first_points, _ = read_vtu(files[0])
    mesh_nodes = directory.parents[1] / "mesh" / "mesh.nodes"
    reference_points = read_elmer_nodes(mesh_nodes) if mesh_nodes.exists() else first_points
    tip_id = nearest(reference_points, (0.6, 0.2))

    rows = []
    for step, file in enumerate(files, start=1):
        _, fields = read_vtu(file)
        displacement = fields.get("displacement")
        if displacement is None:
            raise ValueError(f"No Displacement field in {file}")
        rows.append(
            {
                "time": time_offset + step * dt_output,
                "tip_ux_mm": float(1000.0 * displacement[tip_id, 0]),
                "tip_uy_mm": float(1000.0 * displacement[tip_id, 1]),
            }
        )
    return rows


def target_error(metric: str, value: float) -> float:
    target = COMSOL_TARGETS.get(metric)
    if target is None or target == 0.0 or not math.isfinite(value):
        return float("nan")
    return 100.0 * (value - target) / abs(target)


def summarize_case(directory: Path, dt_output: float, time_offset: float, window_start: float) -> dict[str, float]:
    tip_rows = read_tip_rows(directory, dt_output, time_offset)
    load_rows = analyze_directory(directory, dt_output, time_offset)

    rows = []
    for tip, load in zip(tip_rows, load_rows, strict=True):
        if tip["time"] < window_start:
            continue
        rows.append(
            {
                "time": tip["time"],
                "tip_ux_mm": tip["tip_ux_mm"],
                "tip_uy_mm": tip["tip_uy_mm"],
                "drag_N": -load["cylinder_beam_all_drag_N"],
                "lift_N": -load["cylinder_beam_all_lift_N"],
            }
        )
    if not rows:
        raise ValueError(f"No rows at or after window_start={window_start}")

    times = np.asarray([row["time"] for row in rows], dtype=float)
    summary: dict[str, float] = {
        "time_start": float(times[0]),
        "time_end": float(times[-1]),
        "samples": float(len(rows)),
    }
    for signal in ("tip_ux_mm", "tip_uy_mm", "drag_N", "lift_N"):
        values = np.asarray([row[signal] for row in rows], dtype=float)
        metrics = signal_metrics(times, values)
        summary[f"{signal}_min"] = float(np.min(values))
        summary[f"{signal}_max"] = float(np.max(values))
        for name, value in metrics.items():
            summary[f"{signal}_{name}"] = value
        for name in ("mean", "amp"):
            key = f"{signal}_{name}"
            summary[f"{key}_target"] = COMSOL_TARGETS.get(key, float("nan"))
            summary[f"{key}_error_pct"] = target_error(key, summary[key])
    return summary


def write_summary_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    keys: list[str] = []
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
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.05)
    parser.add_argument("--time-offset", type=float, default=0.0)
    parser.add_argument("--window-start", type=float, default=0.0)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, float | str]] = []
    for directory in args.directories:
        summary = summarize_case(directory, args.dt_output, args.time_offset, args.window_start)
        row: dict[str, float | str] = {"case": directory.name, **summary}
        rows.append(row)

    if args.csv:
        write_summary_csv(args.csv, rows)

    for row in rows:
        print(f"case={row['case']} window={row['time_start']:.6g}-{row['time_end']:.6g}s samples={int(row['samples'])}")
        for signal in ("tip_ux_mm", "tip_uy_mm", "drag_N", "lift_N"):
            print(
                f"  {signal}: mean={row[f'{signal}_mean']:.6g}, "
                f"amp={row[f'{signal}_amp']:.6g}, freq={row[f'{signal}_freq_Hz']:.6g} Hz, "
                f"range={row[f'{signal}_min']:.6g}..{row[f'{signal}_max']:.6g}"
            )


if __name__ == "__main__":
    main()
