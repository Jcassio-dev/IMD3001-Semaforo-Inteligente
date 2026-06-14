from __future__ import annotations

try:
    from .grid import Grid
except ImportError:
    from grid import Grid


class SistemaCongestionamento:
    def __init__(self, grid: Grid) -> None:
        self._grid = grid

    def atualizar(self, carros: list) -> None:
        self._grid.resetar_congestionamento()
        for carro in carros:
            if carro.chegou:
                continue
            proximo = carro.proximo_no
            if proximo is not None:
                self._grid.incrementar_congestionamento(carro.posicao_atual, proximo)
