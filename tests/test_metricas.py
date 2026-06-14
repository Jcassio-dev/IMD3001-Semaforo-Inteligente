import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from modelos import Algoritmo, Resultado
from metricas import ColetorMetricas


def _resultado(algoritmo, nos=10, custo=5.0, tempo=1.0, encontrou=True):
    return Resultado(
        algoritmo=algoritmo,
        encontrou=encontrou,
        nos_expandidos=nos,
        custo_total=custo,
        tempo_ms=tempo,
        caminho=[(0, 0), (0, 1)] if encontrou else [],
    )


def test_comparar_algoritmos_vazio():
    m = ColetorMetricas()
    r = m.comparar_algoritmos()
    assert isinstance(r, dict)


def test_registrar_resultado():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.BFS, nos=8, custo=4.0, tempo=0.5))
    r = m.comparar_algoritmos()
    assert Algoritmo.BFS in r


def test_nos_expandidos_medio():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.BFS, nos=10))
    m.registrar(_resultado(Algoritmo.BFS, nos=20))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.BFS]["nos_expandidos_medio"] == 15.0


def test_custo_medio():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.A_ESTRELA, custo=4.0))
    m.registrar(_resultado(Algoritmo.A_ESTRELA, custo=6.0))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.A_ESTRELA]["custo_medio"] == 5.0


def test_tempo_medio():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.DFS, tempo=2.0))
    m.registrar(_resultado(Algoritmo.DFS, tempo=4.0))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.DFS]["tempo_medio_ms"] == 3.0


def test_recalculos_por_acidente():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.GREEDY), recalculos=3)
    m.registrar(_resultado(Algoritmo.GREEDY), recalculos=1)
    r = m.comparar_algoritmos()
    assert r[Algoritmo.GREEDY]["total_recalculos"] == 4


def test_algoritmos_independentes():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.BFS, nos=10))
    m.registrar(_resultado(Algoritmo.A_ESTRELA, nos=5))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.BFS]["nos_expandidos_medio"] == 10.0
    assert r[Algoritmo.A_ESTRELA]["nos_expandidos_medio"] == 5.0


def test_total_buscas():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.BFS))
    m.registrar(_resultado(Algoritmo.BFS))
    m.registrar(_resultado(Algoritmo.BFS))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.BFS]["total_buscas"] == 3


def test_registrar_sem_encontrar_nao_conta_custo():
    m = ColetorMetricas()
    m.registrar(_resultado(Algoritmo.BFS, encontrou=False, custo=0.0))
    m.registrar(_resultado(Algoritmo.BFS, custo=4.0))
    r = m.comparar_algoritmos()
    assert r[Algoritmo.BFS]["custo_medio"] == 4.0
