# Simulador de Trânsito Inteligente

Simulador de trânsito multiagente com algoritmos de busca (BFS, DFS, Greedy, A*), semáforos inteligentes e recálculo dinâmico de rotas.

**IMD3001 - Introdução à Inteligência Artificial (IMD-UFRN)**

## Sobre

Agentes autônomos (veículos) navegam uma malha viária modelada como grafo ponderado, buscando rotas ótimas em um ambiente dinâmico com semáforos adaptativos e acidentes aleatórios. O sistema registra métricas de desempenho por algoritmo e permite interação em tempo real com o grid.

## Estrutura

```
simulador-transito-inteligente/
├── src/
│   ├── grid.py              # Ambiente: malha viária como grafo ponderado
│   ├── modelos.py           # Classes auxiliares: Estado, Resultado, Config
│   ├── algoritmos.py        # BFS, DFS, Greedy, A*
│   ├── agente_carro.py      # Agente veículo com pathfinding e recálculo
│   ├── agente_semaforo.py   # Agente semáforo adaptativo
│   ├── congestionamento.py  # Sistema de congestionamento por aresta
│   ├── acidentes.py         # Sistema de acidentes probabilístico
│   ├── metricas.py          # Coleta e comparação de métricas por algoritmo
│   ├── simulacao.py         # Loop principal e gerenciamento de estado
│   └── visualizador.py      # Interface Pygame interativa
├── tests/
│   ├── run_tests.py
│   ├── test_grid.py
│   ├── test_modelos.py
│   ├── test_algoritmos.py
│   ├── test_agentes.py
│   ├── test_congestionamento.py
│   ├── test_acidentes.py
│   └── test_metricas.py
├── main.py                  # Ponto de entrada
├── requirements.txt
└── README.md
```

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

## Interface Visual

Ao executar `python main.py`, abre uma janela Pygame redimensionável com:

- **Área do grid** (esquerda): ruas, cruzamentos, carros, semáforos e acidentes.
- **Painel de controle** (direita): parâmetros via sliders arrastáveis.

### Controles do painel

| Controle | Descrição |
|----------|-----------|
| Linhas / Colunas do grid | Dimensões da malha viária |
| Quantidade de carros | Número de agentes veículo |
| Quantidade de semáforos | Semáforos posicionados aleatoriamente |
| Incidentes ativos | Acidentes aleatórios no início |
| Duração do incidente | Ticks até o acidente ser removido |
| Velocidade (ticks/s) | Cadência de simulação |
| Algoritmo dos carros | BFS, DFS, Greedy ou A* |

### Botões

- `Aplicar configuracao`: recria a simulação com os valores atuais.
- `Pausar / Retomar`: congela e retoma a execução.
- `Desempenho`: abre modal com métricas detalhadas por carro.

### Interação com o grid (mouse)

| Ação | Efeito |
|------|--------|
| Clique esquerdo em nó | Adiciona semáforo (ou remove se já existir) |
| Clique esquerdo em aresta | Cria acidente (ou remove se já bloqueada) |
| Clique direito em nó | Remove semáforo |
| Clique direito em aresta | Remove acidente |
| Hover sobre carro | Exibe tooltip com algoritmo, custo, recálculos e estado |

### Legenda visual

- **Carro**: sprite com número, orientado na direção do movimento.
- **Rastro**: círculos com fade de opacidade na cor do carro (últimos 10 nós).
- **Marcador de destino**: bandeirinha na cor do carro sobre o nó de destino.
- **Heatmap**: sobreposição laranja-vermelho nos nós mais visitados.
- **Semáforo**: sprite verde/amarelo/vermelho fixado no nó.
- **Acidente**: aresta em vermelho grosso com contador de ticks restantes (`!` para acidentes manuais).

### Modal de desempenho

Exibe por carro: origem, destino, posição atual, estado, mudanças de direção/trajetória, recálculos e tempo até chegada (em ticks).

## Módulos do sistema

### `SistemaCongestionamento`

Atualiza o peso das arestas com base na quantidade de carros que as ocupam a cada tick. Permite que os algoritmos informados (Greedy, A*) evitem rotas sobrecarregadas.

### `SistemaAcidentes`

A cada tick gera acidentes aleatórios com probabilidade configurável. Ao criar um acidente, notifica os carros com rota afetada para recalcular imediatamente.

### `ColetorMetricas`

Registra `Resultado` de cada busca (algoritmo, nós expandidos, custo, tempo). Expõe `comparar_algoritmos()` com médias agrupadas por algoritmo.

## Testes

```bash
python tests/run_tests.py
```

Ou individualmente:

```bash
python tests/test_grid.py
python tests/test_algoritmos.py
python tests/test_agentes.py
python tests/test_congestionamento.py
python tests/test_acidentes.py
python tests/test_metricas.py
```

## Algoritmos

| Algoritmo | Tipo | Prioridade | Ótimo? |
|-----------|------|-----------|--------|
| BFS | Busca cega | FIFO | S (custo uniforme) |
| DFS | Busca cega | LIFO | N |
| Greedy | Informada | h(n) | N |
| A* | Informada | g(n) + h(n) | S |

Heurística: distância de Manhattan ponderada pelo tamanho médio de célula.

## Referências

- Russell & Norvig — Artificial Intelligence: A Modern Approach, 4ª ed. (cap. 2-4)
- CS188 Berkeley — Introduction to Artificial Intelligence
