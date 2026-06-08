import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid
from modelos import Algoritmo, Resultado
from algoritmos import bfs, dfs


def test_bfs_retorna_resultado():
    g = Grid(3, 3)
    r = bfs(g, (0, 0), (2, 2))
    assert isinstance(r, Resultado)
    assert r.algoritmo == Algoritmo.BFS


def test_bfs_encontra_caminho_simples():
    g = Grid(3, 3)
    r = bfs(g, (0, 0), (0, 1))
    assert r.encontrou is True
    assert r.caminho == [(0, 0), (0, 1)]


def test_bfs_encontra_caminho_grid():
    g = Grid(5, 5)
    r = bfs(g, (0, 0), (4, 4))
    assert r.encontrou is True
    assert r.caminho[0] == (0, 0)
    assert r.caminho[-1] == (4, 4)


def test_bfs_caminho_valido_sem_saltos():
    g = Grid(5, 5)
    r = bfs(g, (0, 0), (4, 4))
    for i in range(len(r.caminho) - 1):
        a, b = r.caminho[i], r.caminho[i + 1]
        assert b in g.vizinhos(a), f"{b} nao e vizinho de {a}"


def test_bfs_origem_igual_destino():
    g = Grid(3, 3)
    r = bfs(g, (1, 1), (1, 1))
    assert r.encontrou is True
    assert r.caminho == [(1, 1)]


def test_bfs_sem_caminho():
    g = Grid(3, 3)
    # Isola (0,0) bloqueando todas as saidas
    g.bloquear_aresta((0, 0), (0, 1))
    g.bloquear_aresta((0, 0), (1, 0))
    r = bfs(g, (0, 0), (2, 2))
    assert r.encontrou is False
    assert r.caminho == []


def test_bfs_nos_expandidos():
    g = Grid(5, 5)
    r = bfs(g, (0, 0), (4, 4))
    assert r.nos_expandidos > 0


def test_bfs_custo_total():
    g = Grid(3, 3, peso_base=1.0)
    r = bfs(g, (0, 0), (0, 2))
    # Caminho minimo tem 2 arestas de peso 1.0
    assert r.encontrou is True
    assert r.custo_total == 2.0


def test_bfs_custo_com_congestionamento():
    g = Grid(3, 3, peso_base=1.0)
    g.incrementar_congestionamento((0, 0), (0, 1))  # peso vira 1.5
    # BFS ignora pesos — caminho minimo em saltos
    r = bfs(g, (0, 0), (0, 2))
    assert r.encontrou is True
    # custo soma os pesos reais das arestas percorridas
    assert r.custo_total == 1.5 + 1.0  # (0,0)->(0,1) + (0,1)->(0,2)


def test_bfs_tempo_medido():
    g = Grid(5, 5)
    r = bfs(g, (0, 0), (4, 4))
    assert r.tempo_ms >= 0


def test_bfs_menor_numero_de_passos():
    g = Grid(5, 5)
    r = bfs(g, (0, 0), (0, 4))
    # Caminho minimo em linhas retas = 4 arestas = 5 nos
    assert len(r.caminho) == 5


# DFS

def test_dfs_retorna_resultado():
    g = Grid(3, 3)
    r = dfs(g, (0, 0), (2, 2))
    assert isinstance(r, Resultado)
    assert r.algoritmo == Algoritmo.DFS


def test_dfs_encontra_caminho_simples():
    g = Grid(3, 3)
    r = dfs(g, (0, 0), (0, 1))
    assert r.encontrou is True
    assert r.caminho[0] == (0, 0)
    assert r.caminho[-1] == (0, 1)


def test_dfs_encontra_caminho_grid():
    g = Grid(5, 5)
    r = dfs(g, (0, 0), (4, 4))
    assert r.encontrou is True
    assert r.caminho[0] == (0, 0)
    assert r.caminho[-1] == (4, 4)


def test_dfs_caminho_valido_sem_saltos():
    g = Grid(5, 5)
    r = dfs(g, (0, 0), (4, 4))
    for i in range(len(r.caminho) - 1):
        a, b = r.caminho[i], r.caminho[i + 1]
        assert b in g.vizinhos(a), f"{b} nao e vizinho de {a}"


def test_dfs_origem_igual_destino():
    g = Grid(3, 3)
    r = dfs(g, (1, 1), (1, 1))
    assert r.encontrou is True
    assert r.caminho == [(1, 1)]


def test_dfs_sem_caminho():
    g = Grid(3, 3)
    g.bloquear_aresta((0, 0), (0, 1))
    g.bloquear_aresta((0, 0), (1, 0))
    r = dfs(g, (0, 0), (2, 2))
    assert r.encontrou is False
    assert r.caminho == []


def test_dfs_nos_expandidos():
    g = Grid(5, 5)
    r = dfs(g, (0, 0), (4, 4))
    assert r.nos_expandidos > 0


def test_dfs_custo_total():
    g = Grid(3, 3, peso_base=1.0)
    r = dfs(g, (0, 0), (0, 2))
    assert r.encontrou is True
    assert r.custo_total > 0


def test_dfs_custo_com_congestionamento():
    g = Grid(3, 3, peso_base=1.0)
    g.incrementar_congestionamento((0, 0), (0, 1))
    r = dfs(g, (0, 0), (0, 2))
    assert r.encontrou is True
    # custo soma os pesos reais das arestas percorridas
    assert r.custo_total > 0


def test_dfs_tempo_medido():
    g = Grid(5, 5)
    r = dfs(g, (0, 0), (4, 4))
    assert r.tempo_ms >= 0


def test_dfs_nao_repete_nos():
    g = Grid(5, 5)
    r = dfs(g, (0, 0), (4, 4))
    assert len(r.caminho) == len(set(r.caminho))
