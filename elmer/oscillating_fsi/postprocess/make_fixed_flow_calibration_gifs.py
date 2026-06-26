"""Render side-by-side fixed-flow calibration GIFs for the wake screen."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

from analyze_vtu import read_vtu
from make_result_gifs import frame_to_image, triangles_from_fields


@dataclass(frozen=True)
class CaseSpec:
    name: str
    label: str
    dt_output: float


CASES = (
    CaseSpec("fixed_flow_nostab_outfine_5s", "attempted reduction, output 0.01 s", 0.01),
    CaseSpec("fixed_flow_bubbles_5s", "bubbles", 0.05),
)


def case_file(case_root: Path, case: CaseSpec, time: float) -> Path:
    index = max(1, int(round(time / case.dt_output)))
    return case_root / "results_raw" / case.name / f"{case.name}_t{index:04d}.vtu"


def velocity_values(fields: dict[str, np.ndarray]) -> np.ndarray:
    velocity = fields["velocity"]
    return np.linalg.norm(velocity[:, :2], axis=1)


def color_limits(case_root: Path, times: np.ndarray) -> tuple[float, float]:
    values = []
    for case in CASES:
        for time in times[:: max(1, len(times) // 12)]:
            _, fields = read_vtu(case_file(case_root, case, float(time)))
            fluid_triangles = triangles_from_fields(fields, body=1)
            ids = np.unique(fluid_triangles)
            values.append(velocity_values(fields)[ids])
    all_values = np.concatenate(values)
    vmin = float(np.nanpercentile(all_values, 1.0))
    vmax = float(np.nanpercentile(all_values, 99.0))
    if np.isclose(vmin, vmax):
        vmax = vmin + 1.0
    return vmin, vmax


def render_panel(ax: plt.Axes, file: Path, label: str, vmin: float, vmax: float) -> object:
    points, fields = read_vtu(file)
    fluid_triangles = triangles_from_fields(fields, body=1)
    solid_triangles = triangles_from_fields(fields, body=2)
    values = velocity_values(fields)

    fluid = mtri.Triangulation(points[:, 0], points[:, 1], fluid_triangles)
    contour = ax.tripcolor(fluid, values, shading="gouraud", cmap="viridis", vmin=vmin, vmax=vmax)
    ax.triplot(fluid, color="black", linewidth=0.04, alpha=0.08)

    if len(solid_triangles):
        solid = mtri.Triangulation(points[:, 0], points[:, 1], solid_triangles)
        ax.tripcolor(solid, np.ones(points.shape[0]), color="#d9d9d9", edgecolors="none", zorder=4)
        ax.triplot(solid, color="black", linewidth=0.30, alpha=0.85, zorder=5)

    cylinder = plt.Circle((0.20, 0.20), 0.05, facecolor="#f2f2f2", edgecolor="black", linewidth=0.9, zorder=6)
    ax.add_patch(cylinder)
    ax.set_xlim(0.10, 0.95)
    ax.set_ylim(0.10, 0.31)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(label)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    return contour


def render_compare(case_root: Path, output: Path, start: float, end: float, frames: int, fps: float) -> Path:
    times = np.linspace(start, end, frames)
    vmin, vmax = color_limits(case_root, times)
    images = []
    for time in times:
        fig, axes = plt.subplots(1, 2, figsize=(12, 3.4), dpi=130, sharex=True, sharey=True)
        contour = None
        for ax, case in zip(axes, CASES, strict=True):
            contour = render_panel(ax, case_file(case_root, case, float(time)), case.label, vmin, vmax)
        fig.suptitle(f"Fixed-flow wake comparison, t={time:.3f} s")
        cbar = fig.colorbar(contour, ax=axes.ravel().tolist(), fraction=0.025, pad=0.015)
        cbar.set_label("|u| m/s")
        fig.tight_layout()
        images.append(frame_to_image(fig))
        plt.close(fig)

    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output, images, fps=fps, loop=0)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--start", type=float, default=4.0)
    parser.add_argument("--end", type=float, default=5.0)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--fps", type=float, default=12.0)
    args = parser.parse_args()

    output = args.output or args.case_root / "visualizations" / "fixed_flow_calibration_outfine_vs_bubbles_t4to5.gif"
    print(render_compare(args.case_root, output, args.start, args.end, args.frames, args.fps))


if __name__ == "__main__":
    main()
