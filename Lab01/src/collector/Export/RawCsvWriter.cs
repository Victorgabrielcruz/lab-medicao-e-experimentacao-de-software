namespace Lab01.Collector;

// Escreve o CSV bruto, que e o contrato entre a coleta em C# e a analise em
// Python. Mudar coluna aqui quebra src/metrics e src/build_dataset.
public static class RawCsvWriter
{
    private const string Header =
        "id,name_with_owner,url,owner,stargazer_count,is_archived,collected_at," +
        "created_at,merged_pull_requests,total_pull_requests," +
        "releases_count,updated_at,pushed_at,default_branch,total_commits,last_commit_date," +
        "primary_language,open_issues,closed_issues";

    public static void Write(string path, IEnumerable<Repository> repositories, string collectedAt)
    {
        var lines = new List<string> { Header };

        foreach (var repository in repositories)
        {
            var commits = repository.DefaultBranchRef?.Target;

            lines.Add(string.Join(",",
                repository.Id,
                CsvField.Escape(repository.NameWithOwner),
                CsvField.Escape(repository.Url),
                CsvField.Escape(repository.Owner.Login),
                repository.StargazerCount,
                repository.IsArchived.ToString().ToLowerInvariant(),
                collectedAt,
                repository.CreatedAt,
                repository.MergedPullRequests.TotalCount,
                repository.TotalPullRequests.TotalCount,
                repository.Releases.TotalCount,
                repository.UpdatedAt,
                repository.PushedAt,
                CsvField.Escape(repository.DefaultBranchRef?.Name),
                commits?.LastCommit.TotalCount,
                commits?.LastCommit.Nodes.FirstOrDefault()?.CommittedDate,
                CsvField.Escape(repository.PrimaryLanguage?.Name),
                repository.OpenIssues.TotalCount,
                repository.ClosedIssues.TotalCount));
        }

        File.WriteAllLines(path, lines);
    }
}
