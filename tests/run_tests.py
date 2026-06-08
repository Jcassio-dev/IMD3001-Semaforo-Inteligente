import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_grid import *
from test_modelos import *
from test_algoritmos import *

TESTES = [
    # Grid
    test_grid_criacao,
    test_grid_vizinhos_centro,
    test_grid_vizinhos_canto,
    test_grid_vizinhos_borda,
    test_grid_peso_base,
    test_grid_bloquear_aresta,
    test_grid_desbloquear_aresta,
    test_grid_congestionamento,
    test_grid_decrementar_congestionamento,
    test_grid_resetar_congestionamento,
    test_grid_no_valido,
    test_grid_todos_os_nos,
    test_grid_repr,
    # Modelos
    test_resultado_criacao,
    test_resultado_com_caminho,
    test_timer,
    test_heuristica_manhattan,
    test_heuristica_euclidiana,
    test_config_validar,
    test_config_carros_demais,
    test_algoritmo_enum,
    # Algoritmos
    test_bfs_retorna_resultado,
    test_bfs_encontra_caminho_simples,
    test_bfs_encontra_caminho_grid,
    test_bfs_caminho_valido_sem_saltos,
    test_bfs_origem_igual_destino,
    test_bfs_sem_caminho,
    test_bfs_nos_expandidos,
    test_bfs_custo_total,
    test_bfs_custo_com_congestionamento,
    test_bfs_tempo_medido,
    test_bfs_menor_numero_de_passos,
]

if __name__ == "__main__":
    passou = 0
    falhou = 0

    print(f"\nRodando {len(TESTES)} testes...\n")

    for teste in TESTES:
        try:
            teste()
            print(f"  PASS  {teste.__name__}")
            passou += 1
        except Exception as e:
            print(f"  FAIL  {teste.__name__}: {e}")
            falhou += 1

    print(f"\n{passou} passaram  |  {falhou} falharam\n")
    sys.exit(1 if falhou else 0)
