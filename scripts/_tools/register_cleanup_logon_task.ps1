# ============================================================
#  register_cleanup_logon_task.ps1
#
#  Registers an auto-start entry that runs ``on_open_cleanup.cmd``
#  every time the current user logs on. Pairs with Cursor's
#  project-level ``.vscode/tasks.json`` which runs the same cleanup
#  on every folder open.
#
#  Two registration strategies are attempted in order:
#    1. Windows Task Scheduler (preferred — supports time limits,
#       battery awareness, delayed start)
#    2. HKCU Run registry key (fallback — works when Task Scheduler
#       is blocked by security policy; no admin required)
#
#  Run from PowerShell (no admin required):
#
#      powershell -ExecutionPolicy Bypass -File scripts\register_cleanup_logon_task.ps1
#
#  To remove the entry later:
#
#      scripts\on_open_cleanup.cmd --unregister
# ============================================================

$ErrorActionPreference = 'Stop'

$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir '..')
$cmdPath     = Join-Path $scriptDir 'on_open_cleanup.cmd'

if (-not (Test-Path $cmdPath)) {
    throw "Missing launcher script: $cmdPath"
}

$taskName = 'CleanupCursorHistoryAtLogon'
$runKeyName = 'CleanupCursorHistory'
$runKeyPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$cmdValue = "`"$cmdPath`" --apply"

# ---- Strategy 1: Task Scheduler (preferred) -------------------------
$taskRegistered = $false
try {
    # Idempotent: delete the task if it already exists.
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    $action  = New-ScheduledTaskAction -Execute $cmdPath -Argument '--apply'
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description ('Removes Cursor / Roo Code history older than ' +
                      '14 days whenever the user logs on.') `
        -Principal (New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive) | Out-Null

    Write-Host "Registered Task Scheduler task '$taskName' -> $cmdPath"
    $taskRegistered = $true
} catch {
    Write-Host "Task Scheduler registration failed: $_"
    Write-Host "Falling back to HKCU Run key..."
}

# ---- Strategy 2: HKCU Run key (fallback) ----------------------------
if (-not $taskRegistered) {
    try {
        if (-not (Test-Path $runKeyPath)) {
            New-Item -Path $runKeyPath -Force | Out-Null
        }
        $existing = Get-ItemProperty -Path $runKeyPath -Name $runKeyName -ErrorAction SilentlyContinue
        if ($existing) {
            Set-ItemProperty -Path $runKeyPath -Name $runKeyName -Value $cmdValue
            Write-Host "Updated HKCU Run key '$runKeyName' -> $cmdValue"
        } else {
            New-ItemProperty -Path $runKeyPath -Name $runKeyName -Value $cmdValue -PropertyType String -Force | Out-Null
            Write-Host "Created HKCU Run key '$runKeyName' -> $cmdValue"
        }
    } catch {
        throw "Both Task Scheduler and HKCU Run key registration failed. Last error: $_"
    }
}

# ---- Cleanup any stale alternative registration ---------------------
# If we registered via Task Scheduler, remove any stale Run key (and vice versa).
if ($taskRegistered) {
    try {
        $staleRun = Get-ItemProperty -Path $runKeyPath -Name $runKeyName -ErrorAction SilentlyContinue
        if ($staleRun) {
            Remove-ItemProperty -Path $runKeyPath -Name $runKeyName -ErrorAction SilentlyContinue
            Write-Host "Removed stale HKCU Run key (Task Scheduler is active)."
        }
    } catch { }
}

Write-Host ""
Write-Host "Auto-cleanup at logon is now active."
Write-Host "To unregister later: scripts\on_open_cleanup.cmd --unregister"
