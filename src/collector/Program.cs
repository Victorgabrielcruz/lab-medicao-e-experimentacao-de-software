using System.Globalization;
using Lab01.Collector;
using Lab01.Metrics;

// src/collector/bin/Debug/net8.0 -> raiz do repositorio
var root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../.."));

var collectedAt = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
var stamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHHmmssZ", CultureInfo.InvariantCulture);

var logPath = Path.Combine(root, "logs", $"collect_{stamp}.log");
Log.Start(logPath);

var rawDir = Path.Combine(root, "data", "raw");
Directory.CreateDirectory(rawDir);

var repos = new List<Repository>();
string? cursor = null;
var page = 1;

try
{
    var env = ReadEnv(Path.Combine(root, ".env"));

    var searchQuery = Required(env, "SEARCH_QUERY");
    var pageSize = int.Parse(Required(env, "PAGE_SIZE"));
    var targetRepos = int.Parse(Required(env, "TARGET_REPOS"));

    var api = new GitHubApi(Required(env, "GITHUB_TOKEN"), Path.Combine(root, "src", "github", "queries"));

    Log.Info($"inicio | alvo {targetRepos} repositorios | pagina de {pageSize} | filtro \"{searchQuery}\"");

    while (repos.Count < targetRepos)
    {
        var (data, raw) = await api.FetchPageAsync(searchQuery, pageSize, cursor);

        File.WriteAllText(Path.Combine(rawDir, $"repos_raw_{stamp}_p{page:D3}.json"), raw);

        var nodes = data.Search.Nodes.OfType<Repository>().ToList();
        repos.AddRange(nodes);

        if (nodes.Count < data.Search.Nodes.Count)
            Log.Warn($"pagina {page}: {data.Search.Nodes.Count - nodes.Count} node(s) nulo(s) descartado(s)");

        Log.Info($"pagina {page} | total {repos.Count}/{targetRepos} " +
                 $"| custo {data.RateLimit.Cost} | restante {data.RateLimit.Remaining}");

        if (!data.Search.PageInfo.HasNextPage)
        {
            Log.Warn($"a busca acabou com {repos.Count} repositorios, abaixo do alvo de {targetRepos}");
            break;
        }

        cursor = data.Search.PageInfo.EndCursor;
        page++;
    }

    var csvPath = Path.Combine(rawDir, $"repos_raw_{stamp}.csv");
    WriteCsv(csvPath, repos.Take(targetRepos), collectedAt);

    var refinedDir = Path.Combine(root, "data", "processed");
    Directory.CreateDirectory(refinedDir);
    var refinedCsvPath = Path.Combine(refinedDir, $"pilot_rq05_rq06_{stamp}.csv");
    WriteRefinedCsv(refinedCsvPath, repos.Take(targetRepos), collectedAt);

    Log.Info($"fim | {Math.Min(repos.Count, targetRepos)} repositorios | {page} paginas | " +
             $"csv: {csvPath} | csv refinado: {refinedCsvPath}");
    return 0;
}
catch (FatalApiException ex)
{
    Log.Error(ex.Message);
    Log.Error($"coleta interrompida na pagina {page} com {repos.Count} repositorios. " +
              $"As paginas ja baixadas estao em data/raw/. Log: {logPath}");
    return 1;
}

static Dictionary<string, string> ReadEnv(string path)
{
    if (!File.Exists(path))
        throw new FatalApiException($"arquivo .env nao encontrado em {path}");

    return File.ReadAllLines(path)
        .Where(line => line.Contains('=') && !line.TrimStart().StartsWith('#'))
        .ToDictionary(line => line.Split('=', 2)[0].Trim(), line => line.Split('=', 2)[1].Trim());
}

static string Required(Dictionary<string, string> env, string key) =>
    env.TryGetValue(key, out var value) && value.Length > 0
        ? value
        : throw new FatalApiException($"chave {key} ausente ou vazia no .env");

static void WriteCsv(string path, IEnumerable<Repository> repos, string collectedAt)
{
    var lines = new List<string>
    {
        "id,name_with_owner,url,owner,stargazer_count,is_archived,collected_at," +
        "created_at,merged_pull_requests,total_pull_requests," +
        "releases_count,updated_at,pushed_at,default_branch,total_commits,last_commit_date," +
        "primary_language,open_issues,closed_issues"
    };

    foreach (var r in repos)
    {
        var commits = r.DefaultBranchRef?.Target;

        lines.Add(string.Join(",",
            r.Id,
            Csv(r.NameWithOwner),
            Csv(r.Url),
            Csv(r.Owner.Login),
            r.StargazerCount,
            r.IsArchived.ToString().ToLowerInvariant(),
            collectedAt,
            r.CreatedAt,
            r.MergedPullRequests.TotalCount,
            r.TotalPullRequests.TotalCount,
            r.Releases.TotalCount,
            r.UpdatedAt,
            r.PushedAt,
            Csv(r.DefaultBranchRef?.Name),
            commits?.LastCommit.TotalCount,
            commits?.LastCommit.Nodes.FirstOrDefault()?.CommittedDate,
            Csv(r.PrimaryLanguage?.Name),
            r.OpenIssues.TotalCount,
            r.ClosedIssues.TotalCount));
    }

    File.WriteAllLines(path, lines);
}

static string Csv(string? value) =>
    string.IsNullOrEmpty(value) ? "" : value.Contains(',') ? $"\"{value}\"" : value;

static void WriteRefinedCsv(string path, IEnumerable<Repository> repos, string collectedAt)
{
    var lines = new List<string>
    {
        "id,name_with_owner,collected_at,primary_language,is_popular_language," +
        "open_issues,closed_issues,total_issues,has_issues,closed_issues_percentage"
    };

    foreach (var r in repos)
    {
        var metrics = Rq05Rq06Processor.Calculate(
            r.PrimaryLanguage?.Name, r.OpenIssues.TotalCount, r.ClosedIssues.TotalCount);

        lines.Add(string.Join(",",
            r.Id,
            Csv(r.NameWithOwner),
            collectedAt,
            Csv(metrics.PrimaryLanguage),
            metrics.IsPopularLanguage.ToString().ToLowerInvariant(),
            r.OpenIssues.TotalCount,
            r.ClosedIssues.TotalCount,
            metrics.TotalIssues,
            metrics.HasIssues.ToString().ToLowerInvariant(),
            metrics.ClosedIssuesPercentage?.ToString(CultureInfo.InvariantCulture) ?? ""));
    }

    File.WriteAllLines(path, lines);
}
