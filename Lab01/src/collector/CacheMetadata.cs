namespace Lab01.Collector;

public sealed record CacheMetadata(
    string? SearchQuery,
    int? PageSize,
    int? TargetRepos,
    string QueryVersion,
    DateTimeOffset? CollectedAt,
    DateTimeOffset? CompletedAt,
    string? RunStamp,
    int? RepositoriesCollected,
    bool Completed
)
{
    public bool CanUseCache(CollectorOptions options, DateTimeOffset nowUtc, string queryVersion)
    {
        if (!Completed)
            return false;

        if (string.IsNullOrWhiteSpace(SearchQuery) || PageSize is null || TargetRepos is null
            || CollectedAt is null || CompletedAt is null || string.IsNullOrWhiteSpace(RunStamp) || RepositoriesCollected is null)
        {
            return false;
        }

        if (options.SearchQuery != SearchQuery)
            return false;

        if (options.PageSize != PageSize)
            return false;

        if (options.TargetRepos != TargetRepos)
            return false;

        if (queryVersion != QueryVersion)
            return false;

        if (RepositoriesCollected < options.TargetRepos)
            return false;

        if (CompletedAt > nowUtc)
            return false;

        if (nowUtc - CompletedAt.Value >= TimeSpan.FromHours(24))
            return false;

        return true;
    }
}