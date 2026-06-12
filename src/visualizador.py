from __future__ import annotations

from typing import Optional

import pygame

from grid import Grid
from modelos import EstadoSemaforo

COR_FUNDO = (30, 30, 40)
COR_NO = (180, 190, 210)
COR_NO_BORDA = (100, 110, 130)
COR_BLOQUEIO = (120, 40, 40)
COR_VEICULO = (60, 160, 255)
COR_TEXTO = (220, 220, 220)

COR_SEMAFORO = {
    EstadoSemaforo.VERDE: (40, 200, 80),
    EstadoSemaforo.AMARELO: (230, 200, 50),
    EstadoSemaforo.VERMELHO: (220, 50, 50),
}

# Congestionamento — escala contínua (verde → amarelo → vermelho)
_COR_FLUXO_LIVRE = (40, 200, 80)       # verde
_COR_FLUXO_MODERADO = (230, 200, 50)   # amarelo
_COR_FLUXO_CRITICO = (220, 50, 50)     # vermelho

_MARGEM = 60
_RAIO_NO = 8
_RAIO_SEMAFORO = 10
_RAIO_VEICULO = 6
_LARGURA_ARESTA = 3
_LARGURA_ARESTA_BLOQUEADA = 2
_CONGESTIONAMENTO_MAX = 6  # saturação visual da escala de cor


def _lerp_cor(cor_a: tuple[int, ...], cor_b: tuple[int, ...], t: float) -> tuple[int, ...]:
    """Interpolação linear entre duas cores RGB, t ∈ [0, 1]."""
    return tuple(int(a + (b - a) * t) for a, b in zip(cor_a, cor_b))


def _cor_congestionamento(nivel: int) -> tuple[int, ...]:
    """Mapeia nível de congestionamento (0..+∞) para verde→amarelo→vermelho."""
    t = min(nivel / _CONGESTIONAMENTO_MAX, 1.0)
    if t <= 0.5:
        return _lerp_cor(_COR_FLUXO_LIVRE, _COR_FLUXO_MODERADO, t * 2)
    return _lerp_cor(_COR_FLUXO_MODERADO, _COR_FLUXO_CRITICO, (t - 0.5) * 2)


def _pos_tela(
    no: tuple[int, int],
    largura: int,
    altura: int,
    linhas: int,
    colunas: int,
) -> tuple[int, int]:
    """Converte coordenada do grid (linha, coluna) para pixel na janela."""
    area_w = largura - 2 * _MARGEM
    area_h = altura - 2 * _MARGEM
    espaco_x = area_w / max(colunas - 1, 1)
    espaco_y = area_h / max(linhas - 1, 1)
    px = int(_MARGEM + no[1] * espaco_x)
    py = int(_MARGEM + no[0] * espaco_y)
    return px, py


def _desenhar_arestas(
    tela: pygame.Surface,
    grid: Grid,
    largura: int,
    altura: int,
) -> None:
    """Desenha todas as arestas (ruas) com cor baseada no congestionamento."""
    desenhadas: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    for aresta, cong in grid._congestionamento.items():
        origem, destino = aresta
        # Evita desenhar a mesma aresta duas vezes (ida e volta)
        par = (min(origem, destino), max(origem, destino))
        if par in desenhadas:
            continue
        desenhadas.add(par)

        p1 = _pos_tela(origem, largura, altura, grid.linhas, grid.colunas)
        p2 = _pos_tela(destino, largura, altura, grid.linhas, grid.colunas)

        if grid.aresta_bloqueada(origem, destino):
            # Aresta bloqueada — tracejado vermelho escuro
            _desenhar_linha_tracejada(tela, COR_BLOQUEIO, p1, p2, _LARGURA_ARESTA_BLOQUEADA)
        else:
            cor = _cor_congestionamento(cong)
            pygame.draw.line(tela, cor, p1, p2, _LARGURA_ARESTA)


def _desenhar_linha_tracejada(
    tela: pygame.Surface,
    cor: tuple[int, ...],
    p1: tuple[int, int],
    p2: tuple[int, int],
    largura: int,
    comprimento_traco: int = 8,
    espaco: int = 6,
) -> None:
    """Desenha uma linha tracejada entre p1 e p2."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = max((dx**2 + dy**2) ** 0.5, 1)
    ux, uy = dx / dist, dy / dist
    passo = comprimento_traco + espaco
    pos = 0.0
    while pos < dist:
        ini_x = p1[0] + ux * pos
        ini_y = p1[1] + uy * pos
        fim = min(pos + comprimento_traco, dist)
        fim_x = p1[0] + ux * fim
        fim_y = p1[1] + uy * fim
        pygame.draw.line(tela, cor, (int(ini_x), int(ini_y)), (int(fim_x), int(fim_y)), largura)
        pos += passo


def _desenhar_nos(
    tela: pygame.Surface,
    grid: Grid,
    largura: int,
    altura: int,
) -> None:
    """Desenha os nós (cruzamentos/interseções) do grid."""
    for no in grid.todos_os_nos():
        pos = _pos_tela(no, largura, altura, grid.linhas, grid.colunas)

        # Se há semáforo no nó, usa a cor do estado
        semaforo = grid.semaforos.get(no)
        if semaforo is not None and hasattr(semaforo, "estado"):
            cor = COR_SEMAFORO.get(semaforo.estado, COR_NO)
            pygame.draw.circle(tela, cor, pos, _RAIO_SEMAFORO)
            pygame.draw.circle(tela, COR_NO_BORDA, pos, _RAIO_SEMAFORO, 2)
        else:
            pygame.draw.circle(tela, COR_NO, pos, _RAIO_NO)
            pygame.draw.circle(tela, COR_NO_BORDA, pos, _RAIO_NO, 2)


def _desenhar_veiculos(
    tela: pygame.Surface,
    grid: Grid,
    posicoes_veiculos: list[tuple[int, int]],
    largura: int,
    altura: int,
) -> None:
    """Desenha os veículos nas suas posições atuais."""
    for pos_grid in posicoes_veiculos:
        pos = _pos_tela(pos_grid, largura, altura, grid.linhas, grid.colunas)
        pygame.draw.circle(tela, COR_VEICULO, pos, _RAIO_VEICULO)


def _desenhar_hud(
    tela: pygame.Surface,
    fonte: pygame.font.Font,
    passo: int,
    num_veiculos: int,
) -> None:
    """Desenha informações textuais (HUD) no topo da tela."""
    texto = f"Passo: {passo}  |  Veículos: {num_veiculos}"
    superficie = fonte.render(texto, True, COR_TEXTO)
    tela.blit(superficie, (10, 10))


def _desenhar_legenda(
    tela: pygame.Surface,
    fonte: pygame.font.Font,
    largura: int,
    altura: int,
) -> None:
    """Desenha legenda de cores no canto inferior direito."""
    itens = [
        (_COR_FLUXO_LIVRE, "Livre"),
        (_COR_FLUXO_MODERADO, "Moderado"),
        (_COR_FLUXO_CRITICO, "Crítico"),
        (COR_BLOQUEIO, "Bloqueado"),
    ]
    x_base = largura - 140
    y_base = altura - 20 - len(itens) * 22

    for i, (cor, rotulo) in enumerate(itens):
        y = y_base + i * 22
        pygame.draw.rect(tela, cor, (x_base, y, 14, 14))
        superficie = fonte.render(rotulo, True, COR_TEXTO)
        tela.blit(superficie, (x_base + 20, y - 1))


def iniciar_pygame(
    largura: int = 800,
    altura: int = 600,
    titulo: str = "Simulador de Trânsito Inteligente",
) -> tuple[pygame.Surface, pygame.time.Clock, pygame.font.Font]:
    """Inicializa o Pygame e retorna (tela, clock, fonte)."""
    pygame.init()
    tela = pygame.display.set_mode((largura, altura))
    pygame.display.set_caption(titulo)
    clock = pygame.time.Clock()
    fonte = pygame.font.SysFont("consolas", 16)
    return tela, clock, fonte


def desenhar_frame(
    tela: pygame.Surface,
    fonte: pygame.font.Font,
    grid: Grid,
    posicoes_veiculos: Optional[list[tuple[int, int]]] = None,
    passo: int = 0,
) -> None:
    """Desenha um quadro completo da simulação na tela.

    Chamado a cada step do modelo Mesa para atualizar a visualização.
    """
    largura, altura = tela.get_size()
    if posicoes_veiculos is None:
        posicoes_veiculos = []

    tela.fill(COR_FUNDO)
    _desenhar_arestas(tela, grid, largura, altura)
    _desenhar_nos(tela, grid, largura, altura)
    _desenhar_veiculos(tela, grid, posicoes_veiculos, largura, altura)
    _desenhar_hud(tela, fonte, passo, len(posicoes_veiculos))
    _desenhar_legenda(tela, fonte, largura, altura)
    pygame.display.flip()


def processar_eventos() -> bool:
    """Processa eventos do Pygame. Retorna False se o usuário fechou a janela."""
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            return False
    return True


def encerrar_pygame() -> None:
    """Fecha a janela e libera recursos do Pygame."""
    pygame.quit()
