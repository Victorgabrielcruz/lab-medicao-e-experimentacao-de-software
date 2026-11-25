"""Lançador da coleta #306; mantém o terminal e registra início/fim do processo."""

import ctypes
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

raiz = Path(__file__).resolve().parents[2]
saida = raiz / "data" / "coleta-completa-01"
saida.mkdir(exist_ok=False)
shutil.copyfile(__file__, saida / "lancador.py")
sys.stdout.reconfigure(encoding="utf-8")
fontes = ["executar.py", "experimento/benchmark.py", "experimento/config.py", "experimento/ambiente.py"]
comando = [sys.executable, str(raiz / "executar.py"), "--diretorio", str(saida),
           "--repeticoes", "30", "--aquecimentos", "3", "--semente", "42", "--progresso"]
registro = {
    "status": "em_execucao",
    "inicio_utc": datetime.now(timezone.utc).isoformat(),
    "commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
    "sha256_fontes": {nome: hashlib.sha256((raiz / nome).read_bytes()).hexdigest() for nome in fontes},
    "sha256_lancador": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "comando": comando,
    "cpu": "AMD Ryzen 5 8500G w/ Radeon 740M Graphics",
    "nucleos_fisicos": 6,
    "processadores_logicos": 12,
    "memoria_fisica_bytes": 16221278208,
    "disco": "WD Green SN350 500GB 2G0C",
    "tipo_disco": "SSD NVMe", "sistema_arquivos": "NTFS",
    "plano_energia": "Equilibrado (381b4222-f694-41f0-9685-ff5bb260df2e)",
    "condicoes": "Hardware e plano de energia consultados antes da coleta. Aplicativos existentes não foram encerrados; sem isolamento do SO, limpeza de cache ou desativação de proteções. Alimentação externa não instrumentada. Nenhum teste, análise ou outro benchmark iniciado pelo agente durante a execução.",
    "progresso": "Uma linha por execução concluída, após o cronômetro e a limpeza; sem alteração das cargas ou da sequência sorteada.",
}
api = ctypes.windll.kernel32.SetThreadExecutionState
api.argtypes = [ctypes.c_uint]
api.restype = ctypes.c_uint
anterior = api(0x80000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED; pedido transitório.
registro["suspensao_impedida"] = bool(anterior)
if not anterior:
    raise RuntimeError("Não foi possível impedir suspensão durante a coleta.")

def salvar():
    (saida / "execucao.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

try:
    salvar()
    print("COLETA COMPLETA #306 | 396 execuções (36 aquecimentos + 360 medições)", flush=True)
    print("Estimativa do piloto: 8 min; janela reservada: 16 min. Não suspenda ou feche este terminal.", flush=True)
    print(f"Saída: {saida}", flush=True)
    inicio = perf_counter()
    try:
        retorno = subprocess.run(comando, cwd=raiz, check=False).returncode
        registro["codigo_saida"] = retorno
        registro["status"] = "concluida" if retorno == 0 else "falha"
    except BaseException as erro:
        registro["status"] = "interrompida"
        registro["erro"] = repr(erro)
        raise
    finally:
        registro["duracao_parede_s"] = perf_counter() - inicio
        registro["fim_utc"] = datetime.now(timezone.utc).isoformat()
        salvar()
finally:
    api(0x80000000)  # Libera o pedido transitório; não altera o plano de energia.
print(f"\nColeta {registro['status']}; duração total: {registro['duracao_parede_s']:.2f} s", flush=True)
print("O terminal pode permanecer aberto. A validação dos dados será feita após a coleta.", flush=True)
raise SystemExit(retorno)
