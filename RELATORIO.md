# Relatorio curto: estruturas, Big-O e escolhas

## Objetivo

O sistema foi organizado em camadas para separar interface, regras de negocio, persistencia e relatorios. A ideia e simular o dia a dia de uma clinica ou central de atendimento com fila comum, fila de prioridade e historico de atendimentos.

## Estruturas usadas

### Vetor ordenado

Arquivo: `atendimento/structures.py`

`VetorClientesOrdenado` mantem clientes ordenados por id. A busca por id usa busca binaria recursiva.

- Busca: O(log n)
- Insercao: O(n), pois pode deslocar elementos
- Remocao: O(n)

Essa escolha atende ao requisito de busca rapida por cliente e demonstra o uso de vetor ordenado.

### Vetor nao ordenado

Arquivo: `atendimento/service.py`

`clientes_temporarios` e `atendentes` sao listas Python usadas como vetores nao ordenados para cadastros e iteracoes simples.

- Insercao no fim: O(1) amortizado
- Busca linear por atendente: O(n)

Essa estrutura e suficiente para cadastros pequenos e ajuda a manter os dados em ordem simples para persistencia.

### Fila comum e fila de prioridade

Arquivo: `atendimento/structures.py`

A classe `Fila` usa `collections.deque`. O sistema possui duas filas: `fila_prioridade` e `fila_comum`.

- Enfileirar: O(1)
- Desenfileirar: O(1)
- Verificar/remover cliente especifico: O(n)

A regra de chamada consulta primeiro a fila de prioridade. Como cada fila e FIFO, a ordem de chegada e mantida dentro de cada grupo.

### Pilha

Arquivo: `atendimento/structures.py`

`Pilha` guarda as finalizacoes recentes. Ao desfazer, remove a ultima finalizacao registrada.

- Empilhar: O(1)
- Desempilhar: O(1)

Essa estrutura implementa o comportamento LIFO esperado para desfazer a ultima acao.

### Lista encadeada

Arquivo: `atendimento/structures.py`

`ListaClientesAtivos` representa os clientes ativos em uma lista encadeada. Ela e reconstruida a partir dos cadastros e usada no fluxo de remocao de inativos.

- Adicionar no fim: O(n)
- Remover inativos: O(n)
- Listar ids: O(n)

Foi escolhida para atender ao requisito de lista encadeada e demonstrar remocao por ponteiros.

## Ordenacao

Arquivo: `atendimento/reports.py`

O projeto usa duas ordenacoes:

- `merge_sort_por_total`: ordena o top de clientes mais atendidos.
- `quick_sort_registros`: ordena atendimentos por duracao.

Complexidades:

- Merge sort: O(n log n) no pior caso.
- Quick sort: media O(n log n), pior caso O(n²).

## Recursao

A recursao aparece em:

- Busca binaria recursiva em `VetorClientesOrdenado._buscar_recursivo`.
- Merge sort e quick sort em `atendimento/reports.py`.

## Persistencia

Arquivo: `atendimento/repository.py`

Os dados sao salvos em JSON para facilitar leitura e entrega. O arquivo principal gerado em execucao e `data/atendimentos.json`.

## Qualidade e testes

Os testes em `tests/test_service.py` cobrem:

- Busca binaria por cliente.
- Ordem da fila de prioridade.
- Finalizacao e desfazer.
- Bloqueio de remocao de cliente com atendimento aberto.
- Media, top clientes e alertas.

Execucao:

```bash
python -m unittest discover -v
```

## Logs

Operacoes importantes sao registradas em `logs/operacoes.log`, incluindo cadastros, abertura, chamada, finalizacao e remocao.