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

    private string FilePath(string runStamp, int page) =>
        Path.Combine(_directory, $"repos_raw_{runStamp}_p{page:D3}.json");
}
