namespace Lab01.Collector;

public record GraphQlResponse(ResponseData Data);

public record ResponseData(RateLimit RateLimit, SearchResult Search);

public record RateLimit(int Cost, int Remaining, int Limit, string ResetAt);

public record SearchResult(int RepositoryCount, PageInfo PageInfo, List<Repository> Nodes);

public record PageInfo(bool HasNextPage, string? EndCursor);

public record Repository(
    string Id,
    string NameWithOwner,
    string Url,
    Owner Owner,
    int StargazerCount,
    bool IsArchived,
    string CreatedAt,
    Count MergedPullRequests,
    Count TotalPullRequests,
    Count Releases,
    string UpdatedAt,
    string PushedAt,
    BranchRef? DefaultBranchRef,
    Language? PrimaryLanguage,
    Count OpenIssues,
    Count ClosedIssues);

public record Owner(string Login);

public record Count(int TotalCount);

public record Language(string Name);

public record BranchRef(string Name, CommitTarget? Target);

public record CommitTarget(History History);

public record History(int TotalCount, List<Commit> Nodes);

public record Commit(string CommittedDate);
