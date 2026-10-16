@echo off
echo ==========================================
echo Building DC2PC Patch (Launcher + DLL)
echo ==========================================

if not exist build mkdir build
cd build

echo [1/2] Configuring CMake for Visual Studio 2022 (Win32)...
cmake .. -G "Visual Studio 17 2022" -A Win32
if %errorlevel% neq 0 (
    echo [ERROR] CMake configuration failed.
    pause
    exit /b %errorlevel%
)

echo [2/2] Compiling Release Win32...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo [SUCCESS] Build completed!
echo ==========================================
echo.
echo Solution file:
echo   - build\DC2PCPatch.sln
echo.
echo Output files:
echo   - build\Release\DC2PCLauncher.exe
echo   - build\Release\DC2PCPatch.dll
echo.
echo Installation:
echo   1. Copy BOTH files to the DC2PC game folder
echo   2. Run DC2PCLauncher.exe instead of DC2PC.EXE
echo.
pause
