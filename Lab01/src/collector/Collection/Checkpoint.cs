using System.Text.Json;

namespace Lab01.Collector;

// Permite retomar uma coleta interrompida sem refazer as paginas ja baixadas.
// Os parametros ficam gravados junto: se alguem mudar o .env, o checkpoint
// deixa de valer, porque a amostra seria outra.
public record Checkpoint(
    string Stamp,
    string CollectedAt,
    string SearchQuery,
    int PageSize,
    int TargetRepos,
    string? Cursor,
    int NextPage,
    int Collected)
{
    private static readonly JsonSerializerOptions Json = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true
    };

    public static Checkpoint? Load(string path)
    {
        if (!File.Exists(path)) return null;

        try
        {
            return JsonSerializer.Deserialize<Checkpoint>(File.ReadAllText(path), Json);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public void Save(string path) =>
        File.WriteAllText(path, JsonSerializer.Serialize(this, Json));

    public bool MatchesConfig(string searchQuery, int pageSize, int targetRepos) =>
        SearchQuery == searchQuery && PageSize == pageSize && TargetRepos == targetRepos;
}
