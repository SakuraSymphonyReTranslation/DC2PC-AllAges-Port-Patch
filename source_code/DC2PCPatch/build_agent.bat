@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars32.bat"

if not exist build mkdir build
cd build

echo Configuring CMake for Visual Studio 2022 (Win32)...
cmake .. -G "Visual Studio 17 2022" -A Win32
if %errorlevel% neq 0 exit /b %errorlevel%

echo Compiling DC2PC Release Win32...
cmake --build . --config Release
if %errorlevel% neq 0 exit /b %errorlevel%

echo Build SUCCESS
