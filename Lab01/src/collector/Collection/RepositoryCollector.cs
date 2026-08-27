using System.Globalization;

namespace Lab01.Collector;

// Loop de paginacao por cursor, com deduplicacao por id e checkpoint de
// retomada. Toda a regra da coleta vive aqui; o Program apenas monta e chama.
public sealed class RepositoryCollector
{
    private const string TimestampFormat = "yyyy-MM-ddTHH:mm:ssZ";

    private readonly GitHubApi _api;
    private readonly PageStore _pages;
    private readonly CollectorOptions _options;
    private readonly string _checkpointFile;

    public RepositoryCollector(
        GitHubApi api,
        PageStore pages,
        CollectorOptions options,
        string checkpointFile)
    {
        _api = api;
        _pages = pages;
        _options = options;
        _checkpointFile = checkpointFile;
    }

    public async Task<CollectionResult> CollectAsync(string executionStamp)
    {
        var repositories = new List<Repository>();
        var seenIds = new HashSet<string>();
        var duplicates = 0;
        var lastPage = 0;
        var page = 1;
        string? cursor = null;

        var checkpoint = LoadCheckpoint();
        string runStamp;
        string collectedAt;

        if (checkpoint is null)
        {
            runStamp = executionStamp;
            collectedAt = DateTime.UtcNow.ToString(TimestampFormat, CultureInfo.InvariantCulture);
        }
        else
        {
            runStamp = checkpoint.Stamp;
            collectedAt = checkpoint.CollectedAt;
            cursor = checkpoint.Cursor;
            page = checkpoint.NextPage;
            lastPage = checkpoint.NextPage - 1;

            duplicates += Restore(repositories, seenIds, runStamp);
            WarnIfStale(collectedAt);
        }

        Log.Info($"inicio | alvo {_options.TargetRepos} repositorios | pagina de {_options.PageSize} " +
                 $"| filtro \"{_options.SearchQuery}\" | referencia {collectedAt}");

        while (repositories.Count < _options.TargetRepos)
        {
            var (data, raw) = await _api.FetchPageAsync(_options.SearchQuery, _options.PageSize, cursor);

            _pages.Save(runStamp, page, raw);
            lastPage = page;

            var nodes = data.Search.Nodes.OfType<Repository>().ToList();

            if (nodes.Count < data.Search.Nodes.Count)
                Log.Warn($"pagina {page}: {data.Search.Nodes.Count - nodes.Count} node(s) nulo(s) descartado(s)");

            var added = 0;
            var repeated = 0;

            foreach (var repository in nodes)
            {
                if (seenIds.Add(repository.Id))
                {
                    repositories.Add(repository);
                    added++;
                }
                else
                {
                    repeated++;
                }
            }

            duplicates += repeated;

            // O ranking muda durante a coleta: um repositorio pode trocar de
            // pagina e reaparecer. O id e a chave que garante a amostra unica.
            if (repeated > 0)
                Log.Warn($"pagina {page}: {repeated} repositorio(s) repetido(s) descartado(s)");

            Log.Info($"pagina {page} | +{added} | total {repositories.Count}/{_options.TargetRepos} " +
                     $"| custo {data.RateLimit.Cost} | restante {data.RateLimit.Remaining}");

            Log.Info($"pagina {page} | hasNextPage {data.Search.PageInfo.HasNextPage} " +
                     $"| endCursor {Describe(data.Search.PageInfo.EndCursor)} " +
                     $"| resultados na busca {data.Search.RepositoryCount}");

            if (!data.Search.PageInfo.HasNextPage)
            {
                if (repositories.Count < _options.TargetRepos)
                    Log.Warn($"a busca acabou com {repositories.Count} repositorios, abaixo do alvo de " +
                             $"{_options.TargetRepos}. O search do GitHub devolve no maximo 1000 resultados");
                else
                    Log.Info($"a busca acabou junto com o alvo de {_options.TargetRepos} repositorios");

                break;
            }

            cursor = data.Search.PageInfo.EndCursor;
            page++;

            SaveCheckpoint(runStamp, collectedAt, cursor, page, repositories.Count);
        }

        if (File.Exists(_checkpointFile))
            File.Delete(_checkpointFile);

        var collected = repositories.Take(_options.TargetRepos).ToList();

        return new CollectionResult(collected, runStamp, collectedAt, lastPage, duplicates, cursor);
    }

    private Checkpoint? LoadCheckpoint()
    {
        var checkpoint = Checkpoint.Load(_checkpointFile);

        if (checkpoint is null)
            return null;

        if (!checkpoint.MatchesConfig(_options.SearchQuery, _options.PageSize, _options.TargetRepos))
        {
            Log.Warn("checkpoint descartado: os parametros do .env mudaram, a amostra seria outra");
            return null;
        }

        Log.Info($"retomando a coleta {checkpoint.Stamp} a partir da pagina {checkpoint.NextPage} " +
                 $"| cursor {Describe(checkpoint.Cursor)}");

        return checkpoint;
    }

    private int Restore(List<Repository> repositories, HashSet<string> seenIds, string runStamp)
    {
        var duplicates = 0;

        foreach (var repository in _pages.ReadAll(runStamp))
        {
            if (seenIds.Add(repository.Id))
                repositories.Add(repository);
            else
                duplicates++;
        }

        Log.Info($"{repositories.Count} repositorio(s) recuperado(s) de data/raw sem nova requisicao");

        return duplicates;
    }

    // A referencia continua sendo a da primeira execucao, senao o CSV teria
    // bases temporais diferentes dentro da mesma amostra.
    private static void WarnIfStale(string collectedAt)
    {
        var age = DateTime.UtcNow - DateTime.Parse(
            collectedAt,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal);

        if (age > TimeSpan.FromHours(1))
            Log.Warn($"o checkpoint tem {age.TotalHours:F1}h. A referencia segue {collectedAt}, mas o " +
                     "ranking de estrelas ja mudou. Considere apagar data/raw/checkpoint.json e recomecar");
    }

    private void SaveCheckpoint(string runStamp, string collectedAt, string? cursor, int nextPage, int collected) =>
        new Checkpoint(
            runStamp,
            collectedAt,
            _options.SearchQuery,
            _options.PageSize,
            _options.TargetRepos,
            cursor,
            nextPage,
            collected).Save(_checkpointFile);

    private static string Describe(string? cursor) =>
        string.IsNullOrEmpty(cursor) ? "(nenhum)" : cursor;
}
