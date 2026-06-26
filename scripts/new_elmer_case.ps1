param(
  [Parameter(Mandatory = $true, Position = 0)]
  [ValidatePattern('^[a-z][a-z0-9_]*$')]
  [string]$Name
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$template = Join-Path $root 'templates\elmer_case'
$destination = Join-Path $root "elmer\$Name"

if (-not (Test-Path -LiteralPath $template)) {
  throw "Template directory is missing: $template"
}
if (Test-Path -LiteralPath $destination) {
  throw "Case already exists: $destination"
}

Copy-Item -LiteralPath $template -Destination $destination -Recurse
$date = Get-Date -Format 'yyyy-MM-dd'
$textExtensions = @('.md', '.yaml', '.template', '.geo', '.txt')
Get-ChildItem -LiteralPath $destination -Recurse -File | Where-Object {
  $textExtensions -contains $_.Extension
} | ForEach-Object {
  $content = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
  $content = $content.Replace('{{CASE_ID}}', $Name).Replace('{{DATE}}', $date)
  Set-Content -LiteralPath $_.FullName -Value $content -Encoding UTF8
}

Write-Output "Created Elmer case scaffold: $destination"
Write-Output "Start with: $destination\model_spec.yaml"

