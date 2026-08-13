using Lab01.Metrics;

AssertMetrics("Python", 20, 80, "Python", true, 100, true, 80m);
AssertMetrics("Java", 10, 0, "Java", true, 10, true, 0m);
AssertMetrics("Rust", 0, 10, "Rust", false, 10, true, 100m);
AssertMetrics(null, 0, 0, Rq05Rq06Processor.UnidentifiedLanguage, false, 0, false, null);

Console.WriteLine("RQ05/RQ06: todos os testes passaram.");

static void AssertMetrics(
    string? language, int open, int closed, string expectedLanguage, bool expectedPopular,
    int expectedTotal, bool expectedHasIssues, decimal? expectedPercentage)
{
    var result = Rq05Rq06Processor.Calculate(language, open, closed);
    if (result.PrimaryLanguage != expectedLanguage ||
        result.IsPopularLanguage != expectedPopular ||
        result.TotalIssues != expectedTotal ||
        result.HasIssues != expectedHasIssues ||
        result.ClosedIssuesPercentage != expectedPercentage)
    {
        throw new InvalidOperationException($"Resultado inesperado para {language ?? "null"}.");
    }
}
