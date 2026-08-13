namespace Lab01.Metrics;

public static class Rq05Rq06Processor
{
    public const string UnidentifiedLanguage = "Sem linguagem identificada";

    // GitHub Octoverse 2025, ranking por contribuidores (agosto de 2025).
    private static readonly HashSet<string> PopularLanguages = new(StringComparer.OrdinalIgnoreCase)
    {
        "TypeScript", "Python", "JavaScript", "Java", "C#",
        "PHP", "Shell", "C++", "HCL", "Go"
    };

    public static Rq05Rq06Metrics Calculate(string? primaryLanguage, int openIssues, int closedIssues)
    {
        if (openIssues < 0) throw new ArgumentOutOfRangeException(nameof(openIssues));
        if (closedIssues < 0) throw new ArgumentOutOfRangeException(nameof(closedIssues));

        var language = string.IsNullOrWhiteSpace(primaryLanguage)
            ? UnidentifiedLanguage
            : primaryLanguage.Trim();
        var totalIssues = openIssues + closedIssues;

        return new Rq05Rq06Metrics(
            language,
            language != UnidentifiedLanguage && PopularLanguages.Contains(language),
            totalIssues,
            totalIssues > 0,
            totalIssues == 0 ? null : (decimal)closedIssues / totalIssues * 100m);
    }
}

public record Rq05Rq06Metrics(
    string PrimaryLanguage,
    bool IsPopularLanguage,
    int TotalIssues,
    bool HasIssues,
    decimal? ClosedIssuesPercentage);
