namespace Lab01.Collector;

// Parametros da coleta, lidos do .env. Ficam tipados em um lugar so para que
// o resto do codigo nao dependa de dicionario de string.
public sealed record CollectorOptions(
    string Token,
    string SearchQuery,
    int PageSize,
    int TargetRepos)
{
    public static CollectorOptions FromEnvFile(string path)
    {
        if (!File.Exists(path))
            throw new FatalApiException($"arquivo .env nao encontrado em {path}");

        var env = File.ReadAllLines(path)
            .Where(line => line.Contains('=') && !line.TrimStart().StartsWith('#'))
            .ToDictionary(line => line.Split('=', 2)[0].Trim(), line => line.Split('=', 2)[1].Trim());

        return new CollectorOptions(
            Required(env, "GITHUB_TOKEN"),
            Required(env, "SEARCH_QUERY"),
            int.Parse(Required(env, "PAGE_SIZE")),
            int.Parse(Required(env, "TARGET_REPOS")));
    }

    private static string Required(Dictionary<string, string> env, string key) =>
        env.TryGetValue(key, out var value) && value.Length > 0
            ? value
            : throw new FatalApiException($"chave {key} ausente ou vazia no .env");
}
