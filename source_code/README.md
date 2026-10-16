# Source code / Kode sumber

## English

- `DC2PCMesTextTool_GUI/`: C# WinForms editor, CLI, project workflow, JSON/MES validation, and embedded English/Indonesian strings.
- `DC2PCPatch/`: C++ runtime hooks and launcher, plus bundled dependency sources/licenses.
- `Pipeline_Scripts/`: eleven Python scripts used for port/data work. These are developer utilities, not required GUI steps. External PC/PS2 data, mappings, and `dc2_transfer` are not all bundled; some historical paths require adjustment. See `PETA_PIPELINE.txt`.

Build the GUI on Windows with the .NET 8 SDK, from the repository root:

```powershell
dotnet build source_code/DC2PCMesTextTool_GUI/DC2PCMesTextTool_GUI.csproj -c Release
dotnet run --project tests/LanguageCheck/LanguageCheck.csproj -c Release
```

The GUI build output is `source_code/DC2PCMesTextTool_GUI/bin/Release/net8.0-windows/`. End users need .NET 8 Desktop Runtime, not the SDK. Ready-to-run files are in `../Tools_Terjemahan/`.

For the C++ runtime, use Visual Studio with the C++ desktop workload and CMake 3.15+. From the repository root, copy the two supplied locale DLLs into the runtime source directory because `launcher.rc` embeds them, then build for **Win32/x86**:

```powershell
Copy-Item LoaderDll.dll, LocaleEmulator.dll source_code/DC2PCPatch/
cmake -S source_code/DC2PCPatch -B source_code/DC2PCPatch/build -A Win32
cmake --build source_code/DC2PCPatch/build --config Release
```

Building the C# editor does not rebuild the runtime. The published runtime binaries retain the tested choice renderer and existing popup/textbox settings. The English-game trial and corpus limitations are documented in the [main README](../README.md). Component attribution is in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Bahasa Indonesia

- `DC2PCMesTextTool_GUI/`: editor WinForms C#, CLI, alur proyek, validasi JSON/MES, serta resource English/Indonesia yang ditanam ke DLL.
- `DC2PCPatch/`: hook runtime C++, launcher, serta source/lisensi dependency bawaan.
- `Pipeline_Scripts/`: sebelas skrip Python untuk pekerjaan port/data. Ini utilitas pengembang, bukan langkah wajib GUI. Bahan PC/PS2, mapping, serta `dc2_transfer` belum seluruhnya tersedia; beberapa jalur lama perlu disesuaikan. Baca `PETA_PIPELINE.txt`.

Bangun GUI di Windows memakai .NET 8 SDK, lalu jalankan uji bahasa dengan dua perintah `dotnet` di atas dari root repository. Hasil GUI berada di `source_code/DC2PCMesTextTool_GUI/bin/Release/net8.0-windows/`. Pengguna aplikasi cukup memasang .NET 8 Desktop Runtime. File siap jalan ada di `../Tools_Terjemahan/`.

Untuk runtime C++, pasang Visual Studio dengan workload C++ desktop dan CMake 3.15+. Perintah PowerShell di atas menyalin kedua DLL locale ke direktori source runtime karena `launcher.rc` menanamkannya, kemudian membangun target **Win32/x86**.

Build editor C# tidak membangun ulang runtime. Biner runtime yang diterbitkan mempertahankan renderer pilihan yang telah diuji beserta pengaturan popup/textbox. Catatan uji game Inggris dan batas korpus ada di [README utama](../README.md); atribusi komponen ada di [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
