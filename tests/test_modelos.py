import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from modelos import (
    Algoritmo, Resultado, Timer, ConfigSimulacao,
    heuristica_manhattan, heuristica_euclidiana,
)


def test_resultado_criacao():
    r = Resultado(algoritmo=Algoritmo.A_ESTRELA)
    assert r.algoritmo == Algoritmo.A_ESTRELA
    assert r.encontrou is False
    assert r.nos_expandidos == 0
    assert r.caminho == []


def test_resultado_com_caminho():
    r = Resultado(
        algoritmo=Algoritmo.BFS,
        caminho=[(0, 0), (0, 1), (0, 2)],
        encontrou=True,
        nos_expandidos=15,
        custo_total=2.0,
        tempo_ms=0.5,
    )
    assert r.encontrou is True
    assert len(r.caminho) == 3
    assert r.custo_total == 2.0


def test_timer():
    with Timer() as t:
        total = sum(range(10000))
    assert t.tempo_ms > 0
    assert t.tempo_ms < 1000


def test_heuristica_manhattan():
    assert heuristica_manhattan((0, 0), (3, 4)) == 7
    assert heuristica_manhattan((2, 2), (2, 2)) == 0
    assert heuristica_manhattan((0, 0), (0, 5)) == 5


def test_heuristica_euclidiana():
    assert heuristica_euclidiana((0, 0), (3, 4)) == 5.0
    assert heuristica_euclidiana((0, 0), (0, 0)) == 0.0


def test_config_validar():
    ConfigSimulacao(grid_linhas=10, grid_colunas=10, num_carros=5).validar()

    try:
        ConfigSimulacao(grid_linhas=2, grid_colunas=2).validar()
        assert False, "Deveria ter dado ValueError"
    except ValueError:
        pass


def test_config_carros_demais():
    try:
        ConfigSimulacao(grid_linhas=3, grid_colunas=3, num_carros=100).validar()
        assert False, "Deveria ter dado ValueError"
    except ValueError:
        pass


def test_algoritmo_enum():
    assert len(Algoritmo) == 4
    assert Algoritmo.BFS.value == "BFS"
    assert Algoritmo.DFS.value == "DFS"
    assert Algoritmo.GREEDY.value == "Greedy"
    assert Algoritmo.A_ESTRELA.value == "A*"
