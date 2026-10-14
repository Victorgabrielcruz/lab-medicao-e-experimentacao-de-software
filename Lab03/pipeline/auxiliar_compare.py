"""Antecipa candidatos e compares sem reiniciar o integrado (#151).

Somente novos checkpoints compatíveis e respostas GET são compartilhados. Não
altera configuração, progresso, consolidados ou código do processo principal.
"""

import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import requests

from pipeline import compare, integrado, consolidado, workflow_runs_completos
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import ConfigError, janela_utc, load_config, read_token
from pipeline.github_api import GitHubClient

log = logging.getLogger(__name__)


class PausaAuxiliar(Exception):
    """Cede recursos à coleta principal; páginas concluídas ficam no cache."""


class EncerrarAuxiliar(Exception):
    """A principal atingiu o alvo ou já encerrou; não disputar seus compares."""


class AdiarCandidato(PausaAuxiliar):
    """Rotaciona candidatos grandes sem descartar as páginas já coletadas."""


def ler(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def digest(dados):
    return hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()


def caminho_compare(raw, repo, inicio, fim, api):
    # Contrato do integrado existente: mudar esta chave impede o reaproveitamento.
    contexto = {"releases": repo, "janela": {"inicio": compare._iso(inicio), "fim_exclusivo": compare._iso(fim)},
                "api": api, "versao_compare": 1}
    return Path(raw) / "checkpoints" / "compare" / digest(contexto) / f"{repo['id']}.json"


def publicar(origem, destino):
    """Publica um JSON completo sem substituir um checkpoint já existente.

    Hard link do temporário fechado faz a criação atômica no mesmo volume,
    inclusive em NTFS. A cópia é local; a origem pode estar em outro volume.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destino.parent, suffix=".tmp", delete=False) as arquivo:
        temporario = Path(arquivo.name)
        with Path(origem).open("rb") as fonte:
            shutil.copyfileobj(fonte, arquivo)
    try:
        try:
            os.link(temporario, destino)
        except FileExistsError:
            return False
        return True
    finally:
        temporario.unlink(missing_ok=True)


@contextmanager
def instancia_unica(pasta):
    """Lock do sistema operacional, liberado também se a auxiliar cair."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    with (pasta / "auxiliar.lock").open("a+b") as arquivo:
        arquivo.seek(0, 2)
        if arquivo.tell() == 0:
            arquivo.write(b"0")
            arquivo.flush()
        arquivo.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
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


class Principal:
    def __init__(self, config, fonte, relogio=time.time):
        self.config, self.raw, self.relogio = config, Path(config["caminhos"]["raw"]), relogio
        inicio, fim = janela_utc(config)
        self.contexto = {"janela": {"inicio": compare._iso(inicio), "fim_exclusivo": compare._iso(fim)},
                         "inclusao": config["inclusao"], "runs": config["runs"],
                         "api": config["api"]["base_url"], "versao": 2,
                         "versao_coletor_runs": workflow_runs_completos.VERSAO_COLETOR,
                         "fonte_sha256": hashlib.sha256(Path(fonte).read_bytes()).hexdigest()}
        self.pasta = self.raw / "checkpoints" / digest(self.contexto)
        self.candidatos = ler(fonte)["candidatos"]
        if len({r["id"] for r in self.candidatos}) != len(self.candidatos):
            raise ConfigError("IDs duplicados na fonte da auxiliar")
        self.vistos, self.fila = set(), {}
        self.alvo = None
        self.max_candidatos = len(self.candidatos)

    def conferir(self):
        if (self.raw / "auxiliar-compare" / "parar").exists():
            raise EncerrarAuxiliar("parada solicitada somente para a auxiliar")
        try:
            estado, progresso = ler(self.raw / "processo.json"), ler(self.raw / "progresso.json")
        except FileNotFoundError:
            raise PausaAuxiliar("aguardando estado da principal") from None
        if progresso.get("contexto") != self.contexto:
            raise ConfigError("Contexto da principal divergente: não compartilhar checkpoints")
        if self.alvo is None:
            self.alvo = progresso["alvo"]
        if progresso["alvo"] != self.alvo:
            raise ConfigError("Alvo da principal mudou durante a execução auxiliar")
        self.max_candidatos = min(len(self.candidatos), estado.get("max_candidatos", len(self.candidatos)))
        if progresso["elegiveis_com_coleta_completa"] >= self.alvo or estado["estado"] in ("concluido", "alvo_nao_atingido"):
            raise EncerrarAuxiliar("seleção encerrada; comparações ficam com a principal")
        sinal = dt.datetime.fromisoformat(estado["atualizado_utc"]).timestamp()
        if estado["estado"] != "executando" or self.relogio() - sinal > 120:
            raise PausaAuxiliar("principal inativa, aguardando retomada")
        if shutil.disk_usage(self.raw).free < 10 * 1024**3:
            raise PausaAuxiliar("disco livre abaixo de 10 GiB")
        return progresso

    def descobrir(self):
        progresso = self.conferir()
        # Somente candidatos já consumidos em ordem pelo coordenador principal.
        for candidato in self.candidatos[:progresso["candidatos_avaliados"]]:
            chave = candidato["id"]
            if chave in self.vistos:
                continue
            caminho = self.pasta / f"{chave}.json"
            if not caminho.is_file():
                continue
            registro = ler(caminho)
            if (registro["candidato"]["id"] != chave or
                    registro["candidato"]["full_name"].lower() != candidato["full_name"].lower()):
                raise ConfigError("Identidade divergente no checkpoint da principal")
            if registro["elegivel"]:
                repo = registro["aprovados"]["releases"]
                if repo["id"] != chave or repo["full_name"].lower() != candidato["full_name"].lower():
                    raise ConfigError("Identidade divergente nas releases da principal")
                self.fila[chave] = repo
            self.vistos.add(chave)
        # Concluir primeiro projetos menores não muda a seleção da principal.
        return sorted(self.fila.values(), key=lambda r: (len(r["releases"]), r["id"]))

    def conferir_candidato(self, indice):
        progresso = self.conferir()
        # O integrado pode ter até workers candidatos em voo, após o último
        # consumido. Uma margem extra deixa a principal avançar antes de ceder.
        inicio = progresso["candidatos_avaliados"] + integrado._workers(self.config) + 6
        if indice < inicio:
            raise PausaAuxiliar("principal alcançou a margem do candidato antecipado")
        return progresso

    def proximos(self):
        progresso = self.conferir()
        inicio = progresso["candidatos_avaliados"] + integrado._workers(self.config) + 6
        # Fila curta e próxima da principal; não pré-coletar toda a população.
        fim = min(self.max_candidatos, inicio + 32)
        return [(i, self.candidatos[i]) for i in range(inicio, fim)
                if not (self.pasta / f"{self.candidatos[i]['id']}.json").is_file()]


class ClienteAuxiliar(GitHubClient):
    def __init__(self, token, config, principal, notificar=lambda **_: None, intervalo=6.0,
                 reserva=2000, session=None, sleep=time.sleep, relogio=time.time):
        if intervalo < 6 or reserva < 500:
            raise ConfigError("Auxiliar exige intervalo >=6s e reserva >=500 requisições")
        super().__init__(token, config["api"]["base_url"], config["api"].get("timeout_s", 30),
                         session=session, cache=CacheDisco(config["caminhos"]["cache"]),
                         sleep=sleep, relogio=relogio, paralelismo=1)
        self.principal, self.notificar = principal, notificar
        self.intervalo, self.reserva = intervalo, reserva
        self.sleep, self.relogio = sleep, relogio
        self.ultima, self.verificada, self.cota = None, None, None
        self.consultas_cota = self.requisicoes_reais = 0
        self.pausa_ate = 0
        self.validar_tarefa = None

    def _conferir(self):
        self.principal.conferir()
        if self.validar_tarefa is not None:
            self.validar_tarefa()

    def estatisticas(self):
        dados = super().estatisticas()
        dados["tentativas_controlador"] = dados["requisicoes"]
        dados["requisicoes"] = self.requisicoes_reais
        dados["consultas_cota"] = self.consultas_cota
        return dados

    def _consultar_cota(self):
        self._conferir()
        resposta = self.session.get(f"{self.base_url}/rate_limit", timeout=self.timeout_s)
        self.consultas_cota += 1
        resposta.raise_for_status()
        self.cota = resposta.json()["resources"]["core"]
        self.verificada = self.relogio()

    def _requisitar(self, path, params):
        # Executado antes de CADA tentativa de rede, inclusive backoff/retries.
        self._conferir()
        agora = self.relogio()
        if agora < self.pausa_ate:
            raise PausaAuxiliar("cooldown da API; prioridade da principal")
        if self.ultima is not None and agora - self.ultima < self.intervalo:
            self.sleep(self.intervalo - (agora - self.ultima))
        self._conferir()
        agora = self.relogio()
        if self.verificada is None or agora - self.verificada >= 30 or agora >= self.cota["reset"]:
            self._consultar_cota()
        cota = self.cota
        restante_janela = min(3600, max(0, cota["reset"] - self.relogio()))
        # Reserva 90% do orçamento proporcional ao tempo que falta + margem.
        piso = max(self.reserva, math.ceil(0.9 * cota["limit"] * restante_janela / 3600) + 250)
        self.notificar(cota_restante=cota["remaining"], cota_reservada=piso,
                       reset_utc=dt.datetime.fromtimestamp(cota["reset"], dt.timezone.utc).isoformat())
        if cota["remaining"] <= piso:
            raise PausaAuxiliar("cota reservada para a principal")
        self.ultima = self.relogio()
        self.requisicoes_reais += 1
        resposta = super()._requisitar(path, params)
        # Headers das respostas prevalecem sobre o snapshot do /rate_limit.
        if resposta.headers.get("X-RateLimit-Resource", "core") == "core":
            for chave, header in (("remaining", "X-RateLimit-Remaining"), ("reset", "X-RateLimit-Reset"), ("limit", "X-RateLimit-Limit")):
                if header in resposta.headers:
                    self.cota[chave] = int(resposta.headers[header])
        if resposta.status_code in (403, 429):
            # O controlador normal trata cooldown; cancelar a auxiliar cede a vez.
            if (resposta.status_code == 429 or self.cota["remaining"] == 0
                    or "secondary rate limit" in resposta.text.lower()
                    or "abuse detection" in resposta.text.lower()):
                try:
                    espera = max(60, int(resposta.headers.get("Retry-After", 60)))
                except ValueError:
                    espera = 60
                self.pausa_ate = max(self.relogio() + espera,
                                     self.cota["reset"] + 1 if self.cota["remaining"] == 0 else 0)
                self.verificada = None
                raise PausaAuxiliar("rate limit: auxiliar cede prioridade à principal")
        return resposta


def antecipar(config, principal, client, repo, pasta):
    inicio, fim = janela_utc(config)
    destino = caminho_compare(config["caminhos"]["raw"], repo, inicio, fim, config["api"]["base_url"])
    origem = Path(pasta) / "prontos" / destino.parent.name / destino.name
    if destino.is_file():
        return "reutilizado"
    principal.conferir()
    if not origem.is_file():
        dados = compare.coletar_repositorio(client, repo, inicio, fim)
        if dados["id"] != repo["id"] or dados["full_name"].lower() != repo["full_name"].lower():
            raise ConfigError("Identidade divergente no compare auxiliar")
        gravar_json(origem, dados, compacto=True)
    principal.conferir()
    return "publicado" if publicar(origem, destino) else "reutilizado"


def antecipar_candidato(config, principal, client, indice, repo, pasta, anteriores=None):
    """Usa o coletor original; publica seu arquivo completo, nunca o resumo em RAM."""
    principal.conferir_candidato(indice)
    destino = principal.pasta / f"{repo['id']}.json"
    if destino.is_file():
        return "reutilizado", None
    privados = Path(pasta) / "candidatos" / principal.pasta.name
    inicio, fim = janela_utc(config)
    validacao_anterior = getattr(client, "validar_tarefa", None)
    inicio_requisicoes = getattr(client, "requisicoes_reais", 0)
    def validar():
        principal.conferir_candidato(indice)
        if getattr(client, "requisicoes_reais", 0) - inicio_requisicoes >= 30:
            raise AdiarCandidato("30 requisições nesta rodada; próximo candidato, mantendo cache")
    client.validar_tarefa = validar
    try:
        registro = integrado._coletar_candidato(config, client, repo, privados, anteriores or {}, inicio, fim)
        principal.conferir_candidato(indice)
        # O coletor gravou os runs inteiros antes de compactar o retorno em RAM.
        resultado = "publicado" if publicar(privados / destino.name, destino) else "reutilizado"
        return resultado, registro["elegivel"]
    finally:
        client.validar_tarefa = validacao_anterior


def carregar_anteriores(caminho, principal):
    if caminho is None:
        return {}
    if consolidado.cabecalho(caminho).get("janela") != principal.contexto["janela"]:
        raise ConfigError("Janela dos runs reutilizados divergente na auxiliar")
    progresso = principal.conferir()
    ids_futuros = {r["id"] for r in principal.candidatos[progresso["candidatos_avaliados"]:]}
    return {r["id"]: r for r in consolidado.repositorios(caminho) if r["id"] in ids_futuros}


def executar(config, fonte, token, pasta=None, reutilizar_runs=None):
    raw = Path(config["caminhos"]["raw"])
    pasta = Path(pasta) if pasta else raw / "auxiliar-compare"
    # Manter estado isolado: não aceitar o diretório de progresso da principal.
    if pasta.resolve() == raw.resolve():
        raise ConfigError("Estado auxiliar deve ficar em um subdiretório separado")
    estado = {"estado": "preparando", "pid": os.getpid(), "repositorios_concluidos": 0,
              "checkpoints_publicados": 0, "checkpoints_reutilizados": 0,
              "intervalo_minimo_s": 6, "reserva_minima": 2000, "principal_raw": str(raw),
              "prioridade": "candidatos", "candidatos_antecipados": 0,
              "elegiveis_antecipados": 0, "descartados_antecipados": 0,
              "candidatos_publicados": 0, "candidatos_reutilizados": 0,
              "candidatos_adiados": 0, "limite_requisicoes_por_candidato": 30}

    def atualizar(**campos):
        estado.update(campos)
        estado["atualizado_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        gravar_json(pasta / "estado.json", estado)

    with instancia_unica(pasta):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                            handlers=[logging.FileHandler(pasta / "auxiliar.log", encoding="utf-8"), logging.StreamHandler()])
        atualizar()
        principal = Principal(config, fonte)
        anteriores = None
        client = ClienteAuxiliar(token, config, principal, notificar=atualizar)
        feitos = set()
        adiados = set()
        try:
            while True:
                try:
                    futuros = principal.proximos()
                    candidatos_futuros = [(i, r) for i, r in futuros if r["id"] not in adiados]
                    if futuros and not candidatos_futuros:
                        adiados.clear()
                        candidatos_futuros = futuros
                    if candidatos_futuros:
                        if anteriores is None:
                            anteriores = carregar_anteriores(reutilizar_runs, principal)
                        indice, candidato = candidatos_futuros[0]
                        atualizar(estado="coletando_candidato", tarefa="candidato",
                                  repositorio_atual=candidato["full_name"], posicao_candidato=indice + 1,
                                  candidatos_principal=principal.conferir()["candidatos_avaliados"])
                        resultado, elegivel = antecipar_candidato(config, principal, client, indice,
                                                                 candidato, pasta, anteriores)
                        estado["candidatos_antecipados"] += 1
                        estado["candidatos_publicados" if resultado == "publicado" else "candidatos_reutilizados"] += 1
                        if resultado == "publicado":
                            estado["elegiveis_antecipados" if elegivel else "descartados_antecipados"] += 1
                        atualizar(http=client.estatisticas())
                        log.info("Candidato antecipado: %s; posição %d; elegível=%s; %s",
                                 candidato["full_name"], indice + 1, elegivel, resultado)
                        continue
                    pendentes = [r for r in principal.descobrir() if r["id"] not in feitos]
                    if not pendentes:
                        atualizar(estado="aguardando_repositorios", repositorios_aprovados=len(principal.fila))
                        time.sleep(15)
                        continue
                    repo = pendentes[0]
                    atualizar(estado="coletando_compare", tarefa="compare", repositorio_atual=repo["full_name"],
                              repositorios_aprovados=len(principal.fila))
                    resultado = antecipar(config, principal, client, repo, pasta)
                    feitos.add(repo["id"])
                    chave = "checkpoints_publicados" if resultado == "publicado" else "checkpoints_reutilizados"
                    estado[chave] += 1
                    atualizar(repositorios_concluidos=len(feitos), http=client.estatisticas())
                    log.info("Compare pronto: %s (%s); %d repositórios concluídos", repo["full_name"], resultado, len(feitos))
                except AdiarCandidato as exc:
                    adiados.add(candidato["id"])
                    estado["candidatos_adiados"] += 1
                    atualizar(estado="rotacionando_candidato", motivo=str(exc), http=client.estatisticas())
                    log.info("Candidato adiado: %s; páginas retidas no cache", candidato["full_name"])
                except PausaAuxiliar as exc:
                    atualizar(estado="pausada", motivo=str(exc), http=client.estatisticas())
                    time.sleep(15)
                except requests.RequestException as exc:
                    status = getattr(getattr(exc, "response", None), "status_code", None)
                    if status is not None and status < 500:
                        raise
                    atualizar(estado="aguardando_rede", erro=type(exc).__name__)
                    log.warning("Falha temporária %s; retomada em 60s", type(exc).__name__)
                    for _ in range(4):
                        time.sleep(15)
                        atualizar()
        except EncerrarAuxiliar as exc:
            atualizar(estado="encerrada", motivo=str(exc), http=client.estatisticas())
        except Exception as exc:
            atualizar(estado="falhou", erro=type(exc).__name__)
            raise
        finally:
            client.close()
    return estado


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Configuração absoluta da principal em execução")
    parser.add_argument("--candidatos", required=True, help="Mesma fonte de candidatos da principal")
    parser.add_argument("--estado-dir", help="Pasta privada; padrão: raw/auxiliar-compare")
    parser.add_argument("--reutilizar-runs", help="Mesmo consolidado de runs reutilizado pela principal")
    args = parser.parse_args(argv)
    try:
        executar(load_config(args.config), args.candidatos, read_token(), args.estado_dir, args.reutilizar_runs)
    except (ConfigError, OSError, ValueError, requests.RequestException) as exc:
        print(f"Auxiliar encerrou: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
