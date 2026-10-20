"""Fila limitada com resultados na ordem de entrada e cancelamento ao encerrar."""

from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager


@contextmanager
def mapear_ordenado(buscar, itens, workers, limite=None):
    """Não submete a lista inteira; `limite` pode reduzir a fila perto do alvo.

    O coordenador consome em ordem. Ao sair, tarefas não iniciadas são
    canceladas e as já iniciadas terminam seus checkpoints antes do retorno.
    """
    if workers == 1:
        yield map(buscar, itens)
        return
    executor = ThreadPoolExecutor(max_workers=workers)
    pendentes = deque()
    entradas = iter(itens)

    def preencher():
        capacidade = workers if limite is None else min(workers, limite())
        while len(pendentes) < capacidade:
            try:
                item = next(entradas)
            except StopIteration:
                break
            pendentes.append(executor.submit(buscar, item))

    def resultados():
        preencher()
        while pendentes:
            yield pendentes.popleft().result()
            preencher()

    try:
        yield resultados()
    finally:
        for futuro in pendentes:
            futuro.cancel()
        executor.shutdown(wait=True, cancel_futures=True)


@contextmanager
def mapear_concluidos(buscar, itens, workers, limite=None):
    """Mantém vagas ocupadas mesmo quando um repositório demora mais que os outros."""
    executor = ThreadPoolExecutor(max_workers=workers)
    pendentes = set()
    entradas = iter(itens)

    def resultados():
        while True:
            capacidade = workers if limite is None else min(workers, limite())
            while len(pendentes) < capacidade:
                try:
                    item = next(entradas)
                except StopIteration:
                    break
                pendentes.add(executor.submit(buscar, item))
            if not pendentes:
                return
            prontos, _ = wait(pendentes, return_when=FIRST_COMPLETED)
            # Retira um só: os outros ainda contam para o limite perto da meta.
            pronto = next(iter(prontos))
            pendentes.remove(pronto)
            yield pronto.result()

    try:
        yield resultados()
    finally:
        for futuro in pendentes:
            futuro.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
