@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title DC2PC AllAges Port Patch - Indonesian data / Data Indonesia
set "SCRIPT_DIR=%~dp0"

echo DC2PC AllAges Port Patch - Indonesian data / Data Indonesia
echo Close the game and back up the installation before continuing.
echo Tutup game dan cadangkan instalasi sebelum melanjutkan.
echo This installer does not create a backup / Installer tidak membuat backup.
echo English-version users: read INSTALL_EN_ID.txt first.
echo Pengguna versi Inggris: baca INSTALL_EN_ID.txt terlebih dahulu.
echo.

for %%F in (DC2PCLauncher.exe DC2PCPatch.dll DC2PCPatch.ini LoaderDll.dll LocaleEmulator.dll) do (
    if not exist "%SCRIPT_DIR%%%F" goto MISSING_PACKAGE
)
if not exist "%SCRIPT_DIR%AdvData\MES\*.mes" goto MISSING_PACKAGE
if not exist "%SCRIPT_DIR%id_Data\MES\*.mes" goto MISSING_PACKAGE

if exist "%SCRIPT_DIR%DC2PC.EXE" goto LOCAL_INSTALL
set "TARGET_DIR="
set /p "TARGET_DIR=Game folder / Folder game: "
if not defined TARGET_DIR goto INVALID_TARGET
set "TARGET_DIR=%TARGET_DIR:"=%"
if not defined TARGET_DIR goto INVALID_TARGET
if not exist "%TARGET_DIR%\DC2PC.EXE" goto INVALID_TARGET

for %%D in (AdvData id_Data) do (
    if exist "%TARGET_DIR%\%%D" if not exist "%TARGET_DIR%\%%D\" goto COPY_FAILED
)
for %%F in (DC2PCLauncher.exe DC2PCPatch.dll DC2PCPatch.ini LoaderDll.dll LocaleEmulator.dll INSTALL_EN_ID.txt) do (
    if exist "%TARGET_DIR%\%%F\" goto COPY_FAILED
)
echo Installing to / Memasang ke "%TARGET_DIR%"
xcopy "%SCRIPT_DIR%AdvData" "%TARGET_DIR%\AdvData\" /E /I /Y /Q >nul
if errorlevel 1 goto COPY_FAILED
xcopy "%SCRIPT_DIR%id_Data" "%TARGET_DIR%\id_Data\" /E /I /Y /Q >nul
if errorlevel 1 goto COPY_FAILED
for %%F in (DC2PCLauncher.exe DC2PCPatch.dll DC2PCPatch.ini LoaderDll.dll LocaleEmulator.dll) do (
    copy /y "%SCRIPT_DIR%%%F" "%TARGET_DIR%\" >nul
    if errorlevel 1 goto COPY_FAILED
)
if not exist "%SCRIPT_DIR%INSTALL_EN_ID.txt" goto INSTALLED
copy /y "%SCRIPT_DIR%INSTALL_EN_ID.txt" "%TARGET_DIR%\" >nul
if errorlevel 1 goto COPY_FAILED

:INSTALLED
echo [SUCCESS / SUKSES] Patch files copied / Berkas patch telah disalin.
echo Run / Jalankan "%TARGET_DIR%\DC2PCLauncher.exe"
pause
exit /b 0

:LOCAL_INSTALL
echo Package files and DC2PC.EXE are already in this folder.
echo Berkas paket dan DC2PC.EXE sudah berada di folder ini.
echo Run / Jalankan "%SCRIPT_DIR%DC2PCLauncher.exe"
pause
exit /b 0

:MISSING_PACKAGE
echo [ERROR] Incomplete package: runtime files and AdvData/id_Data MES are required.
echo [GALAT] Paket tidak lengkap: runtime serta MES AdvData/id_Data diperlukan.
echo Download the full repository ZIP / Unduh ZIP repository lengkap.
pause
exit /b 1

:INVALID_TARGET
echo [ERROR] Choose a game folder containing DC2PC.EXE.
echo [GALAT] Pilih folder game yang memiliki DC2PC.EXE.
pause
exit /b 1

:COPY_FAILED
echo [ERROR] Copy failed. Installation may be partial; restore your backup.
echo [GALAT] Penyalinan gagal. Instalasi mungkin sebagian; pulihkan backup Anda.
echo Check permissions and free space / Periksa izin akses dan ruang penyimpanan.
pause
exit /b 1
