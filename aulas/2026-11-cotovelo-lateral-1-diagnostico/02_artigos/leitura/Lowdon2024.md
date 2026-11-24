# Ficha de leitura — Lowdon2024 (Lowdon et al., 2024)

> **Base: só resumo — conferir no texto completo.** Ficha escrita a partir do resumo do PubMed (PMID 38678448),
> copiado em `01_busca/registros.json` e conferido com a API do PubMed (efetch) em 24/11/2026. Artigo pago
> (Elsevier, "All rights reserved" no PubMed), sem PDF aberto encontrado pelo baixador; aguardando o PDF em
> `02_artigos/manual/` (`02_artigos/pendentes.md`, item 26). O OpenAlex aponta uma versão "green" no repositório
> institucional da Edge Hill University (`url_oa` em `01_busca/registros.json`, licença cc-by-nc-nd informada pelo
> OpenAlex); não foi baixada nem conferida: é um caminho legal para o usuário obter o manuscrito aceito.
> Campos marcados com **[texto completo]** ficaram em branco de propósito. Sem imagem de reserva na aula base.

- Citação: Lowdon H, Chong HH, Dhingra M, Gomaa AR, Teece L, Booth S, Watts AC, Singh HP. Comparison of interventions for lateral elbow tendinopathy: a systematic review and network meta-analysis for Patient-Rated Tennis Elbow Evaluation pain outcome. J Hand Surg Am. 2024;49(7):639-648. · DOI 10.1016/j.jhsa.2024.03.007 · PMID 38678448
- Texto lido: só resumo
- Papel na aula: aula 2, contraponto. Meta-análise em rede que coloca exercício, corticoide, agulhamento, sangue autólogo e outros contra controle/placebo num mesmo desfecho (PRTEE dor) e conclui que nada acelera a melhora da dor de forma convincente.
- Licença do PDF: todos os direitos reservados na versão da editora (PubMed: "Copyright © 2024 American Society for Surgery of the Hand. Published by Elsevier Inc. All rights reserved."); a versão do repositório seria cc-by-nc-nd segundo o OpenAlex (não conferido).

## Pergunta

Em pessoas com tendinopatia lateral do cotovelo, qual tratamento reduz mais a dor do PRTEE comparado com controle/placebo, combinando evidência direta e indireta, no curto prazo (até 6 semanas) e no médio prazo (> 6 semanas a 6 meses)? (resumo)

## Desenho

Revisão sistemática com meta-análise em rede (efeitos aleatórios) de ECR que relataram a subescala de dor do PRTEE (resumo). Bases, data da busca, registro do protocolo, ferramenta de risco de viés: **[texto completo]**.

## Análise

- Rede com efeitos aleatórios; evidência direta e indireta combinada (resumo). Abordagem (frequentista ou bayesiana), checagem de incoerência, transitividade, ranking (SUCRA ou P-score), GRADE/CINeMA: **[texto completo]**.
- 13 estudos para 12 nós (incluindo controle/placebo) (resumo): menos de um estudo e meio por tratamento. A maioria das ligações deve depender de um único ensaio pequeno. Mapa da rede: **[texto completo]**.
- O nó "control/placebo" junta controle sem tratamento e placebo (resumo): se reúne esperar para ver, injeção de soro e órtese simulada, a transitividade fica em dúvida.

## Amostra

- 13 ECR, 12 comparadores (resumo). Nº de participantes, idade, duração dos sintomas: **[texto completo]**.
- Critério de inclusão restritivo: só ensaios que relataram a dor do PRTEE (resumo). Isso exclui muitos ensaios de exercício e de corticoide que usaram EVA ou PRTEE total; a rede não representa toda a evidência.

## Intervenção (com dose)

- Fisioterapia/exercício, corticoide, agulhamento seco, sangue autólogo e outros (resumo cita só esses). Lista dos 12 nós e dose de cada um: **[texto completo]**.

## Comparador

Controle/placebo (resumo). Composição exata do nó: **[texto completo]**.

## Desfechos

- Único: subescala de dor do PRTEE (resumo). A aula base trata as subescalas do PRTEE em escala de 0 a 50 (notas dos slides 41–42); confirmar no texto completo que a rede usou essa escala.
- Curto prazo: até 6 semanas; médio prazo: > 6 semanas a 6 meses (resumo). Longo prazo não analisado.

## Resultado principal

- Curto prazo: nenhum tratamento melhorou a dor do PRTEE de forma significativa contra controle/placebo (resumo). Estimativas e IC por tratamento: **[texto completo]**.
- Médio prazo: fisioterapia/exercício x placebo, DM −4,32 (IC 95% −7,58 a −1,07) pontos na dor do PRTEE (resumo).
- Corticoide, agulhamento seco e sangue autólogo "exhibited potential treatment effects", com "pitfalls" (resumo). Números e quais armadilhas (para o corticoide, provavelmente a recidiva tardia; confirmar): **[texto completo]**.
- DMCI: o resumo não informa. Poltawski2011 dá 7 a 11 pontos para o PRTEE total (0–100) (`leitura/Poltawski2011.md`); não há DMCI conferida para a subescala de dor. Não dividir a DMCI do total por 2 sem fonte.
- Calculado por mim: se a escala for 0–50, 4,32 pontos = 8,6% da escala (4,32 / 50); IC de 2,1% a 15,2% (1,07 / 50 a 7,58 / 50). Diferença real e pequena.
- Eventos adversos: **[texto completo]**.

## Risco de viés (AMSTAR 2 mais transitividade e incoerência)

| Domínio | Julgamento | Motivo |
|---|---|---|
| Protocolo registrado antes | não avaliável | **[texto completo]** |
| Busca abrangente | não avaliável | **[texto completo]** |
| Seleção pelo desfecho | preocupação | só entram ensaios que relataram a dor do PRTEE (resumo) |
| Risco de viés dos estudos considerado | não avaliável | **[texto completo]** |
| Transitividade | preocupação | nó "control/placebo" mistura condições diferentes (resumo) |
| Incoerência entre evidência direta e indireta | não avaliável | **[texto completo]** |
| Imprecisão | alta | 13 estudos pequenos para 12 nós; os próprios autores pedem cautela (resumo) |

Global: confiança baixa; o próprio resumo diz que poucos estudos pequenos e escassez de dados pedem cautela.

## Certeza da evidência

O resumo não diz se aplicou GRADE ou CINeMA. Pelas limitações declaradas (poucos estudos pequenos), certeza baixa a muito baixa (meu julgamento).

## Aplicabilidade à clínica

É a frase que o paciente precisa ouvir no primeiro dia: nenhum tratamento acelera claramente a melhora da dor nas primeiras 6 semanas; o exercício tem a única vantagem estatística no médio prazo, e ela é pequena. Não serve para escolher entre técnicas (rede esparsa) nem para prazos acima de 6 meses.

## O que muda na conduta

1. Diga ao paciente que nenhum tratamento mostrou melhora mais rápida da dor nas primeiras 6 semanas contra controle/placebo (resumo) e combine a expectativa de melhora gradual.
2. Mantenha o exercício como base do plano: é o único com benefício estatístico no médio prazo, DM −4,32 (IC −7,58 a −1,07) na dor do PRTEE (resumo), pequeno (calculado: cerca de 9% da escala, se 0–50).
3. Não use o ranking da rede para escolher agulhamento, sangue autólogo ou corticoide: o resumo aponta "pitfalls" e dados escassos.

## Figuras e tabelas que valem slide

| Rótulo | Página | O que ensina | Como usar |
|---|---|---|---|
| Mapa da rede (**[texto completo]**) | ? | Quantas ligações dependem de um estudo só | Recortar a 300 dpi quando o PDF chegar; licença reservada na versão da editora |
| Forest plot da rede contra controle/placebo no médio prazo (**[texto completo]**) | ? | Só o exercício tem IC fora do zero, e por pouco | Redesenhar "Adaptado de" com 4–5 tratamentos |

## Para a aula em camadas

- Âncora para iniciante: o que é comparação indireta (A x C e B x C permitem estimar A x B) e por que ela vale menos que a direta.
- Desafio avançado: 13 estudos para 12 tratamentos, e só entram os que mediram a dor do PRTEE. Que viés isso cria, e o que acontece com a transitividade quando "controle" e "placebo" viram um nó só?

## Citações textuais

- "Patients should be informed that there is currently no strong evidence that any treatment produces more rapid improvement in pain symptoms when compared with control/placebo in the short and medium terms." (resumo)
- "The limited number of small studies and paucity of data call for caution in interpreting the results and need for further evidence." (resumo)

## Pendências de verificação

- Escala da subescala de dor do PRTEE usada (0–50?) e DMCI adotada; sem isso, o cálculo de 8,6% fica condicional.
- Lista dos 12 nós, mapa da rede, estimativas de curto e médio prazo por tratamento, ranking, incoerência, GRADE/CINeMA.
- Quais são as "pitfalls" de corticoide, agulhamento seco e sangue autólogo.
- Obter o manuscrito aceito pelo repositório da Edge Hill (link no registro) ou o PDF da editora pelo acesso institucional; conferir a licença da versão de repositório.
