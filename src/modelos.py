from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Algoritmo(Enum):
    BFS = "BFS"
    DFS = "DFS"
    GREEDY = "Greedy"
    A_ESTRELA = "A*"


class EstadoSemaforo(Enum):
    VERDE = "verde"
    VERMELHO = "vermelho"
    AMARELO = "amarelo"


class Direcao(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


No = tuple[int, int]
Caminho = list[No]


@dataclass
class Resultado:
    algoritmo: Algoritmo
    caminho: Caminho = field(default_factory=list)
    encontrou: bool = False
    nos_expandidos: int = 0
    custo_total: float = 0.0
    tempo_ms: float = 0.0

    def __repr__(self) -> str:
        status = "✓" if self.encontrou else "✗"
        return (
            f"Resultado({status} {self.algoritmo.value}: "
            f"custo={self.custo_total:.1f}, "
            f"nós={self.nos_expandidos}, "
            f"tempo={self.tempo_ms:.2f}ms, "
            f"passos={len(self.caminho)})"
        )


class Timer:
    def __init__(self):
        self.inicio: float = 0.0
        self.fim: float = 0.0
        self.tempo_ms: float = 0.0

    def __enter__(self) -> Timer:
        self.inicio = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.fim = time.perf_counter()
        self.tempo_ms = (self.fim - self.inicio) * 1000


@dataclass
class ConfigSimulacao:
    grid_linhas: int = 10
    grid_colunas: int = 10
    num_carros: int = 5
    algoritmo_padrao: Algoritmo = Algoritmo.A_ESTRELA
    prob_acidente: float = 0.02
    duracao_acidente: int = 10
    fator_congestionamento: float = 0.5
    intervalo_semaforo: int = 5
    seed: Optional[int] = None

    def validar(self) -> None:
        if self.grid_linhas < 3 or self.grid_colunas < 3:
            raise ValueError("Grid deve ter pelo menos 3x3.")
        if self.num_carros < 1:
            raise ValueError("Deve ter pelo menos 1 carro.")
        if self.num_carros > self.grid_linhas * self.grid_colunas // 2:
            raise ValueError("Carros demais pro tamanho do grid.")
        if not 0.0 <= self.prob_acidente <= 1.0:
            raise ValueError("Probabilidade de acidente deve estar entre 0 e 1.")


def heuristica_manhattan(no_atual: No, no_destino: No) -> float:
    return abs(no_atual[0] - no_destino[0]) + abs(no_atual[1] - no_destino[1])


def heuristica_euclidiana(no_atual: No, no_destino: No) -> float:
    return ((no_atual[0] - no_destino[0]) ** 2 + (no_atual[1] - no_destino[1]) ** 2) ** 0.5
