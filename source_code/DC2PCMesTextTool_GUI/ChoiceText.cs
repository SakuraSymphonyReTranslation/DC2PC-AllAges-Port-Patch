using DC2PCMesTextTool_GUI;
using System.Text;

namespace DC2PCMesTextTool;

/// <summary>Canonical, single-line choice labels shared by import and export.</summary>
internal static class ChoiceText
{
    public static bool IsLabel(string? text) =>
        !string.IsNullOrWhiteSpace(text) && text.TrimStart().StartsWith('○');

    public static string Normalize(string text, bool restoreMarker = false)
    {
        // Both JSON line breaks and the editor's literal escape notation are
        // word separators in a choice, never dialogue wrapping instructions.
        text = text.Replace("\\r\\n", " ").Replace("\\n", " ")
                   .Replace("\\r", " ").Replace("\\t", " ");
        var result = new StringBuilder(text.Length);
        bool pendingSpace = false;
        foreach (char source in text)
        {
            char c = source is >= '\uFF01' and <= '\uFF5E'
                ? (char)(source - 0xFEE0) : source;
            if (char.IsWhiteSpace(c))
            {
                pendingSpace = result.Length > 0;
                continue;
            }
            if (char.IsControl(c))
                throw new InvalidDataException(UiText.T("Choice contains an unsupported control character."));
            if (pendingSpace)
                result.Append(' ');
            result.Append(c);
            pendingSpace = false;
        }

        string normalized = result.ToString();
        if (normalized.StartsWith('○'))
            normalized = normalized[1..].TrimStart();
        else if (!restoreMarker)
            return normalized;

        if (normalized.Length == 0)
            throw new InvalidDataException(UiText.T("Choice text is empty. Enter a label after ○."));
        return "○ " + normalized;
    }
}
