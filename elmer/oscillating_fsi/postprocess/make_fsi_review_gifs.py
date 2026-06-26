"""Render review GIFs for oscillating-FSI motion and mesh evolution."""

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
from make_result_gifs import frame_to_image, sample_files, triangles_from_fields


@dataclass(frozen=True)
class ReviewJob:
    name: str
    directories: tuple[str, ...]
    kind: str
    title: str
    max_frames: int = 60
    dt_output: float = 0.05
    deform_scale: float = 20.0
    zoom: bool = True
    field: str = "velocity"


JOBS = (
    ReviewJob(
        "fixed_flow_long_velocity_review",
        ("fixed_flow_long",),
        "motion",
        "fixed obstacle flow, velocity",
        max_frames=50,
        deform_scale=1.0,
    ),
    ReviewJob(
        "fsi_0to5_motion_x20_review",
        ("fsi_pilot_1s", "fsi_1to2", "fsi_2to5"),
        "motion",
        "baseline FSI 0-5 s, deformed x20",
        max_frames=80,
    ),
    ReviewJob(
        "fsi_0to5_mesh_x20_review",
        ("fsi_pilot_1s", "fsi_1to2", "fsi_2to5"),
        "mesh",
        "baseline FSI mesh evolution, deformed x20",
        max_frames=80,
    ),
    ReviewJob(
        "fsi_tip_fsi_trigger_2s_motion_x20_review",
        ("fsi_tip_fsi_trigger_2s",),
        "motion",
        "tip FSI + trigger, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_tip_fsi_trigger_2s_mesh_x20_review",
        ("fsi_tip_fsi_trigger_2s",),
        "mesh",
        "tip FSI + trigger mesh evolution, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_tip_trigger_only_2s_motion_x20_review",
        ("fsi_tip_trigger_only_2s",),
        "motion",
        "tip trigger only, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_tip_trigger_only_2s_mesh_x20_review",
        ("fsi_tip_trigger_only_2s",),
        "mesh",
        "tip trigger only mesh evolution, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_inlet_vpulse_2s_motion_x20_review",
        ("fsi_inlet_vpulse_2s",),
        "motion",
        "inlet y-pulse FSI, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_inlet_vpulse_2s_mesh_x20_review",
        ("fsi_inlet_vpulse_2s",),
        "mesh",
        "inlet y-pulse FSI mesh evolution, deformed x20",
        max_frames=40,
    ),
    ReviewJob(
        "fsi_refined_linear_bubbles_probe_partial_motion_x20_review",
        ("fsi_refined_linear_bubbles_probe_2s",),
        "motion",
        "refined linear bubbles FSI probe, deformed x20",
        max_frames=20,
    ),
    ReviewJob(
        "fsi_refined_linear_bubbles_probe_partial_mesh_x20_review",
        ("fsi_refined_linear_bubbles_probe_2s",),
        "mesh",
        "refined linear bubbles FSI probe mesh, deformed x20",
        max_frames=20,
    ),
    ReviewJob(
        "solid_force_1N_mesh_x20_review",
        ("solid_force_1N",),
        "mesh",
        "dry solid 1 N mesh evolution, deformed x20",
        max_frames=80,
        dt_output=0.01,
        zoom=True,
    ),
)


def collect_files(case_root: Path, directories: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        files.extend(sorted((case_root / "results_raw" / directory).glob("*.vtu")))
    return files


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


def draw_obstacles(ax: plt.Axes) -> None:
    cylinder = plt.Circle((0.20, 0.20), 0.05, facecolor="#f2f2f2", edgecolor="black", linewidth=0.9, zorder=6)
    ax.add_patch(cylinder)


def set_view(ax: plt.Axes, job: ReviewJob, points: np.ndarray, fields: dict[str, np.ndarray]) -> None:
    if job.zoom:
        ax.set_xlim(0.12, 0.76)
        ax.set_ylim(0.125, 0.275)
    else:
        ax.set_xlim(float(points[:, 0].min()), float(points[:, 0].max()))
        ax.set_ylim(float(points[:, 1].min()), float(points[:, 1].max()))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")


def render_motion_frame(
    ax: plt.Axes,
    file: Path,
    job: ReviewJob,
    vmin: float,
    vmax: float,
) -> tuple[object, str]:
    points, fields = read_vtu(file)
    draw_points = deformed_points(points, fields, job.deform_scale)
    fluid_triangles = triangles_from_fields(fields, body=1)
    solid_triangles = triangles_from_fields(fields, body=2)
    values, label = values_for_field(fields, job.field)

    if len(fluid_triangles):
        fluid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], fluid_triangles)
        contour = ax.tripcolor(fluid, values, shading="gouraud", cmap="viridis", vmin=vmin, vmax=vmax)
        ax.triplot(fluid, color="black", linewidth=0.05, alpha=0.08)
    else:
        solid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], solid_triangles)
        contour = ax.tripcolor(solid, values, shading="gouraud", cmap="magma", vmin=vmin, vmax=vmax)

    if len(solid_triangles):
        solid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], solid_triangles)
        ax.tripcolor(solid, np.full(draw_points.shape[0], 1.0), color="#d9d9d9", edgecolors="none", zorder=4)
        ax.triplot(solid, color="black", linewidth=0.30, alpha=0.90, zorder=5)
    draw_obstacles(ax)
    set_view(ax, job, draw_points, fields)
    return contour, label


def render_mesh_frame(ax: plt.Axes, file: Path, job: ReviewJob) -> None:
    points, fields = read_vtu(file)
    draw_points = deformed_points(points, fields, job.deform_scale)
    fluid_triangles = triangles_from_fields(fields, body=1)
    solid_triangles = triangles_from_fields(fields, body=2)

    if len(fluid_triangles):
        fluid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], fluid_triangles)
        ax.triplot(fluid, color="#9aa0a6", linewidth=0.12, alpha=0.45)
    if len(solid_triangles):
        solid = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], solid_triangles)
        ax.triplot(solid, color="#111111", linewidth=0.45, alpha=0.95)
        ax.tripcolor(solid, np.full(draw_points.shape[0], 1.0), color="#e6e6e6", edgecolors="none", alpha=0.65)
    draw_obstacles(ax)
    set_view(ax, job, draw_points, fields)


def field_limits(files: list[Path], job: ReviewJob, sampled: list[tuple[int, Path]]) -> tuple[float, float]:
    values = []
    for _, file in sampled:
        _, fields = read_vtu(file)
        data, _ = values_for_field(fields, job.field)
        triangles = triangles_from_fields(fields, body=1)
        if len(triangles):
            values.append(data[np.unique(triangles)])
        else:
            values.append(data)
    all_values = np.concatenate(values)
    vmin = float(np.nanpercentile(all_values, 1.0))
    vmax = float(np.nanpercentile(all_values, 99.0))
    if np.isclose(vmin, vmax):
        vmax = vmin + 1.0
    return vmin, vmax


def render_job(case_root: Path, output_dir: Path, job: ReviewJob, fps: float) -> Path:
    files = collect_files(case_root, job.directories)
    if not files:
        raise FileNotFoundError(f"No VTU files for {job.name}: {job.directories}")
    sampled = sample_files(files, job.max_frames)
    vmin = vmax = 0.0
    if job.kind == "motion":
        vmin, vmax = field_limits(files, job, sampled)

    images = []
    for absolute_index, file in sampled:
        fig, ax = plt.subplots(figsize=(9.6, 3.2), dpi=130)
        time = (absolute_index + 1) * job.dt_output
        if job.kind == "motion":
            contour, label = render_motion_frame(ax, file, job, vmin, vmax)
            cbar = fig.colorbar(contour, ax=ax, fraction=0.035, pad=0.02)
            cbar.set_label(label)
        else:
            render_mesh_frame(ax, file, job)
        ax.set_title(f"{job.title}   t={time:.2f} s")
        fig.tight_layout()
        images.append(frame_to_image(fig))
        plt.close(fig)

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{job.name}.gif"
    imageio.mimsave(output, images, fps=fps, loop=0)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--jobs", nargs="*")
    parser.add_argument("--fps", type=float, default=10.0)
    args = parser.parse_args()

    output_dir = args.output_dir or args.case_root / "visualizations"
    selected = set(args.jobs or [job.name for job in JOBS])
    known = {job.name for job in JOBS}
    unknown = selected - known
    if unknown:
        raise SystemExit(f"Unknown job(s): {', '.join(sorted(unknown))}")
    for job in JOBS:
        if job.name not in selected:
            continue
        print(render_job(args.case_root, output_dir, job, args.fps))


if __name__ == "__main__":
    main()
