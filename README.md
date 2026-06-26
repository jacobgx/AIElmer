# ElmerFEM AI Modeling Knowledge Base

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![ElmerFEM 26.2](https://img.shields.io/badge/ElmerFEM-26.2-green)](https://github.com/ElmerCSC/elmerfem)

An **AI-ready framework** for building, auditing, validating, and sharing ElmerFEM multiphysics models. It enforces a structured modeling workflow with evidence gates, provides reusable case templates, and maintains a searchable knowledge layer of ElmerFEM modeling patterns.

---

## What's Inside

| Layer | Contents |
|-------|----------|
| `knowledge/` | Searchable ElmerFEM quick reference, AI modeling standard (8-gate workflow), keyword index, physics/solver cards, distilled official case indexes |
| `templates/elmer_case/` | Reusable case scaffold: `model_spec.yaml`, `formulation.md`, `syntax_evidence.md`, `validation_plan.md`, `uncertainties.md` |
| `scripts/` | Powershell/Python tools: KB search, new case creation, case integrity checks, Elmer runner, postprocessing, GitHub export |
| `elmer/` | Worked examples: cylinder-flow benchmark (Navier–Stokes, heat, species transport), oscillating FSI (Turek-Hron FSI3), official Elmer test reproductions |
| `docs/` | AI agent guide, setup guide, repository layout, GitHub publishing instructions |

## Setup

New environment? See **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** — covers ElmerFEM, Gmsh, WSL, and OpenMPI installation.

## Quick Start

```powershell
# One-time: configure your WSL distribution
. .\scripts\elmer_env.ps1

# Search the local knowledge base
.\scripts\query_kb.ps1 'Navier-Stokes'
.\scripts\query_kb.ps1 'TemperatureBoundary'

# Check ElmerFEM
wsl -d $env:ELMER_WSL_DISTRO -- ElmerSolver --version

# Create a new AI-auditable Elmer case
.\scripts\new_elmer_case.ps1 -Name heat_exchanger
.\scripts\check_elmer_case.ps1 .\elmer\heat_exchanger

# Distill official Elmer test cases into searchable indexes
python .\scripts\distill_sif_tests.py
```

## For AI Agents

Tell the AI to read these files **before** generating or modifying any Elmer model:

1. `docs/AI_AGENT_GUIDE.md` — first-read protocol
2. `knowledge/ELMER_AI_MODELING_STANDARD.md` — 8-gate workflow
3. `knowledge/ELMER_KB_DISTILLATION_PLAN.md` — evidence rules
4. `templates/elmer_case/README.md` — case contract

The AI **must not** write a final SIF until it has recorded physical assumptions, syntax evidence, mesh boundary mapping, and a validation plan.

## Worked Examples

### Cylinder Flow Benchmark

Navier–Stokes flow past a cylinder at Re=100, with thermal and species-transport extensions.

```powershell
.\scripts\run_elmer_cylinder.ps1 -Case baseline   # Navier–Stokes
.\scripts\run_elmer_cylinder.ps1 -Case thermal     # + Heat transfer
.\scripts\run_elmer_cylinder.ps1 -Case species     # + Advection-diffusion
python .\scripts\postprocess_elmer_cylinder.py
```

See `elmer/cylinder_flow/README.md` for reference parameters and boundary IDs.

### Oscillating FSI (Turek-Hron FSI3)

Fluid-structure interaction with an elastic beam behind a cylinder. Includes fixed-flow, solid-only, and full FSI solver variants with stabilization and discretization screening.

See `elmer/oscillating_fsi/README.md` for status and baseline results.

### Official Elmer Test Reproductions

Verified reproductions of upstream Elmer test cases under `elmer/official_runs/`:
- `fsi_beam` — FSI beam benchmark
- `EMWaveBoxHexas` — electromagnetic wave in a box
- `elstat` — electrostatic analysis

## Publish to GitHub

This repository contains local solver outputs (`*.mph`, `*.vtu`, `*.result`, logs, raw results) that are excluded via `.gitignore`.

**Option A — Init Git in this root** (recommended):

```powershell
git init
git add .
git status   # verify only source files are staged
git commit -m "Initial Elmer AI knowledge-base framework"
```

**Option B — Export a clean copy**:

```powershell
.\scripts\prepare_github_share.ps1 -Force
cd dist\github\ElmerFEM-AI-KB
git init
git add .
git commit -m "Initial Elmer AI knowledge-base framework"
```

See `docs/GITHUB_PUBLISHING.md` for detailed instructions.

## Repository Layout

```text
.
├── README.md
├── LICENSE.md
├── .gitignore
├── .gitattributes
├── docs/                    # Guides: AI agent, publishing, official cases workflow
├── knowledge/               # Searchable KB: quickref, standards, distilled indexes
│   ├── distilled/           #   AI-ready solver/physics cards, keyword indexes
│   └── ...
├── templates/
│   └── elmer_case/          # Reusable case contract (docs, spec, evidence templates)
├── scripts/                 # Powershell + Python tools
├── elmer/                   # Local Elmer cases
│   ├── cylinder_flow/       #   Navier–Stokes benchmark (flow, thermal, species)
│   ├── oscillating_fsi/     #   Turek-Hron FSI3 reproduction
│   └── official_runs/       #   Verified upstream Elmer test reproductions
```

## License

The knowledge-base framework files are released under the [MIT License](LICENSE.md). ElmerFEM itself, upstream Elmer examples, and local simulation outputs are not relicensed by this repository.

---

Built with [ElmerFEM](https://github.com/ElmerCSC/elmerfem) — open-source multiphysics FEM.
