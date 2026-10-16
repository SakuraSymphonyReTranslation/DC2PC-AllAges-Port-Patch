# DC2PC Patch runtime / Runtime patch DC2PC

## English

Runtime source: `src/dc2pcpatch.cpp`, `src/choice_text_renderer.inl`, and `src/popup_text_renderer.inl`. Launcher: `src/launcher.cpp` and `src/launcher.rc`.

Download **DC2PC_AllAges_Patch DLL + Executable.rar** from this project's [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest). It contains the launcher, patch DLL, INI, locale libraries, and installation documentation. It does not contain `DC2PC.EXE` or game script data. Follow [INSTALL_EN_ID.txt](../../INSTALL_EN_ID.txt).

The patch can be tried with the English version of Da Capo 2 Plus Communication All Age; compatibility remains unverified. Some menus/popups remain Indonesian. Back up an English installation and preserve its scripts/assets. Language-folder redirection uses `Language=0` for original paths, `1` for `id_Data` (the bundled default), and `2` for compatible `eng_data` assets, which are not included.

Build instructions and locale-resource prerequisites are in [source_code/README.md](../README.md). Use CMake 3.15+ and MSVC **Win32/x86**. Export/import tools and C++ runtime builds are independent.

## Bahasa Indonesia

Source runtime: `src/dc2pcpatch.cpp`, `src/choice_text_renderer.inl`, dan `src/popup_text_renderer.inl`. Launcher: `src/launcher.cpp` dan `src/launcher.rc`.

Unduh **DC2PC_AllAges_Patch DLL + Executable.rar** dari [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest) proyek ini. Isinya launcher, DLL patch, INI, library locale, dan petunjuk pemasangan. `DC2PC.EXE` serta data naskah game tidak disertakan dalam RAR. Ikuti [INSTALL_EN_ID.txt](../../INSTALL_EN_ID.txt).

Patch bisa dicoba pada Da Capo 2 Plus Communication All Age bahasa Inggris; kompatibilitas belum terverifikasi. Sebagian menu/popup masih Indonesia. Cadangkan instalasi Inggris dan pertahankan naskah/asetnya. Pengalihan folder memakai `Language=0` untuk jalur asli, `1` untuk `id_Data` (default bawaan), dan `2` untuk aset `eng_data` yang kompatibel, yang tidak disertakan.

Cara build serta kebutuhan resource locale ada di [source_code/README.md](../README.md). Gunakan CMake 3.15+ dan MSVC **Win32/x86**. Build tools ekspor/impor dan runtime C++ terpisah.
