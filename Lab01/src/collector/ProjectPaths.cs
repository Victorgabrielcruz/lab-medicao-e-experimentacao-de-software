namespace Lab01.Collector;

// Resolve os caminhos do projeto a partir do diretorio de saida do build,
// para que o executavel encontre .env, queries e data independente de onde
// for chamado.
public sealed class ProjectPaths
{
    public string Root { get; }

    private ProjectPaths(string root) => Root = root;

    // src/collector/bin/Debug/net8.0 -> raiz do Lab01
    public static ProjectPaths Discover() =>
        new(Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../..")));

    public string EnvFile => Path.Combine(Root, ".env");

    public string QueriesDir => Path.Combine(Root, "src", "github", "queries");

    public string RawDir => Path.Combine(Root, "data", "raw");

    public string ProcessedDir => Path.Combine(Root, "data", "processed");
    
    public string CacheDir => Path.Combine(Root, "data", "cache");

    public string LogsDir => Path.Combine(Root, "logs");

    public string CheckpointFile => Path.Combine(RawDir, "checkpoint.json");
}
