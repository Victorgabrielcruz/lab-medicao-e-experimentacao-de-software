using System.Text.Json;

namespace Lab01.Collector;

// Guarda e rele as respostas brutas de cada pagina. Sao a evidencia da coleta
// exigida pela metodologia e o que permite retomar sem gastar requisicao.
public sealed class PageStore
{
    private readonly string _directory;

    public PageStore(string directory)
    {
        _directory = directory;
        Directory.CreateDirectory(directory);
    }

    public void Save(string runStamp, int page, string rawJson) =>
        File.WriteAllText(FilePath(runStamp, page), rawJson);

    public IEnumerable<Repository> ReadAll(string runStamp)
    {
        var files = Directory
            .GetFiles(_directory, $"repos_raw_{runStamp}_p*.json")
            .OrderBy(file => file);

        foreach (var file in files)
        {
            var data = GitHubApi.ParsePage(File.ReadAllText(file));

            foreach (var repository in data.Search.Nodes.OfType<Repository>())
                yield return repository;
        }
    }

    public bool TryReadCache(string runStamp, int targetRepos,
        out IReadOnlyList<Repository> repositories,
        out int pagesRead,
        out int duplicates)
    {
        repositories = Array.Empty<Repository>();
        pagesRead = 0;
        duplicates = 0;

        if (targetRepos < 1)
            return false;

        var files = Directory
            .GetFiles(_directory, $"repos_raw_{runStamp}_p*.json")
            .OrderBy(file => file)
            .ToList();

        if (files.Count == 0)
            return false;

        var recovered = new List<Repository>();
        var seenIds = new HashSet<string>();

        try
        {
            foreach (var file in files)
            {
                var rawJson = File.ReadAllText(file);
                var data = GitHubApi.ParsePage(rawJson);
                pagesRead++;

                foreach (var repository in data.Search.Nodes.OfType<Repository>())
                {
                    if (seenIds.Add(repository.Id))
                    {
                        recovered.Add(repository);
                    }
                    else
                    {
                        duplicates++;
                    }
                }
            }
        }
        catch (IOException)
        {
            return false;
        }
        catch (JsonException)
        {
            return false;
        }

        if (recovered.Count < targetRepos)
            return false;

        repositories = recovered.Take(targetRepos).ToList();
        return true;
    }
    
    private string FilePath(string runStamp, int page) =>
        Path.Combine(_directory, $"repos_raw_{runStamp}_p{page:D3}.json");
    
}
