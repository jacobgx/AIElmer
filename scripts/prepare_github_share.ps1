param(
  [string]$OutputDir = (Join-Path (Split-Path -Parent $PSScriptRoot) 'dist\github\ElmerFEM-AI-KB'),
  [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$output = [IO.Path]::GetFullPath($OutputDir)

if (Test-Path -LiteralPath $output) {
  if (-not $Force) {
    throw "Output directory already exists: $output. Use -Force to replace it."
  }
  Remove-Item -LiteralPath $output -Recurse -Force
}

New-Item -ItemType Directory -Path $output | Out-Null

# --- Root files ---
$includeFiles = @(
  'README.md',
  'LICENSE.md',
  'CONTRIBUTING.md',
  '.gitignore',
  '.gitattributes'
)

foreach ($file in $includeFiles) {
  $source = Join-Path $root $file
  if (Test-Path -LiteralPath $source -PathType Leaf) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $output $file)
  }
}

# --- Directories to copy in full ---
$includeDirs = @(
  'docs',
  'knowledge',
  'templates'
)

foreach ($dir in $includeDirs) {
  $source = Join-Path $root $dir
  if (Test-Path -LiteralPath $source -PathType Container) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $output $dir) -Recurse
  }
}

# --- Scripts ---
$includeScripts = @(
  'check_elmer_case.ps1',
  'distill_sif_tests.py',
  'elmer_env.ps1',
  'new_elmer_case.ps1',
  'postprocess_elmer_cylinder.py',
  'prepare_github_share.ps1',
  'query_kb.ps1',
  'run_elmer_cylinder.ps1',
  'run_elmer_oscillating_fsi.ps1'
)

$scriptOut = Join-Path $output 'scripts'
New-Item -ItemType Directory -Path $scriptOut | Out-Null
foreach ($file in $includeScripts) {
  $source = Join-Path (Join-Path $root 'scripts') $file
  if (Test-Path -LiteralPath $source -PathType Leaf) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $scriptOut $file)
  }
}

# --- Elmer cases: copy source files, skip solver outputs ---
# The .gitignore handles exclusion at git-add time.
# At copy time we exclude known-heavy directories and binaries.
$elmerSource = Join-Path $root 'elmer'
$elmerOut = Join-Path $output 'elmer'

$excludeDirs = @('mesh', 'logs', 'results_raw', 'visualizations', 'postprocess', '__pycache__')
$excludeExts = @('*.vtu', '*.pvtu', '*.pvd', '*.ep', '*.result', '*.dat',
                  '*.log', '*.out', '*.err', '*.exitcode', '*.wsl.log',
                  '*.mph', '*.class', '*.gif', '*.mp4', '*.avi',
                  '*.tgz', '*.tar.gz', '*.zip')

if (Test-Path -LiteralPath $elmerSource -PathType Container) {
  $robocopyArgs = @($elmerSource, $elmerOut, '/E', '/NFL', '/NDL', '/NJH', '/NJS')
  foreach ($d in $excludeDirs) { $robocopyArgs += "/XD"; $robocopyArgs += $d }
  foreach ($e in $excludeExts) { $robocopyArgs += "/XF"; $robocopyArgs += $e }
  # robocopy returns 0-7 for success; 8+ is error
  $rc = & robocopy @robocopyArgs
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
  # Remove any empty excluded dirs that robocopy still creates
  Get-ChildItem -LiteralPath $elmerOut -Recurse -Directory |
    Where-Object { $_.Name -in $excludeDirs } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Output "Created clean GitHub share directory:"
Write-Output $output
Write-Output ''
Write-Output 'Next steps:'
Write-Output "  cd `"$output`""
Write-Output '  git init'
Write-Output '  git add .'
Write-Output '  git commit -m "Initial Elmer AI knowledge-base framework"'
Write-Output ''
Write-Output 'Or, for an even cleaner alternative, initialize Git in the project root:'
Write-Output "  cd `"$root`""
Write-Output '  git init'
Write-Output '  git add .'
Write-Output '  git status   # verify only intended files are staged'
