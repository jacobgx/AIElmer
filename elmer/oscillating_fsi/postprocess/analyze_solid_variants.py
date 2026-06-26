"""Analyze arbitrary solid-only variants against the current COMSOL frequency target."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analyze_solid_sweep import analyze_case


DEFAULT_CASES = (
    ("solid_force_1N", 1.0),
    ("solid_force_1N_no_plane_stress", 1.0),
    ("solid_force_1N_density_142kg", 1.0),
    ("solid_force_1N_E_39p3MPa", 1.0),
)

COMSOL_UY_FREQ_HZ = 5.3


def parse_case(value: str) -> tuple[str, float]:
    if ":" not in value:
        return value, 1.0
    name, force = value.split(":", 1)
    return name, float(force)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--dt-output", type=float, default=0.01)
    parser.add_argument("--summary-csv", type=Path)
    parser.add_argument("--tip-csv-dir", type=Path)
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="Case name or case:force_N. Defaults to the current structural variants.",
    )
    args = parser.parse_args()

    cases = [parse_case(case) for case in args.cases] if args.cases else list(DEFAULT_CASES)
    rows = []
    for case, force in cases:
        row = analyze_case(args.case_root / "results_raw" / case, force, args.dt_output, args.tip_csv_dir)
        freq = row["uy_zero_crossing_freq_Hz"]
        if isinstance(freq, float) and freq == freq:
            row["freq_error_pct_vs_comsol"] = 100.0 * (freq - COMSOL_UY_FREQ_HZ) / COMSOL_UY_FREQ_HZ
        else:
            row["freq_error_pct_vs_comsol"] = float("nan")
        rows.append(row)

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
