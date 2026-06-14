from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable

try:
    from .grid import Grid
    from .modelos import Algoritmo, Resultado, No, EstadoSemaforo, Direcao
    from .algoritmos import bfs, dfs, greedy_best_first, a_estrela
except ImportError:
    from grid import Grid
    from modelos import Algoritmo, Resultado, No, EstadoSemaforo, Direcao
    from algoritmos import bfs, dfs, greedy_best_first, a_estrela


_ALGORITMOS: dict[Algoritmo, Callable[[Grid, No, No], Resultado]] = {
    Algoritmo.BFS: bfs,
    Algoritmo.DFS: dfs,
    Algoritmo.GREEDY: greedy_best_first,
    Algoritmo.A_ESTRELA: a_estrela,
}


class EstadoCarro(Enum):
    EM_ROTA = "em_rota"          # movendo-se normalmente
    AGUARDANDO = "aguardando"    # parado em semáforo vermelho
    CHEGOU = "chegou"            # destino alcançado
    SEM_ROTA = "sem_rota"        # sem caminho disponível


@dataclass
class AgenteCarro:
    id: int
    origem: No
    destino: No
    grid: Grid
    algoritmo: Algoritmo = Algoritmo.A_ESTRELA

    # Estado interno — não passados na construção
    posicao_atual: No = field(init=False)
    rota: list[No] = field(default_factory=list, init=False)
    _indice_rota: int = field(default=0, init=False)
    estado: EstadoCarro = field(default=EstadoCarro.SEM_ROTA, init=False)
    ultimo_resultado: Optional[Resultado] = field(default=None, init=False)

    # Métricas acumuladas
    distancia_percorrida: float = field(default=0.0, init=False)
    passos_aguardando: int = field(default=0, init=False)
    recalculos: int = field(default=0, init=False)

    # Rota anterior ao último recálculo (para visualização)
    prev_rota: list[No] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.posicao_atual = self.origem
        self.planejar_rota()

    # ------------------------------------------------------------------
    # Planejamento de rota
    # ------------------------------------------------------------------

    def planejar_rota(self) -> Resultado:
        """Calcula a rota da posição atual até o destino usando o algoritmo configurado."""
        fn = _ALGORITMOS[self.algoritmo]
        resultado = fn(self.grid, self.posicao_atual, self.destino)
        self.ultimo_resultado = resultado

        if resultado.encontrou:
            self.rota = resultado.caminho
            self._indice_rota = 0
            self.estado = (
                EstadoCarro.CHEGOU
                if self.posicao_atual == self.destino
                else EstadoCarro.EM_ROTA
            )
        else:
            self.rota = []
            self._indice_rota = 0
            self.estado = EstadoCarro.SEM_ROTA

        return resultado

    def recalcular_rota(self) -> Resultado:
        """Força replanejamento a partir da posição atual (ex: após acidente ou bloqueio)."""
        self.prev_rota = list(self.rota[self._indice_rota:])
        self.recalculos += 1
        return self.planejar_rota()

    # ------------------------------------------------------------------
    # Movimentação
    # ------------------------------------------------------------------

    def avancar(self) -> bool:
        """
        Tenta mover o agente um passo na rota planejada.

        Retorna True se o agente avançou de nó, False caso contrário
        (semáforo vermelho, sem rota, ou já chegou).
        """
        if self.estado in (EstadoCarro.CHEGOU, EstadoCarro.SEM_ROTA):
            return False

        # Verifica semáforo no nó atual
        if self._semaforo_vermelho():
            if self.estado != EstadoCarro.AGUARDANDO:
                # Primeira vez que para neste semáforo — notifica chegada
                self._notificar_semaforo_chegou()
            self.estado = EstadoCarro.AGUARDANDO
            self.passos_aguardando += 1
            return False

        proximo = self.proximo_no
        if proximo is None:
            self.estado = EstadoCarro.CHEGOU
            return False

        # Verifica se a aresta até o próximo nó ainda está disponível
        if proximo not in self.grid.vizinhos(self.posicao_atual):
            resultado = self.recalcular_rota()
            if not resultado.encontrou:
                self.estado = EstadoCarro.SEM_ROTA
            return False

        # Se estava aguardando em semáforo, notifica que passou
        if self.estado == EstadoCarro.AGUARDANDO:
            self._notificar_semaforo_passou()

        # Move o agente
        custo = self.grid.peso(self.posicao_atual, proximo)
        self.distancia_percorrida += custo
        self.posicao_atual = proximo
        self._indice_rota += 1

        self.estado = (
            EstadoCarro.CHEGOU
            if self.posicao_atual == self.destino
            else EstadoCarro.EM_ROTA
        )
        return True

    # ------------------------------------------------------------------
    # Propriedades auxiliares
    # ------------------------------------------------------------------

    @property
    def rota_restante(self) -> list[No]:
        return self.rota[self._indice_rota:]

    @property
    def proximo_no(self) -> Optional[No]:
        """Próximo nó na rota, ou None se não houver."""
        idx = self._indice_rota + 1
        return self.rota[idx] if idx < len(self.rota) else None

    @property
    def passos_restantes(self) -> int:
        """Número de passos que faltam para chegar ao destino."""
        if not self.rota:
            return 0
        return max(0, len(self.rota) - 1 - self._indice_rota)

    @property
    def chegou(self) -> bool:
        return self.estado == EstadoCarro.CHEGOU

    @property
    def bloqueado(self) -> bool:
        return self.estado == EstadoCarro.SEM_ROTA

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _semaforo_vermelho(self) -> bool:
        semaforo = self.grid.semaforos.get(self.posicao_atual)
        if semaforo is None:
            return False
        return getattr(semaforo, "estado", None) == EstadoSemaforo.VERMELHO

    def _direcao_movimento(self) -> Direcao:
        """Infere a direção do movimento com base no próximo nó da rota."""
        proximo = self.proximo_no
        if proximo is None:
            return Direcao.HORIZONTAL
        di = proximo[0] - self.posicao_atual[0]
        # movimento vertical (norte/sul) → di != 0
        return Direcao.VERTICAL if di != 0 else Direcao.HORIZONTAL

    def _notificar_semaforo_chegou(self) -> None:
        semaforo = self.grid.semaforos.get(self.posicao_atual)
        if semaforo is not None and hasattr(semaforo, "carro_chegou"):
            semaforo.carro_chegou(self._direcao_movimento())

    def _notificar_semaforo_passou(self) -> None:
        semaforo = self.grid.semaforos.get(self.posicao_atual)
        if semaforo is not None and hasattr(semaforo, "carro_passou"):
            semaforo.carro_passou(self._direcao_movimento())

    def __repr__(self) -> str:
        return (
            f"AgenteCarro("
            f"id={self.id}, "
            f"pos={self.posicao_atual}, "
            f"destino={self.destino}, "
            f"estado={self.estado.value}, "
            f"passos_restantes={self.passos_restantes}, "
            f"dist={self.distancia_percorrida:.1f})"
        )
