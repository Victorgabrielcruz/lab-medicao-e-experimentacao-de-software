using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Lab01.Collector;

public class GitHubClient
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private readonly HttpClient _http;
    private readonly string _apiUrl;
    private readonly string _query;

    public GitHubClient(string token, string userAgent, string apiUrl, string queriesPath)
    {
        _apiUrl = apiUrl;
        _query = LoadQuery(queriesPath);

        _http = new HttpClient { Timeout = TimeSpan.FromMinutes(2) };
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        _http.DefaultRequestHeaders.UserAgent.ParseAdd(userAgent);
    }

    // Ignora arquivos "_*": sao copias geradas e duplicariam os fragments.
    private static string LoadQuery(string queriesPath)
    {
        var files = Directory.GetFiles(queriesPath, "*.graphql")
            .Where(f => !Path.GetFileName(f).StartsWith('_'))
            .OrderBy(f => f);

        return string.Join("\n\n", files.Select(File.ReadAllText));
    }

    public async Task<(GraphQlResponse Parsed, string Raw)> FetchPageAsync(
        string searchQuery, int pageSize, string? cursor)
    {
        var payload = JsonSerializer.Serialize(new
        {
            query = _query,
            variables = new { searchQuery, pageSize, cursor }
        });

        using var content = new StringContent(payload, Encoding.UTF8, "application/json");
        var response = await _http.PostAsync(_apiUrl, content);
        var body = await response.Content.ReadAsStringAsync();

        var parsed = JsonSerializer.Deserialize<GraphQlResponse>(body, JsonOptions)!;
        return (parsed, body);
    }
}
