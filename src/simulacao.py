from __future__ import annotations

from dataclasses import dataclass
import random

try:
    from .agente_carro import AgenteCarro
    from .agente_semaforo import AgenteSemaforo
    from .grid import Grid
    from .modelos import Algoritmo, Direcao
    from .congestionamento import SistemaCongestionamento
    from .acidentes import SistemaAcidentes
    from .metricas import ColetorMetricas
except ImportError:
    from agente_carro import AgenteCarro
    from agente_semaforo import AgenteSemaforo
    from grid import Grid
    from modelos import Algoritmo, Direcao
    from congestionamento import SistemaCongestionamento
    from acidentes import SistemaAcidentes
    from metricas import ColetorMetricas


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

        self._congestionamento = SistemaCongestionamento(self.grid)
        self._acidentes = SistemaAcidentes(
            self.grid,
            prob_acidente=0.05,
            duracao_acidente=config.duracao_incidente,
            seed=config.seed,
        )
        self.metricas = ColetorMetricas()

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

    def iniciar(self) -> None:
        pass

    def tick(self) -> None:
        self.step()

    def resetar(self) -> None:
        for semaforo in self.semaforos:
            semaforo.remover(self.grid)
        self.grid = Grid(self.config.linhas, self.config.colunas)
        self.carros = []
        self.semaforos = []
        self.incidentes_ativos = {}
        self.ticks = 0
        self.movimentos_no_tick = 0
        self._telemetria = {}
        self._congestionamento = SistemaCongestionamento(self.grid)
        self._acidentes = SistemaAcidentes(
            self.grid,
            prob_acidente=0.05,
            duracao_acidente=self.config.duracao_incidente,
            seed=self.config.seed,
        )
        self.metricas = ColetorMetricas()
        self._criar_semaforos(self.config.num_semaforos)
        self._criar_carros(self.config.num_carros, self.config.algoritmo_carros)

    def step(self) -> None:
        self.ticks += 1

        # 1) Atualiza semaforos
        for semaforo in self.semaforos:
            semaforo.tick()

        # 2) Acidentes via SistemaAcidentes
        self._acidentes.tick(self.carros)
        self.incidentes_ativos = self._acidentes.acidentes_ativos

        # 3) Congestionamento via SistemaCongestionamento
        self._congestionamento.atualizar(self.carros)

        # 4) Move carros
        movimentos = 0
        for carro in self.carros:
            pos_antes = carro.posicao_atual
            rota_antes = tuple(carro.rota)

            moveu = carro.avancar()
            if moveu:
                movimentos += 1
                if carro.ultimo_resultado:
                    self.metricas.registrar(carro.ultimo_resultado, carro.recalculos)
            elif carro.bloqueado:
                carro.recalcular_rota()

            self._atualizar_telemetria_carro(carro, pos_antes, rota_antes, moveu)

        self.movimentos_no_tick = movimentos

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
