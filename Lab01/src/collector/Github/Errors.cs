namespace Lab01.Collector;

// Transitorio: vale retentar (rede, timeout, 5xx, rate limit).
public class TransientApiException : Exception
{
    public TransientApiException(string message) : base(message) { }
}

// Fatal: retentar nao resolve (token invalido, query malformada).
public class FatalApiException : Exception
{
    public FatalApiException(string message) : base(message) { }
}
