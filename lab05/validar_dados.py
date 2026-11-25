"""Valida os dados da #307 e publica relatórios sem alterar as entradas."""

import argparse
import csv
import json
from pathlib import Path

from experimento.config import DIR_DADOS
from experimento.validacao import COLUNAS_OUTLIERS, COLUNAS_TEMPORAIS, sha256, validar


def publicar(diretorio: Path, saida: Path) -> dict:
    # Protege entradas e também a publicação anterior contra uma saída que as substitua.
    diretorio, saida = Path(diretorio).resolve(), Path(saida).resolve()
    if saida == diretorio or diretorio.is_relative_to(saida):
        raise ValueError("A saída deve ser uma subpasta ou um diretório separado das entradas.")
    relatorio = validar(diretorio)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "validacao.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8",
    )
    for nome, campos, linhas in (
        ("outliers.csv", COLUNAS_OUTLIERS, relatorio["outliers"]),
        ("diagnostico-temporal.csv", COLUNAS_TEMPORAIS, relatorio["diagnostico_temporal"]),
    ):
        with (saida / nome).open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(linhas)
    manifesto = {
        "versao": 1, "coleta": relatorio["coleta"], "status": relatorio["status"],
        "publicado_para_analise_exploratoria": relatorio["status"] == "aprovada",
        "dados": "../resultados.csv" if saida.parent == diretorio else str(diretorio / "resultados.csv"),
        "dicionario": "lab05/docs/07-validacao-dicionario-dados.md",
        "medicoes": relatorio["medicoes_lidas"], "colunas": relatorio["colunas"],
        "entradas_sha256": relatorio["entradas_sha256"],
        "relatorios_sha256": {nome: sha256(saida / nome) for nome in (
            "validacao.json", "outliers.csv", "diagnostico-temporal.csv",
        )},
        "inferencia": relatorio["inferencia"], "observacoes_excluidas": 0,
    }
    (saida / "manifesto.json").write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8",
    )
    return relatorio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diretorio", type=Path, default=DIR_DADOS / "coleta-completa-01")
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args(argv)
    try:
        relatorio = publicar(args.diretorio, args.saida or args.diretorio / "validacao")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Validação {relatorio['status']}: {relatorio['medicoes_lidas']} medições, "
          f"{len(relatorio['erros'])} erros, {relatorio['outliers_observacoes_unicas']} observações sinalizadas.")
    return 0 if relatorio["status"] == "aprovada" else 1


if __name__ == "__main__":
    raise SystemExit(main())
