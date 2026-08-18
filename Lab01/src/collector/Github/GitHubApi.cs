using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace Lab01.Collector;

public class GitHubApi
{
    private const string ApiUrl = "https://api.github.com/graphql";
    private const int MaxAttempts = 4;

    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };

    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMinutes(2) };
    private readonly string _query;

    public GitHubApi(string token, string queriesPath)
    {
        _query = string.Join("\n\n", Directory.GetFiles(queriesPath, "*.graphql").Select(File.ReadAllText));

        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("lab01-eng-sw");
    }

    public static ResponseData ParsePage(string rawJson) =>
        JsonSerializer.Deserialize<GraphQlResponse>(rawJson, Json)!.Data!;

    public async Task<(ResponseData Data, string Raw)> FetchPageAsync(
        string searchQuery, int pageSize, string? cursor)
    {
        for (var attempt = 1; ; attempt++)
        {
            try
            {
                return await SendAsync(searchQuery, pageSize, cursor);
            }
            catch (TransientApiException ex)
            {
                if (attempt == MaxAttempts)
                    throw new FatalApiException($"{MaxAttempts} tentativas falharam. Ultimo erro: {ex.Message}");

                var delay = TimeSpan.FromSeconds(5 * Math.Pow(2, attempt - 1));
                Log.Warn($"tentativa {attempt}/{MaxAttempts}: {ex.Message} | repetindo em {delay.TotalSeconds}s");
                await Task.Delay(delay);
            }
        }
    }

    private async Task<(ResponseData, string)> SendAsync(string searchQuery, int pageSize, string? cursor)
    {
        var payload = JsonSerializer.Serialize(new
        {
            query = _query,
            variables = new { searchQuery, pageSize, cursor }
        });

        using var content = new StringContent(payload, Encoding.UTF8, "application/json");

        HttpResponseMessage response;
        try
        {
            response = await _http.PostAsync(ApiUrl, content);
        }
        catch (HttpRequestException ex)
        {
            throw new TransientApiException($"falha de rede: {ex.Message}");
        }
        catch (TaskCanceledException)
        {
            throw new TransientApiException("timeout da requisicao");
        }

        var body = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
            throw Classify(response.StatusCode, body);

        var parsed = JsonSerializer.Deserialize<GraphQlResponse>(body, Json)!;

        // A API pode devolver 200 com um array "errors" no corpo.
        if (parsed.Errors is { Count: > 0 })
        {
            var messages = string.Join(" | ", parsed.Errors.Select(e => e.Message));

            if (parsed.Errors.Any(e => e.Type == "RATE_LIMITED"))
                throw new TransientApiException($"rate limit: {messages}");

            throw new FatalApiException($"erro GraphQL: {messages}");
        }

        if (parsed.Data is null)
            throw new TransientApiException($"resposta sem 'data': {Preview(body)}");

        return (parsed.Data, body);
    }

    private static Exception Classify(HttpStatusCode status, string body) => (int)status switch
    {
        401 => new FatalApiException(
            "401 token invalido ou expirado. Gere outro em github.com/settings/tokens e atualize o .env"),

        403 when body.Contains("rate limit", StringComparison.OrdinalIgnoreCase) =>
            new TransientApiException("403 rate limit atingido"),

        403 => new FatalApiException(
            "403 acesso negado. Confira o header User-Agent e as permissoes do token"),

        400 => new FatalApiException($"400 requisicao malformada, provavel erro na query: {Preview(body)}"),

        429 => new TransientApiException("429 requisicoes demais"),

        >= 500 => new TransientApiException(
            $"{(int)status} erro no servidor do GitHub."),

        _ => new FatalApiException($"{(int)status} {Preview(body)}")
    };

    private static string Preview(string body) =>
        body.Length <= 200 ? body : body[..200] + "...";
}
