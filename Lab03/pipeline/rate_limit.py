"""Espera pelo rate limit e repetição limitada de respostas HTTP temporárias."""

import logging
import threading
import time

BACKOFF_5XX = (1, 2, 4, 8)
MAX_REPETICOES_LIMITE = 4
MARGEM_RESET_S = 1
ESPERA_SECUNDARIA_S = 60

log = logging.getLogger(__name__)


def _inteiro(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero >= 0 else None


class ControleRequisicoes:
    def __init__(self, sleep=time.sleep, relogio=time.time, paralelismo=1):
        self.sleep = sleep
        self.relogio = relogio
        self.resets = {}
        self.recursos = {}
        self.pausa_global = 0
        self._vagas = threading.BoundedSemaphore(paralelismo)
        self._estatisticas = dict(requisicoes=0, repeticoes_limite=0, repeticoes_5xx=0,
                                 espera_rate_limit_s=0.0, espera_backoff_s=0.0)
        self._trava = threading.Lock()

    def estatisticas(self):
        with self._trava:
            return dict(self._estatisticas)

    def _recurso(self, path):
        if path == "/search/code":
            padrao = "code_search"
        else:
            padrao = "search" if path.startswith("/search/") else "core"
        return self.recursos.get(path, padrao)

    def _registrar(self, path, resposta):
        restante = _inteiro(resposta.headers.get("X-RateLimit-Remaining"))
        reset = _inteiro(resposta.headers.get("X-RateLimit-Reset"))
        with self._trava:
            recurso = resposta.headers.get("X-RateLimit-Resource") or self._recurso(path)
            self.recursos[path] = recurso
            if restante == 0 and reset is not None:
                self.resets[recurso] = max(self.resets.get(recurso, 0), reset + MARGEM_RESET_S)
            # Respostas concorrentes podem chegar fora de ordem. Uma cota
            # positiva não revoga uma pausa estabelecida por outra resposta.
        return restante, reset

    def _aguardar(self, path):
        while True:
            with self._trava:
                recurso = self._recurso(path)
                reset = self.resets.get(recurso)
                global_ = self.pausa_global
                prazo = max(reset or 0, global_)
            espera = max(0, prazo - self.relogio())
            if espera > 0:
                log.info("Rate limit: aguardando %.1fs antes de consultar %s", espera, path)
                self.sleep(espera)
                with self._trava:
                    self._estatisticas["espera_rate_limit_s"] += espera
            with self._trava:
                if self.resets.get(recurso) == reset:
                    self.resets.pop(recurso, None)
                if self.pausa_global == global_:
                    self.pausa_global = 0
                # Uma resposta pode prolongar a pausa durante o sleep.
                if not self.resets.get(recurso) and not self.pausa_global:
                    return

    def _pausar(self, path, resposta, restante, reset, espera):
        with self._trava:
            prazo = self.relogio() + espera
            if restante == 0 and reset is not None and "Retry-After" not in resposta.headers:
                recurso = self._recurso(path)
                self.resets[recurso] = max(self.resets.get(recurso, 0), prazo)
            else:
                # Retry-After e limites secundários se aplicam a todas as threads.
                self.pausa_global = max(self.pausa_global, prazo)

    def _espera_limite(self, resposta, restante, reset, repeticoes):
        if resposta.status_code not in (403, 429):
            return None
        retry_after = _inteiro(resposta.headers.get("Retry-After"))
        espera_reset = (max(0, reset + MARGEM_RESET_S - self.relogio())
                        if restante == 0 and reset is not None else None)
        if retry_after is not None:
            return max(1, retry_after, espera_reset or 0)
        if espera_reset is not None:
            return espera_reset
        try:
            corpo = resposta.json()
        except ValueError:
            corpo = {}
        mensagem = str(corpo.get("message", "")).lower() if isinstance(corpo, dict) else ""
        if (resposta.status_code == 429 or restante == 0
                or "secondary rate limit" in mensagem or "abuse detection" in mensagem):
            return ESPERA_SECUNDARIA_S * 2 ** repeticoes
        return None

    def executar(self, requisitar, path):
        """Faz até quatro repetições por motivo e propaga o erro final.

        Uma resposta bem-sucedida que esgota a cota é devolvida imediatamente;
        a espera fica reservada para a próxima chamada à API daquele recurso.
        """
        falhas, limites = 0, 0
        while True:
            # Esperas não ocupam vagas HTTP: outros recursos podem ter cota.
            self._aguardar(path)
            with self._vagas:
                with self._trava:
                    # Uma resposta pode impor pausa enquanto aguardávamos vaga.
                    prazo = max(self.resets.get(self._recurso(path), 0), self.pausa_global)
                    if prazo > self.relogio():
                        continue
                    self._estatisticas["requisicoes"] += 1
                resposta = requisitar()
                restante, reset = self._registrar(path, resposta)
                espera = self._espera_limite(resposta, restante, reset, limites)
                if espera is not None:
                    self._pausar(path, resposta, restante, reset, espera)
            if espera is not None and limites < MAX_REPETICOES_LIMITE:
                limites += 1
                log.warning("Rate limit HTTP %d: repetição %d/%d após %.1fs (%s)",
                            resposta.status_code, limites, MAX_REPETICOES_LIMITE, espera, path)
                with self._trava:
                    self._estatisticas["repeticoes_limite"] += 1
                if espera == 0:
                    self.sleep(0)
                continue
            if 500 <= resposta.status_code < 600 and falhas < len(BACKOFF_5XX):
                espera = BACKOFF_5XX[falhas]
                falhas += 1
                log.warning("HTTP %d: repetição %d/%d após %ds (%s)",
                            resposta.status_code, falhas, len(BACKOFF_5XX), espera, path)
                self.sleep(espera)
                with self._trava:
                    self._estatisticas["repeticoes_5xx"] += 1
                    self._estatisticas["espera_backoff_s"] += espera
                continue
            resposta.raise_for_status()
            return resposta
