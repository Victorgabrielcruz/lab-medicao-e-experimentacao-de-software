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
        var parsed = JsonSerializer.Deserialize<GraphQlResponse>(body, Json);

        if (!response.IsSuccessStatusCode || parsed?.Data is null)
        {
            throw new InvalidOperationException(
                $"A API GraphQL do GitHub não retornou dados (HTTP {(int)response.StatusCode}). " +
                $"Detalhe: {GetErrorMessage(body)}");
        }

        return (parsed, body);
    }

    private static string GetErrorMessage(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            if (document.RootElement.TryGetProperty("message", out var message))
                return message.GetString() ?? "mensagem não informada";

            if (document.RootElement.TryGetProperty("errors", out var errors))
            {
                var details = errors.EnumerateArray()
                    .Select(error => error.TryGetProperty("message", out var errorMessage)
                        ? errorMessage.GetString()
                        : null)
                    .Where(message => !string.IsNullOrWhiteSpace(message));
                return string.Join("; ", details);
            }
        }
        catch (JsonException)
        {
            // A resposta não era JSON; a mensagem genérica abaixo será usada.
        }

        return "mensagem não informada";
    }
}
