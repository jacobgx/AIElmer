#!/usr/bin/env python3
from __future__ import annotations

import io
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MESH_DIR = ROOT / "shoebox_hexas"
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
        return _array_from_block(data, raw_base, int(offset_m.group(1)), vtk_type, comps)

    point_block = re.search(r"<PointData>(.*?)</PointData>", xml, re.S).group(1)
    for tag in re.findall(r"<DataArray[^>]+/>", point_block):
        name_m = re.search(r'Name="([^"]+)"', tag)
        if name_m:
            point_data[name_m.group(1)] = parse_tag(tag)

    points_tag = re.search(r"<Points>\s*(<DataArray[^>]+/>)\s*</Points>", xml, re.S).group(1)
    points = parse_tag(points_tag)
    return points, point_data


def center_y_slice(points: np.ndarray) -> np.ndarray:
    ys = np.unique(np.round(points[:, 1], 12))
    y0 = ys[np.argmin(np.abs(ys - np.median(ys)))]
    return np.isclose(points[:, 1], y0, atol=1e-12)


def plot_field(path: Path, output: Path, title: str, vmin: float | None = None, vmax: float | None = None) -> None:
    points, fields = read_vtu(path)
    elfield = fields["elfield"]
    mag = np.linalg.norm(elfield, axis=1)
    mask = center_y_slice(points)

    fig, ax = plt.subplots(figsize=(7.8, 4.6), constrained_layout=True)
    sc = ax.scatter(points[mask, 2], points[mask, 0], c=mag[mask], s=42, cmap="viridis", vmin=vmin, vmax=vmax)
    ax.set_xlabel("z")
    ax.set_ylabel("x")
    ax.set_title(title)
    ax.set_aspect("auto")
    fig.colorbar(sc, ax=ax, label="|E|")
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_field_png_and_gif(vtus: list[Path]) -> None:
    max_values = []
    for path in vtus:
        _, fields = read_vtu(path)
        max_values.append(float(np.linalg.norm(fields["elfield"], axis=1).max()))
    vmax = max(max_values)
    plot_field(vtus[-1], OUT / "emwave_efield_magnitude_final.png", "EMWaveBoxHexas: |E| at final timestep", 0.0, vmax)

    frames = []
    for i, path in enumerate(vtus, 1):
        points, fields = read_vtu(path)
        mag = np.linalg.norm(fields["elfield"], axis=1)
        mask = center_y_slice(points)
        fig, ax = plt.subplots(figsize=(7.2, 4.3), constrained_layout=True)
        sc = ax.scatter(points[mask, 2], points[mask, 0], c=mag[mask], s=38, cmap="viridis", vmin=0.0, vmax=vmax)
        ax.set_xlabel("z")
        ax.set_ylabel("x")
        ax.set_title(f"EMWaveBoxHexas: |E| timestep {i:02d}/{len(vtus)}")
        fig.colorbar(sc, ax=ax, label="|E|", shrink=0.88)
        bio = io.BytesIO()
        fig.savefig(bio, format="png", dpi=130)
        plt.close(fig)
        bio.seek(0)
        frames.append(Image.open(bio).convert("P", palette=Image.Palette.ADAPTIVE))
    frames[0].save(OUT / "emwave_efield_magnitude_timesteps.gif", save_all=True, append_images=frames[1:], duration=120, loop=0)


def save_scalar_plot() -> None:
    gdat = np.loadtxt(ROOT / "g.dat")
    steps = np.arange(1, gdat.shape[0] + 1)
    fig, ax = plt.subplots(figsize=(7.8, 4.3), constrained_layout=True)
    ax.plot(steps, gdat[:, 0], marker="o", ms=3, label="min(E)")
    ax.plot(steps, gdat[:, 1], marker="o", ms=3, label="max(E)")
    ax.set_xlabel("timestep")
    ax.set_ylabel("SaveScalars value")
    ax.set_title("EMWaveBoxHexas: g.dat min/max E")
    ax.grid(True, alpha=0.28)
    ax.legend()
    fig.savefig(OUT / "emwave_gdat_minmax.png", dpi=180)
    plt.close(fig)


def save_line_plot() -> None:
    ldat = np.loadtxt(ROOT / "l.dat")
    last_step = int(ldat[:, 0].max())
    row = ldat[ldat[:, 0] == last_step]
    z = row[:, 6]
    e2 = row[:, 8]
    elfield2 = row[:, 11]
    fig, ax = plt.subplots(figsize=(7.8, 4.3), constrained_layout=True)
    ax.plot(z, e2, label="E edge component 2")
    ax.plot(z, elfield2, label="elfield 2")
    ax.set_xlabel("z")
    ax.set_ylabel("field value")
    ax.set_title(f"EMWaveBoxHexas: l.dat centerline, timestep {last_step}")
    ax.grid(True, alpha=0.28)
    ax.legend()
    fig.savefig(OUT / "emwave_ldat_centerline_final.png", dpi=180)
    plt.close(fig)


def main() -> None:
    vtus = sorted(MESH_DIR.glob("g_t*.vtu"))
    save_field_png_and_gif(vtus)
    save_scalar_plot()
    save_line_plot()
    print(f"Wrote visualizations to {OUT}")


if __name__ == "__main__":
    main()
