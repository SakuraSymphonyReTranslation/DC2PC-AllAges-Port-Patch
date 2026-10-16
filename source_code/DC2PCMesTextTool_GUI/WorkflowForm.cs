using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace DC2PCMesTextTool_GUI;

public sealed class WorkflowForm : Form
{
    private readonly TranslationWorkflow _flow = new();
    private readonly TextBox _game = new() { Dock = DockStyle.Fill };
    private readonly TextBox _source = new() { Dock = DockStyle.Fill };
    private readonly TextBox _project = new() { Dock = DockStyle.Fill };
    private readonly TextBox _log = new() { Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill };
    private readonly Label _status = new() { AutoSize = true, MaximumSize = new Size(820, 0), Text = "Mulai dengan memilih MES sumber dan folder proyek baru." };
    private readonly ProgressBar _progress = new() { Dock = DockStyle.Bottom, Height = 8, Style = ProgressBarStyle.Marquee, Visible = false };
    private readonly Panel _work = new() { Dock = DockStyle.Fill, AutoScroll = true };
    private bool _busy;
    private bool _refreshingLanguage;
    private bool _hasStatus;
    private readonly ComboBox _language = new() { Name = "LanguageSelector", DropDownStyle = ComboBoxStyle.DropDownList, Width = 190 };
    private readonly ComboBox _basis = new() { Name = "ProjectSource", DropDownStyle = ComboBoxStyle.DropDownList, Dock = DockStyle.Fill };
    private UiCaptions _captions = null!;
    private static readonly string[] BasisKeys = { "Indonesia saat ini — id_Data\\MES", "Jepang terpasang — AdvData\\MES (edisi belum terverifikasi)", "Folder MES lain — pilih sendiri" };

    public WorkflowForm()
    {
        Text = "DC2PC — Alur Ekspor / Impor Terjemahan";
        AutoScaleMode = AutoScaleMode.Dpi;
        Font = new Font("Segoe UI", 10);
        MinimumSize = new Size(880, 680); Size = new Size(1020, 840);
        StartPosition = FormStartPosition.CenterScreen;
        var page = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 3, Padding = new Padding(16) };
        page.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 154));
        page.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        page.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 135));
        int row = 0;
        void Wide(Control c) { page.Controls.Add(c, 0, row++); page.SetColumnSpan(c, 3); }
        Label Hint(string text) => new() { Text = text, AutoSize = true, MaximumSize = new Size(800, 0), Margin = new Padding(0, 4, 0, 12) };
        void PathRow(string title, TextBox box)
        {
            page.Controls.Add(new Label { Text = title, AutoSize = true, Anchor = AnchorStyles.Left }, 0, row);
            page.Controls.Add(box, 1, row);
            var browse = new Button { Text = "Pilih folder...", Dock = DockStyle.Fill, AutoSize = true };
            browse.Click += (_, _) => { using var dialog = new FolderBrowserDialog { Description = UiText.T("Pilih folder"), UseDescriptionForTitle = true, InitialDirectory = Directory.Exists(box.Text) ? box.Text : "" }; if (dialog.ShowDialog(this) == DialogResult.OK) box.Text = dialog.SelectedPath; };
            page.Controls.Add(browse, 2, row++);
        }
        FlowLayoutPanel Actions(params (string title, Action action)[] actions)
        {
            var p = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, WrapContents = true, Margin = new Padding(0, 3, 0, 10) };
            foreach (var (title, action) in actions)
            {
                var button = new Button { Text = title, AutoSize = true, Padding = new Padding(6, 3, 6, 3), Margin = new Padding(0, 0, 8, 6) };
                button.Click += (_, _) => { try { action(); } catch (Exception ex) { MessageBox.Show(this, ex.Message, UiText.T("Periksa langkah ini"), MessageBoxButtons.OK, MessageBoxIcon.Information); } };
                p.Controls.Add(button);
            }
            return p;
        }
        _language.Items.AddRange(new object[] { "English", "Bahasa Indonesia" });
        var languageRow = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 10) };
        languageRow.Controls.Add(new Label { Text = "Language / Bahasa", AutoSize = true, Margin = new Padding(0, 5, 12, 0) });
        languageRow.Controls.Add(_language);
        foreach (var (title, file) in new[] { ("Tutorial English", "TUTORIAL_ENGLISH.txt"), ("Tutorial Indonesia", "TUTORIAL_INDONESIA.txt") })
        {
            var tutorial = new Button { Text = title, AutoSize = true, Margin = new Padding(12, 0, 0, 0), Padding = new Padding(5, 0, 5, 0) };
            tutorial.Click += (_, _) => { try { OpenDoc(file); } catch (Exception ex) { MessageBox.Show(this, ex.Message, UiText.T("Periksa langkah ini"), MessageBoxButtons.OK, MessageBoxIcon.Information); } };
            languageRow.Controls.Add(tutorial);
        }
        Wide(languageRow);
        Wide(new Label { Text = "Dari MES ke JSON, lalu kembali ke game", Font = new Font(Font, FontStyle.Bold), AutoSize = true });
        Wide(Hint("Ikuti langkah 1–5. Untuk memperbaiki terjemahan yang sekarang, pilih basis Indonesia. Proyek lama dapat dilanjutkan lewat Buka proyek."));
        PathRow("Folder utama game", _game);
        var basis = _basis;
        basis.Items.AddRange(BasisKeys);
        page.Controls.Add(new Label { Text = "Basis proyek", AutoSize = true, Anchor = AnchorStyles.Left }, 0, row);
        page.Controls.Add(basis, 1, row++); page.SetColumnSpan(basis, 2);
        void SetSource() { if (!_refreshingLanguage && !string.IsNullOrWhiteSpace(_game.Text) && basis.SelectedIndex is 0 or 1) _source.Text = Path.Combine(_game.Text, basis.SelectedIndex == 0 ? "id_Data" : "AdvData", "MES"); }
        basis.SelectedIndexChanged += (_, _) => SetSource();
        _game.TextChanged += (_, _) => SetSource();
        PathRow("MES sumber", _source);
        Wide(Hint("Ekspor/impor mempertahankan isi sumber; proses ini tidak mengubah edisi menjadi All Age. Audit instalasi ini menemukan sisa konten 18+ di AdvData\\MES. Baca STATUS_SUMBER.txt sebelum menjadikannya acuan All Age."));
        PathRow("Folder proyek", _project);
        Wide(Hint("Pilih folder kerja kosong untuk proyek baru, atau klik Buka proyek untuk melanjutkan proyek yang memiliki proyek.json. Folder proyek bukan folder utama game."));
        Wide(Actions(("1. Buat proyek + ekspor", () => { string s = _source.Text, p = _project.Text; _ = Run(() => _flow.Prepare(s, p)); }),
            ("Buka proyek...", OpenProject)));
        Wide(Hint("2. Edit hanya isi message/name di 03_JSON_EDIT. Pertahankan nama file, urutan entri, dan ○. JSON 18+ perlu dicocokkan per teks/konteks; jangan langsung mengganti seluruh folder."));
        Wide(Actions(("2. Buka JSON untuk diedit", () => OpenFolder(TranslationWorkflow.EditDir)),
            ("Buka JSON acuan", () => OpenFolder(TranslationWorkflow.JsonDir))));
        Wide(Actions(("3. Periksa JSON", () => { string p = _project.Text; _ = Run(() => _flow.Validate(p)); }),
            ("4. Impor JSON → MES", () => { string p = _project.Text; _ = Run(() => _flow.Build(p)); }),
            ("Lihat hasil", () => OpenFolder(TranslationWorkflow.BuildsDir))));
        Wide(Hint("5. Tutup game sebelum memasang. Hanya file MES yang diedit beserta peta replay terkait yang disalin ke id_Data; backup dibuat lebih dahulu. Setelah itu uji adegan, pilihan, save/load, dan replay yang Anda ubah."));
        Wide(Actions(("5. Pasang hasil ke game", () => { string p = _project.Text, g = _game.Text; _ = Run(() => _flow.Deploy(p, g)); }),
            ("Buka backup", () => OpenFolder(TranslationWorkflow.BackupsDir)),
            ("Buka laporan", () => OpenFolder(TranslationWorkflow.LogsDir))));
        Wide(Actions(("Daftar skrip Python", () => OpenDoc("PETA_PIPELINE.txt")),
            ("Cek bahan pipeline", () => { _log.Text = PipelineAudit.Describe(); }),
            ("Mode manual", () => { using var form = new MainForm(); form.ShowDialog(this); })));
        Wide(_status);
        _work.Controls.Add(page);
        var root = new TableLayoutPanel { Dock = DockStyle.Fill, RowCount = 2 };
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100)); root.RowStyles.Add(new RowStyle(SizeType.Absolute, 160));
        root.Controls.Add(_work, 0, 0); root.Controls.Add(_log, 0, 1);
        Controls.Add(root); Controls.Add(_progress);
        _flow.Log += s => { if (!IsDisposed) BeginInvoke(new Action(() => { _log.AppendText(s + Environment.NewLine); _status.Text = s; _hasStatus = true; })); };
        FormClosing += (_, e) => { if (_busy) { e.Cancel = true; _status.Text = UiText.T("Proses masih berjalan. Tunggu sampai selesai agar berkas tidak terputus."); } };
        string game = FindGame();
        _game.Text = game; basis.SelectedIndex = 0;
        // Project location is an explicit user choice; do not guess a Documents/OneDrive path.
        _captions = new UiCaptions(this, _status);
        _language.SelectedIndexChanged += (_, _) => { if (!_refreshingLanguage && _language.SelectedIndex >= 0) UiText.Language = (InterfaceLanguage)_language.SelectedIndex; };
        UiText.LanguageChanged += RefreshLanguage;
        Disposed += (_, _) => UiText.LanguageChanged -= RefreshLanguage;
        RefreshLanguage();
    }

    private void RefreshLanguage()
    {
        _refreshingLanguage = true;
        SuspendLayout();
        _basis.BeginUpdate();
        try
        {
            _captions.Refresh();
            _language.SelectedIndex = (int)UiText.Language;
            _project.PlaceholderText = UiText.T("Pilih folder proyek sendiri...");
            int selected = _basis.SelectedIndex;
            _basis.Items.Clear();
            _basis.Items.AddRange(BasisKeys.Select(UiText.T).ToArray());
            _basis.SelectedIndex = selected;
            if (!_hasStatus) _status.Text = UiText.T("Mulai dengan memilih MES sumber dan folder proyek baru.");
        }
        finally { _basis.EndUpdate(); ResumeLayout(true); _refreshingLanguage = false; }
    }

    private async Task Run(Action action)
    {
        if (_busy) return;
        _busy = true; _hasStatus = true; _work.Enabled = false; _progress.Visible = true; _log.Clear();
        try { await Task.Run(action); }
        catch (Exception ex) { _log.AppendText(UiText.T("Belum selesai: ") + ex.Message + Environment.NewLine); _status.Text = UiText.T("Perlu diperbaiki: ") + ex.Message; }
        finally { _busy = false; _work.Enabled = true; _progress.Visible = false; }
    }
    private void OpenProject()
    {
        using var dialog = new OpenFileDialog { Title = UiText.T("Buka proyek terjemahan"), Filter = UiText.T("Proyek terjemahan (proyek.json)") + "|proyek.json" };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        string folder = Path.GetDirectoryName(dialog.FileName)!;
        var m = _flow.Load(folder); _project.Text = folder; _source.Text = m.SourceMes;
        _hasStatus = true;
        _status.Text = UiText.Format("Proyek dibuka: {0} file. Lanjutkan edit, periksa JSON, atau buat MES.", m.MesHashes.Count);
    }
    private void OpenFolder(string folder)
    {
        if (string.IsNullOrWhiteSpace(_project.Text))
            throw new InvalidOperationException(UiText.T("Pilih folder proyek atau buka proyek.json dahulu."));
        string target = Path.Combine(_project.Text, folder);
        if (!Directory.Exists(target)) throw new DirectoryNotFoundException(UiText.T("Folder belum ada. Buat atau buka proyek dahulu."));
        Process.Start(new ProcessStartInfo(target) { UseShellExecute = true });
    }
    private static void OpenDoc(string name)
    {
        string path = Path.Combine(AppContext.BaseDirectory, name);
        if (!File.Exists(path)) throw new FileNotFoundException(UiText.T("Panduan belum ada di sebelah aplikasi: ") + name);
        Process.Start(new ProcessStartInfo(path) { UseShellExecute = true });
    }
    private static string FindGame()
    {
        for (DirectoryInfo? d = new DirectoryInfo(AppContext.BaseDirectory); d is not null; d = d.Parent)
            if (File.Exists(Path.Combine(d.FullName, "DC2PC.EXE"))) return d.FullName;
        return "";
    }
}

internal static class PipelineAudit
{
    public static string Describe()
    {
        string? scripts = null;
        for (DirectoryInfo? d = new DirectoryInfo(AppContext.BaseDirectory); d is not null && scripts is null; d = d.Parent)
            foreach (string candidate in new[] { Path.Combine(d.FullName, "Pipeline_Scripts"), Path.Combine(d.FullName, "source_code", "Pipeline_Scripts") })
                if (Directory.Exists(candidate)) { scripts = candidate; break; }
        if (scripts is null) return UiText.T("Pipeline_Scripts tidak ditemukan. Alur GUI tetap dapat dipakai tanpa Python. Baca PETA_PIPELINE.txt.");
        string root = Path.GetDirectoryName(scripts)!;
        var lines = new List<string> { UiText.T("Pemeriksaan bahan (tidak menjalankan skrip)"), "Folder: " + scripts, "", UiText.T("GUI ekspor/impor memakai .NET 8, tidak memerlukan Python."), UiText.T("Bahan untuk rebuild_all_scripts.py:") };
        foreach (string name in new[] { "DC2PC/AdvData/MES", "PS2_extracted/DAT/MES.DAT", "opcode_map_final.json", "allages_wording_diffs.json", "cg_map.json", "ALLAGES/AdvData/MES" })
        {
            string p = Path.Combine(root, name.Replace('/', Path.DirectorySeparatorChar));
            lines.Add((File.Exists(p) || Directory.Exists(p) ? UiText.T("[ADA] ") : UiText.T("[BELUM ADA] ")) + p);
        }
        lines.AddRange(new[] { "", UiText.T("Pemeriksaan ini hanya memeriksa keberadaan; isi mapping/CG juga harus sesuai."),
            UiText.T("apply_translations_to_ss_json.py masih mengacu E:/projek atho/dc2ps dan modul dc2_transfer yang tidak dibundel."),
            UiText.T("patch_final_226.py / patch_final_6.py menimpa naskah dengan indeks dari proyek lama. Tidak dijalankan oleh alur GUI."),
            UiText.T("Baca PETA_PIPELINE.txt untuk masukan, keluaran, dan urutan pipeline khusus.") });
        return string.Join(Environment.NewLine, lines);
    }
}
