from __future__ import annotations
from collections import defaultdict

try:
    from .modelos import Algoritmo, Resultado
except ImportError:
    from modelos import Algoritmo, Resultado


class ColetorMetricas:
    def __init__(self) -> None:
        self._dados: dict[Algoritmo, list[dict]] = defaultdict(list)

    def registrar(self, resultado: Resultado, recalculos: int = 0) -> None:
        self._dados[resultado.algoritmo].append({
            "nos_expandidos": resultado.nos_expandidos,
            "custo_total": resultado.custo_total if resultado.encontrou else None,
            "tempo_ms": resultado.tempo_ms,
            "encontrou": resultado.encontrou,
            "recalculos": recalculos,
        })

    def comparar_algoritmos(self) -> dict[Algoritmo, dict]:
        resultado = {}
        for algoritmo, registros in self._dados.items():
            nos = [r["nos_expandidos"] for r in registros]
            custos = [r["custo_total"] for r in registros if r["custo_total"] is not None]
            tempos = [r["tempo_ms"] for r in registros]
            recalculos = [r["recalculos"] for r in registros]

            resultado[algoritmo] = {
                "total_buscas": len(registros),
                "nos_expandidos_medio": sum(nos) / len(nos) if nos else 0.0,
                "custo_medio": sum(custos) / len(custos) if custos else 0.0,
                "tempo_medio_ms": sum(tempos) / len(tempos) if tempos else 0.0,
                "total_recalculos": sum(recalculos),
            }
        return resultado
