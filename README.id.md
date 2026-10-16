# DC2PC AllAges Port Patch

[English](README.md) | **[Bahasa Indonesia](README.id.md)**

Patch runtime, pekerjaan port All Age yang masih berlangsung, data naskah Indonesia, dan tools terjemahan dua bahasa untuk **Da Capo 2 Plus Communication All Age**. Proyek ini diterbitkan di repository tersendiri.

## Unduhan

Ambil kedua arsip dari [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest):

| Arsip | Isi dan kegunaan |
| --- | --- |
| `DC2PC_AllAges_Patch DLL + Executable.rar` | Launcher, DLL patch, INI, dua DLL Locale Emulator, panduan pemasangan dua bahasa, dan keterangan komponen pihak ketiga. Executable yang dimaksud adalah **DC2PCLauncher.exe**; executable game asli tidak disertakan. |
| `Tools_Terjemahan_or_Translate.rar` | Editor MES/JSON siap jalan beserta DLL/config, modul tutorial Inggris dan Indonesia, serta panduan. Memerlukan **.NET 8 Desktop Runtime untuk Windows**. |

GitHub mengganti spasi pada nama aset menjadi titik. Label runtime tetap seperti di atas, tetapi berkas terunduh bernama `DC2PC_AllAges_Patch.DLL.+.Executable.rar`; isinya identik dengan arsip lokal.

Kedua RAR tidak memuat folder naskah `AdvData` / `id_Data`. Untuk data port Indonesia bawaan, unduh repository melalui **Code > Download ZIP**, atau pilih **Source code (zip)** pada halaman release. Anda tetap memerlukan instalasi game dengan `DC2PC.EXE` dan aset aslinya. Repository ini bukan instalasi game lengkap.

## Memasang data Indonesia bawaan

1. Tutup game dan cadangkan instalasinya, termasuk berkas yang akan ditimpa.
2. Ekstrak ZIP repository ke folder terpisah. Salin `AdvData`, `id_Data`, `DC2PCLauncher.exe`, `DC2PCPatch.dll`, `DC2PCPatch.ini`, `LoaderDll.dll`, dan `LocaleEmulator.dll` ke folder game yang memiliki `DC2PC.EXE`.
3. Pertahankan berkas dan library lain milik game. INI bawaan memakai `[Settings] Language=1` untuk `id_Data`.
4. Jalankan `DC2PCLauncher.exe` dari folder game tersebut. Uji dialog, pilihan, cabang, replay, serta save/load.

`PASANG_PATCH_OTOMATIS.bat` tersedia sebagai pilihan untuk menyalin isi yang sama dan melaporkan kegagalan. Skrip membutuhkan repository/paket lengkap, tidak membuat backup, dan ditujukan untuk data Indonesia bawaan. Petunjuk manual ada di [INSTALL_EN_ID.txt](INSTALL_EN_ID.txt).

## Mencoba versi bahasa Inggris

**Patch ini bisa dicoba pada Da Capo 2 Plus Communication All Age versi bahasa Inggris. Kompatibilitasnya belum terverifikasi.** Executable dan patch yang sudah terpasang dapat memengaruhi hasil. Sebagian menu runtime dan terjemahan popup masih berbahasa Indonesia; pilihan English pada tools tidak menerjemahkan antarmuka game.

Gunakan backup atau salinan instalasi Inggris. Mulai dengan RAR runtime saja. Pertahankan naskah/aset Inggris Anda; jangan menimpanya dengan `id_Data` Indonesia atau `AdvData` yang belum terverifikasi dari repository ini. Sesuaikan pengaturan dengan lokasi aset Inggris yang kompatibel:

| `DC2PCPatch.ini` pada `[Settings]` | Sumber naskah |
| --- | --- |
| `Language=0` | Jalur asli game; tanpa pengalihan ke folder bahasa. Pengaturan ini tidak menerjemahkan berkas menjadi bahasa Jepang. |
| `Language=1` | `id_Data` Indonesia (default INI bawaan). |
| `Language=2` | Aset Inggris yang kompatibel di `eng_data`, misalnya `eng_data\MES`. Aset ini tidak disertakan. |

Pengaturan tersebut memilih jalur berkas, bukan memperbaiki kompatibilitas. Rilis Inggris yang berbeda mungkin memakai susunan berkas lain. Alur build/pasang terpandu pada tools saat ini menulis ke **`id_Data`**; jangan menganggapnya sebagai installer game Inggris. Untuk pekerjaan Inggris, gunakan MES sumber yang cocok dan periksa hasil yang disimpan terpisah sebelum memasangnya ke folder data Inggris yang tepat.

## Tools terjemahan dan tutorial

Buka `Tools_Terjemahan\DC2PCMesTextTool_GUI.exe`. Antarmuka memakai **English setiap kali aplikasi dibuka**. **Language / Bahasa** mengganti English dan Bahasa Indonesia pada mode terpandu maupun manual. Pergantian mempertahankan isian folder, pilihan proyek, log, dan pengaturan manual. Ini hanya mengganti antarmuka tools.

**Folder proyek awalnya kosong.** Pilih folder kerja baru yang kosong dan terpisah dari game serta MES sumber. Untuk melanjutkan proyek lama, gunakan **Buka proyek...** lalu pilih `proyek.json`.

Alurnya: **Buat proyek + ekspor → edit `03_JSON_EDIT` → Periksa JSON → Impor JSON → MES → Pasang hasil**. Pemasangan hasil membuat backup di `06_BACKUP` milik proyek. Baca tutorial sebelum mengubah struktur JSON:

- [Modul tutorial Bahasa Indonesia](TUTORIAL_INDONESIA.txt)
- [English tutorial module](TUTORIAL_ENGLISH.txt)
- Keduanya dapat dibuka melalui **Tutorial English / Tutorial Indonesia** pada aplikasi.

Python dan IDA tidak diperlukan untuk alur GUI ini. Kode sumber tersedia di [source_code](source_code/README.md).

## Pembaruan dan batas verifikasi

- Teks pilihan memakai spasi proporsional, satu spasi setelah lingkaran, margin kiri 16 piksel, dan penyesuaian font untuk teks panjang. Pengaturan ukuran popup/textbox dipertahankan.
- GUI menyediakan menu dua bahasa, lokasi proyek yang dipilih pengguna, serta dua modul tutorial. Impor memvalidasi struktur JSON/MES dan menolak perubahan yang tidak cocok.
- **Korpus bawaan belum terverifikasi sebagai All Age bersih.** Audit mengonfirmasi sisa konten dewasa pada `ind_0127_f3_kko.mes` dan label cabang sumber rusak pada `ind_0127_f1_nnk.mes` (24 label Indonesia / 12 Jepang). Impor perubahan berkas terakhir ditolak.
- Delapan naskah pengalih dan 25 adegan pengganti tidak membuktikan seluruh naskah, gambar, suara, atau replay sudah bersih. Ekspor/impor tidak menghapus konten dewasa atau memeriksa makna terjemahan. Sumber Jepang All Age resmi yang bersih belum ditetapkan untuk paket ini.
- Rincian audit ada di [STATUS_SUMBER.txt](STATUS_SUMBER.txt). Nama proyek menjelaskan pekerjaan port, bukan sertifikasi bahwa audit konten telah selesai.

## Peta folder

| Lokasi | Isi |
| --- | --- |
| `AdvData/` | Naskah Jepang terpasang dan aset port; edisi belum terverifikasi |
| `id_Data/` | Naskah Indonesia dan peta replay |
| `Tools_Terjemahan/` | Editor siap jalan dan tutorial |
| `source_code/DC2PCMesTextTool_GUI/` | Kode GUI/CLI C# |
| `source_code/DC2PCPatch/` | Patch C++, launcher, dan dependency |
| `source_code/Pipeline_Scripts/` | Skrip port pengembang; bahan eksternal belum lengkap |

Lihat [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) untuk atribusi komponen.

## Pemeriksaan

Persiapan release lulus build .NET tanpa warning/error, 582 pemeriksaan bahasa/status proyek, enam skenario installer, serta pemeriksaan ekstraksi/hash kedua RAR. Hash biner runtime dan editor siap jalan tetap sama dengan paket yang telah diuji.

- [Checksum untuk nama arsip lokal](RELEASE_SHA256SUMS.txt)
- [Checksum untuk nama unduhan GitHub](GITHUB_RELEASE_SHA256SUMS.txt)
