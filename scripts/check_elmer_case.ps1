param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$CaseDir
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$casePath = [IO.Path]::GetFullPath($CaseDir)
$elmerRoot = [IO.Path]::GetFullPath((Join-Path $root 'elmer')) + [IO.Path]::DirectorySeparatorChar
if (-not $casePath.StartsWith($elmerRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Case must be located under $elmerRoot"
}
if (-not (Test-Path -LiteralPath $casePath -PathType Container)) {
  throw "Case directory does not exist: $casePath"
}

$required = @(
  'README.md',
  'model_spec.yaml',
  'formulation.md',
  'uncertainties.md',
  'syntax_evidence.md',
  'validation_plan.md'
)
$rows = foreach ($file in $required) {
  $path = Join-Path $casePath $file
  [pscustomobject]@{
    Artifact = $file
    Present = Test-Path -LiteralPath $path -PathType Leaf
  }
}
$rows | Format-Table -AutoSize

$missing = @($rows | Where-Object { -not $_.Present })
if ($missing.Count -gt 0) {
  throw "Case contract incomplete: $($missing.Artifact -join ', ')"
}

$modelSpec = Get-Content -LiteralPath (Join-Path $casePath 'model_spec.yaml') -Raw -Encoding UTF8
$unresolvedDoc = Get-Content -LiteralPath (Join-Path $casePath 'uncertainties.md') -Raw -Encoding UTF8
$syntaxDoc = Get-Content -LiteralPath (Join-Path $casePath 'syntax_evidence.md') -Raw -Encoding UTF8
$validationDoc = Get-Content -LiteralPath (Join-Path $casePath 'validation_plan.md') -Raw -Encoding UTF8

$checks = @(
  [pscustomobject]@{ Check = 'model_spec has case_id'; Passed = $modelSpec -match '(?m)^case_id:\s*\S+' },
  [pscustomobject]@{ Check = 'no template placeholders'; Passed = ($modelSpec + $unresolvedDoc + $syntaxDoc + $validationDoc) -notmatch '\{\{[^}]+\}\}' },
  [pscustomobject]@{ Check = 'no unresolved items'; Passed = ($modelSpec + $unresolvedDoc) -notmatch '(?i)\bUNRESOLVED\b' },
  [pscustomobject]@{ Check = 'syntax evidence verified'; Passed = $syntaxDoc -notmatch '(?i)\bUNVERIFIED\b' },
  [pscustomobject]@{ Check = 'validation plan completed'; Passed = $validationDoc -notmatch '(?i)TODO|NOT VALIDATED|NOT RUN' }
)
$checks | Format-Table -AutoSize

Write-Output 'Audit is advisory after the required artifact check.'
Write-Output 'A failed advisory check means the corresponding gate is not yet closed.'

