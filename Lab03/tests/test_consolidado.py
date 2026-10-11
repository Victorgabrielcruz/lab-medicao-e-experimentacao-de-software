import hashlib
import json

import pytest

from pipeline import consolidado

JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
REPOS = [{"id": 1, "full_name": "org/a", "workflow_runs": [{"id": 10, "name": "CI\n]"}, {"id": 11, "name": "ação"}]},
         {"id": 2, "full_name": "org/b", "workflow_runs": []},
         {"id": 3, "full_name": "org/c", "workflow_runs": [{"id": 30, "name": "},"}]}]
DESCARTES = [{"id": 9, "full_name": "org/z", "motivo": "repositorio_inacessivel"}]


@pytest.mark.parametrize("repos", [REPOS, REPOS[:1], []])
@pytest.mark.parametrize("cabecalho, rodape", [({"janela": JANELA}, {"descartes": DESCARTES}),
                                               ({"janela": JANELA}, None), ({}, None), ({}, {"descartes": []})])
def test_arquivo_e_json_valido_com_as_mesmas_chaves_e_a_mesma_ordem(tmp_path, repos, cabecalho, rodape):
    caminho = tmp_path / "raw" / "runs.json"
    assert consolidado.gravar(caminho, cabecalho, iter(repos), rodape) == len(repos)
    esperado = {**cabecalho, "repositorios": repos, **(rodape or {})}
    lido = json.loads(caminho.read_text(encoding="utf-8"))
    assert lido == esperado and list(lido) == list(esperado)
    assert list(consolidado.repositorios(caminho)) == repos
    assert consolidado.cabecalho(caminho) == {**cabecalho, **(rodape or {})}


def test_um_repositorio_por_linha(tmp_path):
    caminho = tmp_path / "runs.json"
    consolidado.gravar(caminho, {"janela": JANELA}, REPOS, {"descartes": DESCARTES})
    linhas = caminho.read_bytes().decode("utf-8").split("\n")
    assert len(linhas) == len(REPOS) + 3 and linhas[-1] == "" and b"\r" not in caminho.read_bytes()
    assert linhas[0].endswith('"repositorios": [') and linhas[-2].startswith('], "descartes"')
    assert [json.loads(linha.removesuffix(",")) for linha in linhas[1:-2]] == REPOS


def test_leitura_entrega_um_repositorio_por_vez(tmp_path):
    caminho = tmp_path / "runs.json"
    consolidado.gravar(caminho, {"janela": JANELA}, REPOS)
    leitor = consolidado.repositorios(caminho)
    assert next(leitor) == REPOS[0]
    caminho_novo = tmp_path / "outro.json"
    consolidado.gravar(caminho_novo, {}, (repo for repo in [next(leitor)]))
    assert list(consolidado.repositorios(caminho_novo)) == [REPOS[1]]


@pytest.mark.parametrize("formatar", [json.dumps, lambda d: json.dumps(d, indent=2),
                                      lambda d: json.dumps(d, separators=(",", ":"))])
def test_consolidados_antigos_sao_lidos_inteiros(tmp_path, formatar):
    caminho = tmp_path / "antigo.json"
    caminho.write_text(formatar({"janela": JANELA, "repositorios": REPOS, "descartes": DESCARTES}), encoding="utf-8")
    assert list(consolidado.repositorios(caminho)) == REPOS
    assert consolidado.cabecalho(caminho) == {"janela": JANELA, "descartes": DESCARTES}


def test_rodape_maior_que_o_bloco_de_leitura(tmp_path, monkeypatch):
    monkeypatch.setattr(consolidado, "BLOCO", 16)
    caminho = tmp_path / "runs.json"
    descartes = [{"id": i, "detalhe": "x" * 40} for i in range(20)]
    consolidado.gravar(caminho, {"janela": JANELA}, REPOS, {"descartes": descartes})
    assert consolidado.cabecalho(caminho) == {"janela": JANELA, "descartes": descartes}
    assert consolidado.sha256(caminho) == hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_falha_no_meio_da_gravacao_preserva_o_arquivo_anterior(tmp_path):
    caminho = tmp_path / "runs.json"
    consolidado.gravar(caminho, {"janela": JANELA}, REPOS)
    anterior = caminho.read_bytes()

    def interrompido():
        yield REPOS[0]
        raise RuntimeError("leitura do checkpoint falhou")

    with pytest.raises(RuntimeError):
        consolidado.gravar(caminho, {"janela": JANELA}, interrompido())
    assert caminho.read_bytes() == anterior
    assert [p.name for p in tmp_path.iterdir()] == ["runs.json"]


def test_json_invalido_em_uma_linha_e_erro(tmp_path):
    caminho = tmp_path / "runs.json"
    consolidado.gravar(caminho, {"janela": JANELA}, REPOS)
    caminho.write_text(caminho.read_text(encoding="utf-8").replace('{"id": 2,', '{"id": 2;'), encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        list(consolidado.repositorios(caminho))
