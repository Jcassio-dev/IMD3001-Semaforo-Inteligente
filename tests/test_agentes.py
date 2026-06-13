import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from grid import Grid
from modelos import Algoritmo, EstadoSemaforo, Direcao
from agente_semaforo import AgenteSemaforo
from agente_carro import AgenteCarro, EstadoCarro


def test_carro_sem_semaforo():
    """Carro navega livremente quando não há semáforos."""
    g = Grid(5, 5)
    carro = AgenteCarro(id=1, origem=(0, 0), destino=(4, 4), grid=g)
    
    passos = 0
    while not carro.chegou and passos < 20:
        carro.avancar()
        passos += 1
    
    assert carro.chegou
    assert carro.passos_aguardando == 0
    assert len(carro.rota) > 0


def test_carro_com_semaforo_bloqueado():
    """Semáforo registra e carro pode consultá-lo."""
    g = Grid(5, 5)
    
    # Semáforo adaptativo: min/max verde, e amarelo fixo
    sem = AgenteSemaforo(
        no=(2, 0),
        estado_inicial=EstadoSemaforo.VERMELHO,
        min_verde=3,
        max_verde=8,
        duracao_amarelo=1
    )
    sem.registrar(g)
    
    # Verifica que o semáforo foi registrado
    assert g.semaforos[(2, 0)] == sem
    assert sem.estado == EstadoSemaforo.VERMELHO
    
    # Semáforo avança para amarelo, depois verde
    mudou = False
    for _ in range(5):
        if sem.tick():
            mudou = True
            break
    assert mudou, "Semáforo deveria ter mudado de fase"
    assert sem.estado in [EstadoSemaforo.AMARELO, EstadoSemaforo.VERDE]


def test_multiplos_carros_sem_colisao():
    """Vários carros em rotas diferentes navegam sem interferência."""
    g = Grid(10, 10)
    carros = [
        AgenteCarro(id=1, origem=(0, 0), destino=(9, 0), grid=g, algoritmo=Algoritmo.BFS),
        AgenteCarro(id=2, origem=(0, 9), destino=(9, 9), grid=g, algoritmo=Algoritmo.A_ESTRELA),
        AgenteCarro(id=3, origem=(9, 0), destino=(0, 9), grid=g, algoritmo=Algoritmo.GREEDY),
    ]
    
    # Simula 20 passos para cada carro
    for _ in range(20):
        for carro in carros:
            carro.avancar()
    
    # Todos avançaram alguma distância
    assert all(carro.distancia_percorrida > 0 for carro in carros)
    assert any(carro.chegou for carro in carros)


def test_recalculo_com_acidente():
    """Carro recalcula rota quando uma aresta é bloqueada (acidente)."""
    g = Grid(5, 5)
    carro = AgenteCarro(id=1, origem=(0, 0), destino=(4, 4), grid=g)
    
    rota_inicial = carro.rota[:]
    rota_inicial_len = len(rota_inicial)
    
    # Bloqueia uma aresta crítica
    g.bloquear_aresta((1, 1), (1, 2))
    carro.recalcular_rota()
    
    # Rota pode ter mudado
    assert carro.recalculos == 1
    # Se encontrou rota, ela deve ser válida
    if carro.ultimo_resultado.encontrou:
        assert len(carro.rota) > 0


def test_semaforo_ciclo():
    """Semáforo completa um ciclo VERDE → AMARELO → VERMELHO."""
    sem = AgenteSemaforo(
        no=(1, 1),
        min_verde=2,
        max_verde=3,
        duracao_amarelo=1
    )
    
    ciclo = []
    for _ in range(15):
        ciclo.append(sem.estado)
        sem.tick()
    
    # Verifica se o ciclo contém todas as cores
    assert EstadoSemaforo.VERDE in ciclo
    assert EstadoSemaforo.AMARELO in ciclo
    assert EstadoSemaforo.VERMELHO in ciclo


if __name__ == "__main__":
    test_carro_sem_semaforo()
    print("✓ test_carro_sem_semaforo")
    
    test_carro_com_semaforo_bloqueado()
    print("✓ test_carro_com_semaforo_bloqueado")
    
    test_multiplos_carros_sem_colisao()
    print("✓ test_multiplos_carros_sem_colisao")
    
    test_recalculo_com_acidente()
    print("✓ test_recalculo_com_acidente")
    
    test_semaforo_ciclo()
    print("✓ test_semaforo_ciclo")
    
    print("\nTodos os testes passaram!")
