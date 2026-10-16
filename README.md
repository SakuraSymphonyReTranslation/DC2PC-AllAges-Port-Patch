# DC2PC AllAges Port Patch

**[English](README.md)** | [Bahasa Indonesia](README.id.md)

Patch runtime, an All Age port work in progress, Indonesian script data, and bilingual translation tools for **Da Capo 2 Plus Communication All Age**. This project is published in its own repository.

## Downloads

Get the two archives from [Releases](https://github.com/SakuraSymphonyReTranslation/DC2PC-AllAges-Port-Patch/releases/latest):

| Archive | Contents and purpose |
| --- | --- |
| `DC2PC_AllAges_Patch DLL + Executable.rar` | Launcher, patch DLL, INI, two Locale Emulator DLLs, bilingual installation guide, and third-party notices. The executable is **DC2PCLauncher.exe**; the base game executable is not included. |
| `Tools_Terjemahan_or_Translate.rar` | Ready-to-run MES/JSON editor with its DLL/config files, English and Indonesian tutorial modules, and guides. Requires **.NET 8 Desktop Runtime for Windows**. |

GitHub replaces spaces in asset filenames with dots. The runtime asset keeps the display label above, but downloads as `DC2PC_AllAges_Patch.DLL.+.Executable.rar`; its contents are identical to the locally named archive.

Neither RAR contains the `AdvData` / `id_Data` script folders. For the bundled Indonesian port data, download this repository using **Code > Download ZIP**, or select **Source code (zip)** on the release page. You still need an installed copy of the game containing `DC2PC.EXE` and its original assets. This repository is not a complete game installation.

## Install the bundled Indonesian data

1. Close the game and back up the installation, including files you will overwrite.
2. Extract the repository ZIP into a separate folder. Copy `AdvData`, `id_Data`, `DC2PCLauncher.exe`, `DC2PCPatch.dll`, `DC2PCPatch.ini`, `LoaderDll.dll`, and `LocaleEmulator.dll` into the game folder containing `DC2PC.EXE`.
3. Keep the game's other required files and libraries. The included INI uses `[Settings] Language=1` for `id_Data`.
4. Start `DC2PCLauncher.exe` from that game folder. Test dialogue, choices, branches, replay, and save/load.

The optional `PASANG_PATCH_OTOMATIS.bat` copies the same payload and reports copy failures. It requires the full repository/package, does not create a backup, and is for the bundled Indonesian data. Manual installation is described in [INSTALL_EN_ID.txt](INSTALL_EN_ID.txt).

## Trying the English version

**This patch can be tried with the English version of Da Capo 2 Plus Communication All Age. Compatibility has not yet been verified.** Different executables and existing patches may behave differently. Some runtime menus and popup translations remain Indonesian; selecting English in the translation tool does not translate the game's interface.

Use a backup or separate copy of the English installation. Start with the runtime RAR only. Keep your existing English scripts/assets; do not copy this repository's Indonesian `id_Data` or unverified `AdvData` over them. Select runtime settings according to where your compatible English assets are located:

| `DC2PCPatch.ini` under `[Settings]` | Script source |
| --- | --- |
| `Language=0` | Original game paths; no language-folder redirection. It does not translate those files into Japanese. |
| `Language=1` | Indonesian `id_Data` (included INI default). |
| `Language=2` | Compatible English assets in `eng_data`, such as `eng_data\MES`. These assets are not included. |

These are routing settings, not a compatibility fix. Existing English releases may store files differently. The guided tool's build/install workflow currently targets **`id_Data`**; it must not be treated as an English-game installer. For English work, use matching source MES and review separately saved output before applying it to the appropriate English data folder.

## Translation tool and tutorials

Open `Tools_Terjemahan\DC2PCMesTextTool_GUI.exe`. The interface starts in **English on each launch**; **Language / Bahasa** switches between English and Bahasa Indonesia in both guided and manual modes. Switching preserves entered paths, project selections, logs, and manual settings. It changes only the tool interface.

**Project folder starts empty.** Choose your own new, empty working folder, separate from the game and source MES folders. To continue existing work, use **Open project...** and select `proyek.json`.

Follow: **Create project + export → edit `03_JSON_EDIT` → Validate JSON → Import JSON → MES → Install output to game**. Installing edited output creates a backup in the project's `06_BACKUP`. Read the tutorials before modifying JSON structure:

- [English tutorial module](TUTORIAL_ENGLISH.txt)
- [Modul tutorial Bahasa Indonesia](TUTORIAL_INDONESIA.txt)
- Both modules are available through **Tutorial English / Tutorial Indonesia** in the app.

Python and IDA are not required for this GUI workflow. The source code is in [source_code](source_code/README.md).

## Current changes and limits

- Choice text uses proportional spacing, one space after the circle marker, a 16-pixel left margin, and font adjustment for long text. Existing popup/textbox sizing settings are retained.
- The GUI has bilingual menus, an explicit project location, and two tutorial modules. Imports validate JSON/MES structure and reject incompatible edits.
- **The bundled corpus is not verified as clean All Age content.** The audit confirmed remaining adult content in `ind_0127_f3_kko.mes` and invalid source branch labels in `ind_0127_f1_nnk.mes` (24 Indonesian / 12 Japanese labels). Edited imports of the latter are rejected.
- Eight jump stubs and 25 replacement scenes do not establish that every script, image, audio file, or replay is clean. Export/import does not remove adult content or verify translation meaning. A clean official Japanese All Age source has not been established for this package.
- See [STATUS_SUMBER.txt](STATUS_SUMBER.txt) for the detailed Indonesian audit. The project title describes the port effort, not a completed content certification.

## Folder map

| Path | Contents |
| --- | --- |
| `AdvData/` | Installed Japanese scripts and port assets; edition unverified |
| `id_Data/` | Indonesian scripts and replay maps |
| `Tools_Terjemahan/` | Ready-to-run editor and tutorials |
| `source_code/DC2PCMesTextTool_GUI/` | C# GUI/CLI source |
| `source_code/DC2PCPatch/` | C++ patch, launcher, and dependencies |
| `source_code/Pipeline_Scripts/` | Developer port scripts; external inputs are incomplete |

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for component attribution.

## Verification

The release preparation passed a .NET build with zero warnings/errors, 582 language/project-state assertions, six installer scenarios, and extraction/hash checks for both RAR archives. Runtime and ready-to-run editor binaries retain the tested package's hashes.

- [Checksums for local archive filenames](RELEASE_SHA256SUMS.txt)
- [Checksums for GitHub download filenames](GITHUB_RELEASE_SHA256SUMS.txt)
