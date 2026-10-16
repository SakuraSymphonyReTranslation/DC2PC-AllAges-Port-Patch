# DC2PC Translation Tool / Tools Terjemahan

## English

Run **DC2PCMesTextTool_GUI.exe** with every accompanying DLL and configuration file in the same folder. Install **.NET 8 Desktop Runtime for Windows** first.

The interface starts in **English on every launch**. Use **Language / Bahasa** to switch to **Bahasa Indonesia** in guided or manual mode. Your paths, current project, logs, tabs, and wrap settings are preserved. The selection changes the editor interface, not game text.

**Project folder starts empty.** Choose your own new, empty work folder, separate from the game and source MES folders. For an existing project, click **Open project...** and select `proyek.json`.

1. Choose the installed game, source MES, and a project folder.
2. **Create project + export**, then edit text in `03_JSON_EDIT`.
3. **Validate JSON**, then **Import JSON → MES**.
4. Review output, close the game, then **Install output to game**. This writes to `id_Data` and creates a backup under `06_BACKUP`.

Start with [TUTORIAL_ENGLISH.txt](TUTORIAL_ENGLISH.txt); it explains every step, JSON examples, and restoring backups. Both tutorials also open from the buttons at the top of the application. Python and IDA are not required.

The runtime patch can be tried with the English version of Da Capo 2 Plus Communication All Age, but compatibility is unverified. This guided workflow targets **id_Data**, not **eng_data**. Keep existing English data separate and review matching MES output manually before installing. The runtime patch and game data are separate downloads in the [project repository](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch).

The bundled source corpus is not verified as clean All Age content. Remaining adult content was confirmed in `ind_0127_f3_kko.mes`; `ind_0127_f1_nnk.mes` has invalid source branch labels and edited imports are rejected. Export/import does not remove adult content or verify translation meaning.

## Bahasa Indonesia

Buka **DC2PCMesTextTool_GUI.exe** dengan seluruh DLL dan config pendamping tetap dalam folder yang sama. Pasang **.NET 8 Desktop Runtime untuk Windows** terlebih dahulu.

Antarmuka memakai **English setiap kali dibuka**. Gunakan **Language / Bahasa** untuk beralih ke **Bahasa Indonesia** pada mode terpandu maupun manual. Isian folder, proyek aktif, log, tab, dan pengaturan wrap tetap dipertahankan. Pilihan bahasa mengubah editor, bukan teks game.

**Folder proyek awalnya kosong.** Pilih folder kerja baru yang kosong, terpisah dari game dan MES sumber. Untuk proyek lama, klik **Buka proyek...** lalu pilih `proyek.json`.

1. Pilih instalasi game, MES sumber, dan folder proyek.
2. **Buat proyek + ekspor**, lalu edit teks dalam `03_JSON_EDIT`.
3. **Periksa JSON**, kemudian **Impor JSON → MES**.
4. Periksa hasil, tutup game, lalu **Pasang hasil**. Proses menulis ke `id_Data` dan membuat backup di `06_BACKUP`.

Mulai dari [TUTORIAL_INDONESIA.txt](TUTORIAL_INDONESIA.txt) yang berisi langkah, contoh JSON, dan pemulihan backup. Kedua tutorial juga dapat dibuka melalui tombol di bagian atas aplikasi. Python dan IDA tidak diperlukan.

Patch runtime bisa dicoba pada Da Capo 2 Plus Communication All Age bahasa Inggris, tetapi kompatibilitasnya belum terverifikasi. Alur terpandu ini menargetkan **id_Data**, bukan **eng_data**. Pertahankan data Inggris dan periksa hasil MES yang sesuai secara manual sebelum dipasang. Unduhan runtime dan data game tersedia terpisah di [repository proyek](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch).

Korpus sumber bawaan belum terverifikasi All Age bersih. Konten dewasa terkonfirmasi pada `ind_0127_f3_kko.mes`; `ind_0127_f1_nnk.mes` memiliki label cabang sumber rusak sehingga impor perubahannya ditolak. Ekspor/impor tidak menghapus konten dewasa atau memeriksa makna terjemahan.

## Guides / Panduan

- [English tutorial](TUTORIAL_ENGLISH.txt)
- [Tutorial Indonesia](TUTORIAL_INDONESIA.txt)
- [English beginner guide](BEGINNER_GUIDE.txt)
- [Panduan pemula](PANDUAN_PEMULA.txt)
- [Status sumber](STATUS_SUMBER.txt)
- [Peta pipeline pengembang](PETA_PIPELINE.txt)


## Build / Kompilasi

From this directory, with .NET 8 SDK on Windows / Dari folder ini, dengan .NET 8 SDK di Windows:

```powershell
dotnet build DC2PCMesTextTool_GUI.csproj -c Release
```

Output / Hasil: `bin/Release/net8.0-windows/`. `UiStrings.json` is embedded in the DLL / ditanam ke DLL.
