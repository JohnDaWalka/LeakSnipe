@echo off
setlocal EnableDelayedExpansion
echo ================================================================
echo   Poker Therapist Suite - Portable EXE Builder
echo ================================================================
echo.

cd /d "C:\PokerBuild\poker-trainer"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cannot access C:\PokerBuild\poker-trainer
    exit /b 1
)

REM ── Step 1: Verify tools ────────────────────────────────────────
echo [1/5] Checking prerequisites...
call node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found. Install from https://nodejs.org
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do echo   Node: %%v
for /f "tokens=*" %%v in ('npm --version') do echo   npm:  %%v
echo.

REM ── Step 2: Install dependencies ───────────────────────────────
echo [2/5] Installing dependencies...
call npm install --prefer-offline 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: npm install had issues, attempting to continue...
)
echo   Dependencies ready.
echo.

REM ── Step 3: TypeScript check ───────────────────────────────────
echo [3/5] TypeScript compilation check...
call npx tsc -b --noEmit 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: TypeScript found issues (non-blocking, continuing build)
)
echo   TypeScript check complete.
echo.

REM ── Step 4: Vite build (frontend + electron bundles) ───────────
echo [4/5] Building application with Vite...
call npx vite build 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Vite build failed!
    echo Check that index.html and src/main.tsx exist and are valid.
    exit /b 1
)
echo   Vite build complete.
echo.

REM ── Step 5: Package as portable .exe ───────────────────────────
echo [5/5] Packaging portable Windows EXE...
set CSC_IDENTITY_AUTO_DISCOVERY=false
set ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true
call npx electron-builder --win portable 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: electron-builder failed!
    exit /b 1
)
echo.

REM ── Report results ─────────────────────────────────────────────
echo ================================================================
echo   BUILD COMPLETE
echo ================================================================
if exist "release\PokerTherapistSuite.exe" (
    for %%F in ("release\PokerTherapistSuite.exe") do (
        echo   Output: %%~fF
        set /a sizeMB=%%~zF / 1048576
        echo   Size:   !sizeMB! MB
    )
    echo.
    echo   To run: double-click release\PokerTherapistSuite.exe
) else (
    echo   WARNING: Expected output not found at release\PokerTherapistSuite.exe
    echo   Checking release folder...
    dir /b release\*.exe 2>nul
)
echo ================================================================
