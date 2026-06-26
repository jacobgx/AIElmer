param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Query,
  [int]$Context = 2
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SearchRoots = @(
  (Join-Path $ProjectRoot 'knowledge'),
  (Join-Path $ProjectRoot 'elmer')
) | Where-Object { Test-Path -LiteralPath $_ }

& rg -n -i -C $Context --glob '*.md' --glob '*.sif' --glob '*.java' --glob '*.ps1' -- $Query $SearchRoots
if ($LASTEXITCODE -eq 1) { Write-Output "No local match for: $Query"; exit 0 }
exit $LASTEXITCODE
