"""Retoma a meta de 500 com três tokens e um único coordenador de escrita."""
import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import logging
import os
from pathlib import Path
import queue
import shutil
import threading
import time

import requests

from pipeline import integrado, workflow_runs_completos
from pipeline.cache import CacheDisco, gravar_json, substituir_atomico
from pipeline.config import ConfigError, janela_utc, load_config
from pipeline.github_api import GitHubClient
from pipeline.workflow_runs import _iso

log = logging.getLogger(__name__)
BASE = Path(__file__).resolve().parents[1]


def ler_tokens(caminho, ambiente=None):
    """Lê apenas as três chaves esperadas; não executa comandos do .env."""
    ambiente = os.environ if ambiente is None else ambiente
    valores = {}
    caminho = Path(caminho)
    if caminho.is_file():
        for linha in caminho.read_text(encoding="utf-8-sig").splitlines():
            if linha.strip() and not linha.lstrip().startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                valores[chave.strip()] = valor.strip().strip("\"'")
    tokens = []
    for i in range(1, 4):
        chave = f"GITHUB_TOKEN_{i}"
        token = (ambiente.get(chave) or valores.get(chave, "")).strip()
        if not token:
            raise ConfigError(f"Preencha {chave} no .env ou no ambiente")
        tokens.append(token)
    if len(set(tokens)) != 3:
        raise ConfigError("Configure três tokens diferentes")
    return tokens


class Sessoes:
    """Reserva um cliente/token durante toda a tarefa de um repositório."""
    def __init__(self, clientes):
        self.clientes = clientes
        self.paralelismo = sum(c.paralelismo for c in clientes)
        self.fila = queue.Queue()
        self.trava = threading.Lock()
        self.ativas = {}
        for i, cliente in enumerate(clientes, 1):
            self.fila.put((i, cliente))

    @contextmanager
    def sessao(self, repo):
        numero, cliente = self.fila.get()
        with self.trava:
            self.ativas[numero] = repo["full_name"]
        log.info("Sessão %d: %s", numero, repo["full_name"])
        try:
            yield cliente
        finally:
            with self.trava:
                self.ativas.pop(numero, None)
            self.fila.put((numero, cliente))

    def status(self):
        with self.trava:
            return {str(i): self.ativas.get(i, "livre") for i in range(1, 4)}

    def estatisticas(self):
        totais = {"cache_hits": 0}
        controles = set()
        for cliente in self.clientes:
            dados = cliente.estatisticas()
            totais["cache_hits"] += dados.pop("cache_hits", 0)
            if id(cliente.controle) not in controles:
                controles.add(id(cliente.controle))
                for chave, valor in dados.items():
                    totais[chave] = totais.get(chave, 0) + valor
        return totais

    def close(self):
        for cliente in self.clientes:
            cliente.close()


def autenticar(tokens, config):
    """Valida credenciais e compartilha controle de cota entre tokens da mesma conta."""
    clientes, contas = [], {}
    try:
        for numero, token in enumerate(tokens, 1):
            cliente = GitHubClient(token, config["api"]["base_url"],
                config["api"].get("timeout_s", 30), paralelismo=2)
            clientes.append(cliente)
            usuario = cliente.get("/user")["id"]
            if usuario in contas:
                cliente.controle = contas[usuario]
            else:
                contas[usuario] = cliente.controle
            cliente.cache = CacheDisco(config["caminhos"]["cache"])
            log.info("Token %d: autenticado", numero)
        log.info("Três sessões autenticadas; %d conta(s), com cotas compartilhadas por conta", len(contas))
        return Sessoes(clientes)
    except BaseException:
        for cliente in clientes:
            cliente.close()
        raise


def preparar(config, fonte_original, fonte_anterior):
    """Mantém o prefixo já confirmado e retoma pendentes na ordem original da busca."""
    raw = Path(config["caminhos"]["raw"])
    progresso = raw / "progresso.json"
    anterior = integrado._ler(progresso) if progresso.is_file() else None
    inicio, fim = janela_utc(config)
    regras = {"janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)},
              "inclusao": config["inclusao"], "runs": config["runs"],
              "api": config["api"]["base_url"], "versao": 2,
              "versao_coletor_runs": workflow_runs_completos.VERSAO_COLETOR}
    if anterior and any(anterior["contexto"].get(k) != v for k, v in regras.items()):
        raise ConfigError("Regras incompatíveis com os checkpoints existentes")
    destino = raw / "candidatos-sem-prioridade-tamanho.json"
    if destino.is_file():
        fonte = integrado._ler(destino)
        if fonte.get("agendamento"):
            raise ConfigError("A fonte da coleta paralela ainda contém adiamento")
    else:
        fonte = integrado._ler(fonte_original)
        if fonte.get("agendamento"):
            raise ConfigError("Use a fonte original da busca, sem política de adiamento")
        por_id = {r["id"]: r for r in fonte["candidatos"]}
        if len(por_id) != len(fonte["candidatos"]):
            raise ConfigError("IDs duplicados na fonte original")
        confirmados = anterior.get("ids_avaliados", []) if anterior else []
        if len(set(confirmados)) != len(confirmados) or not set(confirmados) <= por_id.keys():
            raise ConfigError("Prefixo confirmado inválido na fonte original")
        ids = set(confirmados)
        fonte["candidatos"] = ([por_id[i] for i in confirmados]
                                + [r for r in fonte["candidatos"] if r["id"] not in ids])
        fonte["retomada"] = {"prefixo_confirmado": len(confirmados),
            "ordem_pendentes": "ordem original da busca, sem preferência por tamanho",
            "consolidacao": "ordem de conclusão nas três sessões"}
        gravar_json(destino, fonte)
    sha = hashlib.sha256(destino.read_bytes()).hexdigest()
    contexto = {**regras, "fonte_sha256": sha}
    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
    pasta = raw / "checkpoints" / digest
    pasta.mkdir(parents=True, exist_ok=True)
    # Migração só entre contextos com as mesmas regras e registros de candidatos iguais.
    if anterior and anterior["contexto"]["fonte_sha256"] != sha:
        if hashlib.sha256(Path(fonte_anterior).read_bytes()).hexdigest() != anterior["contexto"]["fonte_sha256"]:
            raise ConfigError("Hash da fonte anterior divergente; migração cancelada")
        antigo_digest = hashlib.sha256(json.dumps(anterior["contexto"], sort_keys=True).encode()).hexdigest()
        antiga = raw / "checkpoints" / antigo_digest
        por_id = {r["id"]: r for r in fonte["candidatos"]}
        copiados = elegiveis = 0
        for arquivo in antiga.glob("*.json"):
            registro = integrado._ler(arquivo)
            if registro["candidato"] != por_id.get(registro["candidato"]["id"]):
                raise ConfigError(f"Candidato incompatível no checkpoint {arquivo.name}")
            novo = pasta / arquivo.name
            if not novo.exists():
                temporario = novo.with_suffix(".migrando")
                shutil.copy2(arquivo, temporario)
                substituir_atomico(temporario, novo)
                copiados += 1
            elegiveis += bool(registro["elegivel"])
        backup = raw / "retomada-tres-sessoes"
        backup.mkdir(exist_ok=True)
        if not (backup / "progresso-anterior.json").exists():
            shutil.copy2(progresso, backup / "progresso-anterior.json")
        gravar_json(backup / "migracao.json", {"origem": str(antiga), "destino": str(pasta),
            "checkpoints_copiados": copiados, "elegiveis_reutilizaveis": elegiveis,
            "contexto_anterior": anterior["contexto"], "contexto_novo": contexto})
        log.info("Reaproveitamento: %d checkpoints, %d elegíveis disponíveis", copiados, elegiveis)
    # Os confirmados devem ser consumidos antes dos pendentes. As primeiras tarefas
    # da fila são checkpoints rápidos; a fonte preserva todos os 255 já publicados.
    return destino


@contextmanager
def trava_coleta(raw):
    """Usa a mesma trava do coletor antigo; não permite dois coordenadores."""
    raw.mkdir(parents=True, exist_ok=True)
    with (raw / "coleta.lock").open("a+b") as arquivo:
        if arquivo.tell() == 0:
            arquivo.write(b"0")
            arquivo.flush()
        arquivo.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise ConfigError("Já existe outra coleta ativa usando esta pasta") from None
        else:
            import fcntl
            fcntl.flock(arquivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            arquivo.seek(0)
            if os.name == "nt":
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo, fcntl.LOCK_UN)


def executar_com_retomada(config, fonte, criar_clientes, estado, atualizar, reutilizar_runs=None):
    tentativa = 0
    while True:
        tentativa += 1
        clientes = None
        estado.update(estado="executando", tentativa=tentativa)
        atualizar()
        try:
            clientes = criar_clientes()
            estado["clientes"] = clientes
            return integrado.executar(config, clientes, 500, 100000, fonte, reutilizar_runs)
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError,
                requests.HTTPError) as exc:
            resposta = getattr(exc, "response", None)
            status = getattr(resposta, "status_code", None)
            headers = getattr(resposta, "headers", {})
            limite_403 = status == 403 and (headers.get("X-RateLimit-Remaining") == "0"
                                          or "Retry-After" in headers)
            if isinstance(exc, requests.HTTPError) and not limite_403 and status not in (429, 500, 502, 503, 504):
                raise
            estado.update(estado="aguardando_rede", erro=type(exc).__name__)
            atualizar()
            espera = min(60, 5 * 2 ** min(tentativa - 1, 4))
            log.warning("Rede/API temporariamente indisponível (%s). Retomada em %ds, preservando cache/checkpoints", type(exc).__name__, espera)
        finally:
            estado.pop("clientes", None)
            if clientes is not None:
                clientes.close()
        time.sleep(espera)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(BASE / "data/raw/amostra-final-500/config.yaml"))
    parser.add_argument("--env", default=str(BASE / ".env"))
    parser.add_argument("--fonte-original", default=str(BASE / "data/raw/candidatos.json"))
    parser.add_argument("--fonte-anterior", default=str(BASE / "data/raw/amostra-final-500/candidatos-prioridade-leves.json"))
    parser.add_argument("--preparar", action="store_true", help="valida e migra checkpoints sem consultar a API")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    config["api"]["repositorios_paralelos"] = 3
    raw = Path(config["caminhos"]["raw"])
    raw.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(raw / "coleta-tres-sessoes.log", encoding="utf-8")])
    estado = {"pid": os.getpid(), "alvo": 500, "sessoes": 3}
    fim = threading.Event()

    def atualizar():
        snapshot = {k: v for k, v in estado.copy().items() if k != "clientes"}
        snapshot["atualizado_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        cliente = estado.get("clientes")
        snapshot["tarefas"] = cliente.status() if cliente else {}
        p = raw / "progresso.json"
        if p.is_file():
            progresso = integrado._ler(p)
            for k in ("elegiveis_com_coleta_completa", "candidatos_avaliados", "etapa"):
                snapshot[k] = progresso.get(k)
        gravar_json(raw / "processo-tres-sessoes.json", snapshot)
        log.info("STATUS %s | etapa %s | %s/500 elegíveis | %s candidatos | sessões: %s",
            snapshot.get("estado"), snapshot.get("etapa", "preparando"), snapshot.get("elegiveis_com_coleta_completa", 0),
            snapshot.get("candidatos_avaliados", 0), snapshot["tarefas"])

    def monitorar():
        while not fim.wait(15):
            atualizar()

    try:
        with trava_coleta(raw):
            tokens = ler_tokens(args.env)
            fonte = preparar(config, args.fonte_original, args.fonte_anterior)
            if args.preparar:
                log.info("Preparação concluída; nenhuma chamada à API realizada")
                return 0
            monitor = threading.Thread(target=monitorar, daemon=True)
            monitor.start()
            try:
                seed = BASE / "data/raw/piloto-100/workflow_runs.json"
                resultado = executar_com_retomada(config, fonte, lambda: autenticar(tokens, config),
                    estado, atualizar, seed if seed.is_file() else None)
                estado.update(estado="concluido" if resultado["execucao_completa"] else "fonte_esgotada",
                              resultado=resultado["total_amostra_completa"])
            finally:
                fim.set()
                monitor.join()
            atualizar()
            return 0 if resultado["execucao_completa"] else 3
    except KeyboardInterrupt:
        estado.update(estado="interrompido")
    except (ConfigError, ValueError, OSError, requests.RequestException) as exc:
        estado.update(estado="falhou", erro=type(exc).__name__)
        # Não imprime mensagens retornadas pela API nem valores de credenciais.
        log.error("Coleta interrompida: %s", type(exc).__name__)
        if isinstance(exc, requests.HTTPError):
            log.error("Resposta HTTP %s; confira a validade e as permissões dos tokens", getattr(exc.response, "status_code", None))
        if isinstance(exc, ConfigError):
            log.error("%s", exc)
    atualizar()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
