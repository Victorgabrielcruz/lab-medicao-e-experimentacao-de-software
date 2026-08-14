namespace Lab01.Collector;

public static class Log
{
    private static string _file = "";

    public static void Start(string file)
    {
        _file = file;
        Directory.CreateDirectory(Path.GetDirectoryName(file)!);
    }

    public static void Info(string message) => Write("INFO", message);

    public static void Warn(string message) => Write("WARN", message);

    public static void Error(string message) => Write("ERRO", message);

    private static void Write(string level, string message)
    {
        var line = $"{DateTime.UtcNow:yyyy-MM-ddTHH:mm:ssZ} [{level}] {message}";
        Console.WriteLine(line);
        File.AppendAllText(_file, line + Environment.NewLine);
    }
}
