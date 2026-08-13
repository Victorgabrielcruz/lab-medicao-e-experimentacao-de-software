using System.Globalization;
using System.Text;

namespace Lab01.Collector;

public static class CsvExporter
{
    private const string Header =
        "id,name_with_owner,url,owner,stargazer_count,is_archived,collected_at,page_number," +
        "created_at,merged_pull_requests,total_pull_requests," +
        "releases_count,updated_at,pushed_at,default_branch,total_commits,last_commit_date," +
        "primary_language,open_issues,closed_issues";

    public static void Write(string path, List<CollectedRepo> rows, DateTime collectedAt)
    {
        var timestamp = collectedAt.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);

        var sb = new StringBuilder();
        sb.AppendLine(Header);

        foreach (var row in rows)
        {
            var repo = row.Repo;
            var history = repo.DefaultBranchRef?.Target?.History;

            sb.AppendLine(string.Join(",",
                repo.Id,
                Escape(repo.NameWithOwner),
                Escape(repo.Url),
                Escape(repo.Owner.Login),
                repo.StargazerCount,
                repo.IsArchived.ToString().ToLowerInvariant(),
                timestamp,
                row.Page,
                repo.CreatedAt,
                repo.MergedPullRequests.TotalCount,
                repo.TotalPullRequests.TotalCount,
                repo.Releases.TotalCount,
                repo.UpdatedAt,
                repo.PushedAt,
                Escape(repo.DefaultBranchRef?.Name),
                history?.TotalCount.ToString(),
                history?.Nodes.FirstOrDefault()?.CommittedDate,
                Escape(repo.PrimaryLanguage?.Name),
                repo.OpenIssues.TotalCount,
                repo.ClosedIssues.TotalCount));
        }

        File.WriteAllText(path, sb.ToString(), new UTF8Encoding(false));
    }

    private static string Escape(string? value)
    {
        if (string.IsNullOrEmpty(value)) return "";
        return value.Contains(',') ? $"\"{value}\"" : value;
    }
}
