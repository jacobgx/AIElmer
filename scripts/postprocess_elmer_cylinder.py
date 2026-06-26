from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import meshio
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "elmer" / "cylinder_flow"
OUT = ROOT / "results" / "elmer"
OUT.mkdir(parents=True, exist_ok=True)


def load(path: Path):
    mesh = meshio.read(path)
    points = mesh.points[:, :2]
    triangles = mesh.cells_dict["triangle"]
    velocity = np.asarray(mesh.point_data["velocity"])[:, :2]
    speed = np.linalg.norm(velocity, axis=1)
    temperature = mesh.point_data.get("temperature")
    return points, triangles, speed, temperature


def field_plot(points, triangles, values, label, title, destination, cmap="turbo"):
    tri = mtri.Triangulation(points[:, 0], points[:, 1], triangles)
    fig, ax = plt.subplots(figsize=(13, 3.2), constrained_layout=True)
    levels = np.linspace(float(values.min()), float(values.max()), 80)
    contour = ax.tricontourf(tri, values, levels=levels, cmap=cmap)
    ax.add_patch(plt.Circle((0.2, 0.2), 0.05, color="white", ec="black", lw=0.6, zorder=5))
    ax.set(xlim=(0, 2.2), ylim=(0, 0.41), xlabel="x (m)", ylabel="y (m)", title=title)
    ax.set_aspect("equal")
    fig.colorbar(contour, ax=ax, label=label, pad=0.015)
    fig.savefig(destination, dpi=200)
    plt.close(fig)


baseline_final = sorted((CASE / "results").glob("baseline_t*.vtu"))[-1]
thermal_final = sorted((CASE / "results_thermal").glob("thermal_t*.vtu"))[-1]
bp, bt, bs, _ = load(baseline_final)
tp, tt, ts, temp = load(thermal_final)
temp_c = np.asarray(temp).reshape(-1) - 273.15

field_plot(bp, bt, bs, "Speed (m/s)", "ElmerFEM cylinder flow at t = 7 s", OUT / "baseline_speed_t7.png")
field_plot(tp, tt, ts, "Speed (m/s)", "ElmerFEM heated-cylinder flow at t = 7 s", OUT / "thermal_speed_t7.png")
field_plot(tp, tt, temp_c, "Temperature (°C)", "ElmerFEM temperature field at t = 7 s", OUT / "temperature_t7.png", "inferno")

summary = (
    "ElmerFEM cylinder-flow results at t = 7 s\n"
    f"mesh_nodes={len(bp)}\n"
    f"mesh_triangles={len(bt)}\n"
    f"baseline_speed_min_m_per_s={bs.min():.9g}\n"
    f"baseline_speed_max_m_per_s={bs.max():.9g}\n"
    f"thermal_speed_min_m_per_s={ts.min():.9g}\n"
    f"thermal_speed_max_m_per_s={ts.max():.9g}\n"
    f"temperature_min_degC={temp_c.min():.9g}\n"
    f"temperature_max_degC={temp_c.max():.9g}\n"
)
(OUT / "summary.txt").write_text(summary, encoding="utf-8")
print(summary)

species_files = sorted((CASE / "results_species").glob("species_t*.vtu"))
if species_files:
    species_mesh = meshio.read(species_files[-1])
    sp = species_mesh.points[:, :2]
    st = species_mesh.cells_dict["triangle"]
    concentration = np.asarray(species_mesh.point_data["concentration"]).reshape(-1)
    field_plot(
        sp,
        st,
        concentration,
        "Concentration (mol/m³)",
        "ElmerFEM Fickian species transport at t = 7 s",
        OUT / "concentration_t7.png",
        "viridis",
    )
    p0, p1, p2 = sp[st[:, 0]], sp[st[:, 1]], sp[st[:, 2]]
    edge1, edge2 = p1 - p0, p2 - p0
    areas = 0.5 * np.abs(edge1[:, 0] * edge2[:, 1] - edge1[:, 1] * edge2[:, 0])
    inventory = np.sum(areas * concentration[st].mean(axis=1))
    source_rate = 100.0 * 2.0 * np.pi * 0.05
    species_summary = (
        "ElmerFEM Fickian species result at t = 7 s\n"
        "diffusivity_m2_per_s=0.001\n"
        "cylinder_flux_mol_per_m2_s=100\n"
        f"source_rate_per_unit_depth_mol_per_m_s={source_rate:.9g}\n"
        f"concentration_min_mol_per_m3={concentration.min():.9g}\n"
        f"concentration_max_mol_per_m3={concentration.max():.9g}\n"
        f"domain_inventory_per_unit_depth_mol_per_m={inventory:.9g}\n"
    )
    (OUT / "species_summary.txt").write_text(species_summary, encoding="utf-8")
    print(species_summary)
