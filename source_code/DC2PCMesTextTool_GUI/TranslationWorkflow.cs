using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using DC2PCMesTextTool;

namespace DC2PCMesTextTool_GUI;

public sealed class WorkflowManifest
{
    public int Version { get; set; } = 1;
    public string SourceMes { get; set; } = "";
    public Dictionary<string, string> MesHashes { get; set; } = new();
    public Dictionary<string, string> JsonHashes { get; set; } = new();
    public string CreatedUtc { get; set; } = DateTime.UtcNow.ToString("O");
}

public sealed class WorkflowBuild
{
    public string DirectoryName { get; set; } = "";
    public Dictionary<string, string> JsonHashes { get; set; } = new();
    public Dictionary<string, string> OutputHashes { get; set; } = new();
    public List<string> ChangedMes { get; set; } = new();
}

public sealed class TranslationWorkflow
{
    public const string ManifestName = "proyek.json";
    public const string MesDir = "01_MES_SUMBER";
    public const string JsonDir = "02_JSON_ASLI";
    public const string EditDir = "03_JSON_EDIT";
    public const string BuildsDir = "04_HASIL";
    public const string LogsDir = "05_LAPORAN";
    public const string BackupsDir = "06_BACKUP";
    public event Action<string>? Log;
    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true };
    private void Say(string text) => Log?.Invoke(text);
    public static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
    private static void Save<T>(string path, T value) => File.WriteAllText(path, JsonSerializer.Serialize(value, Options));
    private static string Stamp() => DateTime.Now.ToString("yyyyMMdd_HHmmss_fff") + "_" + Guid.NewGuid().ToString("N")[..6];
    private static string Full(string path) => Path.TrimEndingDirectorySeparator(Path.GetFullPath(path));
    private static bool Inside(string child, string parent) => Full(child).Equals(Full(parent), StringComparison.OrdinalIgnoreCase)
        || Full(child).StartsWith(Full(parent) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);
    private static void SimpleName(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || Path.GetFileName(name) != name || name is "." or "..")
            throw new InvalidDataException(UiText.T("Nama file/folder dalam catatan proyek tidak valid."));
    }
    private static Dictionary<string, string> Files(string directory, string pattern) => Directory.GetFiles(directory, pattern)
        .OrderBy(p => p, StringComparer.OrdinalIgnoreCase).ToDictionary(p => Path.GetFileName(p), p => p, StringComparer.OrdinalIgnoreCase);

    public WorkflowManifest Load(string project)
    {
        if (string.IsNullOrWhiteSpace(project))
            throw new InvalidDataException(UiText.T("Pilih folder proyek atau buka proyek.json dahulu."));
        if (!File.Exists(Path.Combine(project, ManifestName)))
            throw new FileNotFoundException(UiText.T("Catatan proyek tidak ditemukan. Buat atau buka proyek dahulu."));
        var m = JsonSerializer.Deserialize<WorkflowManifest>(File.ReadAllText(Path.Combine(project, ManifestName)))
            ?? throw new InvalidDataException(UiText.T("Catatan proyek tidak terbaca."));
        if (m.Version != 1 || m.MesHashes.Count == 0) throw new InvalidDataException(UiText.T("Versi/proyek tidak valid."));
        foreach (var name in m.MesHashes.Keys.Concat(m.JsonHashes.Keys)) SimpleName(name);
        return m;
    }

    public void Prepare(string source, string project)
    {
        if (string.IsNullOrWhiteSpace(source))
            throw new InvalidDataException(UiText.T("Pilih folder MES sumber dahulu."));
        if (string.IsNullOrWhiteSpace(project))
            throw new InvalidDataException(UiText.T("Pilih folder kerja kosong untuk proyek baru dahulu."));
        source = Full(source); project = Full(project);
        if (!Directory.Exists(source)) throw new DirectoryNotFoundException(UiText.T("Folder MES sumber tidak ditemukan."));
        if (Inside(project, source) || Inside(source, project)) throw new InvalidDataException(UiText.T("Folder proyek harus terpisah dari folder MES sumber."));
        if (Directory.Exists(project) && Directory.EnumerateFileSystemEntries(project).Any())
            throw new InvalidDataException(UiText.T("Pilih folder proyek baru yang kosong. Untuk proyek lama gunakan Buka proyek."));
        var files = Files(source, "*.mes");
        if (files.Count == 0) throw new InvalidDataException(UiText.T("Folder sumber tidak memiliki file .mes langsung di dalamnya."));
        foreach (string folder in new[] { MesDir, JsonDir, EditDir, BuildsDir, LogsDir, BackupsDir })
            Directory.CreateDirectory(Path.Combine(project, folder));
        var manifest = new WorkflowManifest { SourceMes = source };
        var processor = new MesToolProcessor();
        using var log = new StreamWriter(Path.Combine(project, LogsDir, "ekspor.txt"));
        processor.Log += s => log.WriteLine(s);
        int n = 0;
        foreach (var (name, path) in files)
        {
            string copy = Path.Combine(project, MesDir, name), jsonName = Path.ChangeExtension(name, ".json");
            string json = Path.Combine(project, JsonDir, jsonName);
            File.Copy(path, copy);
            if (processor.ExportMesToJson(copy, json) != 0) throw new InvalidDataException(UiText.Format("Ekspor {0} gagal. Lihat 05_LAPORAN/ekspor.txt; gunakan folder proyek baru setelah memperbaiki sumber.", name));
            File.Copy(json, Path.Combine(project, EditDir, jsonName));
            manifest.MesHashes[name] = Hash(copy);
            manifest.JsonHashes[jsonName] = Hash(json);
            if (++n % 100 == 0 || n == files.Count) Say(UiText.Format("Ekspor {0}/{1} file...", n, files.Count));
        }
        // Keep existing replay map rows available when a replay title is edited later.
        foreach (string name in new[] { "replay_titles.tsv", "replay_display_titles.tsv" })
        {
            string direct = Path.Combine(source, name);
            string parent = Path.Combine(Path.GetDirectoryName(source)!, name);
            string candidate = File.Exists(direct) ? direct : parent;
            if (File.Exists(candidate)) File.Copy(candidate, Path.Combine(project, MesDir, name));
        }
        Save(Path.Combine(project, ManifestName), manifest);
        File.WriteAllText(Path.Combine(project, "MULAI_DI_SINI.txt"),
            UiText.T("Edit hanya JSON dalam 03_JSON_EDIT. Pertahankan nama file, urutan, jumlah entri, kolom name/message, dan penanda ○.\r\n") +
            UiText.T("Buka proyek ini di DC2PCMesTextTool_GUI.exe: Periksa JSON > Buat MES > Pasang hasil.\r\n") +
            UiText.T("01_MES_SUMBER dan 02_JSON_ASLI adalah salinan acuan; jangan diedit. File [] adalah naskah tanpa teks.\r\n") +
            UiText.T("JSON edisi lain tidak boleh ditempel massal berdasarkan nomor baris. Cocokkan teks/konteks dengan MES sumber.\r\n") +
            UiText.T("Ekspor/impor tidak memverifikasi edisi atau membuang konten 18+. Gunakan sumber yang telah diaudit bila menargetkan All Age.\r\n"));
        Say(UiText.Format("Proyek siap: {0} file. Edit teks di {1}.", files.Count, Path.Combine(project, EditDir)));
    }

    public int Validate(string project)
    {
        var m = Load(project);
        var errors = new List<string>();
        var edits = Files(Path.Combine(project, EditDir), "*.json");
        if (Directory.GetFiles(Path.Combine(project, EditDir), "*.json", SearchOption.AllDirectories).Length != edits.Count)
            errors.Add(UiText.T("Ada JSON dalam subfolder. Taruh file langsung di 03_JSON_EDIT; subfolder tidak diimpor."));
        foreach (var extra in edits.Keys.Except(m.JsonHashes.Keys, StringComparer.OrdinalIgnoreCase)) errors.Add(UiText.Format("{0}: bukan bagian proyek sumber.", extra));
        int changed = 0, count = 0;
        foreach (var (name, hash) in m.MesHashes)
        {
            string jsonName = Path.ChangeExtension(name, ".json");
            try
            {
                if (Hash(Path.Combine(project, MesDir, name)) != hash) throw new InvalidDataException(UiText.T("Salinan MES sumber berubah."));
                string original = Path.Combine(project, JsonDir, jsonName);
                if (!m.JsonHashes.TryGetValue(jsonName, out var expected) || Hash(original) != expected)
                    throw new InvalidDataException(UiText.T("JSON acuan berubah."));
                if (!edits.TryGetValue(jsonName, out string? edited)) throw new InvalidDataException(UiText.T("JSON edit hilang."));
                var a = ImportValidation.Read(original); var b = ImportValidation.Read(edited);
                ImportValidation.Compare(a, b);
                if (!ImportValidation.Same(a, b))
                {
                    // Diagnose corrupt source branches before any output is built.
                    string mes = Path.Combine(project, MesDir, name);
                    ImportValidation.VerifyMes(mes, mes);
                    changed++;
                }
            }
            catch (Exception ex) { errors.Add($"{jsonName}: {ex.Message}"); }
            if (++count % 250 == 0) Say(UiText.Format("Memeriksa {0}/{1} file...", count, m.MesHashes.Count));
        }
        Directory.CreateDirectory(Path.Combine(project, LogsDir));
        Save(Path.Combine(project, LogsDir, "validasi.json"), new { files = m.MesHashes.Count, changedFiles = changed, errors });
        if (errors.Count > 0) throw new InvalidDataException(UiText.Format("{0} masalah. {1}\nRincian: 05_LAPORAN/validasi.json", errors.Count, errors[0]));
        Say(UiText.Format("Pemeriksaan lulus: {0} file, {1} file diedit. Kecocokan makna/urutan tetap perlu diperiksa manusia.", m.MesHashes.Count, changed));
        return changed;
    }

    public string Build(string project)
    {
        Validate(project);
        var m = Load(project);
        var build = new WorkflowBuild { DirectoryName = "build_" + Stamp() };
        string root = Path.Combine(project, BuildsDir, build.DirectoryName);
        string target = Path.Combine(root, "id_Data", "MES");
        Directory.CreateDirectory(target);
        foreach (string name in new[] { "replay_titles.tsv", "replay_display_titles.tsv" })
            if (File.Exists(Path.Combine(project, MesDir, name))) File.Copy(Path.Combine(project, MesDir, name), Path.Combine(root, "id_Data", name));
        var processor = new MesToolProcessor();
        using var log = new StreamWriter(Path.Combine(root, "impor.txt"));
        processor.Log += s => log.WriteLine(s);
        int count = 0;
        foreach (var name in m.MesHashes.Keys)
        {
            string jsonName = Path.ChangeExtension(name, ".json");
            string json = Path.Combine(project, EditDir, jsonName);
            string source = Path.Combine(project, MesDir, name), output = Path.Combine(target, name);
            string inputHash = Hash(json);
            bool changed = !ImportValidation.Same(ImportValidation.Read(Path.Combine(project, JsonDir, jsonName)), ImportValidation.Read(json));
            if (changed)
            {
                if (processor.ImportJsonToMes(json, source, output) != 0) throw new InvalidDataException(UiText.Format("Impor {0} gagal; lihat {1}/impor.txt. Hasil belum dapat dipasang.", name, root));
                try { ImportValidation.VerifyMes(source, output); }
                catch (InvalidDataException ex) { throw new InvalidDataException(UiText.Format("{0}: {1} Hasil belum dapat dipasang.", name, ex.Message), ex); }
                build.ChangedMes.Add(name);
            }
            else File.Copy(source, output);
            if (Hash(json) != inputHash) throw new InvalidDataException(UiText.Format("{0} diedit ketika build berjalan. Ulangi Buat MES setelah selesai mengedit.", jsonName));
            build.JsonHashes[jsonName] = inputHash;
            build.OutputHashes[Path.Combine("MES", name)] = Hash(output);
            if (++count % 100 == 0 || count == m.MesHashes.Count) Say(UiText.Format("Membuat MES {0}/{1}...", count, m.MesHashes.Count));
        }
        if (build.ChangedMes.Any(n => n.StartsWith("sce_", StringComparison.OrdinalIgnoreCase)))
            foreach (string name in new[] { "replay_titles.tsv", "replay_display_titles.tsv" })
                if (File.Exists(Path.Combine(root, "id_Data", name))) build.OutputHashes[name] = Hash(Path.Combine(root, "id_Data", name));
        // A later edit during the run must invalidate the build too.
        foreach (var (name, hash) in build.JsonHashes)
            if (Hash(Path.Combine(project, EditDir, name)) != hash) throw new InvalidDataException(UiText.T("JSON berubah selama build. Ulangi Buat MES."));
        Save(Path.Combine(root, "hasil.json"), build);
        Save(Path.Combine(project, "hasil_terakhir.json"), build);
        Say(UiText.Format("MES siap: {0} file berubah. Hasil: {1}. Game belum diubah.", build.ChangedMes.Count, root));
        return root;
    }

    public string Deploy(string project, string game)
    {
        Validate(project);
        game = Full(game);
        if (!File.Exists(Path.Combine(game, "DC2PC.EXE"))) throw new InvalidDataException(UiText.T("Pilih folder utama game yang memiliki DC2PC.EXE."));
        if (Process.GetProcessesByName("DC2PC").Any()) throw new InvalidOperationException(UiText.T("Tutup game DC2PC terlebih dahulu, lalu tekan Pasang hasil lagi."));
        if (Inside(project, Path.Combine(game, "id_Data"))) throw new InvalidDataException(UiText.T("Folder proyek tidak boleh berada di dalam id_Data."));
        var build = JsonSerializer.Deserialize<WorkflowBuild>(File.ReadAllText(Path.Combine(project, "hasil_terakhir.json")))!;
        SimpleName(build.DirectoryName);
        string root = Path.Combine(project, BuildsDir, build.DirectoryName, "id_Data");
        foreach (var (name, hash) in build.JsonHashes)
        {
            SimpleName(name);
            if (Hash(Path.Combine(project, EditDir, name)) != hash) throw new InvalidDataException(UiText.T("JSON berubah sejak build terakhir. Tekan Buat MES lagi."));
        }
        foreach (var (name, hash) in build.OutputHashes)
        {
            if (!Inside(Path.Combine(root, name), root) || Hash(Path.Combine(root, name)) != hash)
                throw new InvalidDataException(UiText.T("File hasil berubah. Tekan Buat MES lagi."));
        }
        if (build.ChangedMes.Count == 0) { Say(UiText.T("Tidak ada file diedit; tidak ada yang perlu dipasang.")); return ""; }
        var files = build.ChangedMes.Select(n => { SimpleName(n); return Path.Combine("MES", n); }).ToList();
        files.AddRange(build.OutputHashes.Keys.Where(n => n.EndsWith(".tsv", StringComparison.OrdinalIgnoreCase)));
        if (files.Any(n => !build.OutputHashes.ContainsKey(n))) throw new InvalidDataException(UiText.T("Daftar hasil tidak lengkap. Buat MES ulang."));
        string backup = Path.Combine(project, BackupsDir, "pasang_" + Stamp());
        Directory.CreateDirectory(backup);
        var existed = new Dictionary<string, bool>();
        // Complete backups before any game file is changed.
        foreach (string name in files)
        {
            string destination = Path.Combine(game, "id_Data", name);
            existed[name] = File.Exists(destination);
            if (existed[name])
            {
                string copy = Path.Combine(backup, "id_Data", name);
                Directory.CreateDirectory(Path.GetDirectoryName(copy)!);
                File.Copy(destination, copy);
            }
        }
        Save(Path.Combine(backup, "pemasangan.json"), new { game, existed, sourceBuild = build.DirectoryName });
        var written = new List<string>();
        try
        {
            foreach (string name in files)
            {
                string destination = Path.Combine(game, "id_Data", name);
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                written.Add(name);
                File.Copy(Path.Combine(root, name), destination, true);
                if (Hash(destination) != build.OutputHashes[name]) throw new IOException(UiText.Format("Salinan gagal diverifikasi: {0}", name));
            }
        }
        catch (Exception ex)
        {
            var rollbackErrors = new List<string>();
            foreach (string name in written)
            {
                try
                {
                    string destination = Path.Combine(game, "id_Data", name);
                    if (existed[name]) File.Copy(Path.Combine(backup, "id_Data", name), destination, true);
                    else File.Delete(destination);
                }
                catch (Exception restoreError) { rollbackErrors.Add(name + ": " + restoreError.Message); }
            }
            Save(Path.Combine(backup, "gagal.json"), new { error = ex.Message, rollbackErrors });
            throw new IOException(UiText.Format("Pemasangan gagal: {0}. Pemulihan otomatis: {1}. Backup: {2}", ex.Message,
                rollbackErrors.Count == 0 ? UiText.T("selesai") : UiText.T("perlu pemulihan manual"), backup), ex);
        }
        File.WriteAllText(Path.Combine(backup, "PULIHKAN.txt"), UiText.T("Tutup game. Salin isi folder id_Data di backup ini ke ") + game + UiText.T("\\id_Data dengan timpa file.\r\nLihat pemasangan.json: file dengan existed=false adalah file baru, hapus file itu jika ingin pulih sepenuhnya.\r\n"));
        Say(UiText.Format("Terpasang: {0} MES dan {1} peta replay. Backup: {2}. Jalankan launcher dan uji adegan yang diubah.", build.ChangedMes.Count, files.Count - build.ChangedMes.Count, backup));
        return backup;
    }
}

internal static class WorkflowCli
{
    public static int Run(string[] args)
    {
        var flow = new TranslationWorkflow(); flow.Log += Console.WriteLine;
        try
        {
            switch (args[0].ToLowerInvariant())
            {
                case "project-create" when args.Length == 3: flow.Prepare(args[1], args[2]); break;
                case "project-check" when args.Length == 2: flow.Validate(args[1]); break;
                case "project-build" when args.Length == 2: flow.Build(args[1]); break;
                case "project-deploy" when args.Length == 3: flow.Deploy(args[1], args[2]); break;
                default: throw new ArgumentException("project-create <folder-MES> <proyek-baru> | project-check <proyek> | project-build <proyek> | project-deploy <proyek> <folder-game>");
            }
            return 0;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.Message); return 1; }
    }
}
