using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Lab01.Collector;

public class GitHubApi
{
    private const string ApiUrl = "https://api.github.com/graphql";

    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };

    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(2) };
    private readonly string _query;

    public GitHubApi(string token, string queriesPath)
    {
        _query = string.Join("\n\n", Directory.GetFiles(queriesPath, "*.graphql").Select(File.ReadAllText));

        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("lab01-eng-sw");
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
        var response = await _http.PostAsync(ApiUrl, content);
        var body = await response.Content.ReadAsStringAsync();

        return (JsonSerializer.Deserialize<GraphQlResponse>(body, Json)!, body);
    }
}
