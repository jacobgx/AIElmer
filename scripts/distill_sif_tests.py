#!/usr/bin/env python3
"""Index official Elmer fem/tests SIF cases for AI-assisted modeling."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


KEY_PATTERNS = {
    "mesh_db": re.compile(r'^\s*Mesh\s+DB\s+"([^"]*)"\s+"([^"]+)"', re.I),
    "simulation_type": re.compile(r"^\s*Simulation\s+Type\s*=\s*(.+)$", re.I),
    "equation": re.compile(r"^\s*Equation\s*=\s*(.+)$", re.I),
    "procedure": re.compile(
        r'^\s*Procedure\s*=\s*(?:File\s*)?"([^"]+)"\s+"([^"]+)"', re.I
    ),
    "variable": re.compile(r"^\s*Variable\s*=\s*(.+)$", re.I),
    "active_solvers": re.compile(r"^\s*Active\s+Solvers(?:\([^)]+\))?\s*=\s*(.+)$", re.I),
    "post_file": re.compile(r'^\s*Post\s+File\s*=\s*"?([^"]+)"?', re.I),
    "output_file": re.compile(r'^\s*Output\s+File(?:\s+Name)?\s*=\s*"?([^"]+)"?', re.I),
    "timestep_intervals": re.compile(r"^\s*Timestep\s+Intervals(?:\([^)]+\))?\s*=\s*(.+)$", re.I),
    "timestep_sizes": re.compile(r"^\s*Timestep\s+Sizes(?:\([^)]+\))?\s*=\s*(.+)$", re.I),
}


PHYSICS_RULES = [
    ("fsi", [r"\bfsi\b", r"fluid.?structure", r"structure coupling", r"mesh update"]),
    ("navier_stokes", [r"navier-stokes", r"\bn-s\b", r"flowsolve", r"stokes"]),
    ("heat", [r"heat equation", r"heatsolve", r"temperature"]),
    ("advection_diffusion", [r"advection diffusion", r"advectiondiffusion"]),
    ("advection_reaction", [r"advreact", r"advectionreaction", r"reaction"]),
    ("elasticity", [r"elastic", r"stress analysis", r"stresssolve", r"displacement"]),
    ("beam_shell_plate", [r"beam", r"shell", r"plate", r"timoshenko"]),
    ("contact", [r"contact", r"friction"]),
    ("poisson", [r"\bpoisson\b", r"laplace"]),
    ("electrostatics_current", [r"statelec", r"statcurrent", r"electrostatic", r"electric force", r"capacitance"]),
    ("electromagnetics", [r"emwave", r"magnetodynamic", r"mgdyn", r"helmholtz", r"coil", r"circuit"]),
    ("acoustics_wave", [r"acoustic", r"waveeq", r"helmholtz"]),
    ("radiation", [r"radiation", r"radiosity", r"radiator"]),
    ("phase_change", [r"phasechange", r"phase change", r"enthalpy"]),
    ("porous_richards", [r"richards", r"porous", r"bentonite"]),
    ("battery_electrochemistry", [r"battery", r"electrolyte", r"solidphase"]),
    ("particles", [r"particle"]),
    ("levelset_free_surface", [r"levelset", r"free surface", r"freesurf"]),
    ("mesh_partitioning", [r"elmergrid", r"partition", r"remesh", r"metis", r"zoltan"]),
    ("optimization_control", [r"control", r"topoopt", r"optimize", r"cost"]),
    ("postprocessing", [r"save scalars", r"savescalars", r"resultoutput", r"saveline"]),
    ("linear_solver_benchmark", [r"linearsolver", r"\bwinkel", r"\bamultg\b", r"\bpmultg\b", r"\bgmultg\b", r"\bcmultg\b"]),
]


def strip_comment(line: str) -> str:
    if "!" in line:
        return line.split("!", 1)[0]
    return line


def clean_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^(String|Real|Integer|Logical)\s+", "", value, flags=re.I).strip()
    return value.strip('"').strip()


def unique(values):
    seen = set()
    out = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if not value:
            continue
        key = str(value).lower()
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def git_value(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def parse_sif(path: Path, tests_root: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [strip_comment(line) for line in raw.splitlines()]
    text = "\n".join(lines)
    text_lower = text.lower()

    mesh_dbs = []
    equations = []
    procedures = []
    variables = []
    simulation_types = []
    post_files = []
    output_files = []
    timestep_sizes = []
    timestep_intervals = []
    has_result_output = False
    has_save_scalars = False
    has_save_line = False
    has_vtu = False

    for line in lines:
        if not line.strip():
            continue

        match = KEY_PATTERNS["mesh_db"].match(line)
        if match:
            mesh_dbs.append({"base": match.group(1), "name": match.group(2)})

        match = KEY_PATTERNS["simulation_type"].match(line)
        if match:
            simulation_types.append(clean_value(match.group(1)))

        match = KEY_PATTERNS["equation"].match(line)
        if match:
            value = clean_value(match.group(1))
            if not re.fullmatch(r"[-+]?\d+", value):
                equations.append(value)

        match = KEY_PATTERNS["procedure"].match(line)
        if match:
            module, proc = match.groups()
            procedures.append({"module": module, "procedure": proc})
            proc_lower = f"{module} {proc}".lower()
            has_result_output = has_result_output or "resultoutput" in proc_lower
            has_save_scalars = has_save_scalars or "savescalars" in proc_lower
            has_save_line = has_save_line or "saveline" in proc_lower

        match = KEY_PATTERNS["variable"].match(line)
        if match and not re.match(r"^\s*Variable\s+\d+\s*=", line, flags=re.I):
            variables.append(clean_value(match.group(1)))

        match = KEY_PATTERNS["post_file"].match(line)
        if match:
            post_files.append(clean_value(match.group(1)))

        match = KEY_PATTERNS["output_file"].match(line)
        if match:
            output_files.append(clean_value(match.group(1)))

        match = KEY_PATTERNS["timestep_sizes"].match(line)
        if match:
            timestep_sizes.append(clean_value(match.group(1)))

        match = KEY_PATTERNS["timestep_intervals"].match(line)
        if match:
            timestep_intervals.append(clean_value(match.group(1)))

        if re.search(r"\bVtu\s+Format\s*=\s*(Logical\s*)?True\b", line, re.I):
            has_vtu = True

    rel = path.relative_to(tests_root).as_posix()
    case_id = path.relative_to(tests_root).parts[0]
    case_dir = tests_root / case_id
    startinfo = case_dir / "ELMERSOLVER_STARTINFO"
    cmake = case_dir / "CMakeLists.txt"
    runtest = case_dir / "runtest.cmake"
    makefile = case_dir / "Makefile"
    mesh_sources = sorted(
        p.name
        for p in case_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".grd", ".msh", ".geo", ".mesh", ".nodes"}
    )

    # Use high-signal metadata rather than the full SIF text. Full-text matching
    # misclassifies common settings such as "Poisson Ratio" or "BiCGStab".
    combined_for_classification = " ".join(
        [
            case_id,
            rel,
            " ".join(equations),
            " ".join(f"{p['module']} {p['procedure']}" for p in procedures),
            " ".join(variables),
        ]
    ).lower()
    physics = []
    for name, patterns in PHYSICS_RULES:
        if any(re.search(pattern, combined_for_classification, re.I) for pattern in patterns):
            physics.append(name)
    if not physics:
        physics.append("other")

    return {
        "case_id": case_id,
        "sif": rel,
        "sif_name": path.name,
        "case_dir": case_id,
        "simulation_types": unique(simulation_types),
        "equations": unique(equations),
        "procedures": unique(procedures),
        "variables": unique(variables),
        "physics": unique(physics),
        "mesh_dbs": mesh_dbs,
        "mesh_sources": mesh_sources,
        "has_startinfo": startinfo.exists(),
        "startinfo": startinfo.read_text(encoding="utf-8", errors="replace").strip()
        if startinfo.exists()
        else None,
        "has_cmake": cmake.exists(),
        "has_runtest": runtest.exists(),
        "has_makefile": makefile.exists(),
        "has_result_output": has_result_output,
        "has_save_scalars": has_save_scalars,
        "has_save_line": has_save_line,
        "has_vtu_output": has_vtu or any(".vtu" in v.lower() for v in post_files + output_files),
        "post_files": unique(post_files),
        "output_files": unique(output_files),
        "timestep_sizes": unique(timestep_sizes),
        "timestep_intervals": unique(timestep_intervals),
        "line_count": len(raw.splitlines()),
    }


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "unknown"


def write_text_index(path: Path, rows: list[dict], field: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                f"{row['case_id']}\t{row['sif']}\t{', '.join(row.get(field, []))}\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default="tmp/elmerfem_remote_tree/fem/tests",
        help="Path to Elmer upstream fem/tests directory.",
    )
    parser.add_argument(
        "--output",
        default="knowledge/distilled/test_case_index",
        help="Output index directory.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    source_arg = Path(args.source)
    tests_root = (root / source_arg).resolve()
    output = (root / args.output).resolve()

    if not tests_root.exists():
        raise SystemExit(f"Source tests directory does not exist: {tests_root}")

    upstream_root = tests_root.parents[1]
    commit = git_value(upstream_root, "rev-parse", "HEAD")
    branch = git_value(upstream_root, "rev-parse", "--abbrev-ref", "HEAD")
    remote = git_value(upstream_root, "remote", "get-url", "origin")

    output.mkdir(parents=True, exist_ok=True)
    (output / "by_physics").mkdir(exist_ok=True)
    (output / "by_solver").mkdir(exist_ok=True)
    (output / "by_equation").mkdir(exist_ok=True)

    rows = []
    for sif in sorted(tests_root.rglob("*.sif")):
        rows.append(parse_sif(sif, tests_root))

    generated_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "schema_version": 1,
        "generated_at_utc": generated_at,
        "source": {
            "repository": remote,
            "branch": branch,
            "commit": commit,
            "path": source_arg.as_posix(),
        },
        "counts": {
            "sif_files": len(rows),
            "case_directories": len({row["case_id"] for row in rows}),
        },
    }

    with (output / "cases.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            record = dict(row)
            record["source_commit"] = commit
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    csv_fields = [
        "case_id",
        "sif",
        "physics",
        "simulation_types",
        "equations",
        "procedures",
        "variables",
        "mesh_sources",
        "has_startinfo",
        "has_result_output",
        "has_vtu_output",
        "line_count",
    ]
    with (output / "cases.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "sif": row["sif"],
                    "physics": ";".join(row["physics"]),
                    "simulation_types": ";".join(row["simulation_types"]),
                    "equations": ";".join(row["equations"]),
                    "procedures": ";".join(
                        f"{p['module']}/{p['procedure']}" for p in row["procedures"]
                    ),
                    "variables": ";".join(row["variables"]),
                    "mesh_sources": ";".join(row["mesh_sources"]),
                    "has_startinfo": row["has_startinfo"],
                    "has_result_output": row["has_result_output"],
                    "has_vtu_output": row["has_vtu_output"],
                    "line_count": row["line_count"],
                }
            )

    physics_map = defaultdict(list)
    solver_map = defaultdict(list)
    equation_map = defaultdict(list)
    for row in rows:
        for physics in row["physics"]:
            physics_map[physics].append(row)
        for proc in row["procedures"]:
            solver_map[f"{proc['module']}/{proc['procedure']}"].append(row)
        for equation in row["equations"]:
            equation_map[equation].append(row)

    for name, group in physics_map.items():
        write_text_index(output / "by_physics" / f"{safe_name(name)}.txt", group, "equations")
    for name, group in solver_map.items():
        write_text_index(output / "by_solver" / f"{safe_name(name)}.txt", group, "physics")
    for name, group in equation_map.items():
        write_text_index(output / "by_equation" / f"{safe_name(name)}.txt", group, "physics")

    physics_counts = Counter()
    solver_counts = Counter()
    equation_counts = Counter()
    for row in rows:
        physics_counts.update(row["physics"])
        solver_counts.update(f"{p['module']}/{p['procedure']}" for p in row["procedures"])
        equation_counts.update(row["equations"])

    metadata["top_physics"] = physics_counts.most_common()
    metadata["top_solvers"] = solver_counts.most_common(50)
    metadata["top_equations"] = equation_counts.most_common(50)

    with (output / "metadata.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    with (output / "SUMMARY.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Official Elmer fem/tests Index\n\n")
        handle.write(f"- Generated UTC: `{generated_at}`\n")
        handle.write(f"- Repository: `{remote}`\n")
        handle.write(f"- Branch: `{branch}`\n")
        handle.write(f"- Commit: `{commit}`\n")
        handle.write(f"- Case directories: `{metadata['counts']['case_directories']}`\n")
        handle.write(f"- SIF files: `{metadata['counts']['sif_files']}`\n\n")

        handle.write("## Main Outputs\n\n")
        handle.write("- `cases.jsonl`: complete machine-readable SIF index.\n")
        handle.write("- `cases.csv`: compact spreadsheet-friendly index.\n")
        handle.write("- `by_physics/`: case lists grouped by inferred physics.\n")
        handle.write("- `by_solver/`: case lists grouped by `module/procedure`.\n")
        handle.write("- `by_equation/`: case lists grouped by equation labels.\n\n")

        handle.write("## Inferred Tag Counts\n\n")
        for name, count in physics_counts.most_common():
            handle.write(f"- `{name}`: {count}\n")

        handle.write("\n## Top Solver Procedures\n\n")
        for name, count in solver_counts.most_common(30):
            handle.write(f"- `{name}`: {count}\n")

        handle.write("\n## Top Equation Labels\n\n")
        for name, count in equation_counts.most_common(30):
            handle.write(f"- `{name}`: {count}\n")

    snapshot_dir = output.parent / "source_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with (snapshot_dir / "elmerfem_devel_fem_tests.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        json.dump(metadata["source"] | {"generated_at_utc": generated_at}, handle, indent=2)
        handle.write("\n")

    print(f"Indexed {len(rows)} SIF files from {tests_root}")
    print(f"Wrote {output / 'cases.jsonl'}")
    print(f"Wrote {output / 'SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
