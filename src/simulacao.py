from __future__ import annotations

from dataclasses import dataclass
import random

try:
    from .agente_carro import AgenteCarro, EstadoCarro
    from .agente_semaforo import AgenteSemaforo
    from .grid import Grid
    from .modelos import Algoritmo, Direcao
    from .congestionamento import SistemaCongestionamento
    from .acidentes import SistemaAcidentes
    from .metricas import ColetorMetricas
except ImportError:
    from agente_carro import AgenteCarro, EstadoCarro
    from agente_semaforo import AgenteSemaforo
    from grid import Grid
    from modelos import Algoritmo, Direcao
    from congestionamento import SistemaCongestionamento
    from acidentes import SistemaAcidentes
    from metricas import ColetorMetricas

_TRAIL_MAX = 10


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
    prob_acidente: float = 0.05
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
        self._trails: dict[int, list[No]] = {}
        self._full_trails: dict[int, list[No]] = {}
        self._heatmap: dict[No, int] = {}
        self._recalc_ticks: dict[int, int] = {}
        self._ticks_bloqueado: dict[int, int] = {}

        self._congestionamento = SistemaCongestionamento(self.grid)
        self._acidentes = SistemaAcidentes(
            self.grid,
            prob_acidente=config.prob_acidente,
            duracao_acidente=config.duracao_incidente,
            seed=config.seed,
        )
        self.metricas = ColetorMetricas()

        self._criar_semaforos(config.num_semaforos)
        self._criar_carros(config.num_carros, config.algoritmo_carros)

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
            self._full_trails[carro.id] = [origem]
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
            prob_acidente=self.config.prob_acidente,
            duracao_acidente=self.config.duracao_incidente,
            seed=self.config.seed,
        )
        self.metricas = ColetorMetricas()
        self._recalc_ticks = {}
        self._trails = {}
        self._full_trails = {}
        self._heatmap = {}
        self._ticks_bloqueado = {}
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
        # Snapshot de posições no início do tick (para detecção de sentido oposto)
        movimentos = 0
        pos_to_car: dict[No, AgenteCarro] = {
            c.posicao_atual: c for c in self.carros if not c.chegou
        }
        ocupados: set[No] = set(pos_to_car.keys())

        for carro in self.carros:
            pos_antes = carro.posicao_atual
            rota_antes = tuple(carro.rota)
            recalculos_antes = carro.recalculos
            proximo_antes = carro.proximo_no

            ocupados.discard(pos_antes)

            # Sentidos opostos na mesma aresta: libera passagem (duas faixas)
            # Carro A(X→Y) e carro B(Y→X) em EM_ROTA: não se bloqueiam
            no_liberado: No | None = None
            if proximo_antes is not None and proximo_antes in ocupados:
                outro = pos_to_car.get(proximo_antes)
                if (outro is not None
                        and outro.proximo_no == pos_antes
                        and outro.estado == EstadoCarro.EM_ROTA):
                    ocupados.discard(proximo_antes)
                    no_liberado = proximo_antes

            moveu = carro.avancar(ocupados=ocupados)

            # Restaura nó liberado caso o carro não tenha se movido para ele
            if no_liberado is not None and carro.posicao_atual != no_liberado:
                ocupados.add(no_liberado)

            ocupados.add(carro.posicao_atual)

            if moveu:
                movimentos += 1
                self._ticks_bloqueado[carro.id] = 0
                if carro.ultimo_resultado:
                    self.metricas.registrar(carro.ultimo_resultado, carro.recalculos)
            elif carro.bloqueado:
                carro.recalcular_rota()
                self._ticks_bloqueado[carro.id] = 0
            else:
                # Detecta bloqueio por tráfego: em rota, tinha próximo nó, mas não avançou
                bloqueado_trafico = (
                    proximo_antes is not None
                    and carro.estado == EstadoCarro.EM_ROTA
                    and carro.recalculos == recalculos_antes
                )
                if bloqueado_trafico:
                    cnt = self._ticks_bloqueado.get(carro.id, 0) + 1
                    self._ticks_bloqueado[carro.id] = cnt
                    if cnt >= 5:
                        carro.recalcular_rota()
                        self._ticks_bloqueado[carro.id] = 0
                else:
                    self._ticks_bloqueado[carro.id] = 0

            if carro.recalculos > recalculos_antes:
                self._recalc_ticks[carro.id] = self.ticks

            self._atualizar_telemetria_carro(carro, pos_antes, rota_antes, moveu)

            trail = self._trails.setdefault(carro.id, [])
            if not trail or trail[-1] != carro.posicao_atual:
                trail.append(carro.posicao_atual)
                if len(trail) > _TRAIL_MAX:
                    trail.pop(0)

            full = self._full_trails.setdefault(carro.id, [])
            if not full or full[-1] != carro.posicao_atual:
                full.append(carro.posicao_atual)

            no = carro.posicao_atual
            self._heatmap[no] = self._heatmap.get(no, 0) + 1

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

    def criar_acidente(self, origem: No, destino: No) -> None:
        if not self.grid.aresta_bloqueada(origem, destino):
            self.grid.bloquear_aresta(origem, destino)
            self._acidentes._acidentes[(origem, destino)] = 9999
            for carro in self.carros:
                if not carro.chegou:
                    rota = carro.rota
                    for k in range(len(rota) - 1):
                        if (rota[k], rota[k+1]) in ((origem, destino), (destino, origem)):
                            carro.recalcular_rota()
                            self._recalc_ticks[carro.id] = self.ticks
                            break

    def remover_acidente(self, origem: No, destino: No) -> None:
        self.grid.desbloquear_aresta(origem, destino)
        self._acidentes._acidentes.pop((origem, destino), None)
        self._acidentes._acidentes.pop((destino, origem), None)
        self.incidentes_ativos = self._acidentes.acidentes_ativos

    def criar_semaforo(self, no: No) -> None:
        if any(s.no == no for s in self.semaforos):
            return
        s = AgenteSemaforo(
            no=no,
            direcao_atual=self._rng.choice([Direcao.HORIZONTAL, Direcao.VERTICAL]),
            min_verde=2, max_verde=7, duracao_amarelo=2,
        )
        s.registrar(self.grid)
        self.semaforos.append(s)

    def remover_semaforo(self, no: No) -> None:
        for s in list(self.semaforos):
            if s.no == no:
                s.remover(self.grid)
                self.semaforos.remove(s)
                break

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
