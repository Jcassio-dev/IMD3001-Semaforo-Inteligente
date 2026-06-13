from __future__ import annotations
from dataclasses import dataclass, field

try:
    from .grid import Grid
    from .modelos import EstadoSemaforo, Direcao, No
except ImportError:
    from grid import Grid
    from modelos import EstadoSemaforo, Direcao, No

# Sequência fixa do ciclo: VERDE → AMARELO → VERMELHO → VERDE …
_CICLO = [EstadoSemaforo.VERDE, EstadoSemaforo.AMARELO, EstadoSemaforo.VERMELHO]


@dataclass
class AgenteSemaforo:
    """
    Agente semáforo adaptativo instalado em um nó do grid.

    Lógica adaptativa
    -----------------
    O semáforo mantém duas filas de espera: uma por direção (HORIZONTAL e
    VERTICAL). A cada tick() ele decide se mantém ou encerra a fase VERDE
    atual com base na demanda observada:

    - Verde mínimo (min_verde): garante tempo mínimo aberto para evitar
      piscadas rápidas.
    - Verde máximo (max_verde): limite superior para não causar starvation
      na direção oposta.
    - Troca antecipada: se a fila da direção atual esvaziar antes do
      min_verde, o semáforo ainda aguarda até completá-lo; após isso, se
      a outra direção tiver carros esperando, troca imediatamente.
    - Fase AMARELO: sempre dura duracao_amarelo ticks fixos (transição).
    - Fase VERMELHO: dura até a direção seguinte ficar verde (controlado
      pela lógica de troca, não por timer fixo).

    Atributos públicos configuráveis
    ---------------------------------
        no              : nó do grid onde o semáforo está instalado.
        direcao_atual   : direção com VERDE agora (começa em HORIZONTAL).
        min_verde       : ticks mínimos na fase VERDE.
        max_verde       : ticks máximos na fase VERDE.
        duracao_amarelo : ticks fixos na fase AMARELO.
        estado_inicial  : estado no qual o semáforo inicia.
    """

    no: No
    direcao_atual: Direcao = Direcao.HORIZONTAL
    min_verde: int = 3
    max_verde: int = 10
    duracao_amarelo: int = 2
    estado_inicial: EstadoSemaforo = EstadoSemaforo.VERDE

    # Estado interno
    estado: EstadoSemaforo = field(init=False)
    _ticks_na_fase: int = field(default=0, init=False)
    _ticks_totais: int = field(default=0, init=False)
    # Filas de espera por direção: contagem de carros aguardando
    _fila: dict[Direcao, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.estado = self.estado_inicial
        self._fila = {Direcao.HORIZONTAL: 0, Direcao.VERTICAL: 0}

    # ------------------------------------------------------------------
    # Interface para os carros notificarem presença
    # ------------------------------------------------------------------

    def carro_chegou(self, direcao: Direcao) -> None:
        """Registra que um carro está aguardando nessa direção."""
        self._fila[direcao] = self._fila.get(direcao, 0) + 1

    def carro_passou(self, direcao: Direcao) -> None:
        """Remove um carro da fila quando ele avança."""
        self._fila[direcao] = max(0, self._fila.get(direcao, 0) - 1)

    def carros_aguardando(self, direcao: Direcao) -> int:
        """Retorna quantos carros estão esperando em determinada direção."""
        return self._fila.get(direcao, 0)

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------

    def tick(self) -> bool:
        """
        Avança um tick no ciclo do semáforo.

        Retorna True se houve mudança de estado neste tick.
        """
        self._ticks_na_fase += 1
        self._ticks_totais += 1

        if self.estado == EstadoSemaforo.VERDE:
            return self._tick_verde()
        elif self.estado == EstadoSemaforo.AMARELO:
            return self._tick_amarelo()
        else:  # VERMELHO — controlado via troca de direção
            return self._tick_vermelho()

    def _tick_verde(self) -> bool:
        """Decide se encerra o VERDE com base na demanda."""
        if self._ticks_na_fase < self.min_verde:
            return False  # ainda no mínimo obrigatório

        direcao_oposta = self._direcao_oposta()
        fila_atual = self._fila.get(self.direcao_atual, 0)
        fila_oposta = self._fila.get(direcao_oposta, 0)

        deve_trocar = (
            self._ticks_na_fase >= self.max_verde          # atingiu máximo
            or (fila_atual == 0 and fila_oposta > 0)       # fila atual vazia, outra cheia
        )

        if deve_trocar:
            self._avancar_fase()  # VERDE → AMARELO
            return True
        return False

    def _tick_amarelo(self) -> bool:
        """Amarelo é temporização fixa."""
        if self._ticks_na_fase >= self.duracao_amarelo:
            self._avancar_fase()  # AMARELO → VERMELHO
            return True
        return False

    def _tick_vermelho(self) -> bool:
        """Vermelho termina imediatamente ao entrar — a troca já aconteceu."""
        # Vermelho serve apenas para a direção antiga; a nova direção
        # assumiu VERDE. Se este semáforo é quem foi colocado em VERMELHO,
        # o semáforo parceiro assumiu VERDE.
        # Em implementações com semáforo único por cruzamento, passamos
        # direto para VERDE da nova direção.
        self.direcao_atual = self._direcao_oposta()
        self._avancar_fase()  # VERMELHO → VERDE (nova direção)
        return True

    def _avancar_fase(self) -> None:
        indice_atual = _CICLO.index(self.estado)
        self.estado = _CICLO[(indice_atual + 1) % len(_CICLO)]
        self._ticks_na_fase = 0

    def _direcao_oposta(self) -> Direcao:
        return (
            Direcao.VERTICAL
            if self.direcao_atual == Direcao.HORIZONTAL
            else Direcao.HORIZONTAL
        )

    # ------------------------------------------------------------------
    # Integração com o Grid
    # ------------------------------------------------------------------

    def registrar(self, grid: Grid) -> None:
        """Registra o semáforo no grid para que os carros possam consultá-lo."""
        grid.semaforos[self.no] = self

    def remover(self, grid: Grid) -> None:
        """Remove o semáforo do grid."""
        grid.semaforos.pop(self.no, None)

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------

    @property
    def aberto(self) -> bool:
        """True quando o semáforo está VERDE."""
        return self.estado == EstadoSemaforo.VERDE

    @property
    def fechado(self) -> bool:
        """True quando o semáforo está VERMELHO."""
        return self.estado == EstadoSemaforo.VERMELHO

    @property
    def ticks_na_fase(self) -> int:
        return self._ticks_na_fase

    @property
    def ticks_totais(self) -> int:
        return self._ticks_totais

    def __repr__(self) -> str:
        h = self._fila.get(Direcao.HORIZONTAL, 0)
        v = self._fila.get(Direcao.VERTICAL, 0)
        return (
            f"AgenteSemaforo("
            f"no={self.no}, "
            f"direcao={self.direcao_atual.value}, "
            f"estado={self.estado.value}, "
            f"fila=[H:{h} V:{v}])"
        )
