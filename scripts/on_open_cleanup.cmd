@echo off
REM ============================================================
REM  on_open_cleanup.cmd
REM
REM  Bootstraps the "每次登录自动清理 IDE 历史" trigger.
REM
REM  Usage:
REM      on_open_cleanup.cmd                REM default: --apply mode
REM      on_open_cleanup.cmd --dry-run      REM simulate only
REM      on_open_cleanup.cmd --apply        REM actually delete
REM      on_open_cleanup.cmd --unregister   REM remove auto-start entries
REM
REM  The script:
REM    1) Locates the Python interpreter on PATH (prefers `py -3`).
REM    2) Resolves this project's root (parent of the `scripts` folder).
REM    3) Runs ``cleanup_generated_artifacts.py ide-history --apply ...``
REM       once, with logging into ``reports/cleanup_logon.log``.
REM
REM  Auto-start registration is handled by
REM  ``register_cleanup_logon_task.ps1`` which tries Task Scheduler
REM  first, then falls back to HKCU Run key. Use --unregister to
REM  remove both.
REM ============================================================

setlocal ENABLEEXTENSIONS
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
pushd "%PROJECT_ROOT%" >NUL
set PROJECT_ROOT=%CD%
popd >NUL

set LOGFILE=%PROJECT_ROOT%\reports\cleanup_logon.log
if not exist "%PROJECT_ROOT%\reports" mkdir "%PROJECT_ROOT%\reports"

REM Handle --unregister: remove all auto-start entries and exit.
REM Tries Task Scheduler first, then HKCU Run key (fallback method).
if /I "%~1"=="--unregister" (
    echo [%date% %time%] Unregistering auto-start entries >> "%LOGFILE%"

    REM Strategy 1: Remove Task Scheduler task (may fail if not registered
    REM or if schtasks is blocked by security policy — that's OK).
    schtasks /Delete /TN "CleanupCursorHistoryAtLogon" /F >> "%LOGFILE%" 2>&1

    REM Strategy 2: Remove HKCU Run key (works without admin).
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "CleanupCursorHistory" /f >> "%LOGFILE%" 2>&1

    echo [%date% %time%] Unregister complete >> "%LOGFILE%"
    echo Auto-start entries removed. >> "%LOGFILE%"
    exit /b 0
)

set MODE=apply
if /I "%~1"=="--dry-run" set MODE=dry-run
if /I "%~1"=="--apply"   set MODE=apply

where py >NUL 2>NUL
if not errorlevel 1 (
    set PY=py -3
) else (
    where python >NUL 2>NUL
    if not errorlevel 1 (
        set PY=python
    ) else (
        echo [ERROR] Neither 'py' nor 'python' is on PATH. >> "%LOGFILE%"
        echo [ERROR] No Python interpreter found on PATH. 1>&2
        exit /b 2
    )
)

echo [%date% %time%] Running cleanup (mode=%MODE%) >> "%LOGFILE%"

%PY% "%PROJECT_ROOT%\scripts\cleanup_generated_artifacts.py" ide-history ^
     --%MODE% ^
     --max-age-days 14 ^
     --keep-manifest "%PROJECT_ROOT%\reports\ide_history_manifest.json" ^
     >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] Exit code: %RC% >> "%LOGFILE%"
exit /b %RC%