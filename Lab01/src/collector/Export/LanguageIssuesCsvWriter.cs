using System.Globalization;
using Lab01.Metrics;

namespace Lab01.Collector;

// Saida piloto das RQ05 e RQ06 gerada durante a coleta.
// Duplica src/metrics/rq05_rq06_language_issues.py, que e quem alimenta o
// dataset oficial. Manter enquanto o grupo nao decidir qual das duas fica.
public static class LanguageIssuesCsvWriter
{
    private const string Header =
        "id,name_with_owner,collected_at,primary_language,is_popular_language," +
        "open_issues,closed_issues,total_issues,has_issues,closed_issues_percentage";

    public static void Write(string path, IEnumerable<Repository> repositories, string collectedAt)
    {
        var lines = new List<string> { Header };

        foreach (var repository in repositories)
        {
            var metrics = Rq05Rq06Processor.Calculate(
                repository.PrimaryLanguage?.Name,
                repository.OpenIssues.TotalCount,
                repository.ClosedIssues.TotalCount);

            lines.Add(string.Join(",",
                repository.Id,
                CsvField.Escape(repository.NameWithOwner),
                collectedAt,
                CsvField.Escape(metrics.PrimaryLanguage),
                metrics.IsPopularLanguage.ToString().ToLowerInvariant(),
                repository.OpenIssues.TotalCount,
                repository.ClosedIssues.TotalCount,
                metrics.TotalIssues,
                metrics.HasIssues.ToString().ToLowerInvariant(),
                metrics.ClosedIssuesPercentage?.ToString(CultureInfo.InvariantCulture) ?? ""));
        }

        File.WriteAllLines(path, lines);
    }
}
