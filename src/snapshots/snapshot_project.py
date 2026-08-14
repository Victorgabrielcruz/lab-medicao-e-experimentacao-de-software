"""Exporta os itens do GitHub Projects (v2) e o status atual para CSV.

Uso:
    python src/snapshots/snapshot_project.py [sprint]

Exemplo:
    python src/snapshots/snapshot_project.py Lab01S01

O GitHub Projects nao guarda historico de mudanca de coluna consultavel pela
API. A serie de snapshots acumulada sprint a sprint faz esse papel e vira a
base dos Labs 04 e 05, entao nenhum arquivo antigo deve ser sobrescrito.
"""

import csv
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUERY_FILE = ROOT / "src" / "github" / "queries" / "project" / "snapshot-project.graphql"
OUTPUT_DIR = ROOT / "data" / "snapshots"
API_URL = "https://api.github.com/graphql"

COLUNAS = [
    "sprint",
    "data_snapshot",
    "item_id",
    "tipo",
    "numero",
    "titulo",
    "status",
    "responsaveis",
    "labels",
    "estado",
    "criado_em",
    "fechado_em",
    "atualizado_em",
    "repositorio",
    "url",
]


def ler_env():
    caminho = ROOT / ".env"
    if not caminho.exists():
        raise SystemExit(f"arquivo .env nao encontrado em {caminho}")

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    return {
        linha.split("=", 1)[0].strip(): linha.split("=", 1)[1].strip()
        for linha in linhas
        if "=" in linha and not linha.lstrip().startswith("#")
    }


def exigir(env, chave):
    valor = env.get(chave, "")
    if not valor:
        raise SystemExit(f"chave {chave} ausente ou vazia no .env")
    return valor


def consultar(token, query, variaveis):
    corpo = json.dumps({"query": query, "variables": variaveis}).encode("utf-8")
    requisicao = urllib.request.Request(
        API_URL,
        data=corpo,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "lab01-eng-sw",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")[:300]
        if erro.code == 401:
            raise SystemExit("401 token invalido ou expirado")
        raise SystemExit(f"HTTP {erro.code}: {detalhe}")

    if dados.get("errors"):
        mensagens = " | ".join(e.get("message", "") for e in dados["errors"])
        if "read:project" in mensagens or "INSUFFICIENT_SCOPES" in mensagens:
            raise SystemExit(
                "o token nao tem o escopo read:project. "
                "Gere outro em github.com/settings/tokens marcando read:project"
            )
        raise SystemExit(f"erro GraphQL: {mensagens}")

    return dados["data"]


def valores_dos_campos(item):
    """Achata fieldValues em {nome_do_campo: valor}. O Status vem daqui."""
    campos = {}
    for valor in item.get("fieldValues", {}).get("nodes", []):
        nome_campo = (valor.get("field") or {}).get("name")
        if not nome_campo:
            continue
        for chave in ("name", "title", "text", "date", "number"):
            if valor.get(chave) is not None:
                campos[nome_campo] = valor[chave]
                break
    return campos


def montar_linha(item, sprint, agora):
    conteudo = item.get("content") or {}
    campos = valores_dos_campos(item)

    assignees = [n["login"] for n in (conteudo.get("assignees") or {}).get("nodes", [])]
    labels = [n["name"] for n in (conteudo.get("labels") or {}).get("nodes", [])]

    return {
        "sprint": sprint,
        "data_snapshot": agora,
        "item_id": item.get("id", ""),
        "tipo": item.get("type", ""),
        "numero": conteudo.get("number", ""),
        "titulo": conteudo.get("title") or campos.get("Title", ""),
        "status": campos.get("Status", ""),
        "responsaveis": ";".join(assignees),
        "labels": ";".join(labels),
        "estado": conteudo.get("state", ""),
        "criado_em": conteudo.get("createdAt", ""),
        "fechado_em": conteudo.get("closedAt") or "",
        "atualizado_em": item.get("updatedAt", ""),
        "repositorio": (conteudo.get("repository") or {}).get("nameWithOwner", ""),
        "url": conteudo.get("url", ""),
    }


def coletar_itens(token, query, owner, numero):
    itens = []
    cursor = None
    titulo = ""

    while True:
        dados = consultar(token, query, {"owner": owner, "number": numero, "cursor": cursor})

        dono = dados.get("repositoryOwner")
        if not dono or not dono.get("projectV2"):
            raise SystemExit(
                f"projeto numero {numero} nao encontrado para {owner}. "
                "Confira PROJECT_OWNER e PROJECT_NUMBER no .env"
            )

        board = dono["projectV2"]
        titulo = board["title"]
        pagina = board["items"]

        itens.extend(pagina["nodes"])
        print(f"  {len(itens)}/{pagina['totalCount']} itens")

        if not pagina["pageInfo"]["hasNextPage"]:
            return titulo, itens

        cursor = pagina["pageInfo"]["endCursor"]


def main():
    env = ler_env()
    sprint = sys.argv[1] if len(sys.argv) > 1 else env.get("SPRINT", "sem-sprint")
    owner = exigir(env, "PROJECT_OWNER")
    numero = int(exigir(env, "PROJECT_NUMBER"))
    token = exigir(env, "GITHUB_TOKEN")

    query = QUERY_FILE.read_text(encoding="utf-8")
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"projeto {owner}/{numero} | sprint {sprint}")
    titulo, itens = coletar_itens(token, query, owner, numero)
    print(f"board: {titulo}")

    linhas = [montar_linha(item, sprint, agora) for item in itens]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    carimbo = agora.replace(":", "").replace("-", "")
    saida = OUTPUT_DIR / f"snapshot_{sprint}_{carimbo}.csv"

    with saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)

    por_status = {}
    for linha in linhas:
        chave = linha["status"] or "(sem status)"
        por_status[chave] = por_status.get(chave, 0) + 1

    print()
    for status, quantidade in sorted(por_status.items()):
        print(f"  {status:<20} {quantidade}")
    print(f"\n{len(linhas)} itens | {saida}")


if __name__ == "__main__":
    main()
