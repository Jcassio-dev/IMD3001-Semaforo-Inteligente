from __future__ import annotations
import random

try:
    from .grid import Grid
except ImportError:
    from grid import Grid

No = tuple[int, int]
Aresta = tuple[No, No]


class SistemaAcidentes:
    def __init__(
        self,
        grid: Grid,
        prob_acidente: float,
        duracao_acidente: int,
        seed: int | None = None,
    ) -> None:
        self._grid = grid
        self._prob = prob_acidente
        self._duracao = duracao_acidente
        self._rng = random.Random(seed)
        self._acidentes: dict[Aresta, int] = {}

    @property
    def acidentes_ativos(self) -> dict[Aresta, int]:
        return dict(self._acidentes)

    def tick(self, carros: list) -> None:
        self._decrementar()
        if self._rng.random() < self._prob:
            aresta = self._sortear_aresta_livre()
            if aresta is not None:
                origem, destino = aresta
                self._grid.bloquear_aresta(origem, destino)
                self._acidentes[aresta] = self._duracao
                self._notificar(aresta, carros)

    def _decrementar(self) -> None:
        expirar = [a for a, t in self._acidentes.items() if t <= 1]
        for aresta in expirar:
            origem, destino = aresta
            self._grid.desbloquear_aresta(origem, destino)
            del self._acidentes[aresta]
        for aresta in self._acidentes:
            self._acidentes[aresta] -= 1

    def _notificar(self, aresta: Aresta, carros: list) -> None:
        origem, destino = aresta
        for carro in carros:
            if carro.chegou:
                continue
            rota = carro.rota
            for i in range(len(rota) - 1):
                if (rota[i] == origem and rota[i + 1] == destino) or \
                   (rota[i] == destino and rota[i + 1] == origem):
                    carro.recalcular_rota()
                    break

    def _sortear_aresta_livre(self) -> Aresta | None:
        candidatos: list[Aresta] = []
        for i in range(self._grid.linhas):
            for j in range(self._grid.colunas):
                origem = (i, j)
                for destino in self._grid.vizinhos(origem):
                    if origem < destino and not self._grid.aresta_bloqueada(origem, destino):
                        candidatos.append((origem, destino))
        if not candidatos:
            return None
        return self._rng.choice(candidatos)
