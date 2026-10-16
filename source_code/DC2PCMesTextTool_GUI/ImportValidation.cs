using DC2PCMesTextTool_GUI;
using System.Text;
using System.Text.Json;

namespace DC2PCMesTextTool;

public static class ImportValidation
{
    public static List<TextEntry> Read(string path)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        if (doc.RootElement.ValueKind != JsonValueKind.Array)
            throw new InvalidDataException(UiText.T("JSON harus berupa daftar [ ... ] dari exporter GUI."));
        var result = new List<TextEntry>();
        foreach (var row in doc.RootElement.EnumerateArray())
        {
            int n = result.Count + 1;
            if (row.ValueKind != JsonValueKind.Object)
                throw new InvalidDataException(UiText.Format("Baris {0}: harus berupa objek message/name.", n));
            var fields = new HashSet<string>();
            foreach (var prop in row.EnumerateObject())
            {
                if (!fields.Add(prop.Name) || prop.Name is not ("name" or "message") || prop.Value.ValueKind != JsonValueKind.String)
                    throw new InvalidDataException(UiText.Format("Baris {0}: kolom {1} tidak valid. Gunakan message dan name (jika ada) berupa teks.", n, prop.Name));
            }
            if (!fields.Contains("message")) throw new InvalidDataException(UiText.Format("Baris {0}: message hilang.", n));
            result.Add(new TextEntry { Message = row.GetProperty("message").GetString()!,
                Name = fields.Contains("name") ? row.GetProperty("name").GetString() : null });
        }
        return result;
    }

    public static bool Same(List<TextEntry> a, List<TextEntry> b) => a.Count == b.Count &&
        a.Zip(b).All(p => p.First.Message == p.Second.Message && p.First.Name == p.Second.Name);

    public static void Compare(List<TextEntry> source, List<TextEntry> edited)
    {
        if (source.Count != edited.Count)
            throw new InvalidDataException(UiText.Format("Jumlah entri berbeda: sumber {0}, edit {1}. Jangan menambah, membuang, atau memasukkan JSON edisi lain.", source.Count, edited.Count));
        Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
        var strict = Encoding.GetEncoding(932, EncoderFallback.ExceptionFallback, DecoderFallback.ExceptionFallback);
        for (int i = 0; i < source.Count; i++)
        {
            var a = source[i]; var b = edited[i];
            if ((a.Name is null) != (b.Name is null) || (b.Name is not null && string.IsNullOrWhiteSpace(b.Name)))
                throw new InvalidDataException(UiText.Format("Entri {0}: kolom name harus tetap ada/tidak ada seperti sumber dan tidak boleh kosong.", i + 1));
            bool choice = ChoiceText.IsLabel(a.Message);
            if (choice != ChoiceText.IsLabel(b.Message))
                throw new InvalidDataException(UiText.Format("Entri {0}: posisi penanda pilihan ○ berbeda. Pertahankan penanda dan urutan pilihan.", i + 1));
            if (choice) _ = ChoiceText.Normalize(b.Message);
            foreach (var (oldText, newText) in new[] { (a.Message, b.Message), (a.Name, b.Name) })
            {
                if (oldText == newText || newText is null) continue;
                if (string.IsNullOrWhiteSpace(newText)) throw new InvalidDataException(UiText.Format("Entri {0}: teks tidak boleh dikosongkan.", i + 1));
                if (newText.Any(c => char.IsControl(c) && c is not ('\r' or '\n' or '\t')))
                    throw new InvalidDataException(UiText.Format("Entri {0}: karakter kontrol tidak didukung.", i + 1));
                try { strict.GetBytes(newText); }
                catch (EncoderFallbackException) { throw new InvalidDataException(UiText.Format("Entri {0}: karakter tidak tersedia di CP932. Ganti emoji/tanda kutip melengkung dengan teks biasa.", i + 1)); }
            }
        }
    }

    // Check control flow independently of text lengths after rebuilding.
    public static void VerifyMes(string source, string output)
    {
        var a = new MesScript(); a.Load(source);
        var b = new MesScript(); b.Load(output);
        if (a.Tokens.Count != b.Tokens.Count || a.LabelCount != b.LabelCount)
            throw new InvalidDataException(UiText.T("Struktur token/label hasil berubah."));
        var textOffsets = a.ExtractText(Encoding.GetEncoding(932)).Select(e => e.Offset).ToHashSet();
        for (int i = 0; i < a.Tokens.Count; i++)
        {
            var x = a.Tokens[i]; var y = b.Tokens[i];
            if (x.Opcode != y.Opcode) throw new InvalidDataException(UiText.Format("Opcode berubah pada token {0}.", i));
            if (!textOffsets.Contains(x.Offset) && !a.RawData.AsSpan(a.BytecodeOffset + 2 + x.Offset, x.Length)
                .SequenceEqual(b.RawData.AsSpan(b.BytecodeOffset + 2 + y.Offset, y.Length)))
                throw new InvalidDataException(UiText.Format("Data selain teks berubah pada token {0}.", i));
        }
        var ax = a.Tokens.Select((t, i) => (t.Offset, i)).ToDictionary(t => t.Offset + 2, t => t.i);
        var bx = b.Tokens.Select((t, i) => (t.Offset, i)).ToDictionary(t => t.Offset + 2, t => t.i);
        for (int i = 0; i < a.LabelCount; i++)
        {
            int x = BitConverter.ToInt32(a.RawData, 4 + i * 4), y = BitConverter.ToInt32(b.RawData, 4 + i * 4);
            if (!ax.TryGetValue(x, out int u) || !bx.TryGetValue(y, out int v) || u != v)
                throw new InvalidDataException(UiText.Format("Tujuan cabang label {0} tidak cocok.", i));
        }
        foreach (var s in new[] { a, b })
            if (s.Tokens.Count == 0 || s.BytecodeOffset + 2 + s.Tokens[^1].Offset + s.Tokens[^1].Length != s.RawData.Length)
                throw new InvalidDataException(UiText.T("Parser tidak mencakup seluruh MES; impor dihentikan."));
    }
}
