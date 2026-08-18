namespace Lab01.Collector;

public sealed record CollectionResult(
    IReadOnlyList<Repository> Repositories,
    string RunStamp,
    string CollectedAt,
    int LastPage,
    int Duplicates,
    string? LastCursor);
