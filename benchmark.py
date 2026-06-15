#!/usr/bin/env python3
"""
benchmark.py — Compara algoritmos de busca da simulação de trânsito.

Executa cada algoritmo N ticks com seeds diferentes (mesma config) e salva
os resultados em CSV para análise comparativa.

Uso:
    python benchmark.py
    python benchmark.py --ticks 500 --linhas 25 --colunas 25 --carros 30 \\
        --semaforos 15 --prob-acidente 0.08 --duracao-acidente 25 \\
        --seeds 42 123 456 789 1001 --output benchmark_results.csv
"""

import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simulacao import Simulacao, ConfigVisual
from src.modelos import Algoritmo

ALGORITMOS = [Algoritmo.BFS, Algoritmo.DFS, Algoritmo.GREEDY, Algoritmo.A_ESTRELA]
OUTPUT_PADRAO = "benchmark_results.csv"

CAMPOS = [
    "algoritmo", "seed", "rodada", "ticks",
    "carros_chegaram", "carros_sem_rota", "carros_aguardando",
    "total_movimentos",
    "nos_expandidos_medio", "custo_medio", "tempo_medio_ms",
    "total_recalculos", "media_ticks_chegada",
]


def rodar(algoritmo: Algoritmo, seed: int, rodada: int, args: argparse.Namespace) -> dict:
    config = ConfigVisual(
        linhas=args.linhas,
        colunas=args.colunas,
        num_carros=args.carros,
        num_semaforos=args.semaforos,
        num_incidentes=0,
        duracao_incidente=args.duracao_acidente,
        prob_acidente=args.prob_acidente,
        algoritmo_carros=algoritmo,
        seed=seed,
    )
    sim = Simulacao(config)
    total_movimentos = 0

    for _ in range(args.ticks):
        sim.step()
        total_movimentos += sim.movimentos_no_tick

    metricas = sim.metricas.comparar_algoritmos()
    m = metricas.get(algoritmo, {})

    dados_carros = sim.dados_carros(limite=args.carros)
    tempos = [c["tempo_ate_chegada"] for c in dados_carros if c["tempo_ate_chegada"] is not None]
    media_chegada = round(sum(tempos) / len(tempos), 2) if tempos else ""

    return {
        "algoritmo": algoritmo.value,
        "seed": seed,
        "rodada": rodada,
        "ticks": args.ticks,
        "carros_chegaram": sim.carros_chegaram,
        "carros_sem_rota": sim.carros_sem_rota,
        "carros_aguardando": sim.carros_aguardando,
        "total_movimentos": total_movimentos,
        "nos_expandidos_medio": round(m.get("nos_expandidos_medio", 0.0), 4),
        "custo_medio": round(m.get("custo_medio", 0.0), 4),
        "tempo_medio_ms": round(m.get("tempo_medio_ms", 0.0), 6),
        "total_recalculos": m.get("total_recalculos", 0),
        "media_ticks_chegada": media_chegada,
    }


def imprimir_tabela_resumo(caminho_csv: str) -> None:
    from collections import defaultdict
    import math

    dados: dict[str, list[dict]] = defaultdict(list)
    with open(caminho_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados[row["algoritmo"]].append(row)

    ORDEM = ["BFS", "DFS", "Greedy", "A*"]
    METRICAS = [
        ("nos_expandidos_medio", "Nos expandidos", ".1f"),
        ("custo_medio",          "Custo medio",    ".2f"),
        ("tempo_medio_ms",       "Tempo (ms)",     ".4f"),
        ("total_recalculos",     "Recalculos",     ".0f"),
        ("carros_chegaram",      "Chegaram",       ".1f"),
        ("media_ticks_chegada",  "Ticks chegada",  ".1f"),
    ]

    def media(linhas, campo):
        vals = [float(r[campo]) for r in linhas if r.get(campo, "") not in ("", None)]
        return sum(vals) / len(vals) if vals else 0.0

    def desvio(linhas, campo):
        vals = [float(r[campo]) for r in linhas if r.get(campo, "") not in ("", None)]
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        return math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))

    algos = [a for a in ORDEM if a in dados]
    col_w = 18
    header = f"{'Metrica':<22}" + "".join(f"{a:>{col_w}}" for a in algos)
    sep = "-" * len(header)

    print("\n" + sep)
    print("TABELA RESUMO — medias sobre as rodadas (desvio padrao)")
    print(sep)
    print(header)
    print(sep)

    for campo, label, fmt in METRICAS:
        linha = f"{label:<22}"
        for algo in algos:
            m = media(dados[algo], campo)
            d = desvio(dados[algo], campo)
            cell = f"{m:{fmt}} ±{d:{fmt}}"
            linha += f"{cell:>{col_w}}"
        print(linha)

    print(sep + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark de algoritmos de busca de trânsito")
    parser.add_argument("--ticks",           type=int,   default=1000)
    parser.add_argument("--linhas",          type=int,   default=10)
    parser.add_argument("--colunas",         type=int,   default=10)
    parser.add_argument("--carros",          type=int,   default=8)
    parser.add_argument("--semaforos",       type=int,   default=6)
    parser.add_argument("--prob-acidente",   type=float, default=0.05, dest="prob_acidente")
    parser.add_argument("--duracao-acidente",type=int,   default=20,   dest="duracao_acidente")
    parser.add_argument("--seeds",           type=int,   nargs="+",    default=[42, 137, 999])
    parser.add_argument("--output",          default=OUTPUT_PADRAO)
    args = parser.parse_args()

    total = len(ALGORITMOS) * len(args.seeds)
    atual = 0

    print(f"Benchmark: {len(ALGORITMOS)} algoritmos x {len(args.seeds)} seeds x {args.ticks} ticks")
    print(f"Grid: {args.linhas}x{args.colunas}  |  Carros: {args.carros}  |  Semaforos: {args.semaforos}")
    print(f"Prob. acidente: {args.prob_acidente}  |  Duracao acidente: {args.duracao_acidente} ticks")
    print("-" * 65)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()

        for algoritmo in ALGORITMOS:
            for rodada, seed in enumerate(args.seeds, start=1):
                atual += 1
                label = f"{algoritmo.value:<8}"
                print(f"[{atual:2}/{total}] {label} seed={seed:<6} ticks={args.ticks} ...", end=" ", flush=True)

                t0 = time.perf_counter()
                resultado = rodar(algoritmo, seed, rodada, args)
                dt = time.perf_counter() - t0

                writer.writerow(resultado)
                f.flush()

                chegaram  = resultado["carros_chegaram"]
                recalcs   = resultado["total_recalculos"]
                media_c   = resultado["media_ticks_chegada"] or "N/A"
                print(f"OK ({dt:.1f}s)  chegaram={chegaram}  recalculos={recalcs}  media_chegada={media_c}")

    print("-" * 65)
    print(f"Resultados salvos em: {args.output}")

    imprimir_tabela_resumo(args.output)

    print(f"Para gerar os graficos: python benchmark_plot.py --input {args.output}")


if __name__ == "__main__":
    main()
