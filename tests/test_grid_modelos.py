
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid
from modelos import (
    Algoritmo, Resultado, Timer, ConfigSimulacao,
    heuristica_manhattan, heuristica_euclidiana
)


def test_grid_criacao():
    g = Grid(5, 5)
    assert g.linhas == 5
    assert g.colunas == 5
    assert g.total_nos() == 25


def test_grid_vizinhos_centro():
    g = Grid(5, 5)
    vizinhos = g.vizinhos((2, 2))
    assert len(vizinhos) == 4
    assert (1, 2) in vizinhos  # cima
    assert (3, 2) in vizinhos  # baixo
    assert (2, 1) in vizinhos  # esquerda
    assert (2, 3) in vizinhos  # direita


def test_grid_vizinhos_canto():
    """Nó no canto deve ter 2 vizinhos."""
    g = Grid(5, 5)
    vizinhos = g.vizinhos((0, 0))
    assert len(vizinhos) == 2
    assert (0, 1) in vizinhos
    assert (1, 0) in vizinhos


def test_grid_vizinhos_borda():
    """Nó na borda (não canto) deve ter 3 vizinhos."""
    g = Grid(5, 5)
    vizinhos = g.vizinhos((0, 2))
    assert len(vizinhos) == 3


def test_grid_peso_base():
    """Peso padrão deve ser o peso_base."""
    g = Grid(5, 5, peso_base=1.0)
    assert g.peso((0, 0), (0, 1)) == 1.0


def test_grid_bloquear_aresta():
    """Aresta bloqueada não deve aparecer nos vizinhos."""
    g = Grid(5, 5)
    g.bloquear_aresta((2, 2), (2, 3))
    vizinhos = g.vizinhos((2, 2))
    assert (2, 3) not in vizinhos
    # A aresta inversa também deve estar bloqueada
    vizinhos_inv = g.vizinhos((2, 3))
    assert (2, 2) not in vizinhos_inv


def test_grid_desbloquear_aresta():
    """Aresta desbloqueada deve voltar a aparecer."""
    g = Grid(5, 5)
    g.bloquear_aresta((2, 2), (2, 3))
    g.desbloquear_aresta((2, 2), (2, 3))
    vizinhos = g.vizinhos((2, 2))
    assert (2, 3) in vizinhos


def test_grid_congestionamento():
    """Congestionamento deve aumentar o peso da aresta."""
    g = Grid(5, 5, peso_base=1.0)
    assert g.peso((0, 0), (0, 1)) == 1.0

    g.incrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 1.5  # 1.0 + 1 * 0.5

    g.incrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 2.0  # 1.0 + 2 * 0.5


def test_grid_decrementar_congestionamento():
    """Decrementar congestionamento deve reduzir o peso."""
    g = Grid(5, 5, peso_base=1.0)
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.decrementar_congestionamento((0, 0), (0, 1))
    assert g.peso((0, 0), (0, 1)) == 1.5  # 1.0 + 1 * 0.5


def test_grid_resetar_congestionamento():
    """Resetar deve zerar todo congestionamento."""
    g = Grid(5, 5)
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.incrementar_congestionamento((1, 1), (1, 2))
    g.resetar_congestionamento()
    assert g.peso((0, 0), (0, 1)) == 1.0
    assert g.peso((1, 1), (1, 2)) == 1.0


def test_grid_no_valido():
    """Deve validar se nó está dentro do grid."""
    g = Grid(5, 5)
    assert g.no_valido((0, 0)) is True
    assert g.no_valido((4, 4)) is True
    assert g.no_valido((5, 5)) is False
    assert g.no_valido((-1, 0)) is False


def test_grid_todos_os_nos():
    """Deve retornar todos os nós."""
    g = Grid(3, 3)
    nos = g.todos_os_nos()
    assert len(nos) == 9
    assert (0, 0) in nos
    assert (2, 2) in nos


def test_grid_repr():
    """Repr deve mostrar info legível."""
    g = Grid(10, 10)
    g.bloquear_aresta((0, 0), (0, 1))
    r = repr(g)
    assert "10x10" in r
    assert "100" in r

def test_resultado_criacao():
    """Resultado deve ser criado com valores padrão."""
    r = Resultado(algoritmo=Algoritmo.A_ESTRELA)
    assert r.algoritmo == Algoritmo.A_ESTRELA
    assert r.encontrou is False
    assert r.nos_expandidos == 0
    assert r.caminho == []


def test_resultado_com_caminho():
    """Resultado com caminho deve refletir encontrou=True."""
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
    """Timer deve medir tempo corretamente."""
    with Timer() as t:
        # Simula trabalho
        total = sum(range(10000))
    assert t.tempo_ms > 0
    assert t.tempo_ms < 1000  # Não deve demorar mais que 1s


def test_heuristica_manhattan():
    """Manhattan deve retornar |Δi| + |Δj|."""
    assert heuristica_manhattan((0, 0), (3, 4)) == 7
    assert heuristica_manhattan((2, 2), (2, 2)) == 0
    assert heuristica_manhattan((0, 0), (0, 5)) == 5


def test_heuristica_euclidiana():
    """Euclidiana deve retornar distância em linha reta."""
    assert heuristica_euclidiana((0, 0), (3, 4)) == 5.0
    assert heuristica_euclidiana((0, 0), (0, 0)) == 0.0


def test_config_validar():
    """Config deve validar parâmetros."""
    config = ConfigSimulacao(grid_linhas=10, grid_colunas=10, num_carros=5)
    config.validar()  # Não deve dar erro

    config_ruim = ConfigSimulacao(grid_linhas=2, grid_colunas=2)
    try:
        config_ruim.validar()
        assert False, "Deveria ter dado ValueError"
    except ValueError:
        pass


def test_config_carros_demais():
    """Config deve rejeitar carros demais pro grid."""
    config = ConfigSimulacao(grid_linhas=3, grid_colunas=3, num_carros=100)
    try:
        config.validar()
        assert False, "Deveria ter dado ValueError"
    except ValueError:
        pass


def test_algoritmo_enum():
    """Enum de algoritmos deve ter os 4 valores."""
    assert len(Algoritmo) == 4
    assert Algoritmo.BFS.value == "BFS"
    assert Algoritmo.DFS.value == "DFS"
    assert Algoritmo.GREEDY.value == "Greedy"
    assert Algoritmo.A_ESTRELA.value == "A*"


# ========================================================
# RODAR TESTES
# ========================================================

if __name__ == "__main__":
    testes = [
        # Grid
        test_grid_criacao,
        test_grid_vizinhos_centro,
        test_grid_vizinhos_canto,
        test_grid_vizinhos_borda,
        test_grid_peso_base,
        test_grid_bloquear_aresta,
        test_grid_desbloquear_aresta,
        test_grid_congestionamento,
        test_grid_decrementar_congestionamento,
        test_grid_resetar_congestionamento,
        test_grid_no_valido,
        test_grid_todos_os_nos,
        test_grid_repr,
        # Modelos
        test_resultado_criacao,
        test_resultado_com_caminho,
        test_timer,
        test_heuristica_manhattan,
        test_heuristica_euclidiana,
        test_config_validar,
        test_config_carros_demais,
        test_algoritmo_enum,
    ]

    print(f"\n🧪 Rodando {len(testes)} testes...\n")
    passou = 0
    falhou = 0

    for teste in testes:
        try:
            teste()
            print(f"  PASS {teste.__name__}")
            passou += 1
        except Exception as e:
            print(f"  ERRO {teste.__name__}: {e}")
            falhou += 1

    print(f"\n{'='*40}")
    print(f"  {passou} passaram  |   {falhou} falharam")
    print(f"{'='*40}\n")
