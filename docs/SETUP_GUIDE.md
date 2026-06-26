# Environment Setup Guide

This guide helps you install and configure the computational software used by this knowledge-base framework.

## Overview

The framework uses **ElmerFEM** (open-source multiphysics FEM solver) with **Gmsh** for mesh generation. Python packages are optional for postprocessing.

| Component | Required | Purpose |
|-----------|----------|---------|
| ElmerFEM 26.x | **Yes** | Multiphysics solver |
| Gmsh | **Yes** | Mesh generation |
| WSL (Windows) | Recommended | Run ElmerFEM on Windows |
| OpenMPI | Optional | Parallel solver execution |
| Python 3.9+ | Optional | Postprocessing, knowledge indexing |

---

## Quick Start (Windows + WSL)

### 1. Install WSL

Open PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu-24.04
```

After reboot, launch Ubuntu from the Start menu to complete the initial setup (create a user/password).

### 2. Install ElmerFEM in WSL

**Option A — Pre-built package** (recommended, Ubuntu 22.04/24.04):

```bash
sudo add-apt-repository ppa:elmer-csc-ubuntu/elmer-csc-ppa
sudo apt update
sudo apt install elmerfem-csc
```

Verify:

```bash
ElmerSolver --version
ElmerGrid --version
```

**Option B — Build from source** (for specific versions or MPI features):

```bash
# Install build dependencies
sudo apt install build-essential cmake gfortran libopenmpi-dev \
  libblas-dev liblapack-dev libmumps-dev libmetis-dev libparmetis-dev

# Clone and build
git clone https://github.com/ElmerCSC/elmerfem.git
cd elmerfem
mkdir build && cd build
cmake .. -DWITH_MPI=ON -DWITH_Mumps=ON -DWITH_OpenMP=ON
make -j$(nproc)
sudo make install
```

The default install prefix is `/usr/local`. To install elsewhere, add `-DCMAKE_INSTALL_PREFIX=/opt/elmer-26.2` to the cmake command.

### 3. Install Gmsh

```bash
sudo apt install gmsh
```

Or for the latest version:

```bash
pip install gmsh       # Python API
sudo apt install gmsh  # CLI + GUI
```

Verify:

```bash
gmsh --version
```

### 4. Configure the Framework

Back in Windows PowerShell, configure your WSL distribution name:

```powershell
cd <project-root>
. .\scripts\elmer_env.ps1
```

The script defaults to `Ubuntu-20.04`. To override:

```powershell
$env:ELMER_WSL_DISTRO = 'Ubuntu-24.04'
. .\scripts\elmer_env.ps1
```

Or set it permanently (PowerShell profile):

```powershell
[System.Environment]::SetEnvironmentVariable('ELMER_WSL_DISTRO', 'Ubuntu-24.04', 'User')
```

### 5. Verify

```powershell
# Check ElmerFEM version
. .\scripts\elmer_env.ps1
wsl -d $env:ELMER_WSL_DISTRO -- ElmerSolver --version

# Search the knowledge base
.\scripts\query_kb.ps1 'Navier-Stokes'

# Create a test case
.\scripts\new_elmer_case.ps1 -Name test_case
.\scripts\check_elmer_case.ps1 .\elmer\test_case
```

---

## Linux (Native)

Skip the WSL setup. Install ElmerFEM and Gmsh directly. Update `scripts/elmer_env.ps1` — or bypass PowerShell scripts entirely and run ElmerFEM directly:

```bash
# The SIF files in this repo can be run directly with ElmerSolver
cd elmer/cylinder_flow
gmsh cylinder.geo -2 -format msh2 -o cylinder.msh
ElmerGrid 14 2 cylinder.msh -autoclean -out mesh
ElmerSolver baseline.sif
```

---

## macOS

ElmerFEM is available via Homebrew:

```bash
brew tap elmer-csc/elmerfem
brew install elmerfem
brew install gmsh
```

---

## OpenMPI (Parallel Execution)

For larger cases, install OpenMPI:

```bash
# Ubuntu/Debian
sudo apt install libopenmpi-dev openmpi-bin

# macOS
brew install open-mpi
```

Run with MPI:

```bash
mpirun -np 4 ElmerSolver case.sif
```

For WSL with MPI, ensure your WSL kernel supports shared memory. Most pre-built ElmerFEM PPA packages already include MPI support.

---

## Python Dependencies

Postprocessing scripts in `scripts/` and `elmer/*/postprocess/` may require:

```bash
pip install numpy matplotlib meshio pyvista pillow imageio
```

Minimal postprocessing alternatives (`*_pure.py`) only require the Python standard library.

---

---

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `ELMER_WSL_DISTRO` | `Ubuntu-20.04` | WSL distribution name for PowerShell scripts |
| `ELMER_HOME` | `/opt/elmer-26.2` | ElmerFEM installation path inside WSL |

Override them before sourcing `scripts/elmer_env.ps1`.

---

## Troubleshooting

### WSL: "ElmerSolver: command not found"

Check the installation path. If installed from source to `/usr/local`:

```powershell
$env:ELMER_HOME = '/usr/local'
```

### WSL: NAT/localhost warning

Some WSL versions print a localhost NAT warning to stderr. This is cosmetic — ElmerFEM runs correctly despite it.

### Gmsh: mesh format compatibility

Use `-format msh2` for ElmerGrid compatibility:

```bash
gmsh geometry.geo -2 -format msh2 -o geometry.msh
```

### MPI: "mpirun: command not found"

Install OpenMPI or use single-core ElmerSolver (adequate for most cases in this repository):

```bash
ElmerSolver case.sif  # single-core
```

---

Next steps after setup:

1. Read `docs/AI_AGENT_GUIDE.md` if using AI assistance
2. Follow `knowledge/ELMER_AI_MODELING_STANDARD.md` for modeling workflow
3. Run the cylinder-flow example: `.\scripts\run_elmer_cylinder.ps1 -Case baseline`
