# Ficha de leitura — Vicenzino2009 (Vicenzino et al., 2009)

> **Base: só resumo — conferir no texto completo.** Ficha escrita a partir do resumo do PubMed (PMID 18838330, buscado
> pela API em 24/11/2026: o resumo copiado em `01_busca/registros.json` está truncado no trecho "p<0.15 ... >112N") e do
> print da Tabela 2 que está na aula base (slide 38, `_base-capacitacao-cotovelo/midia/s038_4ca99807ac.png`). PDF pago
> (Manual Therapy, Elsevier), pendente de download manual com acesso institucional (`02_artigos/pendentes.md`, item 16).
> Campos marcados com **[texto completo]** ficaram em branco de propósito. "Resumo" = resumo do PubMed; "Tab. 2 (print)" =
> valores lidos no print da aula base, sem página.

- Citação: Vicenzino B, Smith D, Cleland J, Bisset L. Development of a clinical prediction rule to identify initial responders to mobilisation with movement and exercise for lateral epicondylalgia. Man Ther. 2009;14(5):550-554. · DOI 10.1016/j.math.2008.08.004 · PMID 18838330
- Texto lido: só resumo + print da Tabela 2 na aula base
- Papel na aula: aula 1 (prognóstico e uso da força de preensão sem dor; exercício de leitura de razão de verossimilhança) e aula 2 (quem responde a mobilização com movimento e exercício). A aula base usa no slide 38.
- Licença do PDF: desconhecida (PDF não obtido); imagem de reserva é print da aula base, tratada como "todos os direitos reservados"

## Pergunta

Em pessoas com epicondilalgia lateral tratadas com mobilização com movimento (MWM) e exercício, que características da linha de base identificam quem relata melhora em 3 semanas? (resumo)

## Desenho

Análise post hoc de dados de ensaio para derivar uma regra de predição clínica (resumo). Variáveis com relação univariada com "melhora" (p<0,15) entraram em regressão logística passo a passo; pontos de corte das variáveis contínuas por curva ROC (resumo). Os autores a chamam de regra "Level IV" (resumo). De qual ensaio vêm os dados: **[texto completo]**; provável que seja o ECR Bisset 2006 (mesmos autores, mesmos braços MWM + exercício e "esperar para ver"; ver `Bisset2006b.md`).

## Amostra

- Fisioterapia padronizada: 64 (resumo). Braço "esperar para ver" usado para testar a especificidade da regra: 57 (resumo).
- As notas da aula base (slide 38, que seguem a diretriz) falam em 62 sujeitos com idade média de 48,2 anos e 5 sessões de MWM e exercício: divergem do resumo (64). Conferir no texto.
- Quem são, perdas, número de sessões em 3 semanas: **[texto completo]**.
- **Calculado** (do resumo e da Tab. 2): com 79% de melhora em 64, ≈ 51 melhoraram e ≈ 13 não melhoraram (as sensibilidades 0,61, 0,53, 0,49 e 0,75 batem com 31, 27, 25 e 38 de 51; a especificidade 0,77 bate com 10 de 13). Toda especificidade da tabela vem de cerca de 13 pessoas.

## Intervenção (com dose)

- MWM (técnica de Mulligan) do cotovelo + exercício, padronizados (resumo). Dose (séries, repetições, carga, frequência, sessões em 3 semanas, exercício em casa): **[texto completo]**.

## Comparador

"Esperar para ver" (n = 57), usado para verificar se a regra prediz melhora também sem tratamento: não predisse (resumo).

## Desfechos

- Referência: "melhora" x "sem melhora" relatada em 3 semanas (resumo). Escala e ponto de corte que definem "melhora" (provável escala de mudança global): **[texto completo]**.

## Resultado principal

- Regra final: idade < 49 anos (+LR 2,6), força de preensão sem dor no lado afetado > 112 N (+LR 2,3) e no lado não afetado < 336 N (+LR 2,1) (resumo).
- Probabilidade de melhora: de 79% (pré-teste) para 100% com os três critérios positivos (resumo). Quantos pacientes tinham os três: **[texto completo]**.
- A regra não predisse o resultado no "esperar para ver" (resumo).
- Acurácia de cada critério (Tab. 2, print):

| Critério | Sensibilidade (IC 95%) | Especificidade (IC 95%) | +LR (IC 95%) | Prob. pós-teste | % que preenche |
|---|---|---|---|---|---|
| Idade < 49 anos | 0,61 (0,46 a 0,74) | 0,77 (0,46 a 0,94) | 2,6 (0,96 a 7,3) | 91% | 53% |
| Preensão sem dor afetado > 112 N | 0,53 (0,38 a 0,67) | 0,77 (0,46 a 0,93) | 2,3 (0,82 a 6,4) | 90% | 47% |
| Preensão sem dor não afetado < 336 N | 0,49 (0,35 a 0,63) | 0,77 (0,46 a 0,94) | 2,1 (0,76 a 6,0) | 89% | 44% |
| Ganho de preensão com MWM > 25% | 0,75 (0,58 a 0,87) | 0,5 (0,20 a 0,80) | 1,5 (0,78 a 2,9) | 85% | 52% |

- Rodapé do print: a probabilidade pós-teste foi calculada com a +LR assumindo pré-teste de 79%. Conferência (**calculado**): chance pré-teste 0,79/0,21 = 3,76; × 2,6 = 9,8; probabilidade 9,8/10,8 = 91% (bate).
- Leitura crítica: **os quatro IC da +LR incluem 1** (0,96 a 7,3; 0,82 a 6,4; 0,76 a 6,0; 0,78 a 2,9). Nenhum critério isolado tem acurácia estatisticamente demonstrada; o salto para 100% com os três vem de poucos pacientes. E como a melhora em 3 semanas já é de 79% sem regra, mesmo um "negativo" na regra continua com probabilidade alta de melhorar.
- Leitura da preensão: o critério "lado não afetado < 336 N" diz que quem tem o lado bom mais fraco responde melhor; junto com "lado afetado > 112 N", aponta para uma razão afetado/não afetado mais alta (menos déficit relativo). Esta é uma interpretação; o artigo não testa a razão (resumo).

## Risco de viés (PROBAST)

| Domínio | Julgamento | Motivo, com página |
|---|---|---|
| Participantes | algumas preocupações | dados de ensaio, com critérios de inclusão de ensaio (resumo) |
| Preditores | baixo | idade e dinamometria são objetivas; examinador cego **[texto completo]** |
| Desfecho | algumas preocupações | melhora autorrelatada em 3 semanas, desfecho curto (resumo); definição **[texto completo]** |
| Análise | alto | ~13 eventos "sem melhora" (**calculado**) para vários candidatos; seleção univariada (p<0,15) e passo a passo; pontos de corte por ROC na mesma amostra; sem validação interna ou externa (resumo) |

Global: alto risco de viés (regra em fase de derivação, sobreajuste provável). Os próprios autores pedem validação (resumo).

## Certeza da evidência

Muito baixa para usar a regra na decisão: derivação post hoc, IC das +LR cruzando 1, sem validação publicada neste artigo. Validação posterior, se existir: buscar (não está nos selecionados).

## Aplicabilidade à clínica

A força de preensão sem dor é medida de rotina na ILLIC e é o instrumento que a aula 1 quer ensinar. A regra não deve decidir quem recebe MWM e exercício; serve para discutir o que torna um preditor útil.

## O que muda na conduta

1. Meça a preensão sem dor nos dois lados e registre em newtons: foi a medida que entrou duas vezes na regra (> 112 N afetado, < 336 N não afetado; resumo).
2. Não negue MWM e exercício a quem "falha" na regra: 79% melhoraram em 3 semanas no geral, e nenhum critério isolado tem +LR com IC acima de 1 (Tab. 2, print).
3. Use a Tab. 2 como exercício de leitura de razão de verossimilhança com a turma (pré-teste 79% → pós-teste 91% com +LR 2,6; conta acima).

## Figuras e tabelas que valem slide

| Rótulo | Página | O que ensina | Como usar |
|---|---|---|---|
| Table 2 | **[texto completo]** | +LR com IC que cruzam 1; pós-teste a partir de 79% | Redesenhar como tabela nativa (3 critérios da regra, +LR com IC, pós-teste), "Adaptado de Vicenzino 2009, Tab. 2", destacando os IC; o print é reserva (ver catálogo) |

Reservas da aula base registradas no catálogo: `Vicenzino2009_aulabase_s038_tab2` (1114×268 px, faixa larga de texto pequeno: não serve para slide inteiro) e `Vicenzino2009_aulabase_s038_cabecalho` (rejeitada; não é figura).

## Citações textuais

- "Probability of improvement rose from 79 to 100% if all three were positive." (resumo)
- "This post hoc analysis has created a Level IV CPR that with further validation will help practitioners identify responders." (resumo)

## Pendências de verificação

- Tudo marcado **[texto completo]**: ensaio de origem, características da amostra, dose do MWM e do exercício, definição de melhora, quantos tinham os três critérios, página da Tab. 2.
- Divergência de n: 64 no resumo x 62 nas notas da aula base (que seguem a diretriz).
- Conferir no PDF os IC da Tab. 2 (lidos de print).
- Buscar se a regra foi validada depois (fora dos selecionados).
