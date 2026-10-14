import json
import sys
from pathlib import Path

import pytest

from pipeline import cache, consolidado


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_bloqueio_temporario_preserva_json_ate_substituicao(tmp_path, monkeypatch, winerror):
    destino = tmp_path / "progresso.json"
    cache.gravar_json(destino, {"avaliados": 7})
    substituir = Path.replace
    tentativas = []
    esperas = []

    def bloqueado(temporario, caminho):
        tentativas.append(temporario)
        assert json.loads(destino.read_text()) == {"avaliados": 7}
        if len(tentativas) <= 2:
            erro = PermissionError("arquivo em leitura")
            erro.winerror = winerror
            raise erro
        return substituir(temporario, caminho)

    monkeypatch.setattr(Path, "replace", bloqueado)
    monkeypatch.setattr(cache.time, "sleep", esperas.append)
    cache.gravar_json(destino, {"avaliados": 8})
    assert json.loads(destino.read_text()) == {"avaliados": 8}
    assert esperas == [0.01, 0.02]
    assert len(set(tentativas)) == 1  # Reutiliza o temporário pronto.
    assert list(tmp_path.iterdir()) == [destino]


def test_bloqueio_persistente_tem_limite_e_preserva_destino(tmp_path, monkeypatch):
    destino = tmp_path / "progresso.json"
    cache.gravar_json(destino, {"avaliados": 7})
    esperas = []

    def bloqueado(*args):
        erro = PermissionError("bloqueio persistente")
        erro.winerror = 5
        raise erro

    monkeypatch.setattr(Path, "replace", bloqueado)
    monkeypatch.setattr(cache.time, "sleep", esperas.append)
    with pytest.raises(PermissionError, match="persistente"):
        cache.gravar_json(destino, {"avaliados": 8})
    assert esperas == list(cache.ESPERAS_SUBSTITUICAO)
    assert json.loads(destino.read_text()) == {"avaliados": 7}
    assert list(tmp_path.iterdir()) == [destino]


def test_erro_de_permissao_sem_codigo_windows_nao_e_repetido(tmp_path, monkeypatch):
    def falhar(*args):
        raise PermissionError("sem acesso ao diretorio")

    monkeypatch.setattr(Path, "replace", falhar)
    monkeypatch.setattr(cache.time, "sleep", lambda _: pytest.fail("erro permanente nao deve repetir"))
    with pytest.raises(PermissionError):
        cache.gravar_json(tmp_path / "progresso.json", {})
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Compartilhamento de arquivos do Windows")
@pytest.mark.parametrize("consolidar", [False, True])
def test_leitor_real_windows_nao_interrompe_escrita_atomica(tmp_path, monkeypatch, consolidar):
    destino = tmp_path / "progresso.json"
    cache.gravar_json(destino, {"avaliados": 7})
    esperas = []
    with destino.open("rb") as leitor:
        def liberar(segundos):
            esperas.append(segundos)
            leitor.close()

        monkeypatch.setattr(cache.time, "sleep", liberar)
        if consolidar:
            consolidado.gravar(destino, {"avaliados": 8}, [{"id": 1}])
        else:
            cache.gravar_json(destino, {"avaliados": 8})
    assert esperas == [0.01]
    assert json.loads(destino.read_text())["avaliados"] == 8
    assert list(tmp_path.iterdir()) == [destino]
