import copy
import csv
import json
import runpy
import sys
from pathlib import Path

import pytest

from pipeline import avaliacao_heuristica as av, cfr_b, consolidado
from pipeline.config import ConfigError

JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def gravar_json(p, d):
    p.write_text(json.dumps(d), encoding="utf-8")


def gravar_consenso(p, rows):
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["repo_id", "full_name", "release_id", "tag_name", "corretiva", "origem_corretiva"])
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def entradas(tmp_path):
    pasta = tmp_path / "amostra"
    pasta.mkdir()
    rels = [{"release_id": i, "tag_name": t, "published_at": d}
            for i, t, d in [(1, "v2.3.0", "2026-05-10T00:00:00Z"),
                            (3, "v2.4.1", "2026-05-14T00:00:00Z"),
                            (4, "v2.5.0", "2026-09-30T00:00:00Z")]]
    manifesto = {"janela": JANELA, "incluir_prereleases": False, "total_repositorios": 1,
                 "total_releases": 3, "releases_por_repositorio": 3,
                 "repositorios": [{"repo_id": 10, "full_name": "org/projeto", "releases": rels}]}
    gravar_json(pasta / "amostra_ouro.json", manifesto)
    consenso = [{"repo_id": 10, "full_name": "org/projeto", "release_id": r["release_id"],
                 "tag_name": r["tag_name"], "corretiva": label, "origem_corretiva": "unanime"}
                for r, label in zip(rels, ["sim", "nao", "sim"])]
    gravar_consenso(pasta / "consenso_releases.csv", consenso)
    pred = {"janela": JANELA, "variante": "b", "versao_heuristica": cfr_b.VERSAO_HEURISTICA,
            "repositorios": [{"id": 10, "full_name": "org/projeto", "releases": [
                r | {"corretiva": v, "falhou": not v, "censurada": r["release_id"] == 4,
                     "motivo_corretiva": "mensagem_commit" if v else "sem_sinais"}
                for r, v in zip(rels, [True, True, False])]}]}
    caminho = tmp_path / "cfr_b.json"
    gravar_json(caminho, pred)
    return pasta, caminho, manifesto, consenso, pred


def test_exemplo_enunciado_40_preditas_30_confirmadas_50_consenso():
    verdade = [True] * 30 + [False] * 10 + [True] * 20 + [False] * 40
    pred = [True] * 40 + [False] * 60
    r = av.calcular_metricas(verdade, pred)
    assert r["precisao"] == .75 and r["recall"] == .60
    assert r["f1"] == pytest.approx(2 / 3)
    assert r["matriz_confusao"] == {"linhas_consenso": ["nao", "sim"], "colunas_previsao": ["nao", "sim"],
                                    "valores": [[40, 10], [20, 30]], "VP": 30, "FP": 10, "FN": 20, "VN": 40}
    assert r["suporte_positivo"] == 50 and r["suporte_negativo"] == 50


@pytest.mark.parametrize("y,p,esperado", [
    ([], [], (None, None, None)), ([False], [False], (None, None, None)),
    ([False], [True], (0, None, 0)), ([True], [False], (None, 0, 0)),
    ([True], [True], (1, 1, 1)), ([True, False], [False, True], (0, 0, 0)),
])
def test_denominador_nulo_nao_se_confunde_com_zero_observado(y, p, esperado):
    r = av.calcular_metricas(y, p)
    assert (r["precisao"], r["recall"], r["f1"]) == esperado


@pytest.mark.parametrize("y,p", [([True], []), ([1], [True]), ([None], [False])])
def test_metricas_rejeitam_vetores_invalidos(y, p):
    with pytest.raises(ConfigError):
        av.calcular_metricas(y, p)


def test_execucao_por_id_inclui_censuradas_e_ignora_falhou(entradas, tmp_path, monkeypatch):
    pasta, caminho, m, consenso, p = entradas
    p["repositorios"][0]["releases"].reverse()
    p["repositorios"].append({"id": 99, "full_name": "fora/amostra", "releases": []})
    gravar_json(caminho, p)
    antes = {f: f.read_bytes() for f in [caminho, *pasta.iterdir()]}
    monkeypatch.setattr("requests.sessions.Session.request", lambda *a, **k: pytest.fail("Não deve consultar a rede"))
    out = tmp_path / "saida"
    r = av.executar(caminho, pasta=pasta, saida=out)
    assert r["avaliacao_completa"] and r["cobertura"]["avaliadas"] == 3
    assert [p["resultado"] for p in r["pares"]] == ["VP", "FP", "FN"]
    assert r["matriz_confusao"]["valores"] == [[0, 1], [1, 1]]
    assert r["precisao"] == r["recall"] == r["f1"] == .5
    assert not r["atinge_limiar_no_subconjunto"]
    assert set(f.name for f in out.iterdir()) == set(av.ARQUIVOS)
    with (out / "pares.csv").open() as f:
        assert [p["previsao"] for p in csv.DictReader(f)] == ["sim", "sim", "nao"]
    assert "**Completa:** 3/3" in (out / "avaliacao.md").read_text()
    with (out / "pendencias.csv").open() as f:
        assert list(csv.DictReader(f)) == []
    assert all(f.read_bytes() == b for f, b in antes.items())
    out2 = tmp_path / "saida2"
    av.executar(caminho, pasta=pasta, saida=out2)
    assert all((out / n).read_bytes() == (out2 / n).read_bytes() for n in av.ARQUIVOS)
    # O arquivo de previsões reduzido também é uma entrada válida e preserva as decisões.
    reavaliado = av.executar(out / "previsoes_amostra.json", pasta=pasta, saida=tmp_path / "saida3")
    assert reavaliado["matriz_confusao"] == r["matriz_confusao"]


def test_ausencias_explicitas_ou_por_linha_omitida_nunca_viram_negativos(entradas, tmp_path):
    pasta, caminho, _, consenso, p = entradas
    consenso[0].update(corretiva="", origem_corretiva="pendente")
    gravar_consenso(pasta / "consenso_releases.csv", consenso[:-1])
    p["repositorios"][0]["releases"][0]["corretiva"] = None
    p["repositorios"][0]["releases"].pop()
    gravar_json(caminho, p)
    r = av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert not r["avaliacao_completa"]
    assert r["cobertura"]["avaliadas"] == 1 and r["cobertura"]["excluidas"] == 2
    assert r["cobertura"]["motivos_exclusao"] == {
        "consenso_ausente": 2, "previsao_ausente": 1, "previsao_indeterminada": 1}
    assert r["matriz_confusao"]["FP"] == 1
    assert r["f1"] == 0
    with (tmp_path / "out/pendencias.csv").open() as f:
        pendencias = list(csv.DictReader(f))
    assert len(pendencias) == 2
    assert pendencias[0]["tipo_pendencia"] == "consenso+evidencias_previsao"
    assert pendencias[1]["tipo_pendencia"] == "consenso+previsao"


def test_nenhuma_previsao_produz_matriz_zero_e_metricas_nulas(entradas, tmp_path):
    pasta, caminho, _, _, p = entradas
    p["repositorios"] = []
    gravar_json(caminho, p)
    r = av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert r["cobertura"]["fracao_avaliada"] == 0
    assert r["f1"] is None and r["atinge_limiar_no_subconjunto"] is None
    assert r["matriz_confusao"]["valores"] == [[0, 0], [0, 0]]


@pytest.mark.parametrize("patch,completo,tipo", [
    (False, False, "commits_compare"), (None, False, "predecessora_historica+commits_compare"),
    (None, True, "predecessora_historica"), (False, True, "evidencias_previsao"),
])
def test_diagnostico_de_pendencias_nao_altera_rotulos(entradas, tmp_path, patch, completo, tipo):
    pasta, caminho, m, _, p = entradas
    m["repositorios"][0]["releases"][0]["compare_url"] = "https://github.com/org/projeto/compare/v2.2.0...v2.3.0"
    gravar_json(pasta / "amostra_ouro.json", m)
    p["repositorios"][0]["releases"][0].update(corretiva=None, patch_semver=patch, compare_completo=completo)
    gravar_json(caminho, p)
    original = caminho.read_bytes()
    r = av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert r["cobertura"]["avaliadas"] == 2 and r["pares"][0]["previsao"] is None
    assert r["cobertura"]["pendencias_por_tipo"] == {tipo: 1}
    with (tmp_path / "out/pendencias.csv").open() as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 1 and linhas[0]["tipo_pendencia"] == tipo
    assert linhas[0]["compare_url"] == m["repositorios"][0]["releases"][0]["compare_url"]
    assert caminho.read_bytes() == original


def test_sinais_resumidos_preservam_decisao_contagem_e_roundtrip(entradas, tmp_path):
    pasta, caminho, _, _, p = entradas
    sinais = [{"sha": str(i), "termo": "fix"} for i in range(20)]
    p["repositorios"][0]["releases"][0]["commits_corretivos"] = sinais
    gravar_json(caminho, p)
    r = av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    filtradas = json.loads((tmp_path / "out/previsoes_amostra.json").read_text())
    rel = filtradas["repositorios"][0]["releases"][0]
    assert rel["corretiva"] is True and rel["total_commits_corretivos"] == 20
    assert rel["exemplos_commits_corretivos"] == sinais[:5] and "commits_corretivos" not in rel
    r2 = av.executar(tmp_path / "out/previsoes_amostra.json", pasta=pasta, saida=tmp_path / "out2")
    assert r2["matriz_confusao"] == r["matriz_confusao"]
    assert json.loads((tmp_path / "out2/previsoes_amostra.json").read_text())["repositorios"] == filtradas["repositorios"]


def test_pares_de_repositorios_diferentes_nao_se_confundem_pela_tag_ou_id_local(entradas, tmp_path):
    pasta, caminho, m, rows, p = entradas
    segundo = copy.deepcopy(m["repositorios"][0])
    segundo.update(repo_id=11, full_name="org/segundo")
    m["repositorios"].append(segundo)
    m.update(total_repositorios=2, total_releases=6)
    gravar_json(pasta / "amostra_ouro.json", m)
    rows.extend([r | {"repo_id": 11, "full_name": "org/segundo", "corretiva": "nao"} for r in rows.copy()])
    gravar_consenso(pasta / "consenso_releases.csv", rows)
    q = copy.deepcopy(p["repositorios"][0])
    q.update(id=11, full_name="org/segundo")
    for r in q["releases"]:
        r["corretiva"] = False
    p["repositorios"].insert(0, q)
    gravar_json(caminho, p)
    r = av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert r["cobertura"]["avaliadas"] == 6 and r["matriz_confusao"]["VN"] == 3
    assert [x["resultado"] for x in r["pares"]] == ["VP", "FP", "FN", "VN", "VN", "VN"]


@pytest.mark.parametrize("mutacao,erro", [
    (lambda p: p.update(variante="a"), "variante=b"),
    (lambda p: p.update(versao_heuristica=None), "Versão"),
    (lambda p: p.update(janela=JANELA | {"inicio": "2025-09-01T00:00:00Z"}), "Janela divergente"),
    (lambda p: p["repositorios"].append(copy.deepcopy(p["repositorios"][0])), "Repositório repetido"),
    (lambda p: p["repositorios"][0]["releases"].append(p["repositorios"][0]["releases"][0]), "Previsão repetida"),
    (lambda p: p["repositorios"][0]["releases"][0].update(corretiva="sim"), "bool ou null"),
    (lambda p: p["repositorios"][0]["releases"][0].update(corretiva=1), "bool ou null"),
    (lambda p: p["repositorios"][0]["releases"][0].pop("corretiva"), "bool ou null"),
    (lambda p: p["repositorios"][0].update(full_name="outro/projeto"), "Nome divergente"),
    (lambda p: p["repositorios"][0]["releases"][0].update(tag_name="v0.0.1"), "Tag divergente"),
    (lambda p: p["repositorios"][0]["releases"][0].update(published_at="2026-05-11T00:00:00Z"), "Data divergente"),
    (lambda p: p["repositorios"][0].pop("releases"), "sem detalhes"),
    (lambda p: p["repositorios"][0]["releases"][0].update(commits_corretivos="fix"), "Sinais de commits"),
])
def test_predicoes_incoerentes_nao_gravam_resultado(entradas, tmp_path, mutacao, erro):
    pasta, caminho, _, _, p = entradas
    mutacao(p)
    gravar_json(caminho, p)
    with pytest.raises(ConfigError, match=erro):
        av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("mutacao,erro", [
    (lambda r: r.append(r[0].copy()), "chave repetida"),
    (lambda r: r[0].update(release_id=999), "fora da amostra"),
    (lambda r: r[0].update(corretiva="incerto"), "Rótulo/origem"),
    (lambda r: r[0].update(corretiva="", origem_corretiva="unanime"), "Rótulo/origem"),
    (lambda r: r[0].update(origem_corretiva="heuristica"), "Origem"),
    (lambda r: r[0].update(repo_id=""), "ID inválido"),
])
def test_consenso_invalido_e_rejeitado(entradas, tmp_path, mutacao, erro):
    pasta, caminho, _, rows, _ = entradas
    mutacao(rows)
    gravar_consenso(pasta / "consenso_releases.csv", rows)
    with pytest.raises(ConfigError, match=erro):
        av.executar(caminho, pasta=pasta, saida=tmp_path / "out")


@pytest.mark.parametrize("conteudo,erro", [
    ("repo_id,release_id,corretiva\n10,1,sim\n", "colunas"),
    ("repo_id,full_name,release_id,tag_name,corretiva,origem_corretiva,repo_id\n", "repetidos"),
    ("repo_id,full_name,release_id,tag_name,corretiva,origem_corretiva\n10,org/projeto\n", "malformada"),
])
def test_csv_com_esquema_errado(entradas, tmp_path, conteudo, erro):
    pasta, caminho, *_ = entradas
    (pasta / "consenso_releases.csv").write_text(conteudo)
    with pytest.raises(ConfigError, match=erro):
        av.executar(caminho, pasta=pasta, saida=tmp_path / "out")


@pytest.mark.parametrize("mutacao", [
    lambda m: m.update(total_releases=99), lambda m: m.update(incluir_prereleases=True),
    lambda m: m["repositorios"].append(m["repositorios"][0]),
    lambda m: m["repositorios"][0]["releases"][0].update(published_at="2020-01-01T00:00:00Z"),
    lambda m: m["repositorios"][0]["releases"][0].update(tag_name=None),
    lambda m: m.update(janela={}),
])
def test_manifesto_inconsistente(entradas, tmp_path, mutacao):
    pasta, caminho, m, *_ = entradas
    mutacao(m)
    gravar_json(pasta / "amostra_ouro.json", m)
    with pytest.raises(ConfigError):
        av.executar(caminho, pasta=pasta, saida=tmp_path / "out")


def test_raw_usa_base_nao_sorteada_e_nao_imputa_negativos(entradas, tmp_path):
    pasta, _, m, *_ = entradas
    rels = [{"id": r["release_id"], "draft": False, "prerelease": False,
             "tag_name": r["tag_name"], "published_at": r["published_at"]} for r in m["repositorios"][0]["releases"]]
    rels.insert(1, {"id": 2, "tag_name": "v2.4.0", "published_at": "2026-05-12T00:00:00Z", "draft": False, "prerelease": False})
    entrada = tmp_path / "releases.json"
    consolidado.gravar(entrada, {"janela": JANELA}, [{"id": 10, "full_name": "org/projeto", "releases": rels}])
    r = av.executar(releases=entrada, pasta=pasta, saida=tmp_path / "out")
    assert [p["previsao"] for p in r["pares"]] == [None, True, None]
    assert r["cobertura"]["avaliadas"] == 1
    assert r["versao_heuristica"] == cfr_b.VERSAO_HEURISTICA
    cp = {"id": 10, "full_name": "org/projeto", "comparacoes": []}
    for base, atual in zip(rels, rels[1:]):
        cp["comparacoes"].append({"release": atual, "release_anterior": base, "commits": [],
                                   "total_commits_api": 0, "total_commits_coletados": 0})
    compare = tmp_path / "compare.json"
    consolidado.gravar(compare, {"janela": JANELA, "definicao_deploy": "release_estavel"}, [cp])
    r = av.executar(releases=entrada, compares=compare, pasta=pasta, saida=tmp_path / "out2")
    assert [p["previsao"] for p in r["pares"]] == [None, True, False]


def test_recusa_saida_que_sobrescreve_entrada(entradas, tmp_path):
    pasta, caminho, *_ = entradas
    renomeado = caminho.rename(tmp_path / "previsoes_amostra.json")
    antes = renomeado.read_bytes()
    with pytest.raises(ConfigError, match="sobrescrever"):
        av.executar(renomeado, pasta=pasta, saida=tmp_path)
    assert renomeado.read_bytes() == antes


def test_recusa_entrada_alterada_durante_leitura(entradas, tmp_path, monkeypatch):
    pasta, caminho, *_ = entradas
    carregar = av.carregar_consenso
    def mudou(p, esperadas):
        r = carregar(p, esperadas)
        p.write_text(p.read_text(encoding="utf-8-sig") + "\n")
        return r
    monkeypatch.setattr(av, "carregar_consenso", mudou)
    with pytest.raises(ConfigError, match="mudou"):
        av.executar(caminho, pasta=pasta, saida=tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.filterwarnings("ignore:.*found in sys.modules.*:RuntimeWarning")
def test_cli_completa_parcial_erro_e_entrypoint(entradas, tmp_path, monkeypatch, capsys):
    pasta, caminho, _, _, p = entradas
    args = ["--previsoes", str(caminho), "--pasta", str(pasta), "--saida", str(tmp_path / "out"), "--exigir-completa"]
    assert av.main(args) == 0
    p["repositorios"] = []
    gravar_json(caminho, p)
    assert av.main(args) == 3
    assert (tmp_path / "out/avaliacao.json").is_file()
    assert av.main(args[:-1]) == 0
    assert av.main(args + ["--compare", "inexistente.json"]) == 2
    caminho.unlink()
    assert av.main(args) == 2
    assert "erro:" in capsys.readouterr().err
    monkeypatch.setattr(sys, "argv", ["avaliacao_heuristica", *args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("pipeline.avaliacao_heuristica", run_name="__main__")
    assert exc.value.code == 2
