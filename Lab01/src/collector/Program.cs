using System.Globalization;
using Lab01.Collector;
using Lab01.Collector.Collection;

const string queryVersion = "1.0.0";

var paths = ProjectPaths.Discover();
var executionStamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHHmmssZ", CultureInfo.InvariantCulture);

Log.Start(Path.Combine(paths.LogsDir, $"collect_{executionStamp}.log"));

try
{
    var options = CollectorOptions.FromEnvFile(paths.EnvFile);

    var pages = new PageStore(paths.RawDir);
    var cache = new CollectionCache(new CacheStore(paths.CacheDir), pages);
    var collectedFromApi = false;
    CollectionResult result;

    if (cache.TryRestore(options, queryVersion, out var cachedResult))
    {
        result = cachedResult!;
    }
    else
    {
        var collector = new RepositoryCollector(new GitHubApi(options.Token, paths.QueriesDir),
            pages, options, paths.CheckpointFile);

        result = await collector.CollectAsync(executionStamp);
        collectedFromApi = true;
    }

    var rawCsv = Path.Combine(paths.RawDir, $"repos_raw_{result.RunStamp}.csv");

    RawCsvWriter.Write(rawCsv, result.Repositories, result.CollectedAt);

    Log.Info($"fim | {result.Repositories.Count} repositorios | {result.LastPage} paginas | " +
             $"{result.Duplicates} duplicado(s) descartado(s) | referencia {result.CollectedAt}");
    Log.Info($"csv bruto: {rawCsv}");

    if (collectedFromApi)
        cache.SaveMetadata(options, queryVersion, result);

    return 0;
}
catch (FatalApiException ex)
{
    Log.Error(ex.Message);
    Log.Error("coleta interrompida. Rode de novo para retomar a partir do checkpoint.");

    return 1;
}
