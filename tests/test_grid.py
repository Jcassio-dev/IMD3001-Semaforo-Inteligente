import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid


def test_grid_criacao():
    g = Grid(5, 5)
    assert g.linhas == 5
    assert g.colunas == 5
    assert g.total_nos() == 25


def test_grid_vizinhos_centro():
    g = Grid(5, 5)
    vizinhos = g.vizinhos((2, 2))
    assert len(vizinhos) == 4
    assert (1, 2) in vizinhos
    assert (3, 2) in vizinhos
    assert (2, 1) in vizinhos
    assert (2, 3) in vizinhos


def test_grid_vizinhos_canto():
    g = Grid(5, 5)
    vizinhos = g.vizinhos((0, 0))
    assert len(vizinhos) == 2
    assert (0, 1) in vizinhos
    assert (1, 0) in vizinhos


def test_grid_vizinhos_borda():
    g = Grid(5, 5)
    vizinhos = g.vizinhos((0, 2))
    assert len(vizinhos) == 3


def test_grid_peso_base():
    g = Grid(5, 5, peso_base=1.0)
    assert g.peso((0, 0), (0, 1)) == 1.0


def test_grid_bloquear_aresta():
    g = Grid(5, 5)
    g.bloquear_aresta((2, 2), (2, 3))
    assert (2, 3) not in g.vizinhos((2, 2))
    assert (2, 2) not in g.vizinhos((2, 3))


def test_grid_desbloquear_aresta():
    g = Grid(5, 5)
    g.bloquear_aresta((2, 2), (2, 3))
    g.desbloquear_aresta((2, 2), (2, 3))
    assert (2, 3) in g.vizinhos((2, 2))


def test_grid_congestionamento():
    g = Grid(5, 5, peso_base=1.0)
    assert g.peso((0, 0), (0, 1)) == 1.0
    g.incrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 1.5
    g.incrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 2.0


def test_grid_decrementar_congestionamento():
    g = Grid(5, 5, peso_base=1.0)
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.decrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 1.5


def test_grid_resetar_congestionamento():
    g = Grid(5, 5)
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.incrementar_congestionamento((1, 1), (1, 2))
    g.resetar_congestionamento()
    assert g.peso((0, 0), (0, 1)) == 1.0
    assert g.peso((1, 1), (1, 2)) == 1.0


def test_grid_no_valido():
    g = Grid(5, 5)
    assert g.no_valido((0, 0)) is True
    assert g.no_valido((4, 4)) is True
    assert g.no_valido((5, 5)) is False
    assert g.no_valido((-1, 0)) is False


def test_grid_todos_os_nos():
    g = Grid(3, 3)
    nos = g.todos_os_nos()
    assert len(nos) == 9
    assert (0, 0) in nos
    assert (2, 2) in nos


def test_grid_repr():
    g = Grid(10, 10)
    g.bloquear_aresta((0, 0), (0, 1))
    r = repr(g)
    assert "10x10" in r
    assert "100" in r
