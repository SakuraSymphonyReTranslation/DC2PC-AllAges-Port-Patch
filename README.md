# DC2PC AllAges Port Patch

**English** | **Bahasa Indonesia**

Patch runtime, an All Age port work in progress, Indonesian script data, and bilingual translation tools for **Da Capo 2 Plus Communication All Age**. This project is published in its own repository.

Patch runtime, pekerjaan port All Age yang masih berlangsung, data naskah Indonesia, dan tools terjemahan dua bahasa untuk **Da Capo 2 Plus Communication All Age**. Proyek ini diterbitkan di repository tersendiri.

## English

### Downloads

Get the two archives from [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest):

| Archive | Contents and purpose |
| --- | --- |
| `DC2PC_AllAges_Patch DLL + Executable.rar` | Launcher, patch DLL, INI, two Locale Emulator DLLs, bilingual installation guide, and third-party notices. The executable is **DC2PCLauncher.exe**; the base game executable is not included. |
| `Tools_Terjemahan_or_Translate.rar` | Ready-to-run MES/JSON editor with its DLL/config files, English and Indonesian tutorial modules, and guides. Requires **.NET 8 Desktop Runtime for Windows**. |

Neither RAR contains the `AdvData` / `id_Data` script folders. For the bundled Indonesian port data, download this repository using **Code > Download ZIP**, or select **Source code (zip)** on the release page. You still need an installed copy of the game containing `DC2PC.EXE` and its original assets. This repository is not a complete game installation.

### Install the bundled Indonesian data

1. Close the game and back up the installation, including files you will overwrite.
2. Extract the repository ZIP into a separate folder. Copy `AdvData`, `id_Data`, `DC2PCLauncher.exe`, `DC2PCPatch.dll`, `DC2PCPatch.ini`, `LoaderDll.dll`, and `LocaleEmulator.dll` into the game folder containing `DC2PC.EXE`.
3. Keep the game's other required files and libraries. The included INI uses `[Settings] Language=1` for `id_Data`.
4. Start `DC2PCLauncher.exe` from that game folder. Test dialogue, choices, branches, replay, and save/load.

The optional `PASANG_PATCH_OTOMATIS.bat` copies the same payload and reports copy failures. It requires the full repository/package, does not create a backup, and is for the bundled Indonesian data. Manual installation is described in [INSTALL_EN_ID.txt](INSTALL_EN_ID.txt).

### Trying the English version

**This patch can be tried with the English version of Da Capo 2 Plus Communication All Age. Compatibility has not yet been verified.** Different executables and existing patches may behave differently. Some runtime menus and popup translations remain Indonesian; selecting English in the translation tool does not translate the game's interface.

Use a backup or separate copy of the English installation. Start with the runtime RAR only. Keep your existing English scripts/assets; do not copy this repository's Indonesian `id_Data` or unverified `AdvData` over them. Select runtime settings according to where your compatible English assets are located:

| `DC2PCPatch.ini` under `[Settings]` | Script source |
| --- | --- |
| `Language=0` | Original game paths; no language-folder redirection. It does not translate those files into Japanese. |
| `Language=1` | Indonesian `id_Data` (included INI default). |
| `Language=2` | Compatible English assets in `eng_data`, such as `eng_data\MES`. These assets are not included. |

These are routing settings, not a compatibility fix. Existing English releases may store files differently. The guided tool's build/install workflow currently targets **`id_Data`**; it must not be treated as an English-game installer. For English work, use matching source MES and review separately saved output before applying it to the appropriate English data folder.

### Translation tool and tutorials

Open `Tools_Terjemahan\DC2PCMesTextTool_GUI.exe`. The interface starts in **English on each launch**; **Language / Bahasa** switches between English and Bahasa Indonesia in both guided and manual modes. Switching preserves entered paths, project selections, logs, and manual settings. It changes only the tool interface.

**Project folder starts empty.** Choose your own new, empty working folder, separate from the game and source MES folders. To continue existing work, use **Open project...** and select `proyek.json`.

Follow: **Create project + export → edit `03_JSON_EDIT` → Validate JSON → Import JSON → MES → Install output to game**. Installing edited output creates a backup in the project's `06_BACKUP`. Read the tutorials before modifying JSON structure:

- [English tutorial module](TUTORIAL_ENGLISH.txt)
- [Modul tutorial Bahasa Indonesia](TUTORIAL_INDONESIA.txt)
- Both modules are available through **Tutorial English / Tutorial Indonesia** in the app.

Python and IDA are not required for this GUI workflow. The source code is in [source_code](source_code/README.md).

### Current changes and limits

- Choice text uses proportional spacing, one space after the circle marker, a 16-pixel left margin, and font adjustment for long text. Existing popup/textbox sizing settings are retained.
- The GUI has bilingual menus, an explicit project location, and two tutorial modules. Imports validate JSON/MES structure and reject incompatible edits.
- **The bundled corpus is not verified as clean All Age content.** The audit confirmed remaining adult content in `ind_0127_f3_kko.mes` and invalid source branch labels in `ind_0127_f1_nnk.mes` (24 Indonesian / 12 Japanese labels). Edited imports of the latter are rejected.
- Eight jump stubs and 25 replacement scenes do not establish that every script, image, audio file, or replay is clean. Export/import does not remove adult content or verify translation meaning. A clean official Japanese All Age source has not been established for this package.
- See [STATUS_SUMBER.txt](STATUS_SUMBER.txt) for the detailed Indonesian audit. The project title describes the port effort, not a completed content certification.

## Bahasa Indonesia

### Unduhan

Ambil kedua arsip dari [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest):

| Arsip | Isi dan kegunaan |
| --- | --- |
| `DC2PC_AllAges_Patch DLL + Executable.rar` | Launcher, DLL patch, INI, dua DLL Locale Emulator, panduan pemasangan dua bahasa, dan keterangan komponen pihak ketiga. Executable yang dimaksud adalah **DC2PCLauncher.exe**; executable game asli tidak disertakan. |
| `Tools_Terjemahan_or_Translate.rar` | Editor MES/JSON siap jalan beserta DLL/config, modul tutorial Inggris dan Indonesia, serta panduan. Memerlukan **.NET 8 Desktop Runtime untuk Windows**. |

Kedua RAR tidak memuat folder naskah `AdvData` / `id_Data`. Untuk data port Indonesia bawaan, unduh repository melalui **Code > Download ZIP**, atau pilih **Source code (zip)** pada halaman release. Anda tetap memerlukan instalasi game dengan `DC2PC.EXE` dan aset aslinya. Repository ini bukan instalasi game lengkap.

### Memasang data Indonesia bawaan

1. Tutup game dan cadangkan instalasinya, termasuk berkas yang akan ditimpa.
2. Ekstrak ZIP repository ke folder terpisah. Salin `AdvData`, `id_Data`, `DC2PCLauncher.exe`, `DC2PCPatch.dll`, `DC2PCPatch.ini`, `LoaderDll.dll`, dan `LocaleEmulator.dll` ke folder game yang memiliki `DC2PC.EXE`.
3. Pertahankan berkas dan library lain milik game. INI bawaan memakai `[Settings] Language=1` untuk `id_Data`.
4. Jalankan `DC2PCLauncher.exe` dari folder game tersebut. Uji dialog, pilihan, cabang, replay, serta save/load.

`PASANG_PATCH_OTOMATIS.bat` tersedia sebagai pilihan untuk menyalin isi yang sama dan melaporkan kegagalan. Skrip membutuhkan repository/paket lengkap, tidak membuat backup, dan ditujukan untuk data Indonesia bawaan. Petunjuk manual ada di [INSTALL_EN_ID.txt](INSTALL_EN_ID.txt).

### Mencoba versi bahasa Inggris

**Patch ini bisa dicoba pada Da Capo 2 Plus Communication All Age versi bahasa Inggris. Kompatibilitasnya belum terverifikasi.** Executable dan patch yang sudah terpasang dapat memengaruhi hasil. Sebagian menu runtime dan terjemahan popup masih berbahasa Indonesia; pilihan English pada tools tidak menerjemahkan antarmuka game.

Gunakan backup atau salinan instalasi Inggris. Mulai dengan RAR runtime saja. Pertahankan naskah/aset Inggris Anda; jangan menimpanya dengan `id_Data` Indonesia atau `AdvData` yang belum terverifikasi dari repository ini. Sesuaikan pengaturan dengan lokasi aset Inggris yang kompatibel:

| `DC2PCPatch.ini` pada `[Settings]` | Sumber naskah |
| --- | --- |
| `Language=0` | Jalur asli game; tanpa pengalihan ke folder bahasa. Pengaturan ini tidak menerjemahkan berkas menjadi bahasa Jepang. |
| `Language=1` | `id_Data` Indonesia (default INI bawaan). |
| `Language=2` | Aset Inggris yang kompatibel di `eng_data`, misalnya `eng_data\MES`. Aset ini tidak disertakan. |

Pengaturan tersebut memilih jalur berkas, bukan memperbaiki kompatibilitas. Rilis Inggris yang berbeda mungkin memakai susunan berkas lain. Alur build/pasang terpandu pada tools saat ini menulis ke **`id_Data`**; jangan menganggapnya sebagai installer game Inggris. Untuk pekerjaan Inggris, gunakan MES sumber yang cocok dan periksa hasil yang disimpan terpisah sebelum memasangnya ke folder data Inggris yang tepat.

### Tools terjemahan dan tutorial

Buka `Tools_Terjemahan\DC2PCMesTextTool_GUI.exe`. Antarmuka memakai **English setiap kali aplikasi dibuka**. **Language / Bahasa** mengganti English dan Bahasa Indonesia pada mode terpandu maupun manual. Pergantian mempertahankan isian folder, pilihan proyek, log, dan pengaturan manual. Ini hanya mengganti antarmuka tools.

**Folder proyek awalnya kosong.** Pilih folder kerja baru yang kosong dan terpisah dari game serta MES sumber. Untuk melanjutkan proyek lama, gunakan **Buka proyek...** lalu pilih `proyek.json`.

Alurnya: **Buat proyek + ekspor → edit `03_JSON_EDIT` → Periksa JSON → Impor JSON → MES → Pasang hasil**. Pemasangan hasil membuat backup di `06_BACKUP` milik proyek. Baca tutorial sebelum mengubah struktur JSON:

- [Modul tutorial Bahasa Indonesia](TUTORIAL_INDONESIA.txt)
- [English tutorial module](TUTORIAL_ENGLISH.txt)
- Keduanya dapat dibuka melalui **Tutorial English / Tutorial Indonesia** pada aplikasi.

Python dan IDA tidak diperlukan untuk alur GUI ini. Kode sumber tersedia di [source_code](source_code/README.md).

### Pembaruan dan batas verifikasi

- Teks pilihan memakai spasi proporsional, satu spasi setelah lingkaran, margin kiri 16 piksel, dan penyesuaian font untuk teks panjang. Pengaturan ukuran popup/textbox dipertahankan.
- GUI menyediakan menu dua bahasa, lokasi proyek yang dipilih pengguna, serta dua modul tutorial. Impor memvalidasi struktur JSON/MES dan menolak perubahan yang tidak cocok.
- **Korpus bawaan belum terverifikasi sebagai All Age bersih.** Audit mengonfirmasi sisa konten dewasa pada `ind_0127_f3_kko.mes` dan label cabang sumber rusak pada `ind_0127_f1_nnk.mes` (24 label Indonesia / 12 Jepang). Impor perubahan berkas terakhir ditolak.
- Delapan naskah pengalih dan 25 adegan pengganti tidak membuktikan seluruh naskah, gambar, suara, atau replay sudah bersih. Ekspor/impor tidak menghapus konten dewasa atau memeriksa makna terjemahan. Sumber Jepang All Age resmi yang bersih belum ditetapkan untuk paket ini.
- Rincian audit ada di [STATUS_SUMBER.txt](STATUS_SUMBER.txt). Nama proyek menjelaskan pekerjaan port, bukan sertifikasi bahwa audit konten telah selesai.

## Folder map / Peta folder

| Path | English / Indonesia |
| --- | --- |
| `AdvData/` | Installed Japanese scripts and port assets; edition unverified / Naskah Jepang terpasang dan aset port; edisi belum terverifikasi |
| `id_Data/` | Indonesian scripts and replay maps / Naskah Indonesia dan peta replay |
| `Tools_Terjemahan/` | Ready-to-run editor and tutorials / Editor siap jalan dan tutorial |
| `source_code/DC2PCMesTextTool_GUI/` | C# GUI/CLI source / Kode GUI/CLI C# |
| `source_code/DC2PCPatch/` | C++ patch, launcher, and dependencies / Patch C++, launcher, dan dependency |
| `source_code/Pipeline_Scripts/` | Developer port scripts; external inputs are incomplete / Skrip port pengembang; bahan eksternal belum lengkap |

See / Lihat [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for component attribution / untuk atribusi komponen.

## Verification / Pemeriksaan

The release preparation passed a .NET build with zero warnings/errors, 582 language/project-state assertions, six installer scenarios, and extraction/hash checks for both RAR archives. Runtime and ready-to-run editor binaries retain the tested package's hashes. Archive checksums: [RELEASE_SHA256SUMS.txt](RELEASE_SHA256SUMS.txt).

Persiapan release lulus build .NET tanpa warning/error, 582 pemeriksaan bahasa/status proyek, enam skenario installer, serta pemeriksaan ekstraksi/hash kedua RAR. Hash biner runtime dan editor siap jalan tetap sama dengan paket yang telah diuji. Checksum arsip: [RELEASE_SHA256SUMS.txt](RELEASE_SHA256SUMS.txt).
