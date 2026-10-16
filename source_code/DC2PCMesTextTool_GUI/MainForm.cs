using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using DC2PCMesTextTool;

namespace DC2PCMesTextTool_GUI
{
    public partial class MainForm : Form
    {
        private readonly MesToolProcessor _processor;
        private bool _busy;
        private UiCaptions _captions = null!;
        private readonly ComboBox _language = new() { Name = "LanguageSelector", DropDownStyle = ComboBoxStyle.DropDownList, Width = 180 };
        private TextBox _logBox = null!;
        
        // Single File Controls
        private TextBox _txtSingleInput = null!;
        private TextBox _txtSingleOutput = null!;
        private NumericUpDown _numSingleWrap = null!;

        // Batch Controls
        private TextBox _txtBatchInput = null!;
        private TextBox _txtBatchOutput = null!;
        private TextBox _txtBatchMesInput = null!;
        private NumericUpDown _numBatchWrap = null!;

        public MainForm()
        {
            InitializeComponent();
            _processor = new MesToolProcessor();
            _processor.Log += LogMessage;
            FormClosing += (_, e) => { if (_busy) e.Cancel = true; };
            _captions = new UiCaptions(this);
            _language.SelectedIndexChanged += (_, _) => { if (_language.SelectedIndex >= 0) UiText.Language = (InterfaceLanguage)_language.SelectedIndex; };
            UiText.LanguageChanged += RefreshLanguage;
            Disposed += (_, _) => UiText.LanguageChanged -= RefreshLanguage;
            RefreshLanguage();
        }

        private void RefreshLanguage()
        {
            SuspendLayout();
            try { _captions.Refresh(); _language.SelectedIndex = (int)UiText.Language; }
            finally { ResumeLayout(true); }
        }

        private void LogMessage(string message)
        {
            if (InvokeRequired)
            {
                Invoke(new Action<string>(LogMessage), message);
                return;
            }
            _logBox.AppendText(message + Environment.NewLine);
        }

        private void InitializeComponent()
        {
            this.Text = "DC2PC — Mode Manual (lanjutan)";
            this.AutoScaleMode = AutoScaleMode.Dpi;
            this.Font = new Font("Segoe UI", 9);
            this.MinimumSize = new Size(680, 560);
            this.Size = new Size(680, 560);
            this.StartPosition = FormStartPosition.CenterParent;
            
            var tabControl = new TabControl { Dock = DockStyle.Top, Height = 300 };
            
            // --- Single File Tab ---
            var tabSingle = new TabPage("Single File");
            
            var lblInput = new Label { Text = "Input MES/JSON:", Top = 20, Left = 10, Width = 150 };
            _txtSingleInput = new TextBox { Top = 20, Left = 170, Width = 350 };
            var btnBrowseInput = new Button { Text = "...", Top = 20, Left = 530, Width = 30 };
            btnBrowseInput.Click += (s, e) => BrowseFile(_txtSingleInput);

            var lblOutput = new Label { Text = "Output JSON/MES:", Top = 50, Left = 10, Width = 150 };
            _txtSingleOutput = new TextBox { Top = 50, Left = 170, Width = 350 };
            var btnBrowseOutput = new Button { Text = "...", Top = 50, Left = 530, Width = 30 };
            btnBrowseOutput.Click += (s, e) => BrowseSaveFile(_txtSingleOutput);

            var lblWrap = new Label { Text = "Word Wrap Width:", Top = 90, Left = 10, Width = 150 };
            _numSingleWrap = new NumericUpDown { Top = 90, Left = 170, Width = 60, Minimum = 10, Maximum = 100, Value = 70 }; 

            var btnExport = new Button { Text = "Export (MES -> JSON)", Top = 130, Left = 20, Width = 190 };
            btnExport.Click += (s, e) => RunSingleExport();
            
            var btnImport = new Button { Text = "Import (JSON -> MES)", Top = 130, Left = 220, Width = 190 };
            btnImport.Click += (s, e) => RunSingleImport();

            tabSingle.Controls.AddRange(new Control[] { 
                lblInput, _txtSingleInput, btnBrowseInput, 
                lblOutput, _txtSingleOutput, btnBrowseOutput,
                lblWrap, _numSingleWrap,
                btnExport, btnImport 
            });

            // --- Batch Tab ---
            var tabBatch = new TabPage("Batch");

            var lblBatchJson = new Label { Text = "JSON Folder:", Top = 20, Left = 10, Width = 150 };
            _txtBatchInput = new TextBox { Top = 20, Left = 170, Width = 350 }; // JSON folder for import, MES folder for export
            var btnBrowseBatchInput = new Button { Text = "...", Top = 20, Left = 530, Width = 30 };
            btnBrowseBatchInput.Click += (s, e) => BrowseFolder(_txtBatchInput);

            var lblBatchMes = new Label { Text = "MES Folder:", Top = 50, Left = 10, Width = 150 };
            _txtBatchMesInput = new TextBox { Top = 50, Left = 170, Width = 350 };
            var btnBrowseBatchMes = new Button { Text = "...", Top = 50, Left = 530, Width = 30 };
            btnBrowseBatchMes.Click += (s, e) => BrowseFolder(_txtBatchMesInput);
            
            var lblBatchOutput = new Label { Text = "Output Folder:", Top = 80, Left = 10, Width = 150 };
            _txtBatchOutput = new TextBox { Top = 80, Left = 170, Width = 350 };
            var btnBrowseBatchOutput = new Button { Text = "...", Top = 80, Left = 530, Width = 30 };
            btnBrowseBatchOutput.Click += (s, e) => BrowseFolder(_txtBatchOutput);

            var lblBatchWrap = new Label { Text = "Word Wrap Width:", Top = 120, Left = 10, Width = 150 };
            _numBatchWrap = new NumericUpDown { Top = 120, Left = 170, Width = 60, Minimum = 10, Maximum = 100, Value = 70 };

            var btnBatchExport = new Button { Text = "Batch Export (MES -> JSON)", Top = 160, Left = 20, Width = 220 };
            btnBatchExport.Click += (s, e) => RunBatchExport();
            
            var btnBatchImport = new Button { Text = "Batch Import (JSON -> MES)", Top = 160, Left = 250, Width = 220 };
            btnBatchImport.Click += (s, e) => RunBatchImport();

            Control lblHint = new Label { Text = "Ekspor: MES Folder -> JSON Folder.\nImpor: JSON Folder + MES Folder -> Output Folder.", Top = 200, Left = 20, Width = 400, AutoSize = true };

            tabBatch.Controls.AddRange(new Control[] { 
                lblBatchJson, _txtBatchInput, btnBrowseBatchInput,
                lblBatchMes, _txtBatchMesInput, btnBrowseBatchMes,
                lblBatchOutput, _txtBatchOutput, btnBrowseBatchOutput,
                lblBatchWrap, _numBatchWrap,
                btnBatchExport, btnBatchImport, lblHint
            });

            tabControl.TabPages.Add(tabSingle);
            tabControl.TabPages.Add(tabBatch);
            
            // --- Log Box ---
            _logBox = new TextBox { 
                Multiline = true, 
                Dock = DockStyle.Bottom, 
                Height = 150, 
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true 
            };

            this.Controls.Add(tabControl);
            this.Controls.Add(_logBox);
            _language.Items.AddRange(new object[] { "English", "Bahasa Indonesia" });
            var languageRow = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 45, Padding = new Padding(10, 7, 10, 3) };
            languageRow.Controls.Add(new Label { Text = "Language / Bahasa", AutoSize = true, Margin = new Padding(0, 4, 12, 0) });
            languageRow.Controls.Add(_language);
            this.Controls.Add(languageRow);
            
            // Allow drag and drop
            this.AllowDrop = true;
            this.DragEnter += MainForm_DragEnter;
            this.DragDrop += MainForm_DragDrop;
        }

        private void BrowseFile(TextBox target)
        {
            using var fd = new OpenFileDialog { Title = UiText.T("Buka file MES atau JSON") };
            if (fd.ShowDialog() == DialogResult.OK) target.Text = fd.FileName;
        }

        private void BrowseSaveFile(TextBox target)
        {
            using var fd = new SaveFileDialog { Title = UiText.T("Simpan file hasil") };
            if (fd.ShowDialog() == DialogResult.OK) target.Text = fd.FileName;
        }

        private void BrowseFolder(TextBox target)
        {
            using var fd = new FolderBrowserDialog { Description = UiText.T("Pilih folder"), UseDescriptionForTitle = true };
            if (fd.ShowDialog() == DialogResult.OK) target.Text = fd.SelectedPath;
        }

        private void RunSingleExport()
        {
            _logBox.Clear();
            string input = _txtSingleInput.Text;
            string output = _txtSingleOutput.Text;
            if (string.IsNullOrWhiteSpace(output)) output = Path.ChangeExtension(input, ".json");
            
            RunJob(() => _processor.ExportMesToJson(input, output));
        }

        private void RunSingleImport()
        {
            _logBox.Clear();
            string jsonPaths = _txtSingleInput.Text; 
            using var sourceDialog = new OpenFileDialog {
                Title = UiText.T("Pilih MES sumber yang dipakai untuk mengekspor JSON ini"),
                Filter = UiText.T("Naskah MES") + "|*.mes", FileName = Path.GetFileNameWithoutExtension(jsonPaths) + ".mes" };
            if (sourceDialog.ShowDialog(this) != DialogResult.OK) return;
            string originalMes = sourceDialog.FileName;

            string output = _txtSingleOutput.Text;
            if (string.IsNullOrWhiteSpace(output))
                output = Path.Combine(Path.GetDirectoryName(originalMes) ?? "", "new_" + Path.GetFileName(originalMes));

            int wrap = (int)_numSingleWrap.Value;
            
            RunJob(() => _processor.ImportJsonToMes(jsonPaths, originalMes, output, wrap));
        }

        private void RunBatchExport()
        {
            _logBox.Clear();
            // Expect MES folder in _txtBatchMesInput
            string input = _txtBatchMesInput.Text;
            string output = _txtBatchInput.Text; // Use JSON folder as output
            if (string.IsNullOrWhiteSpace(output)) output = Path.Combine(input, "json_output");
            
            RunJob(() => _processor.BatchExport(input, output));
        }

        private void RunBatchImport()
        {
            _logBox.Clear();
            string jsonFolder = _txtBatchInput.Text;
            string mesFolder = _txtBatchMesInput.Text;
            string output = _txtBatchOutput.Text;
            if (string.IsNullOrWhiteSpace(output)) output = Path.Combine(mesFolder, "mes_output");
             int wrap = (int)_numBatchWrap.Value;

            RunJob(() => _processor.BatchImport(jsonFolder, mesFolder, output, wrap));
        }
        
        private async void RunJob(Func<int> job)
        {
            if (_busy) return;
            _busy = true;
            foreach (Control c in Controls) if (c != _logBox) c.Enabled = false;
            try { int code = await Task.Run(job); LogMessage(code == 0 ? UiText.T("Selesai.") : UiText.T("Ada kegagalan; periksa log. Jangan pasang hasil parsial.")); }
            catch (Exception ex) { LogMessage(UiText.T("Gagal: ") + ex.Message); }
            finally { _busy = false; foreach (Control c in Controls) c.Enabled = true; }
        }

        private void MainForm_DragEnter(object? sender, DragEventArgs e)
        {
            if (e.Data?.GetDataPresent(DataFormats.FileDrop) == true)
                e.Effect = DragDropEffects.Copy;
        }

        private void MainForm_DragDrop(object? sender, DragEventArgs e)
        {
            if (e.Data?.GetData(DataFormats.FileDrop) is not string[] files)
                return;

            if (files.Length > 0)
            {
                if (Directory.Exists(files[0]))
                {
                    _txtBatchMesInput.Text = files[0];
                    // Smart guess: if folder has json, put in JSON input
                    if (Directory.GetFiles(files[0], "*.json").Length > 0)
                         _txtBatchInput.Text = files[0];
                }
                else
                {
                    _txtSingleInput.Text = files[0];
                }
            }
        }
    }
}
