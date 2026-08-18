using System.Globalization;
using Lab01.Collector;

var paths = ProjectPaths.Discover();
var executionStamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHHmmssZ", CultureInfo.InvariantCulture);

Log.Start(Path.Combine(paths.LogsDir, $"collect_{executionStamp}.log"));

try
{
    var options = CollectorOptions.FromEnvFile(paths.EnvFile);

    var collector = new RepositoryCollector(
        new GitHubApi(options.Token, paths.QueriesDir),
        new PageStore(paths.RawDir),
        options,
        paths.CheckpointFile);

    var result = await collector.CollectAsync(executionStamp);

    Directory.CreateDirectory(paths.ProcessedDir);

    var rawCsv = Path.Combine(paths.RawDir, $"repos_raw_{result.RunStamp}.csv");
    var languageCsv = Path.Combine(paths.ProcessedDir, $"pilot_rq05_rq06_{result.RunStamp}.csv");

    RawCsvWriter.Write(rawCsv, result.Repositories, result.CollectedAt);
    LanguageIssuesCsvWriter.Write(languageCsv, result.Repositories, result.CollectedAt);

    Log.Info($"fim | {result.Repositories.Count} repositorios | {result.LastPage} paginas | " +
             $"{result.Duplicates} duplicado(s) descartado(s) | referencia {result.CollectedAt}");
    Log.Info($"csv bruto: {rawCsv}");
    Log.Info($"csv rq05/rq06: {languageCsv}");

    return 0;
}
catch (FatalApiException ex)
{
    Log.Error(ex.Message);
    Log.Error("coleta interrompida. Rode de novo para retomar a partir do checkpoint.");

    return 1;
}
