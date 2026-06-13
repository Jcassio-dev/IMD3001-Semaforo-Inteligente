from __future__ import annotations

from dataclasses import dataclass
import random

try:
    from .agente_carro import AgenteCarro
    from .agente_semaforo import AgenteSemaforo
    from .grid import Grid
    from .modelos import Algoritmo, Direcao
except ImportError:
    from agente_carro import AgenteCarro
    from agente_semaforo import AgenteSemaforo
    from grid import Grid
    from modelos import Algoritmo, Direcao


No = tuple[int, int]
Aresta = tuple[No, No]


@dataclass
class ConfigVisual:
    linhas: int = 10
    colunas: int = 10
    num_carros: int = 8
    num_semaforos: int = 6
    num_incidentes: int = 3
    duracao_incidente: int = 20
    algoritmo_carros: Algoritmo = Algoritmo.A_ESTRELA
    seed: int | None = None


@dataclass
class TelemetriaCarro:
    origem: No
    destino: No
    inicio_tick: int = 0
    chegada_tick: int | None = None
    mudancas_direcao: int = 0
    mudancas_trajetoria: int = 0
    ultima_direcao: tuple[int, int] | None = None
    ultima_rota: tuple[No, ...] = ()


class Simulacao:
    def __init__(self, config: ConfigVisual):
        self.config = config
        self._rng = random.Random(config.seed)

        self.grid = Grid(config.linhas, config.colunas)
        self.carros: list[AgenteCarro] = []
        self.semaforos: list[AgenteSemaforo] = []

        # aresta -> ticks restantes bloqueada
        self.incidentes_ativos: dict[Aresta, int] = {}

        self.ticks = 0
        self.movimentos_no_tick = 0

        self._telemetria: dict[int, TelemetriaCarro] = {}

        self._criar_semaforos(config.num_semaforos)
        self._criar_carros(config.num_carros, config.algoritmo_carros)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _criar_semaforos(self, quantidade: int) -> None:
        if quantidade <= 0:
            return

        candidatos = self._nos_internos()
        self._rng.shuffle(candidatos)

        for no in candidatos[:min(quantidade, len(candidatos))]:
            semaforo = AgenteSemaforo(
                no=no,
                direcao_atual=self._rng.choice([Direcao.HORIZONTAL, Direcao.VERTICAL]),
                min_verde=2,
                max_verde=7,
                duracao_amarelo=2,
            )
            semaforo.registrar(self.grid)
            self.semaforos.append(semaforo)

    def _criar_carros(self, quantidade: int, algoritmo: Algoritmo) -> None:
        todos = self.grid.todos_os_nos()
        for idx in range(quantidade):
            origem, destino = self._sortear_par_nos_distintos(todos)
            carro = AgenteCarro(
                id=idx + 1,
                origem=origem,
                destino=destino,
                grid=self.grid,
                algoritmo=algoritmo,
            )
            self.carros.append(carro)
            self._telemetria[carro.id] = TelemetriaCarro(
                origem=origem,
                destino=destino,
                inicio_tick=0,
                ultima_rota=tuple(carro.rota),
            )

    def _nos_internos(self) -> list[No]:
        nos: list[No] = []
        for i in range(1, max(1, self.grid.linhas - 1)):
            for j in range(1, max(1, self.grid.colunas - 1)):
                if 0 < i < self.grid.linhas - 1 and 0 < j < self.grid.colunas - 1:
                    nos.append((i, j))
        if not nos:
            return self.grid.todos_os_nos()
        return nos

    def _sortear_par_nos_distintos(self, universo: list[No]) -> tuple[No, No]:
        origem = self._rng.choice(universo)
        destino = self._rng.choice(universo)
        while destino == origem:
            destino = self._rng.choice(universo)
        return origem, destino

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def step(self) -> None:
        self.ticks += 1

        # 1) Atualiza semaforos
        for semaforo in self.semaforos:
            semaforo.tick()

        # 2) Atualiza incidentes ativos e cria novos se necessario
        self._atualizar_incidentes()
        self._garantir_incidentes_alvo()

        # 3) Move carros
        movimentos = 0
        for carro in self.carros:
            pos_antes = carro.posicao_atual
            rota_antes = tuple(carro.rota)

            moveu = carro.avancar()
            if moveu:
                movimentos += 1
            elif carro.bloqueado:
                # tenta recuperar um carro sem rota
                carro.recalcular_rota()

            self._atualizar_telemetria_carro(carro, pos_antes, rota_antes, moveu)

        self.movimentos_no_tick = movimentos

    def _atualizar_incidentes(self) -> None:
        expirar: list[Aresta] = []
        for aresta, restante in list(self.incidentes_ativos.items()):
            restante -= 1
            if restante <= 0:
                expirar.append(aresta)
            else:
                self.incidentes_ativos[aresta] = restante

        for origem, destino in expirar:
            self.grid.desbloquear_aresta(origem, destino)
            self.incidentes_ativos.pop((origem, destino), None)

    def _garantir_incidentes_alvo(self) -> None:
        alvo = max(0, self.config.num_incidentes)
        while len(self.incidentes_ativos) < alvo:
            aresta = self._sortear_aresta_livre()
            if aresta is None:
                break
            origem, destino = aresta
            self.grid.bloquear_aresta(origem, destino)
            self.incidentes_ativos[(origem, destino)] = self.config.duracao_incidente

            # Ao surgir incidente novo, forca recalculo para reduzir travamentos
            for carro in self.carros:
                if not carro.chegou:
                    rota_antes = tuple(carro.rota)
                    carro.recalcular_rota()
                    self._contar_mudanca_trajetoria(carro, rota_antes)

    def _sortear_aresta_livre(self) -> Aresta | None:
        candidatos: list[Aresta] = []
        for i in range(self.grid.linhas):
            for j in range(self.grid.colunas):
                origem = (i, j)
                for destino in self.grid.vizinhos(origem):
                    # evita duplicar aresta inversa
                    if origem < destino and not self.grid.aresta_bloqueada(origem, destino):
                        candidatos.append((origem, destino))

        if not candidatos:
            return None
        self._rng.shuffle(candidatos)
        return candidatos[0]

    def _atualizar_telemetria_carro(
        self,
        carro: AgenteCarro,
        pos_antes: No,
        rota_antes: tuple[No, ...],
        moveu: bool,
    ) -> None:
        t = self._telemetria[carro.id]

        if moveu:
            di = carro.posicao_atual[0] - pos_antes[0]
            dj = carro.posicao_atual[1] - pos_antes[1]
            direcao_atual = (di, dj)
            if t.ultima_direcao is not None and t.ultima_direcao != direcao_atual:
                t.mudancas_direcao += 1
            t.ultima_direcao = direcao_atual

        self._contar_mudanca_trajetoria(carro, rota_antes)

        if carro.chegou and t.chegada_tick is None:
            t.chegada_tick = self.ticks

    def _contar_mudanca_trajetoria(self, carro: AgenteCarro, rota_antes: tuple[No, ...]) -> None:
        t = self._telemetria[carro.id]
        rota_atual = tuple(carro.rota)
        if rota_antes != rota_atual:
            t.mudancas_trajetoria += 1
        t.ultima_rota = rota_atual

    # ------------------------------------------------------------------
    # Metricas
    # ------------------------------------------------------------------

    @property
    def carros_chegaram(self) -> int:
        return sum(1 for c in self.carros if c.chegou)

    @property
    def carros_sem_rota(self) -> int:
        return sum(1 for c in self.carros if c.bloqueado)

    @property
    def carros_aguardando(self) -> int:
        return sum(1 for c in self.carros if c.estado.value == "aguardando")

    def dados_carros(self, limite: int = 8) -> list[dict[str, object]]:
        saida: list[dict[str, object]] = []
        for carro in sorted(self.carros, key=lambda c: c.id)[:limite]:
            t = self._telemetria[carro.id]
            tempo = None
            if t.chegada_tick is not None:
                tempo = t.chegada_tick - t.inicio_tick

            saida.append(
                {
                    "id": carro.id,
                    "origem": t.origem,
                    "destino": t.destino,
                    "posicao": carro.posicao_atual,
                    "estado": carro.estado.value,
                    "mudancas_direcao": t.mudancas_direcao,
                    "mudancas_trajetoria": t.mudancas_trajetoria,
                    "recalculos": carro.recalculos,
                    "tempo_ate_chegada": tempo,
                }
            )
        return saida
