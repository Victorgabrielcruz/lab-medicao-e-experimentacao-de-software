using System.Globalization;

namespace Lab01.Collector.Collection;

public sealed class CollectionCache(CacheStore metadata, PageStore pages)
{
    private const string TimestampFormat = "yyyy-MM-ddTHH:mm:ssZ";

    public bool TryRestore(CollectorOptions options, string queryVersion, out CollectionResult? result)
    {
        result = null;

        if (!options.UseCache)
        {
            Log.Info("cache desabilitado pelo arquivo .env");
            return false;
        }

        var metadata1 = metadata.Load();
        if (metadata1 is null)
        {
            Log.Info("nenhum metadata de cache encontrado");
            return false;
        }

        if (!metadata1.CanUseCache(options, DateTimeOffset.UtcNow, queryVersion))
        {
            Log.Info("cache encontrado, mas invalido, expirado ou incompativel");
            return false;
        }

        Log.Info("metadata de cache compativel; verificando arquivos locais");
        if (!pages.TryReadCache(
                metadata1.RunStamp!,
                options.TargetRepos,
                out var repositories,
                out var pagesRead,
                out var duplicates))
        {
            Log.Warn("metadata de cache valido, mas arquivos locais invalidos ou insuficientes; consultando API");
            return false;
        }

        result = new CollectionResult(
            repositories,
            metadata1.RunStamp!,
            metadata1.CollectedAt!.Value.UtcDateTime.ToString(TimestampFormat, CultureInfo.InvariantCulture),
            pagesRead,
            duplicates,
            null);
        Log.Info($"cache utilizado | {result.Repositories.Count} repositorios recuperados de data/raw sem nova requisicao");
        return true;
    }

    public void SaveMetadata(CollectorOptions options, string queryVersion, CollectionResult result)
    {
        var metadata1 = new CacheMetadata(
            SearchQuery: options.SearchQuery,
            PageSize: options.PageSize,
            TargetRepos: options.TargetRepos,
            QueryVersion: queryVersion,
            CollectedAt: DateTimeOffset.Parse(
                result.CollectedAt,
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal),
            CompletedAt: DateTimeOffset.UtcNow,
            RunStamp: result.RunStamp,
            RepositoriesCollected: result.Repositories.Count,
            Completed: true);

        metadata.Save(metadata1);
        Log.Info($"metadata de cache atualizado: {result.RunStamp}");
    }
}
