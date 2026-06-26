param(
  [ValidateSet('baseline', 'thermal', 'species')]
  [string]$Case = 'baseline'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts\elmer_env.ps1')
$caseDir = Join-Path $root 'elmer\cylinder_flow'
$wslDir = (wsl -d $WslDistro -- wslpath -a ($caseDir -replace '\\', '/')).Trim()

wsl -d $WslDistro --cd $wslDir -- gmsh cylinder.geo -2 -format msh2 -o cylinder.msh
if ($LASTEXITCODE -ne 0) { throw 'Gmsh failed.' }

$meshDir = [IO.Path]::GetFullPath((Join-Path $caseDir 'mesh'))
$safeRoot = [IO.Path]::GetFullPath($caseDir) + [IO.Path]::DirectorySeparatorChar
if (-not $meshDir.StartsWith($safeRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to remove mesh outside case directory: $meshDir"
}
if (Test-Path -LiteralPath $meshDir) {
  Remove-Item -LiteralPath $meshDir -Recurse -Force
}
wsl -d $WslDistro --cd $wslDir -- ElmerGrid 14 2 cylinder.msh -autoclean -out mesh
if ($LASTEXITCODE -ne 0) { throw 'ElmerGrid failed.' }

$resultDir = switch ($Case) {
  'thermal' { 'results_thermal' }
  'species' { 'results_species' }
  default { 'results' }
}
$resultPath = [IO.Path]::GetFullPath((Join-Path $caseDir $resultDir))
if (-not $resultPath.StartsWith($safeRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to remove results outside case directory: $resultPath"
}
if (Test-Path -LiteralPath $resultPath) {
  Remove-Item -LiteralPath $resultPath -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $resultPath | Out-Null
$log = Join-Path $caseDir "$Case.log"
$stderrLog = Join-Path $caseDir "$Case.wsl.log"
$solverArgs = @('-d', "$WslDistro", '--cd', $wslDir, '--', 'ElmerSolver', "$Case.sif")
$solver = Start-Process -FilePath 'wsl.exe' -ArgumentList $solverArgs -WindowStyle Hidden -Wait -PassThru `
  -RedirectStandardOutput $log -RedirectStandardError $stderrLog
Get-Content -LiteralPath $log -Tail 40
if ($solver.ExitCode -ne 0) { throw "ElmerSolver failed; see $log" }
