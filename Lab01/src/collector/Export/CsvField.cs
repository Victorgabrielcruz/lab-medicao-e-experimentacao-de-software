namespace Lab01.Collector;

internal static class CsvField
{
    public static string Escape(string? value)
    {
        if (string.IsNullOrEmpty(value)) return "";

        return value.Contains(',') ? $"\"{value}\"" : value;
    }
}
