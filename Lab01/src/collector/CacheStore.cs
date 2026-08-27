using System.Text.Json;

namespace Lab01.Collector;

public sealed class CacheStore
{
    private readonly string _metadataFile;

    private static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
        WriteIndented = true
    };

    public CacheStore(string cacheDirectory)
    {
        Directory.CreateDirectory(cacheDirectory);
        _metadataFile = Path.Combine(cacheDirectory, "metadata.json");
    }

    public CacheMetadata? Load()
    {
        if (!File.Exists(_metadataFile))
            return null;

        try
        {
            return JsonSerializer.Deserialize<CacheMetadata>(
                File.ReadAllText(_metadataFile),
                Json
            );
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public void Save(CacheMetadata metadata)
    {
        var content = JsonSerializer.Serialize(metadata, Json);
        File.WriteAllText(_metadataFile, content);
    }
}