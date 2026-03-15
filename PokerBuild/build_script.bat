@echo off
cd C:\PokerBuild\poker-trainer
echo === Starting Build Process ===
echo.

echo === Step 1: Check Node/npm versions ===
call node --version
call npm --version
call pnpm --version
echo.

echo === Step 2: Running pnpm install ===
call pnpm install --no-frozen-lockfile
if %ERRORLEVEL% NEQ 0 (
    echo Install failed with error code %ERRORLEVEL%
    exit /b 1
)
echo Install completed successfully
echo.

echo === Step 3: Running build ===
call pnpm run build
if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    exit /b 1
)
echo Build completed successfully
echo.

echo === Step 4: Creating portable EXE ===
call npx electron-builder --win portable
if %ERRORLEVEL% NEQ 0 (
    echo Electron builder failed with error code %ERRORLEVEL%
    exit /b 1
)
echo EXE creation completed successfully
echo.

echo === Step 5: Reporting results ===
cd C:\PokerBuild\poker-trainer\release
for %%F in (PokerTherapistSuite.exe) do (
    echo EXE File: %%~fF
    echo Size: %%~zF bytes
)
