from __future__ import annotations
from collections import deque

from grid import Grid
from modelos import Algoritmo, Resultado, Timer, No


def bfs(grid: Grid, inicio: No, destino: No) -> Resultado:
    if inicio == destino:
        return Resultado(
            algoritmo=Algoritmo.BFS,
            caminho=[inicio],
            encontrou=True,
            nos_expandidos=0,
            custo_total=0.0,
        )

    with Timer() as t:
        fila: deque[tuple[No, list[No]]] = deque()
        fila.append((inicio, [inicio]))
        visitados: set[No] = {inicio}
        nos_expandidos = 0

        while fila:
            atual, caminho = fila.popleft()
            nos_expandidos += 1

            for vizinho in grid.vizinhos(atual):
                if vizinho == destino:
                    caminho_final = caminho + [vizinho]
                    custo = _calcular_custo(grid, caminho_final)
                    return Resultado(
                        algoritmo=Algoritmo.BFS,
                        caminho=caminho_final,
                        encontrou=True,
                        nos_expandidos=nos_expandidos,
                        custo_total=custo,
                        tempo_ms=t.tempo_ms,
                    )
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    fila.append((vizinho, caminho + [vizinho]))

    return Resultado(
        algoritmo=Algoritmo.BFS,
        caminho=[],
        encontrou=False,
        nos_expandidos=nos_expandidos,
        tempo_ms=t.tempo_ms,
    )


def dfs(grid: Grid, inicio: No, destino: No) -> Resultado:
    if inicio == destino:
        return Resultado(
            algoritmo=Algoritmo.DFS,
            caminho=[inicio],
            encontrou=True,
            nos_expandidos=0,
            custo_total=0.0,
        )

    with Timer() as t:
        pilha: list[tuple[No, list[No]]] = [(inicio, [inicio])]
        visitados: set[No] = {inicio}
        nos_expandidos = 0

        while pilha:
            atual, caminho = pilha.pop()
            nos_expandidos += 1

            if atual == destino:
                custo = _calcular_custo(grid, caminho)
                return Resultado(
                    algoritmo=Algoritmo.DFS,
                    caminho=caminho,
                    encontrou=True,
                    nos_expandidos=nos_expandidos,
                    custo_total=custo,
                    tempo_ms=t.tempo_ms,
                )

            for vizinho in grid.vizinhos(atual):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    pilha.append((vizinho, caminho + [vizinho]))

    return Resultado(
        algoritmo=Algoritmo.DFS,
        caminho=[],
        encontrou=False,
        nos_expandidos=nos_expandidos,
        tempo_ms=t.tempo_ms,
    )


def _calcular_custo(grid: Grid, caminho: list[No]) -> float:
    return sum(
        grid.peso(caminho[i], caminho[i + 1])
        for i in range(len(caminho) - 1)
    )
