using System.Globalization;
using Lab01.Collector;
using Lab01.Metrics;

// src/collector/bin/Debug/net8.0 -> raiz do repositorio
var root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../.."));

var env = File.ReadAllLines(Path.Combine(root, ".env"))
    .Where(line => line.Contains('=') && !line.TrimStart().StartsWith('#'))
    .ToDictionary(line => line.Split('=', 2)[0].Trim(), line => line.Split('=', 2)[1].Trim());

var searchQuery = env["SEARCH_QUERY"];
var pageSize = int.Parse(env["PAGE_SIZE"]);
var targetRepos = int.Parse(env["TARGET_REPOS"]);

var api = new GitHubApi(env["GITHUB_TOKEN"], Path.Combine(root, "src", "github", "queries"));

var collectedAt = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
var stamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHHmmssZ", CultureInfo.InvariantCulture);

var rawDir = Path.Combine(root, "data", "raw");
Directory.CreateDirectory(rawDir);

var repos = new List<Repository>();
string? cursor = null;
var page = 1;

while (repos.Count < targetRepos)
{
    var (parsed, raw) = await api.FetchPageAsync(searchQuery, pageSize, cursor);
    var search = parsed.Data.Search;

    File.WriteAllText(Path.Combine(rawDir, $"repos_raw_{stamp}_p{page:D3}.json"), raw);
    repos.AddRange(search.Nodes);

    Console.WriteLine($"pagina {page} | total {repos.Count}/{targetRepos} " +
                      $"| custo {parsed.Data.RateLimit.Cost} | restante {parsed.Data.RateLimit.Remaining}");

    if (!search.PageInfo.HasNextPage) break;

    cursor = search.PageInfo.EndCursor;
    page++;
}

var csvPath = Path.Combine(rawDir, $"repos_raw_{stamp}.csv");
WriteCsv(csvPath, repos.Take(targetRepos), collectedAt);

var refinedDir = Path.Combine(root, "data", "processed");
Directory.CreateDirectory(refinedDir);
var refinedCsvPath = Path.Combine(refinedDir, $"repos_refined_{stamp}.csv");
WriteRefinedCsv(refinedCsvPath, repos.Take(targetRepos), collectedAt);

Console.WriteLine($"\ncsv: {csvPath}");
Console.WriteLine($"csv refinado: {refinedCsvPath}");

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
        var history = r.DefaultBranchRef?.Target?.History;

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
            history?.TotalCount,
            history?.Nodes.FirstOrDefault()?.CommittedDate,
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
