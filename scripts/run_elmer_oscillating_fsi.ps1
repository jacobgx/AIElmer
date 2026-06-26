param(
  [ValidateSet('fixed_flow_mvp', 'fixed_flow', 'fixed_flow_long', 'fixed_flow_quad_2s', 'fixed_flow_nostab_2s', 'fixed_flow_nostab_5s', 'solid_only', 'solid_force_0p1N', 'solid_force_1N', 'solid_force_10N', 'solid_force_100N', 'solid_force_1N_no_plane_stress', 'solid_force_1N_density_142kg', 'solid_force_1N_E_39p3MPa', 'solid_force_1N_quadmesh', 'fsi_mvp', 'fsi', 'fsi_tip_fsi_trigger_2s', 'fsi_tip_trigger_only_2s', 'fsi_relax_0p5_2s', 'fsi_relax_0p3_2s', 'fsi_inlet_vpulse_2s')]
  [string]$Case = 'fixed_flow_mvp',
  [switch]$RebuildMesh
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts\elmer_env.ps1')
$caseDir = Join-Path $root 'elmer\oscillating_fsi'
$wslDir = (wsl -d $WslDistro -- wslpath -a $caseDir.Replace('\','/')).Trim()
$safeRoot = [IO.Path]::GetFullPath($caseDir) + [IO.Path]::DirectorySeparatorChar

if ($RebuildMesh -or -not (Test-Path -LiteralPath (Join-Path $caseDir 'mesh\mesh.header'))) {
  wsl -d $WslDistro --cd $wslDir -- gmsh geometry.geo -2 -format msh2 -o geometry.msh
  if ($LASTEXITCODE -ne 0) { throw 'Gmsh failed.' }
  $meshDir = [IO.Path]::GetFullPath((Join-Path $caseDir 'mesh'))
  if (-not $meshDir.StartsWith($safeRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to replace mesh outside case directory: $meshDir"
  }
  if (Test-Path -LiteralPath $meshDir) { Remove-Item -LiteralPath $meshDir -Recurse -Force }
  wsl -d $WslDistro --cd $wslDir -- ElmerGrid 14 2 geometry.msh -autoclean -out mesh
  if ($LASTEXITCODE -ne 0) { throw 'ElmerGrid failed.' }
}

$resultPath = [IO.Path]::GetFullPath((Join-Path $caseDir "results_raw\$Case"))
if (-not $resultPath.StartsWith($safeRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to replace results outside case directory: $resultPath"
}
if (Test-Path -LiteralPath $resultPath) { Remove-Item -LiteralPath $resultPath -Recurse -Force }
New-Item -ItemType Directory -Force -Path $resultPath | Out-Null

$log = Join-Path $caseDir "logs\$Case.log"
$stderrLog = Join-Path $caseDir "logs\$Case.wsl.log"
$solverArgs = @('-d', "$WslDistro", '--cd', $wslDir, '--', 'ElmerSolver', "$Case.sif")
$solver = Start-Process -FilePath 'wsl.exe' -ArgumentList $solverArgs -WindowStyle Hidden -Wait -PassThru `
  -RedirectStandardOutput $log -RedirectStandardError $stderrLog
Get-Content -LiteralPath $log -Tail 60
if ($solver.ExitCode -ne 0) { throw "ElmerSolver failed; see $log" }
