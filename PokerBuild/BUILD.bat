@echo off
setlocal EnableDelayedExpansion
title Poker Therapist Suite - Build Installer
color 0A

echo.
echo ================================================================
echo   Poker Therapist Suite - Windows Installer Builder
echo   Produces: Setup .exe (NSIS) + Portable .exe
echo   Connects to: CoinPoker, BetACR, DriveHUD2, PokerStars
echo ================================================================
echo.

cd /d "C:\PokerBuild\poker-trainer"

REM ── Find Node.js ────────────────────────────────────────────────
set NODE_EXE=

REM Check PATH first
for /f "tokens=*" %%n in ('where node 2^>nul') do (
    set NODE_EXE=%%n
    goto :found_node
)

REM Common install locations
for %%c in (
    "C:\Program Files\nodejs\node.exe"
    "C:\Program Files (x86)\nodejs\node.exe"
    "%LOCALAPPDATA%\Programs\nodejs\node.exe"
) do (
    if exist %%c (
        set NODE_EXE=%%~c
        goto :found_node
    )
)

REM Search nvm versions
if exist "%APPDATA%\nvm" (
    for /d %%v in ("%APPDATA%\nvm\v*") do (
        if exist "%%v\node.exe" (
            set NODE_EXE=%%v\node.exe
            goto :found_node
        )
    )
)

echo.
echo  *** Node.js not found! ***
echo.
echo  Install Node.js LTS from: https://nodejs.org/en/download
echo    1. Download "Windows Installer (.msi)" - LTS version
echo    2. Run installer with default options (adds to PATH)
echo    3. Restart this script
echo.
pause
exit /b 1

:found_node
for %%p in ("!NODE_EXE!") do set NODE_DIR=%%~dpp
set NPM_CMD=!NODE_DIR!npm.cmd
set NPX_CMD=!NODE_DIR!npx.cmd
set PATH=!NODE_DIR!;!PATH!

for /f "tokens=*" %%v in ('"!NODE_EXE!" --version 2^>nul') do set NODE_VER=%%v
echo [OK] Node.js !NODE_VER! found at !NODE_DIR!
echo.

REM ── Install / sync dependencies ─────────────────────────────────
echo [1/4] Checking dependencies...
if not exist "node_modules\electron" (
    echo   First-time install — this takes 2-4 minutes...
    call "!NPM_CMD!" install
    if !ERRORLEVEL! NEQ 0 (
        echo   WARNING: npm install had issues. Trying to continue...
    )
) else (
    call "!NPM_CMD!" install --prefer-offline --silent 2>nul
)
echo   [OK] Dependencies ready
echo.

REM ── TypeScript ──────────────────────────────────────────────────
echo [2/4] TypeScript check...
call "!NPX_CMD!" tsc -b --noEmit 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo   [WARN] TypeScript warnings found (non-blocking)
) else (
    echo   [OK] No type errors
)
echo.

REM ── Vite build ──────────────────────────────────────────────────
echo [3/4] Building frontend + Electron bundles...
call "!NPX_CMD!" vite build
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo  *** Vite build FAILED — see errors above ***
    pause
    exit /b 1
)
echo   [OK] Build complete
echo.

REM ── Package: NSIS installer + Portable ──────────────────────────
echo [4/4] Creating Windows installer (.exe)...
echo   Building NSIS Setup installer + Portable exe...
set CSC_IDENTITY_AUTO_DISCOVERY=false
set ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true
call "!NPX_CMD!" electron-builder --win nsis portable
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo  *** electron-builder FAILED — see errors above ***
    echo  Tip: Delete node_modules\electron and re-run if stuck.
    pause
    exit /b 1
)
echo   [OK] Packaging complete
echo.

REM ── Results ─────────────────────────────────────────────────────
echo ================================================================
echo   BUILD COMPLETE — Output files:
echo ================================================================
echo.

set SETUP_EXE=
set PORTABLE_EXE=

for %%F in ("release\PokerTherapistSuite-Setup.exe") do (
    if exist %%F (
        set SETUP_EXE=%%~fF
        for %%S in (%%F) do set /a SETUP_MB=%%~zS / 1048576
    )
)

for %%F in ("release\PokerTherapistSuite-Portable.exe") do (
    if exist %%F (
        set PORTABLE_EXE=%%~fF
        for %%S in (%%F) do set /a PORTABLE_MB=%%~zS / 1048576
    )
)

REM Fallback search
if not defined SETUP_EXE (
    for /r "release" %%F in (*Setup*.exe) do (
        set SETUP_EXE=%%F
    )
)
if not defined PORTABLE_EXE (
    for /r "release" %%F in (*Portable*.exe *portable*.exe) do (
        set PORTABLE_EXE=%%F
    )
)

if defined SETUP_EXE (
    echo   INSTALLER:  !SETUP_EXE!
    echo     ^ Double-click to install with Start Menu + Desktop shortcut
    echo.
)
if defined PORTABLE_EXE (
    echo   PORTABLE:   !PORTABLE_EXE!
    echo     ^ Run directly, no install needed
    echo.
)

echo   After installing:
echo     - App data:    %%APPDATA%%\Poker Therapist Suite\
echo     - Database:    %%APPDATA%%\poker-therapist\poker-tracker.sqlite
echo     - Hand histories watched automatically:
echo         CoinPoker:  %%LOCALAPPDATA%%\CoinPoker\HandHistory
echo         BetACR:     %%USERPROFILE%%\Documents\ACR Poker\HandHistory
echo         DriveHUD2:  %%APPDATA%%\DriveHUD 2\ProcessedData
echo         PokerStars: %%USERPROFILE%%\Documents\PokerStars\HandHistory
echo     - Add custom paths from Settings inside the app
echo.

if defined SETUP_EXE (
    choice /c YN /m "Run the installer now?"
    if !ERRORLEVEL! EQU 1 start "" "!SETUP_EXE!"
)

echo.
echo ================================================================
pause

