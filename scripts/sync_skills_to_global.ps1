# Sync project skills/ to Cursor global ~/.cursor/skills/
# Usage: powershell -File scripts/sync_skills_to_global.ps1
#        powershell -File scripts/sync_skills_to_global.ps1 -Skill pptx-gmc-sync-from-word

param(
    [string]$Skill = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$srcRoot = Join-Path $root "skills"
$dstRoot = Join-Path $env:USERPROFILE ".cursor\skills"

if (-not (Test-Path $srcRoot)) {
    Write-Error "skills folder not found: $srcRoot"
}

New-Item -ItemType Directory -Force -Path $dstRoot | Out-Null

if ($Skill) {
    $src = Join-Path $srcRoot $Skill
    if (-not (Test-Path $src)) {
        Write-Error "Skill not found: $src"
    }
    $dstSkill = Join-Path $dstRoot $Skill
    if (Test-Path $dstSkill) {
        Remove-Item -Recurse -Force $dstSkill
    }
    Copy-Item -Recurse -Force $src $dstSkill
    Write-Host "Synced skill: $Skill -> $dstSkill"
} else {
    Copy-Item -Recurse -Force (Join-Path $srcRoot "*") $dstRoot
    Write-Host "Synced all skills -> $dstRoot"
}
