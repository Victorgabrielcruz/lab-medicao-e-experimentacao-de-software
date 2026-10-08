"""Espera pelo rate limit e repetição limitada de respostas HTTP temporárias."""

import logging
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
    def __init__(self, sleep=time.sleep, relogio=time.time):
        self.sleep = sleep
        self.relogio = relogio
        self.resets = {}
        self.recursos = {}

    def _recurso(self, path):
        if path == "/search/code":
            padrao = "code_search"
        else:
            padrao = "search" if path.startswith("/search/") else "core"
        return self.recursos.get(path, padrao)

    def _registrar(self, path, resposta):
        recurso = resposta.headers.get("X-RateLimit-Resource") or self._recurso(path)
        self.recursos[path] = recurso
        restante = _inteiro(resposta.headers.get("X-RateLimit-Remaining"))
        reset = _inteiro(resposta.headers.get("X-RateLimit-Reset"))
        if restante == 0 and reset is not None:
            self.resets[recurso] = reset + MARGEM_RESET_S
        elif restante is not None and restante > 0:
            self.resets.pop(recurso, None)
        return restante, reset

    def _aguardar(self, path):
        prazo = self.resets.pop(self._recurso(path), None)
        if prazo is not None:
            espera = max(0, prazo - self.relogio())
            if espera > 0:
                log.info("Rate limit: aguardando %.1fs antes de consultar %s", espera, path)
                self.sleep(espera)

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
            self._aguardar(path)
            resposta = requisitar()
            restante, reset = self._registrar(path, resposta)
            espera = self._espera_limite(resposta, restante, reset, limites)
            if espera is not None and limites < MAX_REPETICOES_LIMITE:
                limites += 1
                log.warning("Rate limit HTTP %d: repetição %d/%d após %.1fs (%s)",
                            resposta.status_code, limites, MAX_REPETICOES_LIMITE, espera, path)
                self.sleep(espera)
                # A espera calculada já respeitou o reset deste recurso.
                self.resets.pop(self._recurso(path), None)
                continue
            if 500 <= resposta.status_code < 600 and falhas < len(BACKOFF_5XX):
                espera = BACKOFF_5XX[falhas]
                falhas += 1
                log.warning("HTTP %d: repetição %d/%d após %ds (%s)",
                            resposta.status_code, falhas, len(BACKOFF_5XX), espera, path)
                self.sleep(espera)
                continue
            resposta.raise_for_status()
            return resposta
