using System.Globalization;
using Lab01.Collector;

var root = FindRepoRoot();
var env = LoadEnv(Path.Combine(root, ".env"));

var searchQuery = env["SEARCH_QUERY"];
var pageSize = int.Parse(env["PAGE_SIZE"]);
var targetRepos = int.Parse(env["TARGET_REPOS"]);

var client = new GitHubClient(
    env["GITHUB_TOKEN"],
    env["GITHUB_USER_AGENT"],
    env["GITHUB_API_URL"],
    Path.Combine(root, "src", "github", "queries"));

var collectedAt = DateTime.UtcNow;
var stamp = collectedAt.ToString("yyyy-MM-ddTHHmmssZ", CultureInfo.InvariantCulture);

var rawDir = Path.Combine(root, "data", "raw");
Directory.CreateDirectory(rawDir);

var rows = new List<CollectedRepo>();
string? cursor = null;
var page = 1;

while (rows.Count < targetRepos)
{
    var (parsed, raw) = await client.FetchPageAsync(searchQuery, pageSize, cursor);
    var search = parsed.Data.Search;

    File.WriteAllText(Path.Combine(rawDir, $"repos_raw_{stamp}_p{page:D3}.json"), raw);

    foreach (var repo in search.Nodes)
        rows.Add(new CollectedRepo(repo, page));

    Console.WriteLine(
        $"pagina {page} | +{search.Nodes.Count} repos | total {rows.Count}/{targetRepos} " +
        $"| custo {parsed.Data.RateLimit.Cost} | restante {parsed.Data.RateLimit.Remaining}");

    if (!search.PageInfo.HasNextPage) break;

    cursor = search.PageInfo.EndCursor;
    page++;
}

var collected = rows.Take(targetRepos).ToList();

var csvPath = Path.Combine(rawDir, $"repos_raw_{stamp}.csv");
CsvExporter.Write(csvPath, collected, collectedAt);

Console.WriteLine($"\n{collected.Count} repositorios coletados");
Console.WriteLine($"csv: {csvPath}");

static string FindRepoRoot()
{
    var dir = new DirectoryInfo(AppContext.BaseDirectory);

    while (dir is not null && !Directory.Exists(Path.Combine(dir.FullName, "src", "github", "queries")))
        dir = dir.Parent;

    return dir!.FullName;
}

static Dictionary<string, string> LoadEnv(string path)
{
    return File.ReadAllLines(path)
        .Where(line => !line.TrimStart().StartsWith('#') && line.Contains('='))
        .ToDictionary(
            line => line[..line.IndexOf('=')].Trim(),
            line => line[(line.IndexOf('=') + 1)..].Trim());
}
