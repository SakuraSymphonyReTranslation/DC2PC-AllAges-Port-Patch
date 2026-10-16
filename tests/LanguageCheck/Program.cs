using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using DC2PCMesTextTool_GUI;
using DC2PCMesTextTool;

internal static class Program
{
    private static int _checks;
    private static void Check(bool ok, string message) { if (!ok) throw new Exception(message); _checks++; }
    private static T Field<T>(object form, string name) => (T)form.GetType().GetField(name, BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(form)!;
    private static IEnumerable<Control> Tree(Control root) { yield return root; foreach (Control child in root.Controls) foreach (var item in Tree(child)) yield return item; }

    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Check(UiText.Language == InterfaceLanguage.English, "Fresh process must default to English");
        using var workflow = new WorkflowForm();
        var language = Field<ComboBox>(workflow, "_language");
        var basis = Field<ComboBox>(workflow, "_basis");
        Check(workflow.Text == "DC2PC — Translation Export / Import Workflow", "English workflow title");
        Check(language.SelectedIndex == 0, "English selected at startup");
        Check(Tree(workflow).OfType<Button>().Any(c => c.Text == "1. Create project + export"), "English action caption");
        var inputs = new[] { "_game", "_source", "_project" }.Select(n => Field<TextBox>(workflow, n)).ToArray();
        Check(inputs[2].Text == "", "Project folder must start empty");
        Check(inputs[2].PlaceholderText == "Choose your project folder...", "Project location is an explicit choice");
        Check(Tree(workflow).OfType<Button>().Any(c => c.Text == "Tutorial English") && Tree(workflow).OfType<Button>().Any(c => c.Text == "Tutorial Indonesia"), "Both tutorial modules accessible");
        var log = Field<TextBox>(workflow, "_log");
        log.Text = "Historical log — jangan ubah ○";
        inputs[0].Text = @"C:\game-test";
        inputs[2].Text = @"C:\my-project";
        for (int selected = 0; selected < 3; selected++)
        {
            basis.SelectedIndex = selected;
            inputs[1].Text = @"C:\custom MES\source " + selected;
            var before = inputs.Select(t => t.Text).ToArray();
            foreach (int choice in new[] { 1, 0, 1, 0 })
            {
                language.SelectedIndex = choice;
                Check(inputs.Select(t => t.Text).SequenceEqual(before), "Paths preserved while translating source selector");
                Check(basis.SelectedIndex == selected, "Project source index preserved");
                Check(log.Text == "Historical log — jangan ubah ○", "Historical logs preserved");
                Check(Field<Label>(workflow, "_status").Text.StartsWith(choice == 0 ? "Start by" : "Mulai dengan"), "Initial status translated");
                Check(basis.Items[2]!.ToString()!.StartsWith(choice == 0 ? "Other MES" : "Folder MES"), "Source choices translated");
            }
        }
        basis.SelectedIndex = 0;
        inputs[0].Text = @"C:\different-game";
        Check(inputs[1].Text == @"C:\different-game\id_Data\MES", "Source derivation still works after switching");
        language.SelectedIndex = 1;
        Check(Tree(workflow).OfType<Button>().Any(c => c.Text == "1. Buat proyek + ekspor"), "Indonesian action caption");
        using (var manual = new MainForm())
        {
            Check(manual.Text.Contains("Mode Manual"), "Manual inherits language");
            var manualInputs = new[] { "_txtSingleInput", "_txtSingleOutput", "_txtBatchInput", "_txtBatchMesInput", "_txtBatchOutput" }.Select(n => Field<TextBox>(manual,n)).ToArray();
            for (int n = 0; n < manualInputs.Length; n++) manualInputs[n].Text = "Manual path " + n + " ○";
            var before = manualInputs.Select(t=>t.Text).ToArray();
            var singleWrap = Field<NumericUpDown>(manual,"_numSingleWrap");
            var batchWrap = Field<NumericUpDown>(manual,"_numBatchWrap");
            Check(singleWrap.Value == 70 && batchWrap.Value == 70, "Original wrap defaults retained");
            singleWrap.Value = 72; batchWrap.Value = 68;
            var tabs = Tree(manual).OfType<TabControl>().Single(); tabs.SelectedIndex = 1;
            var manualLanguage = Field<ComboBox>(manual,"_language");
            manualLanguage.SelectedIndex = 0;
            Check(manual.Text.Contains("Manual Mode"), "Manual switches to English");
            Check(language.SelectedIndex == 0 && workflow.Text.Contains("Translation"), "Parent follows manual language");
            manualLanguage.SelectedIndex = 1;
            Check(manualInputs.Select(t=>t.Text).SequenceEqual(before), "Manual inputs preserved");
            Check(singleWrap.Value == 72 && batchWrap.Value == 68 && tabs.SelectedIndex == 1, "Wrap values and selected tab preserved");
            Check(tabs.TabPages[0].Text == "Satu File" && tabs.TabPages[1].Text == "Banyak File", "Manual tabs translated");
        }
        // Verify messages on background workers, as used by the GUI conversion jobs.
        string invalidJson = Path.Combine(Path.GetTempPath(), "dc2pc-language-" + Guid.NewGuid() + ".json");
        File.WriteAllText(invalidJson, "{}");
        try
        {
            foreach (int choice in new[] { 0, 1 })
            {
                language.SelectedIndex = choice;
                string message = Task.Run(() => { try { ImportValidation.Read(invalidJson); return "NO ERROR"; } catch (InvalidDataException ex) { return ex.Message; } }).Result;
                Check(message.StartsWith(choice == 0 ? "JSON must be" : "JSON harus"), "Background validation localized");
                try { new TranslationWorkflow().Load(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString())); throw new Exception("Expected missing project"); }
                catch (FileNotFoundException ex) { Check(ex.Message.StartsWith(choice == 0 ? "Project manifest" : "Catatan proyek"), "Missing project error localized"); }
                var logs = new List<string>(); var processor = new MesToolProcessor(); processor.Log += logs.Add;
                Check(processor.BatchExport(Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString()), "unused") == 1, "Missing source rejected");
                Check(logs.Single().StartsWith(choice == 0 ? "Error: Folder not found" : "Kesalahan: Folder tidak ditemukan"), "Manual processor errors localized");
                foreach (Action action in new Action[] { () => new TranslationWorkflow().Load(""), () => new TranslationWorkflow().Prepare("", ""), () => new TranslationWorkflow().Prepare(@"C:\source", " ") })
                {
                    try { action(); throw new Exception("Blank paths must be rejected before any file access"); }
                    catch (InvalidDataException ex) { Check(ex.Message.StartsWith(choice == 0 ? "Choose " : "Pilih "), "Blank path guidance localized"); }
                }
            }
        }
        finally { File.Delete(invalidJson); }
        using var resource = typeof(UiText).Assembly.GetManifestResourceStream("DC2PCMesTextTool_GUI.UiStrings.json")!;
        var catalog = JsonSerializer.Deserialize<Dictionary<string,string[]>>(resource)!;
        foreach (var (key,pair) in catalog)
        {
            Check(pair.Length == 2 && pair.All(v=>!string.IsNullOrEmpty(v)), "Resource has both languages: " + key);
            var expected = Regex.Matches(key, @"\{\d+\}").Select(m=>m.Value).Order().ToArray();
            foreach (string value in pair)
                Check(Regex.Matches(value, @"\{\d+\}").Select(m=>m.Value).Order().SequenceEqual(expected), "Format placeholders preserved: " + key);
        }
        language.SelectedIndex = 0;
        Console.WriteLine($"PASS: {_checks} assertions; default, captions, source selection/paths, manual state, worker messages, and {catalog.Count} bilingual resources.");
    }
}
