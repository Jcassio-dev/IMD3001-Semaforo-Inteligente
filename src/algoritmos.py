from __future__ import annotations
import heapq
from collections import deque

from grid import Grid
from modelos import Algoritmo, Resultado, Timer, No, heuristica_manhattan


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


def greedy_best_first(grid: Grid, inicio: No, destino: No) -> Resultado:
    if inicio == destino:
        return Resultado(
            algoritmo=Algoritmo.GREEDY,
            caminho=[inicio],
            encontrou=True,
            nos_expandidos=0,
            custo_total=0.0,
        )

    with Timer() as t:
        contador = 0
        fila: list[tuple[float, int, No, list[No]]] = []
        heapq.heappush(fila, (heuristica_manhattan(inicio, destino), contador, inicio, [inicio]))
        visitados: set[No] = {inicio}
        nos_expandidos = 0

        while fila:
            _h, _c, atual, caminho = heapq.heappop(fila)
            nos_expandidos += 1

            if atual == destino:
                custo = _calcular_custo(grid, caminho)
                return Resultado(
                    algoritmo=Algoritmo.GREEDY,
                    caminho=caminho,
                    encontrou=True,
                    nos_expandidos=nos_expandidos,
                    custo_total=custo,
                    tempo_ms=t.tempo_ms,
                )

            for vizinho in grid.vizinhos(atual):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    contador += 1
                    h = heuristica_manhattan(vizinho, destino)
                    heapq.heappush(fila, (h, contador, vizinho, caminho + [vizinho]))

    return Resultado(
        algoritmo=Algoritmo.GREEDY,
        caminho=[],
        encontrou=False,
        nos_expandidos=nos_expandidos,
        tempo_ms=t.tempo_ms,
    )


def a_estrela(grid: Grid, inicio: No, destino: No) -> Resultado:
    if inicio == destino:
        return Resultado(
            algoritmo=Algoritmo.A_ESTRELA,
            caminho=[inicio],
            encontrou=True,
            nos_expandidos=0,
            custo_total=0.0,
        )

    with Timer() as t:
        contador = 0
        h_inicio = heuristica_manhattan(inicio, destino)
        fila: list[tuple[float, int, No, list[No]]] = []
        heapq.heappush(fila, (h_inicio, contador, inicio, [inicio]))
        g_custos: dict[No, float] = {inicio: 0.0}
        fechados: set[No] = set()
        nos_expandidos = 0

        while fila:
            _f, _c, atual, caminho = heapq.heappop(fila)

            if atual in fechados:
                continue
            fechados.add(atual)
            nos_expandidos += 1

            if atual == destino:
                return Resultado(
                    algoritmo=Algoritmo.A_ESTRELA,
                    caminho=caminho,
                    encontrou=True,
                    nos_expandidos=nos_expandidos,
                    custo_total=g_custos[atual],
                    tempo_ms=t.tempo_ms,
                )

            g_atual = g_custos[atual]

            for vizinho in grid.vizinhos(atual):
                if vizinho in fechados:
                    continue
                g_novo = g_atual + grid.peso(atual, vizinho)
                if vizinho not in g_custos or g_novo < g_custos[vizinho]:
                    g_custos[vizinho] = g_novo
                    contador += 1
                    f = g_novo + heuristica_manhattan(vizinho, destino)
                    heapq.heappush(fila, (f, contador, vizinho, caminho + [vizinho]))

    return Resultado(
        algoritmo=Algoritmo.A_ESTRELA,
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

