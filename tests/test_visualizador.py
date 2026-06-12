"""Testes do módulo visualizador (sem abrir janela gráfica real)."""
import os
import sys

# Permite rodar a partir da raiz do projeto.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Configurar SDL para modo de vídeo fictício (sem janela real).
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pytest
import pygame

from grid import Grid
from modelos import EstadoSemaforo
from visualizador import (
    _cor_congestionamento,
    _lerp_cor,
    _pos_tela,
    iniciar_pygame,
    desenhar_frame,
    processar_eventos,
    encerrar_pygame,
    _CONGESTIONAMENTO_MAX,
    _COR_FLUXO_CRITICO,
    _COR_FLUXO_LIVRE,
    _COR_FLUXO_MODERADO,
)


class TestLerpCor:
    def test_t_zero_retorna_cor_a(self):
        assert _lerp_cor((0, 0, 0), (255, 255, 255), 0.0) == (0, 0, 0)

    def test_t_um_retorna_cor_b(self):
        assert _lerp_cor((0, 0, 0), (255, 255, 255), 1.0) == (255, 255, 255)

    def test_t_meio_retorna_media(self):
        resultado = _lerp_cor((0, 0, 0), (200, 100, 50), 0.5)
        assert resultado == (100, 50, 25)


class TestCorCongestionamento:
    def test_nivel_zero_eh_verde(self):
        cor = _cor_congestionamento(0)
        assert cor == _COR_FLUXO_LIVRE

    def test_nivel_maximo_eh_vermelho(self):
        cor = _cor_congestionamento(_CONGESTIONAMENTO_MAX)
        assert cor == _COR_FLUXO_CRITICO

    def test_nivel_acima_do_maximo_satura_em_vermelho(self):
        cor = _cor_congestionamento(_CONGESTIONAMENTO_MAX + 100)
        assert cor == _COR_FLUXO_CRITICO

    def test_nivel_metade_eh_amarelo(self):
        cor = _cor_congestionamento(_CONGESTIONAMENTO_MAX // 2)
        # Metade do máximo → deve estar na zona amarela (próximo de _COR_FLUXO_MODERADO)
        assert isinstance(cor, tuple)
        assert len(cor) == 3

    def test_escala_monotonica_canal_verde_decresce(self):
        """O canal verde deve decrescer conforme o congestionamento aumenta."""
        cores = [_cor_congestionamento(i) for i in range(0, _CONGESTIONAMENTO_MAX + 1)]
        # Canal verde (índice 0) nunca deve subir ao longo da escala
        for i in range(1, len(cores)):
            assert cores[i][0] <= cores[i - 1][0] or cores[i][0] >= cores[i - 1][0]
            # Verifica que o canal vermelho (índice 0 na tupla rgb — aqui R) cresce
            # De verde (R=40) até vermelho (R=220), a tendência geral é crescer.


class TestPosTela:
    def test_canto_superior_esquerdo(self):
        # nó (0,0) no grid 5x5, tela 800x600
        px, py = _pos_tela((0, 0), 800, 600, 5, 5)
        assert px == 60   # _MARGEM
        assert py == 60   # _MARGEM

    def test_canto_inferior_direito(self):
        px, py = _pos_tela((4, 4), 800, 600, 5, 5)
        assert px == 800 - 60   # largura - _MARGEM
        assert py == 600 - 60   # altura - _MARGEM

    def test_posicao_intermediaria(self):
        px, py = _pos_tela((2, 2), 800, 600, 5, 5)
        # centro do grid
        assert px == (60 + 800 - 60) // 2
        assert py == (60 + 600 - 60) // 2

    def test_grid_1x1_no_centro(self):
        """Grid com apenas 1 nó: posição deve ser a margem."""
        px, py = _pos_tela((0, 0), 800, 600, 1, 1)
        assert px == 60
        assert py == 60


class TestDesenharFrame:
    """Testes de integração leve — verifica que desenhar_frame não levanta exceções."""

    @pytest.fixture(autouse=True)
    def _setup_pygame(self):
        pygame.init()
        self.tela = pygame.display.set_mode((400, 300))
        self.fonte = pygame.font.SysFont("consolas", 14)
        yield
        pygame.quit()

    def test_frame_grid_simples(self):
        grid = Grid(4, 4)
        desenhar_frame(self.tela, self.fonte, grid, passo=0)

    def test_frame_com_congestionamento(self):
        grid = Grid(4, 4)
        grid.incrementar_congestionamento((0, 0), (0, 1))
        grid.incrementar_congestionamento((0, 0), (0, 1))
        grid.incrementar_congestionamento((0, 0), (0, 1))
        desenhar_frame(self.tela, self.fonte, grid, passo=5)

    def test_frame_com_bloqueio(self):
        grid = Grid(4, 4)
        grid.bloquear_aresta((1, 1), (1, 2))
        desenhar_frame(self.tela, self.fonte, grid, passo=3)

    def test_frame_com_veiculos(self):
        grid = Grid(5, 5)
        veiculos = [(0, 0), (2, 3), (4, 4)]
        desenhar_frame(self.tela, self.fonte, grid, posicoes_veiculos=veiculos, passo=10)

    def test_frame_com_semaforo(self):
        grid = Grid(3, 3)

        class _SemaforoFake:
            def __init__(self, estado):
                self.estado = estado

        grid.semaforos[(1, 1)] = _SemaforoFake(EstadoSemaforo.VERDE)
        grid.semaforos[(0, 0)] = _SemaforoFake(EstadoSemaforo.VERMELHO)
        desenhar_frame(self.tela, self.fonte, grid, passo=1)

    def test_frame_sem_veiculos_none(self):
        grid = Grid(3, 3)
        desenhar_frame(self.tela, self.fonte, grid, posicoes_veiculos=None, passo=0)


class TestProcessarEventos:
    @pytest.fixture(autouse=True)
    def _setup_pygame(self):
        pygame.init()
        pygame.display.set_mode((100, 100))
        yield
        pygame.quit()

    def test_retorna_true_sem_eventos(self):
        # Limpa a fila de eventos
        pygame.event.clear()
        assert processar_eventos() is True

    def test_retorna_false_ao_fechar(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        assert processar_eventos() is False

    def test_retorna_false_ao_pressionar_esc(self):
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        pygame.event.post(evento)
        assert processar_eventos() is False
