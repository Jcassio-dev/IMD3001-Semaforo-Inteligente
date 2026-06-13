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
│   ├── run_tests.py
│   └── test_agentes.py
├── main.py              # Ponto de entrada (launcher)
├── docs/
├── requirements.txt
└── README.md
```

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

## Visual Interativo

Ao executar `python main.py`, abre uma janela Pygame com:

- Área do grid (esquerda): ruas, cruzamentos, carros, semáforos e incidentes.
- Painel de controle (direita): parâmetros de simulação via campos numéricos.
- Janela redimensionável (layout responsivo no painel e no modal de desempenho).

Parâmetros disponíveis no painel:

- `Linhas do grid`
- `Colunas do grid`
- `Quantidade de carros`
- `Quantidade de semáforos`
- `Incidentes ativos`
- `Duração do incidente (ticks)`
- `Velocidade (ticks/s)`
- `Algoritmo dos carros` (select box: BFS, DFS, Greedy, A*)

Botões:

- `Aplicar configuracao`: recria a simulação com os valores atuais.
- `Pausar/Retomar`: controla a execução.
- `Desempenho`: abre um modal com objetivo e métricas por carro.

Modal `Desempenho`:

- Exibe origem/destino por carro.
- Mostra posição atual, estado, recálculos.
- Mostra mudanças de direção e mudanças de trajetória.
- Mostra tempo até chegada (em ticks) quando o carro conclui o percurso.
- Possui botão `Fechar` e atalho `Esc`.

Legenda visual:

- Carros: sprite de carro com número no corpo.
- Semáforos: verde/amarelo/vermelho no nó.
- Incidente: aresta em vermelho grosso, com contador de ticks restantes.

## Testes

```bash
python tests/test_agentes.py
python tests/run_tests.py
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
