# FP_DCC606_Tema_4_RR_2026

Projeto Final da disciplina **DCC606**  
Tema: **Síntese de Invariantes Indutivos para Verificação Formal de Programas com MILP**

## 1. Descrição do Problema

Sistemas embarcados críticos (ex.: ADAS, BMS e dispositivos médico-hospitalares) exigem alta confiabilidade.  
Testes dinâmicos tradicionais não conseguem cobrir todos os caminhos de execução, especialmente em cenários extremos.

Este projeto propõe um motor de **verificação estática** para provar, matematicamente, que estados de erro (como divisão por zero, violação de limites e falhas de segurança) são inalcançáveis, usando:

- Verificação formal por alcançabilidade;
- Síntese automática de invariantes indutivos;
- Otimização combinatória via **MILP** (Programação Linear Inteira Mista).

## 2. Objetivo Geral

Projetar, formular e implementar um sistema que:

1. Receba a especificação de um loop de controle crítico;
2. Traduza transições de estado em restrições lineares;
3. Sintetize invariantes indutivos por resolvedores MILP;
4. Encontre um conjunto mínimo/ótimo de invariantes para provar a inacessibilidade de estados de erro.

## 3. Aplicação Prática

Aplicações-alvo:

- Controle automotivo avançado (ADAS);
- Gerenciamento de baterias em veículos elétricos (BMS);
- Firmware de equipamentos médico-hospitalares.

Benefício: aumento da confiança em software crítico, reduzindo risco de falhas catastróficas em produção.

## 4. Requisitos Acadêmicos Atendidos

Este repositório foi estruturado para contemplar:

- Definição detalhada do cenário e do problema;
- Formulação e implementação do algoritmo;
- Análise de complexidade dos algoritmos;
- Estudo comparativo de desempenho com casos de teste representativos;
- Relatório no padrão IEEE (mínimo 4 páginas);
- Inclusão da URL do repositório no relatório;
- Entrega do relatório no SIGAA e apresentação em seminário na data definida.

> Observação: os programas devem ser desenvolvidos em **C ou C++**.

## 5. Estrutura Esperada do Projeto

```
FP_DCC606_Tema_4_RR_2026/
├── README.md
├── src/                 # implementação principal (C/C++)
├── include/             # headers (se aplicável)
├── tests/               # casos de teste
├── data/                # instâncias/cenários de entrada
└── docs/                # relatório e materiais de apoio
```

## 6. Implementação (Visão Geral)

Fluxo do motor de verificação:

1. Modelagem do programa (estado inicial, transições e estados de erro);
2. Definição de templates de invariantes lineares;
3. Formulação MILP dos coeficientes dos invariantes;
4. Resolução com solver e extração dos invariantes;
5. Verificação indutiva (base + passo indutivo);
6. Emissão de relatório com resultado (seguro/inseguro) e métricas.

## 7. Análise de Complexidade

A análise de complexidade deve incluir:

- Complexidade da etapa de modelagem;
- Complexidade da síntese via MILP (custos de Branch-and-Bound e partição);
- Escalabilidade em função do número de variáveis, restrições e templates;
- Impacto do tamanho das instâncias no tempo de execução.

## 8. Testes e Avaliação de Desempenho

Os testes devem cobrir:

- Casos simples (validação básica);
- Casos médios (diferentes perfis de transição);
- Casos críticos/extremos (limites operacionais).

Para cada cenário, registrar:

- Tempo total de síntese;
- Número de invariantes gerados;
- Qualidade das provas de segurança;
- Comparação entre configurações de template/solver.

## 9. Relatório (Padrão IEEE)

- Formato: artigo IEEE (mínimo 4 páginas);  
- Modelo: https://www.sbc.org.br/wp-content/uploads/2024/07/modelosparapublicaodeartigos.zip  
- Deve conter a URL deste repositório.

## 10. Repositório

URL: https://github.com/LuscaNobre/FP_DCC606_Tema_4_RR_2026

## 11. Equipe

Preencher com os integrantes do grupo e suas responsabilidades.