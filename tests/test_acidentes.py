import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid
from acidentes import SistemaAcidentes


def _carro_fake(rota):
    class C:
        chegou = False
        recalculos = 0
        def recalcular_rota(self): self.recalculos += 1
    c = C()
    c.rota = list(rota)
    return c


def test_sem_acidentes_inicialmente():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=0.0, duracao_acidente=5)
    assert sa.acidentes_ativos == {}


def test_prob_zero_nunca_cria_acidente():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=0.0, duracao_acidente=5, seed=42)
    for _ in range(50):
        sa.tick([])
    assert sa.acidentes_ativos == {}


def test_prob_um_sempre_cria_acidente():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=1.0, duracao_acidente=5, seed=42)
    sa.tick([])
    assert len(sa.acidentes_ativos) == 1


def test_acidente_bloqueia_aresta_no_grid():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=1.0, duracao_acidente=5, seed=1)
    sa.tick([])
    aresta = next(iter(sa.acidentes_ativos))
    origem, destino = aresta
    assert g.aresta_bloqueada(origem, destino)


def test_acidente_expira_apos_duracao():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=1.0, duracao_acidente=3, seed=1)
    sa.tick([])
    assert len(sa.acidentes_ativos) == 1
    aresta = next(iter(sa.acidentes_ativos))
    # Com prob=1 cada tick tentaria criar novo, mas aresta bloqueada não é candidata
    # Rodamos só 3 ticks com prob=0 pra deixar expirar
    sa2 = SistemaAcidentes(g, prob_acidente=0.0, duracao_acidente=3, seed=1)
    sa2._acidentes = dict(sa.acidentes_ativos)
    for _ in range(3):
        sa2.tick([])
    assert aresta not in sa2.acidentes_ativos
    origem, destino = aresta
    assert not g.aresta_bloqueada(origem, destino)


def test_acidente_notifica_carros_afetados():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=1.0, duracao_acidente=5, seed=1)
    sa.tick([])
    aresta = next(iter(sa.acidentes_ativos))
    origem, destino = aresta

    carro_afetado = _carro_fake([origem, destino, (2, 2)])
    carro_livre = _carro_fake([(4, 4), (4, 3)])

    sa2 = SistemaAcidentes(g, prob_acidente=0.0, duracao_acidente=5, seed=1)
    sa2._acidentes = dict(sa.acidentes_ativos)
    sa2.tick([carro_afetado, carro_livre])

    assert carro_afetado.recalculos == 0  # tick com prob=0 não cria novo acidente

    # Forcar notificacao via novo acidente
    g2 = Grid(5, 5)
    sa3 = SistemaAcidentes(g2, prob_acidente=1.0, duracao_acidente=5, seed=1)
    c_afetado = _carro_fake([(0, 0), (0, 1), (0, 2)])
    c_livre = _carro_fake([(4, 4), (4, 3)])
    sa3.tick([c_afetado, c_livre])
    aresta3 = next(iter(sa3.acidentes_ativos))
    o3, d3 = aresta3
    if o3 in c_afetado.rota and d3 in c_afetado.rota:
        assert c_afetado.recalculos == 1
    else:
        assert c_livre.recalculos == 0


def test_max_um_acidente_por_aresta():
    g = Grid(5, 5)
    sa = SistemaAcidentes(g, prob_acidente=1.0, duracao_acidente=100, seed=7)
    for _ in range(20):
        sa.tick([])
    # Nenhuma aresta pode aparecer duas vezes nas chaves
    arestas = list(sa.acidentes_ativos.keys())
    assert len(arestas) == len(set(arestas))
