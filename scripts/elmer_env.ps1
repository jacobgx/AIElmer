# ElmerFEM environment configuration
# Source this file before running ElmerFEM scripts, or let the runner scripts
# load it automatically.
#
# Usage:
#   . .\scripts\elmer_env.ps1
#   .\scripts\run_elmer_cylinder.ps1 -Case baseline

# ---- User-editable settings ----

# WSL distribution name (run "wsl -l -q" to list yours)
$env:ELMER_WSL_DISTRO = if ($env:ELMER_WSL_DISTRO) { $env:ELMER_WSL_DISTRO } else { 'Ubuntu-20.04' }

# ElmerFEM installation path inside the WSL distribution
$env:ELMER_HOME = if ($env:ELMER_HOME) { $env:ELMER_HOME } else { '/opt/elmer-26.2' }

# ---- Derived settings (normally no edits needed) ----

$WslDistro = $env:ELMER_WSL_DISTRO
$ElmerHome = $env:ELMER_HOME

# ---- Sanity check ----

if ($env:ELMER_WSL_DISTRO) {
  Write-Output "ElmerFEM WSL distro : $env:ELMER_WSL_DISTRO"
  Write-Output "ElmerFEM home       : $env:ELMER_HOME"
  Write-Output "Verify : wsl -d $env:ELMER_WSL_DISTRO -- ElmerSolver --version"
}
