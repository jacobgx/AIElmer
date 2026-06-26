"""Render zoomed FSI GIFs with the fluid hole and solid beam made explicit."""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

from analyze_vtu import read_vtu
from make_result_gifs import frame_to_image, sample_files, triangles_from_fields


def values_for_field(fields: dict[str, np.ndarray], field: str) -> tuple[np.ndarray, str]:
    data = fields[field]
    if data.ndim == 1:
        return data, field
    if field == "displacement":
        return 1000.0 * np.linalg.norm(data[:, :2], axis=1), "|d| mm"
    if field == "velocity":
        return np.linalg.norm(data[:, :2], axis=1), "|u| m/s"
    return np.linalg.norm(data[:, :2], axis=1), field


def deformed_points(points: np.ndarray, fields: dict[str, np.ndarray], scale: float) -> np.ndarray:
    draw = points.copy()
    displacement = fields.get("displacement")
    if displacement is not None:
        draw[:, :2] += scale * displacement[:, :2]
    return draw


def render_case(ax: plt.Axes, file: Path, case_label: str, field: str, scale: float, vmin: float, vmax: float) -> None:
    points, fields = read_vtu(file)
    draw_points = deformed_points(points, fields, scale)
    fluid_triangles = triangles_from_fields(fields, body=1)
    solid_triangles = triangles_from_fields(fields, body=2)
    values, label = values_for_field(fields, field)

    fluid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], fluid_triangles)
    solid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], solid_triangles)
    contour = ax.tripcolor(fluid, values, shading="gouraud", cmap="viridis", vmin=vmin, vmax=vmax)
    ax.triplot(fluid, color="black", linewidth=0.06, alpha=0.12)
    ax.tripcolor(solid, np.full(draw_points.shape[0], 1.0), color="#d9d9d9", edgecolors="none")
    ax.triplot(solid, color="black", linewidth=0.35, alpha=0.85)

    cylinder = plt.Circle((0.20, 0.20), 0.05, facecolor="#f2f2f2", edgecolor="black", linewidth=0.9, zorder=5)
    ax.add_patch(cylinder)
    ax.set_xlim(0.12, 0.74)
    ax.set_ylim(0.13, 0.27)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(case_label)
    return contour, label


def render_compare(case_root: Path, left_case: str, right_case: str, output: Path, field: str, scale: float, fps: float) -> None:
    left_files = sorted((case_root / "results_raw" / left_case).glob("*.vtu"))
    right_files = sorted((case_root / "results_raw" / right_case).glob("*.vtu"))
    if not left_files or not right_files:
        raise FileNotFoundError("Missing VTU files for one or both cases.")

    sampled_left = sample_files(left_files, 40)
    sampled_right = sample_files(right_files, 40)
    values = []
    for _, file in sampled_left + sampled_right:
        _, fields = read_vtu(file)
        data, _ = values_for_field(fields, field)
        fluid_triangles = triangles_from_fields(fields, body=1)
        values.append(data[np.unique(fluid_triangles)])
    all_values = np.concatenate(values)
    vmin = float(np.nanpercentile(all_values, 1.0))
    vmax = float(np.nanpercentile(all_values, 99.0))
    if np.isclose(vmin, vmax):
        vmax = vmin + 1.0

    images = []
    for (left_index, left_file), (_, right_file) in zip(sampled_left, sampled_right, strict=True):
        fig, axes = plt.subplots(1, 2, figsize=(12, 3.4), dpi=130, sharex=True, sharey=True)
        contour, label = render_case(axes[0], left_file, "A: tip FSI + trigger", field, scale, vmin, vmax)
        render_case(axes[1], right_file, "B: trigger only", field, scale, vmin, vmax)
        time = (left_index + 1) * 0.05
        fig.suptitle(f"Fluid hole + solid beam overlay, deformed x{scale:g}, t={time:.2f} s")
        cbar = fig.colorbar(contour, ax=axes.ravel().tolist(), fraction=0.025, pad=0.015)
        cbar.set_label(label)
        fig.tight_layout()
        images.append(frame_to_image(fig))
        plt.close(fig)

    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output, images, fps=fps, loop=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--left-case", default="fsi_tip_fsi_trigger_2s")
    parser.add_argument("--right-case", default="fsi_tip_trigger_only_2s")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--field", default="velocity")
    parser.add_argument("--scale", type=float, default=20.0)
    parser.add_argument("--fps", type=float, default=10.0)
    args = parser.parse_args()

    output = args.output or args.case_root / "visualizations" / "fsi_tip_ab_obstacle_zoom_velocity_x20.gif"
    render_compare(args.case_root, args.left_case, args.right_case, output, args.field, args.scale, args.fps)
    print(output)


if __name__ == "__main__":
    main()
