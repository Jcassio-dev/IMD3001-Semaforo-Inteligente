# Simulador de Trânsito Inteligente

Simulador de trânsito multiagente com algoritmos de busca (BFS, DFS, Greedy, A*), semáforos inteligentes e recálculo dinâmico de rotas.

**IMD3001 - Introdução à Inteligência Artificial (IMD-UFRN)**

## Sobre

Agentes autônomos (veículos) navegam uma malha viária modelada como grafo ponderado, buscando rotas ótimas em um ambiente dinâmico com semáforos adaptativos e acidentes aleatórios.

## Estrutura

```
simulador-transito-inteligente/
├── src/
│   ├── grid.py          # Ambiente: malha viária como grafo ponderado
│   ├── modelos.py       # Classes auxiliares: Estado, Resultado, Config
│   ├── algoritmos.py    # BFS, DFS, Greedy, A*
│   ├── agente_carro.py  # Agente veículo
│   ├── agente_semaforo.py # Agente semáforo
│   ├── simulacao.py     # Loop principal
│   └── visualizador.py  # Interface Pygame
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## Como rodar

```bash
pip install -r requirements.txt
python src/main.py
```

## Algoritmos

| Algoritmo | Tipo | Prioridade | Ótimo? |
|-----------|------|-----------|--------|
| BFS | Busca cega | FIFO | S |
| DFS | Busca cega | LIFO | N |
| Greedy | Informada | h(n) | N |
| A* | Informada | g(n)+h(n) | S |

## Referências

- Russell & Norvig — Artificial Intelligence: A Modern Approach, 4ª ed. (cap. 2-4)
- CS188 Berkeley — Introduction to Artificial Intelligence
