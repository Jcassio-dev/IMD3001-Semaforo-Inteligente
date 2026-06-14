import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid
from congestionamento import SistemaCongestionamento


def _carro_fake(posicao, proximo=None):
    class C:
        posicao_atual = posicao
        chegou = False
    c = C()
    c._proximo = proximo
    c.proximo_no = proximo
    return c


def test_atualizar_sem_carros_zera_congestionamento():
    g = Grid(3, 3)
    g.incrementar_congestionamento((0, 0), (0, 1))
    sc = SistemaCongestionamento(g)
    sc.atualizar([])
    assert g.get_congestionamento((0, 0), (0, 1)) == 0


def test_atualizar_incrementa_aresta_ocupada():
    g = Grid(3, 3)
    sc = SistemaCongestionamento(g)
    carro = _carro_fake((0, 0), proximo=(0, 1))
    sc.atualizar([carro])
    assert g.get_congestionamento((0, 0), (0, 1)) == 1


def test_atualizar_ignora_carros_chegados():
    g = Grid(3, 3)
    sc = SistemaCongestionamento(g)

    class CarroChegado:
        posicao_atual = (0, 0)
        proximo_no = (0, 1)
        chegou = True

    sc.atualizar([CarroChegado()])
    assert g.get_congestionamento((0, 0), (0, 1)) == 0


def test_atualizar_ignora_carro_sem_proximo():
    g = Grid(3, 3)
    sc = SistemaCongestionamento(g)
    carro = _carro_fake((1, 1), proximo=None)
    sc.atualizar([carro])
    assert g.get_congestionamento((1, 1), (1, 2)) == 0


def test_atualizar_varios_carros_mesma_aresta():
    g = Grid(3, 3)
    sc = SistemaCongestionamento(g)
    carros = [_carro_fake((0, 0), (0, 1)) for _ in range(3)]
    sc.atualizar(carros)
    assert g.get_congestionamento((0, 0), (0, 1)) == 3


def test_atualizar_reseta_antes_de_incrementar():
    g = Grid(3, 3)
    g.incrementar_congestionamento((0, 0), (0, 1))
    g.incrementar_congestionamento((0, 0), (0, 1))
    sc = SistemaCongestionamento(g)
    carro = _carro_fake((0, 0), (0, 1))
    sc.atualizar([carro])
    assert g.get_congestionamento((0, 0), (0, 1)) == 1


def test_peso_aumenta_com_congestionamento():
    g = Grid(3, 3, peso_base=1.0)
    sc = SistemaCongestionamento(g)
    carros = [_carro_fake((0, 0), (0, 1)) for _ in range(2)]
    sc.atualizar(carros)
    assert g.peso((0, 0), (0, 1)) == 2.0  # 1.0 + 2*0.5
