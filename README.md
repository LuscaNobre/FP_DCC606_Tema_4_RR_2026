# FP_DCC606_Tema_4_RR_2026

Repositório do projeto final da disciplina DCC606 — tema 4: síntese de invariantes indutivos para verificação formal via MILP.

## O que existe neste repositório

- `src/`: código C++ do parser/diagnóstico e programa principal (`main.cpp`, `parser.cpp`, `diagnostics.cpp`).
- `solver/`: solver Python em PuLP que sintetiza invariantes a partir das especificações do problema.
- `tests/`: especificações de casos de teste em JSON.
- `results/`: resultados gerados pelo solver e tabela de desempenho.
- `report/`: relatório em LaTeX no template SBC e PDF final.
- `ANALISE_COMPLEXIDADE.md`: análise detalhada de complexidade e classificação do algoritmo.
- `RASCUNHO_RELATORIO_SBC.md`: rascunho do relatório no formato markdown.

## Requisitos para rodar

- `g++` (compatível com C++17)
- `make`
- Python 3.9+ 
- Biblioteca PuLP (`python -m pip install pulp`)

## Como compilar

```bash
make all
```

## Como executar um caso específico

```bash
./main --case tests/case_bms.json
```

## Como rodar todos os testes

```bash
make test
```

## Como regenerar a tabela de desempenho

```bash
python results/regenerate_performance_csv.py
```

## Observações de implementação

### Implementado

- Parser em C++ que lê especificações JSON de casos de teste e exporta matrizes para o solver.
- Solver em Python/PuLP que gera relações candidatas, valida subsets seguros e seleciona o subset ótimo via MILP de seleção.
- Diagnóstico em C++ que formata o resultado final e exibe métricas de desempenho.
- Caso BMS conforme o enunciado do tema: `x <= 10`, atualizações `x = x+1`, `y = y-1` e erro `x + y = 25`.
- Caso `infeasible` ajustado para ser real inviável.
- Correção do cálculo real de variáveis/constraints do MILP de seleção.
- Ajuste de saída UTF-8 em `diagnostics.cpp` para exibir acentos corretamente.
- Relatório em LaTeX pronto no template SBC e PDF gerado em `report/TrabalhoFinal_DCC606_Tema_4_RR.pdf`.

### Limitações atuais

- O parser C++ ainda não faz análise de código fonte C/C++ real; ele consome especificações JSON com matrizes prontas.
- O modelo ainda não implementa completamente a codificação exata das implicações universais via Big-M ou Lema de Farkas.
- A métrica de taxa de falsos positivos não está automatizada no pipeline atual.
- O projeto foi validado até 3 variáveis; a escalabilidade além disso não foi garantida.

## Estrutura mínima para subir no GitHub

Suba exatamente estes itens no repositório `FP_DCC606_Tema_4_RR_2026`:

- `Makefile`
- `README.md`
- `ANALISE_COMPLEXIDADE.md`
- `RASCUNHO_RELATORIO_SBC.md`
- `report/TrabalhoFinal_DCC606_Tema_4_RR.pdf`
- `report/main.tex`
- `src/`
- `solver/`
- `tests/`
- `results/`

## URL no GitHub

Use o repositório com nome:

`https://github.com/<usuario>/FP_DCC606_Tema_4_RR_2026`

Substitua `<usuario>` pelo nome da sua conta ou da equipe.

## Observação final

O relatório final deve ser enviado também no SIGAA no tópico de apresentação do projeto final.
