from __future__ import annotations
from typing import Optional


class Grid:

    DIRECOES = {
        "cima": (-1, 0),
        "baixo": (1, 0),
        "esquerda": (0, -1),
        "direita": (0, 1),
    }

    def __init__(self, linhas: int, colunas: int, peso_base: float = 1.0):
        self.linhas = linhas
        self.colunas = colunas
        self.peso_base = peso_base
        self._pesos: dict[tuple[tuple[int, int], tuple[int, int]], float] = {}
        self._bloqueadas: set[tuple[tuple[int, int], tuple[int, int]]] = set()
        self._congestionamento: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
        self.semaforos: dict[tuple[int, int], object] = {}
        self._criar_arestas()

    def _criar_arestas(self) -> None:
        for i in range(self.linhas):
            for j in range(self.colunas):
                for di, dj in self.DIRECOES.values():
                    ni, nj = i + di, j + dj
                    if self._dentro_do_grid(ni, nj):
                        aresta = ((i, j), (ni, nj))
                        self._pesos[aresta] = self.peso_base
                        self._congestionamento[aresta] = 0

    def _dentro_do_grid(self, i: int, j: int) -> bool:
        return 0 <= i < self.linhas and 0 <= j < self.colunas

    def no_valido(self, no: tuple[int, int]) -> bool:
        return self._dentro_do_grid(no[0], no[1])

    def vizinhos(self, no: tuple[int, int]) -> list[tuple[int, int]]:
        i, j = no
        resultado = []
        for di, dj in self.DIRECOES.values():
            ni, nj = i + di, j + dj
            if self._dentro_do_grid(ni, nj):
                aresta = ((i, j), (ni, nj))
                if aresta not in self._bloqueadas:
                    resultado.append((ni, nj))
        return resultado

    def peso(self, origem: tuple[int, int], destino: tuple[int, int]) -> float:
        aresta = (origem, destino)
        if aresta in self._bloqueadas:
            raise ValueError(f"Aresta {aresta} está bloqueada (acidente).")
        if aresta not in self._pesos:
            raise ValueError(f"Aresta {aresta} não existe no grid.")
        return self._pesos[aresta] + (self._congestionamento.get(aresta, 0) * 0.5)

    def total_nos(self) -> int:
        return self.linhas * self.colunas

    def todos_os_nos(self) -> list[tuple[int, int]]:
        return [(i, j) for i in range(self.linhas) for j in range(self.colunas)]

    def atualizar_peso(self, origem: tuple[int, int], destino: tuple[int, int], novo_peso: float) -> None:
        self._pesos[(origem, destino)] = novo_peso
        self._pesos[(destino, origem)] = novo_peso

    def bloquear_aresta(self, origem: tuple[int, int], destino: tuple[int, int]) -> None:
        self._bloqueadas.add((origem, destino))
        self._bloqueadas.add((destino, origem))

    def desbloquear_aresta(self, origem: tuple[int, int], destino: tuple[int, int]) -> None:
        self._bloqueadas.discard((origem, destino))
        self._bloqueadas.discard((destino, origem))

    def aresta_bloqueada(self, origem: tuple[int, int], destino: tuple[int, int]) -> bool:
        return (origem, destino) in self._bloqueadas

    def incrementar_congestionamento(self, origem: tuple[int, int], destino: tuple[int, int]) -> None:
        aresta = (origem, destino)
        aresta_inv = (destino, origem)
        self._congestionamento[aresta] = self._congestionamento.get(aresta, 0) + 1
        self._congestionamento[aresta_inv] = self._congestionamento.get(aresta_inv, 0) + 1

    def decrementar_congestionamento(self, origem: tuple[int, int], destino: tuple[int, int]) -> None:
        aresta = (origem, destino)
        aresta_inv = (destino, origem)
        self._congestionamento[aresta] = max(0, self._congestionamento.get(aresta, 0) - 1)
        self._congestionamento[aresta_inv] = max(0, self._congestionamento.get(aresta_inv, 0) - 1)

    def resetar_congestionamento(self) -> None:
        for aresta in self._congestionamento:
            self._congestionamento[aresta] = 0

    def get_congestionamento(self, origem: tuple[int, int], destino: tuple[int, int]) -> int:
        return self._congestionamento.get((origem, destino), 0)

    def __repr__(self) -> str:
        bloqueadas = len(self._bloqueadas) // 2  # registrado nas duas direções
        return (
            f"Grid({self.linhas}x{self.colunas}, "
            f"nós={self.total_nos()}, "
            f"bloqueadas={bloqueadas})"
        )
