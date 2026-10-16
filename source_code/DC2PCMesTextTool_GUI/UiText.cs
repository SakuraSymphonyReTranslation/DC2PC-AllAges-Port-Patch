using System.Text.Json;
using System.Windows.Forms;

namespace DC2PCMesTextTool_GUI;

public enum InterfaceLanguage { English, Indonesian }

/// <summary>Interface messages only; never applies to MES/JSON content or project paths.</summary>
public static class UiText
{
    private static readonly Dictionary<string, string[]> Strings = ReadStrings();
    private static volatile InterfaceLanguage _language = InterfaceLanguage.English;
    public static event Action? LanguageChanged;

    public static InterfaceLanguage Language
    {
        get => _language;
        set
        {
            if (value is not (InterfaceLanguage.English or InterfaceLanguage.Indonesian))
                throw new ArgumentOutOfRangeException(nameof(value));
            if (_language == value) return;
            _language = value;
            LanguageChanged?.Invoke();
        }
    }

    // Resource keys retain the original captions for easy lookup in existing source.
    public static string T(string key) => Strings.TryGetValue(key, out var pair) ? pair[(int)Language] : key;
    public static string Format(string key, params object?[] values) => string.Format(T(key), values);

    private static Dictionary<string, string[]> ReadStrings()
    {
        using var stream = typeof(UiText).Assembly.GetManifestResourceStream("DC2PCMesTextTool_GUI.UiStrings.json")
            ?? throw new InvalidOperationException("Missing embedded interface translations.");
        return JsonSerializer.Deserialize<Dictionary<string, string[]>>(stream)!;
    }
}

/// <summary>Captures only captions. Editable fields, selections, and historical logs are never translated.</summary>
internal sealed class UiCaptions
{
    private readonly List<(Control Control, string Key)> _items = new();
    public UiCaptions(Control root, params Control[] excluded)
    {
        void Capture(Control control)
        {
            if (!excluded.Contains(control) && control is (Form or Label or Button or TabPage))
                _items.Add((control, control.Text));
            foreach (Control child in control.Controls) Capture(child);
        }
        Capture(root);
    }

    public void Refresh()
    {
        foreach (var (control, key) in _items)
            if (!control.IsDisposed) control.Text = UiText.T(key);
    }
}
