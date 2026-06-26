from __future__ import annotations

import math
import re
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
VTU_PATH = ROOT / "elmesh" / "elstatics_t0001.vtu"
OUT_DIR = ROOT / "visualizations"


def _attrs(tag: str) -> dict[str, str]:
    return dict(re.findall(r'([A-Za-z0-9_]+)="([^"]*)"', tag))


def read_vtu_raw(path: Path) -> dict[str, np.ndarray]:
    data = path.read_bytes()
    app_pos = data.index(b"<AppendedData")
    underscore = data.index(b"_", app_pos)
    data_start = underscore + 1
    header = data[:app_pos].decode("utf-8", errors="ignore")

    arrays: dict[str, np.ndarray] = {}
    for match in re.finditer(r"<DataArray[^>]+>", header):
        tag = match.group(0)
        attrs = _attrs(tag)
        if attrs.get("format") != "appended":
            continue

        name = attrs.get("Name")
        if not name:
            before = header[: match.start()]
            if before.rfind("<Points>") > before.rfind("<Cells>"):
                name = "points"
            else:
                name = f"unnamed_{len(arrays)}"

        offset = int(attrs["offset"])
        vtk_type = attrs["type"]
        ncomp = int(attrs.get("NumberOfComponents", "1"))
        dtype = {"Float64": "<f8", "Int32": "<i4"}[vtk_type]
        nbytes = struct.unpack("<I", data[data_start + offset : data_start + offset + 4])[0]
        arr = np.frombuffer(
            data,
            dtype=np.dtype(dtype),
            count=nbytes // np.dtype(dtype).itemsize,
            offset=data_start + offset + 4,
        ).copy()
        if ncomp > 1:
            arr = arr.reshape((-1, ncomp))
        arrays[name] = arr

    return arrays


def colorize(values: np.ndarray, vmin: float | None = None, vmax: float | None = None) -> np.ndarray:
    vals = np.asarray(values, dtype=float)
    if vmin is None:
        vmin = float(np.nanpercentile(vals, 1.0))
    if vmax is None:
        vmax = float(np.nanpercentile(vals, 99.0))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        vmin = float(np.nanmin(vals))
        vmax = float(np.nanmax(vals) + 1.0)

    t = np.clip((vals - vmin) / (vmax - vmin), 0.0, 1.0)
    stops = np.array(
        [
            [0.00, 40, 48, 135],
            [0.18, 37, 104, 177],
            [0.36, 34, 168, 132],
            [0.58, 122, 209, 81],
            [0.78, 253, 190, 60],
            [1.00, 190, 35, 42],
        ],
        dtype=float,
    )
    idx = np.searchsorted(stops[:, 0], t, side="right") - 1
    idx = np.clip(idx, 0, len(stops) - 2)
    t0 = stops[idx, 0]
    t1 = stops[idx + 1, 0]
    frac = ((t - t0) / (t1 - t0))[:, None]
    rgb = stops[idx, 1:] * (1.0 - frac) + stops[idx + 1, 1:] * frac
    return np.clip(rgb, 0, 255).astype(np.uint8)


def add_colorbar(draw: ImageDraw.ImageDraw, x: int, y: int, h: int, label: str, vmin: float, vmax: float) -> None:
    vals = np.linspace(vmax, vmin, h)
    colors = colorize(vals, vmin, vmax)
    for row, color in enumerate(colors):
        draw.line((x, y + row, x + 18, y + row), fill=tuple(int(c) for c in color))
    draw.rectangle((x, y, x + 18, y + h), outline=(40, 40, 40))
    font = ImageFont.load_default()
    draw.text((x + 26, y - 4), f"{vmax:.3g}", fill=(30, 30, 30), font=font)
    draw.text((x + 26, y + h - 8), f"{vmin:.3g}", fill=(30, 30, 30), font=font)
    draw.text((x - 2, y + h + 10), label, fill=(30, 30, 30), font=font)


def draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str = "") -> None:
    font = ImageFont.load_default()
    draw.text((18, 12), title, fill=(20, 20, 20), font=font)
    if subtitle:
        draw.text((18, 30), subtitle, fill=(70, 70, 70), font=font)


def project_3d(points: np.ndarray, azimuth_deg: float, elevation_deg: float) -> tuple[np.ndarray, np.ndarray]:
    pts = points - points.mean(axis=0)
    scale = np.ptp(pts, axis=0).max()
    if scale > 0:
        pts = pts / scale
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    caz, saz = math.cos(az), math.sin(az)
    cel, sel = math.cos(el), math.sin(el)

    x1 = caz * pts[:, 0] - saz * pts[:, 1]
    y1 = saz * pts[:, 0] + caz * pts[:, 1]
    z1 = pts[:, 2]
    y2 = cel * y1 - sel * z1
    z2 = sel * y1 + cel * z1
    return np.column_stack([x1, y2]), z2


def render_point_cloud(
    points: np.ndarray,
    values: np.ndarray,
    output: Path,
    title: str,
    label: str,
    azimuth: float = 38.0,
    elevation: float = 24.0,
    size: tuple[int, int] = (1100, 820),
    radius: int = 2,
    subtitle: str = "",
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    coords, depth = project_3d(points, azimuth, elevation)

    pad_left, pad_right, pad_top, pad_bottom = 50, 170, 58, 48
    xmin, ymin = coords.min(axis=0)
    xmax, ymax = coords.max(axis=0)
    span = max(xmax - xmin, ymax - ymin, 1e-12)
    px = pad_left + (coords[:, 0] - (xmin + xmax - span) / 2.0) / span * (w - pad_left - pad_right)
    py = pad_top + (1.0 - (coords[:, 1] - (ymin + ymax - span) / 2.0) / span) * (h - pad_top - pad_bottom)
    colors = colorize(values)
    vmin = float(np.nanpercentile(values, 1.0))
    vmax = float(np.nanpercentile(values, 99.0))

    order = np.argsort(depth)
    for i in order:
        x = int(round(px[i]))
        y = int(round(py[i]))
        if pad_left <= x < w - pad_right and pad_top <= y < h - pad_bottom:
            color = tuple(int(c) for c in colors[i])
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    draw_title(draw, title, subtitle)
    add_colorbar(draw, w - 130, 120, 520, label, vmin, vmax)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    return img


def render_slice(
    points: np.ndarray,
    values: np.ndarray,
    output: Path,
    title: str,
    label: str,
    axis: int,
    mask: np.ndarray,
    vectors: np.ndarray | None = None,
) -> None:
    axes = [i for i in range(3) if i != axis]
    pts = points[mask][:, axes]
    vals = values[mask]
    vecs = vectors[mask][:, axes] if vectors is not None else None

    w, h = 1100, 820
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    pad_left, pad_right, pad_top, pad_bottom = 70, 170, 60, 70
    xmin, ymin = pts.min(axis=0)
    xmax, ymax = pts.max(axis=0)
    span = max(xmax - xmin, ymax - ymin, 1e-18)
    px = pad_left + (pts[:, 0] - (xmin + xmax - span) / 2.0) / span * (w - pad_left - pad_right)
    py = pad_top + (1.0 - (pts[:, 1] - (ymin + ymax - span) / 2.0) / span) * (h - pad_top - pad_bottom)
    colors = colorize(vals)
    vmin = float(np.nanpercentile(vals, 1.0))
    vmax = float(np.nanpercentile(vals, 99.0))

    for x, y, color in zip(px, py, colors):
        xi, yi = int(round(x)), int(round(y))
        if pad_left <= xi < w - pad_right and pad_top <= yi < h - pad_bottom:
            draw.ellipse((xi - 2, yi - 2, xi + 2, yi + 2), fill=tuple(int(c) for c in color))

    if vecs is not None:
        mag = np.linalg.norm(vecs, axis=1)
        if np.nanmax(mag) > 0:
            bins: dict[tuple[int, int], int] = {}
            for i, (x, y, m) in enumerate(zip(px, py, mag)):
                if not np.isfinite(m) or m <= 0:
                    continue
                key = (int(x // 42), int(y // 42))
                if key not in bins or m > mag[bins[key]]:
                    bins[key] = i
            arrow_ids = list(bins.values())[:260]
            scale = 24.0 / np.nanpercentile(mag[arrow_ids], 95.0)
            for i in arrow_ids:
                vx, vy = vecs[i]
                length = math.hypot(float(vx), float(vy))
                if length <= 0:
                    continue
                dx = float(vx) * scale
                dy = -float(vy) * scale
                dx = max(min(dx, 20), -20)
                dy = max(min(dy, 20), -20)
                x0, y0 = float(px[i]), float(py[i])
                x1, y1 = x0 + dx, y0 + dy
                draw.line((x0, y0, x1, y1), fill=(15, 15, 15), width=1)
                ang = math.atan2(y1 - y0, x1 - x0)
                for da in (2.55, -2.55):
                    draw.line(
                        (x1, y1, x1 + 6 * math.cos(ang + da), y1 + 6 * math.sin(ang + da)),
                        fill=(15, 15, 15),
                        width=1,
                    )

    axis_name = "XYZ"[axis]
    subtitle = f"Slice near median {axis_name}; {mask.sum()} nodes shown"
    draw_title(draw, title, subtitle)
    add_colorbar(draw, w - 130, 120, 520, label, vmin, vmax)
    draw.rectangle((pad_left, pad_top, w - pad_right, h - pad_bottom), outline=(180, 180, 180))
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)


def slice_mask(points: np.ndarray) -> tuple[int, np.ndarray]:
    ranges = np.ptp(points, axis=0)
    axis = int(np.argmax(ranges))
    center = float(np.median(points[:, axis]))
    width = float(ranges[axis]) * 0.025
    mask = np.abs(points[:, axis] - center) <= width
    while mask.sum() < 1200 and width < ranges[axis] * 0.25:
        width *= 1.6
        mask = np.abs(points[:, axis] - center) <= width
    return axis, mask


def boundary_node_mask(arrays: dict[str, np.ndarray], npoints: int) -> np.ndarray:
    conn = arrays.get("connectivity")
    offsets = arrays.get("offsets")
    types = arrays.get("types")
    mask = np.zeros(npoints, dtype=bool)
    if conn is None or offsets is None or types is None:
        return mask

    start = 0
    for end, cell_type in zip(offsets.astype(int), types.astype(int)):
        nodes = conn[start:end].astype(int)
        start = int(end)
        if cell_type != 12:
            mask[nodes] = True
    return mask


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    arrays = read_vtu_raw(VTU_PATH)
    points = arrays["points"]
    potential = arrays["potential"]
    electric_field = arrays["electric field"]
    e_mag = np.linalg.norm(electric_field, axis=1)

    boundary = boundary_node_mask(arrays, len(points))
    if boundary.sum() < 100:
        boundary = np.ones(len(points), dtype=bool)

    axis, smask = slice_mask(points)
    render_slice(
        points,
        potential,
        OUT_DIR / "potential_slice.png",
        "Potential slice",
        "Potential [V]",
        axis,
        smask,
    )

    render_point_cloud(
        points[boundary],
        potential[boundary],
        OUT_DIR / "potential_isosurface.png",
        "Potential surface rendering",
        "Potential [V]",
        subtitle="Boundary-node rendering from VTU output",
    )

    render_slice(
        points,
        np.log10(np.maximum(e_mag, np.nanpercentile(e_mag[e_mag > 0], 1.0))),
        OUT_DIR / "electric_field.png",
        "Electric field magnitude and in-slice vectors",
        "log10(|E|)",
        axis,
        smask,
        vectors=electric_field,
    )

    frames = []
    for az in np.linspace(0, 360, 36, endpoint=False):
        frame = render_point_cloud(
            points[boundary],
            potential[boundary],
            OUT_DIR / "_rotation_frame.png",
            "Potential camera rotation",
            "Potential [V]",
            azimuth=float(az),
            elevation=24.0,
            size=(760, 560),
            radius=1,
            subtitle="Visualization-only rotation of a steady-state solution",
        )
        frames.append(frame)
    frames[0].save(
        OUT_DIR / "potential_rotation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        optimize=True,
    )
    (OUT_DIR / "_rotation_frame.png").unlink(missing_ok=True)

    summary = [
        f"VTU: {VTU_PATH}",
        f"nodes: {len(points)}",
        f"boundary_nodes_rendered: {int(boundary.sum())}",
        f"potential_min_max: {float(potential.min()):.12g}, {float(potential.max()):.12g}",
        f"electric_field_mag_min_max: {float(e_mag.min()):.12g}, {float(e_mag.max()):.12g}",
        "outputs:",
        str(OUT_DIR / "potential_slice.png"),
        str(OUT_DIR / "potential_isosurface.png"),
        str(OUT_DIR / "electric_field.png"),
        str(OUT_DIR / "potential_rotation.gif"),
    ]
    (OUT_DIR / "postprocess_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
