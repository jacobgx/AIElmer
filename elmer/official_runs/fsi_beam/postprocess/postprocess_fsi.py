#!/usr/bin/env python3
from __future__ import annotations

import io
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
VTU = ROOT / "fsi" / "fsi_t0001.vtu"
OUT = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)


def _array_from_block(data: bytes, base: int, offset: int, vtk_type: str, comps: int) -> np.ndarray:
    dtype = {"Float64": "<f8", "Float32": "<f4", "Int32": "<i4", "UInt32": "<u4"}[vtk_type]
    block = base + offset
    nbytes = int(np.frombuffer(data[block : block + 4], dtype="<u4", count=1)[0])
    arr = np.frombuffer(data[block + 4 : block + 4 + nbytes], dtype=np.dtype(dtype)).copy()
    if comps > 1:
        arr = arr.reshape((-1, comps))
    return arr


def read_vtu(path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    data = path.read_bytes()
    xml = data[: data.index(b"<AppendedData")].decode("utf-8", "ignore")
    raw_base = data.index(b"_", data.index(b"<AppendedData")) + 1
    point_data: dict[str, np.ndarray] = {}

    def parse_tag(tag: str) -> np.ndarray:
        offset_m = re.search(r'offset="(\d+)"', tag)
        name_m = re.search(r'Name="([^"]+)"', tag)
        type_m = re.search(r'type="([^"]+)"', tag)
        comps_m = re.search(r'NumberOfComponents="(\d+)"', tag)
        vtk_type = type_m.group(1) if type_m else "Float64"
        comps = int(comps_m.group(1)) if comps_m else 1
        offset = int(offset_m.group(1))
        return _array_from_block(data, raw_base, offset, vtk_type, comps)

    point_block = re.search(r"<PointData>(.*?)</PointData>", xml, re.S).group(1)
    for tag in re.findall(r"<DataArray[^>]+/>", point_block):
        name_m = re.search(r'Name="([^"]+)"', tag)
        if name_m:
            point_data[name_m.group(1)] = parse_tag(tag)

    points_tag = re.search(r"<Points>\s*(<DataArray[^>]+/>)\s*</Points>", xml, re.S).group(1)
    points = parse_tag(points_tag)

    return points, point_data


def triangulation(points: np.ndarray) -> mtri.Triangulation:
    return mtri.Triangulation(points[:, 0], points[:, 1])


def save_field_png(points: np.ndarray, fields: dict[str, np.ndarray]) -> None:
    tri = triangulation(points)
    pressure = fields["pressure"].reshape(-1)
    velocity = fields["velocity"]
    speed = np.linalg.norm(velocity[:, :2], axis=1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    for ax, values, title, cmap in [
        (axes[0], pressure, "Pressure", "viridis"),
        (axes[1], speed, "Velocity magnitude", "magma"),
    ]:
        im = ax.tricontourf(tri, values, levels=36, cmap=cmap)
        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, shrink=0.86)
    fig.suptitle("fsi_beam: fluid field, steady-state result")
    fig.savefig(OUT / "fsi_pressure_velocity.png", dpi=180)
    plt.close(fig)


def displacement_scale(points: np.ndarray, displacement: np.ndarray) -> float:
    mag = np.linalg.norm(displacement[:, :2], axis=1)
    max_mag = float(np.max(mag))
    domain = np.ptp(points[:, :2], axis=0)
    return 0.08 * float(np.max(domain)) / max_mag if max_mag > 0 else 1.0


def save_field_gif(points: np.ndarray, fields: dict[str, np.ndarray], displacement: np.ndarray, final_scale: float) -> None:
    pressure = fields["pressure"].reshape(-1)
    speed = np.linalg.norm(fields["velocity"][:, :2], axis=1)
    disp2 = displacement[:, :2]

    pressure_levels = np.linspace(float(pressure.min()), float(pressure.max()), 37)
    speed_levels = np.linspace(float(speed.min()), float(speed.max()), 37)
    xpad = 0.04 * float(np.ptp(points[:, 0]))
    ypad = 0.12 * float(np.ptp(points[:, 1]))
    frames = []

    for scale in np.linspace(0.0, final_scale, 18):
        xy = points[:, :2] + scale * disp2
        tri = mtri.Triangulation(xy[:, 0], xy[:, 1])
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
        for ax, values, levels, title, cmap in [
            (axes[0], pressure, pressure_levels, "Pressure", "viridis"),
            (axes[1], speed, speed_levels, "Velocity magnitude", "magma"),
        ]:
            im = ax.tricontourf(tri, values, levels=levels, cmap=cmap)
            ax.set_aspect("equal")
            ax.set_xlim(points[:, 0].min() - xpad, points[:, 0].max() + xpad)
            ax.set_ylim(points[:, 1].min() - ypad, points[:, 1].max() + ypad)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_title(title)
            fig.colorbar(im, ax=ax, shrink=0.86)
        fig.suptitle(f"fsi_beam: fluid field, visualization-only deformation x{scale:.1f}")
        bio = io.BytesIO()
        fig.savefig(bio, format="png", dpi=130)
        plt.close(fig)
        bio.seek(0)
        frames.append(Image.open(bio).convert("P", palette=Image.Palette.ADAPTIVE))

    frames[0].save(
        OUT / "fsi_pressure_velocity.gif",
        save_all=True,
        append_images=frames[1:],
        duration=130,
        loop=0,
    )


def save_displacement_png(points: np.ndarray, displacement: np.ndarray) -> float:
    disp2 = displacement[:, :2]
    mag = np.linalg.norm(disp2, axis=1)
    scale = displacement_scale(points, displacement)
    deformed = points[:, :2] + scale * disp2

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    for ax, xy, title in [
        (axes[0], points[:, :2], "Displacement magnitude"),
        (axes[1], deformed, f"Deformed view x{scale:.1f}"),
    ]:
        tri = mtri.Triangulation(xy[:, 0], xy[:, 1])
        im = ax.tricontourf(tri, mag, levels=36, cmap="plasma")
        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, shrink=0.86)
    fig.suptitle("fsi_beam: structural displacement, steady-state result")
    fig.savefig(OUT / "fsi_displacement.png", dpi=180)
    plt.close(fig)
    return scale


def save_displacement_gif(points: np.ndarray, displacement: np.ndarray, final_scale: float) -> None:
    disp2 = displacement[:, :2]
    mag = np.linalg.norm(disp2, axis=1)
    xpad = 0.04 * float(np.ptp(points[:, 0]))
    ypad = 0.12 * float(np.ptp(points[:, 1]))
    frames = []
    for scale in np.linspace(0.0, final_scale, 18):
        deformed = points[:, :2] + scale * disp2
        tri = mtri.Triangulation(deformed[:, 0], deformed[:, 1])
        fig, ax = plt.subplots(figsize=(7.8, 4.4), constrained_layout=True)
        im = ax.tricontourf(tri, mag, levels=36, cmap="plasma", vmin=float(mag.min()), vmax=float(mag.max()))
        ax.set_aspect("equal")
        ax.set_xlim(points[:, 0].min() - xpad, points[:, 0].max() + xpad)
        ax.set_ylim(points[:, 1].min() - ypad, points[:, 1].max() + ypad)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Visualization-only displacement amplification: x{scale:.1f}")
        fig.colorbar(im, ax=ax, label="|displacement|", shrink=0.86)
        bio = io.BytesIO()
        fig.savefig(bio, format="png", dpi=130)
        plt.close(fig)
        bio.seek(0)
        frames.append(Image.open(bio).convert("P", palette=Image.Palette.ADAPTIVE))
    frames[0].save(
        OUT / "fsi_displacement_amplification_visualization_only.gif",
        save_all=True,
        append_images=frames[1:],
        duration=130,
        loop=0,
    )


def main() -> None:
    points, fields = read_vtu(VTU)
    save_field_png(points, fields)
    scale = save_displacement_png(points, fields["displacement"])
    save_field_gif(points, fields, fields["displacement"], scale)
    save_displacement_gif(points, fields["displacement"], scale)
    print(f"Wrote visualizations to {OUT}")


if __name__ == "__main__":
    main()
