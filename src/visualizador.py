from __future__ import annotations

from dataclasses import dataclass
import pygame

try:
    from .modelos import Algoritmo, EstadoSemaforo
    from .simulacao import ConfigVisual, Simulacao
except ImportError:
    from modelos import Algoritmo, EstadoSemaforo
    from simulacao import ConfigVisual, Simulacao


PANEL_W = 460
WINDOW_W = 1540
WINDOW_H = 920
MIN_WINDOW_W = 1100
MIN_WINDOW_H = 760
GRID_MARGIN = 26

BG = (238, 236, 226)
PANEL_BG = (22, 38, 49)
PANEL_ACCENT = (239, 114, 77)
TEXT_LIGHT = (246, 246, 246)
TEXT_DIM = (194, 207, 216)
SKY = (194, 222, 240)
GRASS = (127, 173, 104)
ROAD = (58, 60, 66)
ROAD_EDGE = (34, 36, 40)
LANE_MARK = (232, 216, 128)
INTERSECTION = (80, 84, 93)
BLOCKED_COLOR = (203, 57, 57)

CAR_COLORS = [
    (232, 55, 42),
    (44, 124, 219),
    (245, 162, 33),
    (65, 185, 108),
    (162, 88, 219),
    (0, 163, 136),
]


@dataclass
class InputBox:
    key: str
    label: str
    x: int
    y: int
    w: int
    value: str
    min_val: int
    max_val: int
    active: bool = False

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, 34)

    def handle_event(self, event: pygame.event.Event) -> bool:
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect().collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
                changed = True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
            elif event.unicode.isdigit() and len(self.value) < 3:
                self.value += event.unicode
                changed = True
        return changed

    def int_value(self) -> int:
        if not self.value:
            return self.min_val
        v = int(self.value)
        return max(self.min_val, min(self.max_val, v))

    def draw(self, surf: pygame.Surface, label_font: pygame.font.Font, value_font: pygame.font.Font) -> None:
        surf.blit(label_font.render(self.label, True, TEXT_LIGHT), (self.x, self.y - 21))
        rect = self.rect()
        fill = (18, 31, 40) if not self.active else (30, 50, 64)
        pygame.draw.rect(surf, fill, rect, border_radius=7)
        pygame.draw.rect(surf, PANEL_ACCENT if self.active else (92, 123, 141), rect, 2, border_radius=7)
        txt = self.value if self.value else "0"
        surf.blit(value_font.render(txt, True, TEXT_LIGHT), (self.x + 10, self.y + 8))
        hint = f"[{self.min_val}-{self.max_val}]"
        surf.blit(value_font.render(hint, True, TEXT_DIM), (self.x + self.w - 84, self.y + 8))


@dataclass
class SelectBox:
    label: str
    x: int
    y: int
    w: int
    options: list[Algoritmo]
    selected_idx: int = 0
    open: bool = False

    def main_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, 36)

    def option_rect(self, idx: int) -> pygame.Rect:
        return pygame.Rect(self.x, self.y - ((idx + 1) * 32), self.w, 32)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        pos = event.pos
        if self.main_rect().collidepoint(pos):
            self.open = not self.open
            return False

        if self.open:
            for i in range(len(self.options)):
                if self.option_rect(i).collidepoint(pos):
                    self.selected_idx = i
                    self.open = False
                    return True
            self.open = False
        return False

    def current(self) -> Algoritmo:
        return self.options[self.selected_idx]

    def draw(self, surf: pygame.Surface, label_font: pygame.font.Font, value_font: pygame.font.Font) -> None:
        surf.blit(label_font.render(self.label, True, TEXT_LIGHT), (self.x, self.y - 20))
        rect = self.main_rect()
        pygame.draw.rect(surf, (17, 30, 39), rect, border_radius=7)
        pygame.draw.rect(surf, (91, 123, 140), rect, 2, border_radius=7)
        txt = self.current().value
        surf.blit(value_font.render(txt, True, TEXT_LIGHT), (self.x + 10, self.y + 9))
        surf.blit(value_font.render("v", True, TEXT_DIM), (self.x + self.w - 18, self.y + 9))

        if self.open:
            for i, opt in enumerate(self.options):
                orect = self.option_rect(i)
                bg = (30, 50, 64) if i == self.selected_idx else (17, 30, 39)
                pygame.draw.rect(surf, bg, orect, border_radius=5)
                pygame.draw.rect(surf, (91, 123, 140), orect, 1, border_radius=5)
                surf.blit(value_font.render(opt.value, True, TEXT_LIGHT), (orect.x + 10, orect.y + 7))


@dataclass
class Button:
    text: str
    x: int
    y: int
    w: int
    h: int

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def hit(self, pos: tuple[int, int]) -> bool:
        return self.rect().collidepoint(pos)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        rect = self.rect()
        pygame.draw.rect(surf, color, rect, border_radius=8)
        pygame.draw.rect(surf, (10, 16, 20), rect, 2, border_radius=8)
        txt = font.render(self.text, True, TEXT_LIGHT)
        surf.blit(txt, (self.x + (self.w - txt.get_width()) // 2, self.y + (self.h - txt.get_height()) // 2))


class Visualizador:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Semaforo Inteligente")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("segoeui", 30, bold=True)
        self.small = pygame.font.SysFont("consolas", 21)
        self.tiny = pygame.font.SysFont("consolas", 16)

        self.algoritmos = [Algoritmo.BFS, Algoritmo.DFS, Algoritmo.GREEDY, Algoritmo.A_ESTRELA]

        x = WINDOW_W - PANEL_W + 22
        w = PANEL_W - 44
        self.inputs = {
            "linhas": InputBox("linhas", "Linhas do grid", x, 110, w, "10", 5, 35),
            "colunas": InputBox("colunas", "Colunas do grid", x, 172, w, "10", 5, 35),
            "carros": InputBox("carros", "Quantidade de carros", x, 234, w, "8", 1, 90),
            "semaforos": InputBox("semaforos", "Quantidade de semaforos", x, 296, w, "6", 0, 120),
            "incidentes": InputBox("incidentes", "Incidentes ativos", x, 358, w, "3", 0, 40),
            "duracao": InputBox("duracao", "Duracao incidente (ticks)", x, 420, w, "20", 3, 120),
            "velocidade": InputBox("velocidade", "Velocidade (ticks/s)", x, 482, w, "8", 1, 30),
        }

        self.alg_select = SelectBox("Algoritmo dos carros", x, 558, w, self.algoritmos, selected_idx=3)

        self.btn_apply = Button("Aplicar configuracao", x, 710, w, 44)
        self.btn_play = Button("Pausar", x, 762, w, 44)
        self.btn_perf = Button("Desempenho", x, 814, w, 44)
        self.btn_close_modal = Button("Fechar", 0, 0, 120, 40)

        self.rodando = True
        self.paused = False
        self._tick_acc = 0.0
        self.modal_desempenho_aberto = False

        self._reflow_layout()
        self.sim = self._nova_simulacao()

    def _window_size(self) -> tuple[int, int]:
        return self.screen.get_size()

    def _panel_width(self) -> int:
        width, _ = self._window_size()
        return max(400, min(520, width // 3))

    def _reflow_layout(self) -> None:
        width, height = self._window_size()
        panel_w = self._panel_width()
        panel_x = width - panel_w
        x = panel_x + 22
        w = panel_w - 44

        y_positions = {
            "linhas": 110,
            "colunas": 172,
            "carros": 234,
            "semaforos": 296,
            "incidentes": 358,
            "duracao": 420,
            "velocidade": 482,
        }

        for key, box in self.inputs.items():
            box.x = x
            box.y = y_positions[key]
            box.w = w

        self.alg_select.x = x
        self.alg_select.y = 558
        self.alg_select.w = w

        buttons_y = min(height - 170, 710)
        self.btn_apply.x = x
        self.btn_apply.y = buttons_y
        self.btn_apply.w = w

        self.btn_play.x = x
        self.btn_play.y = buttons_y + 52
        self.btn_play.w = w

        self.btn_perf.x = x
        self.btn_perf.y = buttons_y + 104
        self.btn_perf.w = w

    def _nova_simulacao(self) -> Simulacao:
        linhas = self.inputs["linhas"].int_value()
        colunas = self.inputs["colunas"].int_value()
        max_nos = linhas * colunas

        semaforos = min(self.inputs["semaforos"].int_value(), max_nos)
        carros = min(self.inputs["carros"].int_value(), max(1, max_nos // 2))

        self.inputs["semaforos"].value = str(semaforos)
        self.inputs["carros"].value = str(carros)

        cfg = ConfigVisual(
            linhas=linhas,
            colunas=colunas,
            num_carros=carros,
            num_semaforos=semaforos,
            num_incidentes=self.inputs["incidentes"].int_value(),
            duracao_incidente=self.inputs["duracao"].int_value(),
            algoritmo_carros=self.alg_select.current(),
        )
        return Simulacao(cfg)

    def run(self) -> None:
        while self.rodando:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
                continue

            if event.type == pygame.VIDEORESIZE:
                new_w = max(MIN_WINDOW_W, event.w)
                new_h = max(MIN_WINDOW_H, event.h)
                self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                self._reflow_layout()
                continue

            if self.modal_desempenho_aberto:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if self.btn_close_modal.hit(pos):
                        self.modal_desempenho_aberto = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.modal_desempenho_aberto = False
                continue

            for input_box in self.inputs.values():
                input_box.handle_event(event)

            self.alg_select.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.btn_apply.hit(pos):
                    self.sim = self._nova_simulacao()
                elif self.btn_play.hit(pos):
                    self.paused = not self.paused
                    self.btn_play.text = "Retomar" if self.paused else "Pausar"
                elif self.btn_perf.hit(pos):
                    self.modal_desempenho_aberto = True

    def _update(self, dt: float) -> None:
        if self.paused:
            return

        ticks_por_seg = self.inputs["velocidade"].int_value()
        self._tick_acc += dt * ticks_por_seg
        while self._tick_acc >= 1.0:
            self.sim.step()
            self._tick_acc -= 1.0

    def _draw(self) -> None:
        self._draw_background()
        self._draw_grid_area()
        self._draw_panel()
        if self.modal_desempenho_aberto:
            self._draw_modal_desempenho()

    def _draw_background(self) -> None:
        self.screen.fill(BG)
        width, height = self._window_size()
        area_w = width - self._panel_width()
        pygame.draw.rect(self.screen, SKY, (0, 0, area_w, height // 3))
        pygame.draw.rect(self.screen, GRASS, (0, height // 3, area_w, height - height // 3))

        # blocos urbanos para dar ambientacao
        for bx in range(20, area_w - 130, 150):
            pygame.draw.rect(self.screen, (168, 156, 132), (bx, 44, 82, 42), border_radius=6)
            pygame.draw.rect(self.screen, (182, 171, 146), (bx + 10, 54, 24, 10), border_radius=3)
            pygame.draw.rect(self.screen, (182, 171, 146), (bx + 44, 54, 24, 10), border_radius=3)

    @staticmethod
    def _adjacentes(no: tuple[int, int], linhas: int, colunas: int) -> list[tuple[int, int]]:
        i, j = no
        saida: list[tuple[int, int]] = []
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < linhas and 0 <= nj < colunas:
                saida.append((ni, nj))
        return saida

    def _draw_road_segment(self, p0: tuple[int, int], p1: tuple[int, int], blocked: bool = False) -> None:
        pygame.draw.line(self.screen, ROAD_EDGE, p0, p1, 30)
        pygame.draw.line(self.screen, ROAD, p0, p1, 24)

        if blocked:
            pygame.draw.line(self.screen, BLOCKED_COLOR, p0, p1, 9)
            return

        x0, y0 = p0
        x1, y1 = p1
        steps = 10
        for k in range(steps):
            if k % 2 == 0:
                t0 = k / steps
                t1 = (k + 1) / steps
                sx = int(x0 + (x1 - x0) * t0)
                sy = int(y0 + (y1 - y0) * t0)
                ex = int(x0 + (x1 - x0) * t1)
                ey = int(y0 + (y1 - y0) * t1)
                pygame.draw.line(self.screen, LANE_MARK, (sx, sy), (ex, ey), 2)

    def _draw_traffic_light_sprite(self, x: int, y: int, estado: EstadoSemaforo) -> None:
        post = pygame.Rect(x - 2, y + 13, 4, 14)
        pygame.draw.rect(self.screen, (25, 25, 27), post)

        body = pygame.Rect(x - 10, y - 17, 20, 34)
        pygame.draw.rect(self.screen, (16, 16, 19), body, border_radius=5)
        pygame.draw.rect(self.screen, (8, 8, 10), body, 2, border_radius=5)

        colors = {
            "r": (80, 24, 24),
            "y": (90, 84, 22),
            "g": (24, 80, 42),
        }
        if estado == EstadoSemaforo.VERMELHO:
            colors["r"] = (230, 76, 64)
        elif estado == EstadoSemaforo.AMARELO:
            colors["y"] = (239, 196, 15)
        else:
            colors["g"] = (54, 191, 108)

        pygame.draw.circle(self.screen, colors["r"], (x, y - 10), 4)
        pygame.draw.circle(self.screen, colors["y"], (x, y), 4)
        pygame.draw.circle(self.screen, colors["g"], (x, y + 10), 4)

    def _draw_car_sprite(self, x: int, y: int, color: tuple[int, int, int], heading: tuple[int, int], label: str) -> None:
        # Sprite base horizontal (estilo cartoon com rodas e teto curvo)
        surf = pygame.Surface((46, 26), pygame.SRCALPHA)

        body_rect = pygame.Rect(2, 8, 42, 14)
        roof_rect = pygame.Rect(10, 2, 25, 10)

        pygame.draw.rect(surf, color, body_rect, border_radius=6)
        pygame.draw.ellipse(surf, color, roof_rect)

        # janelas
        pygame.draw.rect(surf, (66, 126, 145), (14, 4, 9, 7), border_radius=2)
        pygame.draw.rect(surf, (66, 126, 145), (24, 4, 9, 7), border_radius=2)

        # rodas
        pygame.draw.circle(surf, (22, 22, 26), (12, 22), 5)
        pygame.draw.circle(surf, (22, 22, 26), (34, 22), 5)
        pygame.draw.circle(surf, (183, 183, 183), (12, 22), 2)
        pygame.draw.circle(surf, (183, 183, 183), (34, 22), 2)

        # farol frontal do sprite base (direita)
        pygame.draw.circle(surf, (255, 227, 143), (42, 12), 2)

        # numero na porta
        badge = pygame.Rect(18, 10, 10, 8)
        pygame.draw.rect(surf, (246, 246, 246), badge, border_radius=2)
        id_txt = self.tiny.render(label, True, (8, 8, 10))
        surf.blit(id_txt, (badge.x + (badge.w - id_txt.get_width()) // 2, badge.y + (badge.h - id_txt.get_height()) // 2 - 1))

        dx, dy = heading
        angle = 0
        if dx == 1:
            angle = -90
        elif dx == -1:
            angle = 90
        elif dy == -1:
            angle = 180

        rotated = pygame.transform.rotate(surf, angle)
        rect = rotated.get_rect(center=(x, y))
        self.screen.blit(rotated, rect)

    def _draw_grid_area(self) -> None:
        width, height = self._window_size()
        area_w = width - self._panel_width()
        area_h = height

        linhas = self.sim.grid.linhas
        colunas = self.sim.grid.colunas

        cell_w = (area_w - 2 * GRID_MARGIN) / max(1, colunas - 1)
        cell_h = (area_h - 2 * GRID_MARGIN) / max(1, linhas - 1)

        def to_px(no: tuple[int, int]) -> tuple[int, int]:
            i, j = no
            x = int(GRID_MARGIN + j * cell_w)
            y = int(GRID_MARGIN + i * cell_h)
            return x, y

        for i in range(linhas):
            for j in range(colunas):
                origem = (i, j)
                ox, oy = to_px(origem)
                for destino in self._adjacentes(origem, linhas, colunas):
                    if origem < destino:
                        dx, dy = to_px(destino)
                        bloqueada = self.sim.grid.aresta_bloqueada(origem, destino)
                        self._draw_road_segment((ox, oy), (dx, dy), blocked=bloqueada)

        for (origem, destino), ticks_rest in self.sim.incidentes_ativos.items():
            ox, oy = to_px(origem)
            dx, dy = to_px(destino)
            cx = (ox + dx) // 2
            cy = (oy + dy) // 2
            txt = self.tiny.render(str(ticks_rest), True, (255, 255, 255))
            pygame.draw.circle(self.screen, (130, 18, 18), (cx, cy), 10)
            self.screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

        for i in range(linhas):
            for j in range(colunas):
                x, y = to_px((i, j))
                pygame.draw.circle(self.screen, INTERSECTION, (x, y), 13)

        for semaforo in self.sim.semaforos:
            x, y = to_px(semaforo.no)
            self._draw_traffic_light_sprite(x + 15, y - 16, semaforo.estado)

        for idx, carro in enumerate(self.sim.carros):
            x, y = to_px(carro.posicao_atual)
            cor = CAR_COLORS[idx % len(CAR_COLORS)]
            proximo = carro.proximo_no
            if proximo is None:
                heading = (0, 1)
            else:
                heading = (
                    proximo[0] - carro.posicao_atual[0],
                    proximo[1] - carro.posicao_atual[1],
                )
            self._draw_car_sprite(x, y, cor, heading, str(carro.id))

    def _draw_panel(self) -> None:
        width, height = self._window_size()
        panel_w = self._panel_width()
        panel = pygame.Rect(width - panel_w, 0, panel_w, height)
        pygame.draw.rect(self.screen, PANEL_BG, panel)

        title = self.font.render("Painel de Controle", True, TEXT_LIGHT)
        self.screen.blit(title, (panel.x + 22, 18))

        subt = self.tiny.render("Digite valores e escolha algoritmo", True, TEXT_DIM)
        self.screen.blit(subt, (panel.x + 24, 58))

        for box in self.inputs.values():
            box.draw(self.screen, self.tiny, self.tiny)

        self.alg_select.draw(self.screen, self.tiny, self.tiny)

        self.btn_apply.draw(self.screen, self.small, (44, 132, 109))
        self.btn_play.draw(self.screen, self.small, (55, 98, 121))
        self.btn_perf.draw(self.screen, self.small, (96, 90, 165))

        y0 = min(height - 84, self.btn_perf.y + 70)
        stats = [
            f"Ticks: {self.sim.ticks}",
            f"Chegaram: {self.sim.carros_chegaram}/{len(self.sim.carros)}",
            f"Aguardando: {self.sim.carros_aguardando}",
            f"Sem rota: {self.sim.carros_sem_rota}",
            f"Movimentos/tick: {self.sim.movimentos_no_tick}",
        ]
        for idx, line in enumerate(stats):
            txt = self.tiny.render(line, True, TEXT_LIGHT)
            self.screen.blit(txt, (panel.x + 24, y0 + idx * 16))

    def _draw_modal_desempenho(self) -> None:
        width, height = self._window_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((5, 8, 12, 165))
        self.screen.blit(overlay, (0, 0))

        modal_w = min(860, width - 60)
        modal_h = min(640, height - 60)
        modal_x = (width - modal_w) // 2
        modal_y = (height - modal_h) // 2
        modal = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        pygame.draw.rect(self.screen, (18, 30, 39), modal, border_radius=14)
        pygame.draw.rect(self.screen, (88, 117, 133), modal, 2, border_radius=14)

        titulo = self.font.render("Objetivo e Desempenho dos Carros", True, TEXT_LIGHT)
        self.screen.blit(titulo, (modal.x + 22, modal.y + 18))
        subt = self.tiny.render("Origem, destino, posicao atual, mudancas de direcao/trajeto e tempo ate chegada", True, TEXT_DIM)
        self.screen.blit(subt, (modal.x + 24, modal.y + 58))

        self.btn_close_modal.x = modal.right - self.btn_close_modal.w - 22
        self.btn_close_modal.y = modal.y + 18
        self.btn_close_modal.draw(self.screen, self.tiny, (130, 65, 62))

        header_y = modal.y + 108
        headers = [
            ("Carro", modal.x + 24),
            ("Percurso", modal.x + 92),
            ("Posicao", modal.x + 314),
            ("Estado", modal.x + 420),
            ("Dir.", modal.x + 518),
            ("Traj.", modal.x + 582),
            ("Recalc.", modal.x + 650),
            ("Tempo", modal.x + 748),
        ]
        for texto, pos_x in headers:
            self.screen.blit(self.tiny.render(texto, True, TEXT_LIGHT), (pos_x, header_y))

        pygame.draw.line(self.screen, (88, 117, 133), (modal.x + 22, header_y + 22), (modal.right - 22, header_y + 22), 1)

        row_y = header_y + 38
        for idx, dado in enumerate(self.sim.dados_carros(limite=12)):
            if idx % 2 == 0:
                faixa = pygame.Rect(modal.x + 18, row_y - 6, modal.w - 36, 34)
                pygame.draw.rect(self.screen, (23, 38, 49), faixa, border_radius=6)

            percurso = f"{dado['origem']} -> {dado['destino']}"
            tempo = "--" if dado["tempo_ate_chegada"] is None else str(dado["tempo_ate_chegada"])
            cols = [
                (f"C{dado['id']}", modal.x + 24),
                (percurso, modal.x + 92),
                (str(dado['posicao']), modal.x + 314),
                (str(dado['estado']), modal.x + 420),
                (str(dado['mudancas_direcao']), modal.x + 528),
                (str(dado['mudancas_trajetoria']), modal.x + 596),
                (str(dado['recalculos']), modal.x + 676),
                (tempo, modal.x + 752),
            ]
            for texto, pos_x in cols:
                self.screen.blit(self.tiny.render(texto, True, TEXT_DIM), (pos_x, row_y))
            row_y += 40
