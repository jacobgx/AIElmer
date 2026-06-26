"""Create GIF visualizations from Elmer VTU result directories."""

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


@dataclass(frozen=True)
class GifJob:
    name: str
    directories: tuple[str, ...]
    field: str
    title: str
    max_frames: int
    dt_output: float
    time_offset: float = 0.0
    deform_scale: float = 1.0


DEFAULT_JOBS = (
    GifJob("fixed_flow_mvp_velocity", ("fixed_flow_mvp",), "velocity", "fixed_flow_mvp velocity", 40, 0.05),
    GifJob("fsi_mvp_displacement", ("fsi_mvp",), "displacement", "fsi_mvp displacement", 40, 0.05),
    GifJob(
        "fsi_0to5_displacement",
        ("fsi_pilot_1s", "fsi_1to2", "fsi_2to5"),
        "displacement",
        "fsi 0-5 s displacement",
        80,
        0.05,
    ),
    GifJob("solid_only_displacement", ("solid_only",), "displacement", "solid_only displacement", 60, 0.05),
    GifJob("solid_force_1N_displacement", ("solid_force_1N",), "displacement", "solid_force_1N displacement", 80, 0.01),
    GifJob("solid_force_10N_displacement", ("solid_force_10N",), "displacement", "solid_force_10N displacement", 80, 0.01),
)


def collect_files(results_root: Path, directories: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        files.extend(sorted((results_root / directory).glob("*.vtu")))
    return files


def sample_files(files: list[Path], max_frames: int) -> list[tuple[int, Path]]:
    if len(files) <= max_frames:
        return list(enumerate(files))
    indices = np.linspace(0, len(files) - 1, max_frames, dtype=int)
    return [(int(i), files[int(i)]) for i in indices]


def triangles_from_fields(fields: dict[str, np.ndarray], body: int | None = None) -> np.ndarray:
    geometry_ids = fields["geometryids"]
    connectivity = fields["connectivity"]
    offsets = fields["offsets"]
    cell_types = fields["types"]
    triangles = []
    begin = 0
    for geometry_id, end, cell_type in zip(geometry_ids, offsets, cell_types):
        if int(cell_type) == 5 and (body is None or int(geometry_id) == body):
            cell = connectivity[begin:int(end)]
            if len(cell) == 3:
                triangles.append([int(cell[0]), int(cell[1]), int(cell[2])])
        begin = int(end)
    return np.asarray(triangles, dtype=int)


def field_values(fields: dict[str, np.ndarray], field: str) -> tuple[np.ndarray, str]:
    data = fields[field]
    if data.ndim == 1:
        return data, field
    values = np.linalg.norm(data[:, :2], axis=1)
    if field == "velocity":
        return values, "|u| m/s"
    if field == "displacement":
        return 1000.0 * values, "|d| mm"
    return values, field


def frame_to_image(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    return rgba[:, :, :3].copy()


def render_gif(job: GifJob, case_root: Path, output_dir: Path, fps: float) -> Path:
    results_root = case_root / "results_raw"
    files = collect_files(results_root, job.directories)
    if not files:
        raise FileNotFoundError(f"No VTU files for {job.name}: {job.directories}")

    sampled = sample_files(files, job.max_frames)
    first_points, first_fields = read_vtu(sampled[0][1])
    body = 2 if job.field == "displacement" and job.name.startswith("solid") else None
    triangles = triangles_from_fields(first_fields, body=body)
    if len(triangles) == 0:
        triangles = triangles_from_fields(first_fields, body=None)

    values_for_limits = []
    for _, file in sampled:
        _, fields = read_vtu(file)
        values, _ = field_values(fields, job.field)
        if body == 2:
            ids = np.unique(triangles)
            values_for_limits.append(values[ids])
        else:
            values_for_limits.append(values)
    all_values = np.concatenate(values_for_limits)
    vmin = float(np.nanpercentile(all_values, 1.0))
    vmax = float(np.nanpercentile(all_values, 99.0))
    if np.isclose(vmin, vmax):
        vmax = vmin + 1.0

    view_ids = np.unique(triangles)
    view_points = first_points[view_ids] if body == 2 else first_points
    xlim = (float(view_points[:, 0].min()), float(view_points[:, 0].max()))
    ylim = (float(view_points[:, 1].min()), float(view_points[:, 1].max()))
    pad_x = 0.02 * (xlim[1] - xlim[0])
    pad_y = max(0.08 * (ylim[1] - ylim[0]), 0.02)
    xlim = (xlim[0] - pad_x, xlim[1] + pad_x)
    ylim = (ylim[0] - pad_y, ylim[1] + pad_y)

    images = []
    for absolute_index, file in sampled:
        points, fields = read_vtu(file)
        values, label = field_values(fields, job.field)
        draw_points = points.copy()
        if job.field == "displacement":
            displacement = fields[job.field]
            draw_points[:, :2] += job.deform_scale * displacement[:, :2]

        triangulation = mtri.Triangulation(draw_points[:, 0], draw_points[:, 1], triangles)
        fig, ax = plt.subplots(figsize=(10, 3.1), dpi=120)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        time = job.time_offset + (absolute_index + 1) * job.dt_output
        ax.set_title(f"{job.title}   t={time:.2f} s")
        contour = ax.tripcolor(triangulation, values, shading="gouraud", cmap="viridis", vmin=vmin, vmax=vmax)
        ax.triplot(triangulation, color="black", linewidth=0.08, alpha=0.18)
        cbar = fig.colorbar(contour, ax=ax, fraction=0.035, pad=0.02)
        cbar.set_label(label)
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
    parser.add_argument("--fps", type=float, default=12.0)
    parser.add_argument("--jobs", nargs="*", help="Optional subset of default job names.")
    args = parser.parse_args()

    output_dir = args.output_dir or args.case_root / "visualizations"
    selected = set(args.jobs or [job.name for job in DEFAULT_JOBS])
    jobs = [job for job in DEFAULT_JOBS if job.name in selected]
    unknown = selected - {job.name for job in DEFAULT_JOBS}
    if unknown:
        raise SystemExit(f"Unknown job(s): {', '.join(sorted(unknown))}")

    for job in jobs:
        output = render_gif(job, args.case_root, output_dir, args.fps)
        print(output)


if __name__ == "__main__":
    main()
