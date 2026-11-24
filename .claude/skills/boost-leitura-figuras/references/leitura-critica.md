# Leitura crítica: a ficha e como ler os gráficos

O leitor final é fisioterapeuta experiente. A ficha não resume o artigo: ela decide **o que da
conduta muda** e **com que confiança**. Tudo o que entrar em slide sai daqui, com página.

## Índice

1. Regras da ficha
2. Campos da ficha
3. Ferramenta de risco de viés por desenho
4. Tamanho de efeito diante da diferença mínima clinicamente importante
5. Como ler (e ensinar) forest plot
6. Como ler curva de sobrevida
7. Como ler gráfico de dispersão
8. Conversões entre medidas, sem errar
9. Erros de leitura que mais aparecem em aula

## 1. Regras da ficha

- Uma ficha por artigo, em `02_artigos/leitura/<chave>.md`, a partir de `assets/ficha_leitura_modelo.md`.
- Leia o texto completo (`02_artigos/texto/<chave>.md`), não só o resumo. Resumo e texto divergem
  com frequência no desfecho primário e no tamanho do efeito.
- Todo número leva a origem: `(p.6, Tab. 2)` ou `(p.5, Fig. 4)`. Página é a do PDF, a mesma do
  arquivo de texto.
- Número que você calculou (NNT, conversão de DMP) fica marcado como **calculado**, com a conta.
- O que não foi possível conferir fica escrito: `não conferido no texto completo` ou
  `só no resumo`. A aula declara isso nas notas do slide de referências.
- Números de tabela: confira na miniatura da página ou no recorte. A extração de texto de
  tabelas embaralha colunas com facilidade.
- Citações textuais: curtas (até duas linhas), no idioma original, entre aspas, com página.
  Servem para o slide quando a frase do autor é a evidência (definição, recomendação, limite).

## 2. Campos da ficha

| Campo | O que registrar |
|---|---|
| Pergunta | PICO em uma frase. Se for diagnóstico ou prognóstico, use PIRD ou PEO. |
| Desenho | Um dos desenhos do registro, mais o que o qualifica: paralelo ou cruzado, superioridade ou não inferioridade, número de centros, registro prospectivo (número) ou não. |
| Amostra | n randomizado e n analisado por grupo; critérios que definem a quem o resultado se aplica (idade, tempo de sintoma, nível esportivo, tratamento prévio); perdas por grupo. |
| Intervenção com dose | Exercício se descreve por dose: tipo, carga (% 1RM, RPE, dor permitida), séries × repetições, tempo sob tensão, frequência semanal, duração, progressão e critério de progressão, supervisão, adesão medida. Se o artigo não informa, escreva `não informado`: é achado de qualidade (TIDieR, CERT). |
| Comparador | A mesma descrição de dose. Compare o que diferiu de fato entre os grupos (volume total, atenção do terapeuta, expectativa). |
| Desfechos | Primário (instrumento, direção da escala, tempo) e secundários. Marque se o primário do artigo é o do registro. |
| Resultado principal | Diferença **entre grupos** com IC 95% e p, no tempo do desfecho primário. Depois compare com a DMCI (seção 4). Mudança dentro do grupo não é efeito do tratamento. |
| Risco de viés | Com a ferramenta do desenho (seção 3), domínio a domínio, em uma linha cada, e julgamento global. |
| Certeza da evidência | GRADE quando houver corpo de evidência (revisão, diretriz); para um estudo isolado, diga o que limita a confiança (viés, imprecisão, evidência indireta). |
| Aplicabilidade | Para quem da clínica isto vale: o paciente típico da ILLIC entraria no estudo? O que falta para aplicar (equipamento, supervisão, tempo)? |
| O que muda na conduta | Uma a três frases no imperativo, cada uma presa a um número. Se nada muda, diga isso. |
| Figuras e tabelas que valem slide | Rótulo, página, o que ensina, e se o melhor é reproduzir, recortar um painel ou redesenhar. |
| Citações textuais | Até três, com página. |
| Pendências de verificação | O que ficou sem conferir e por quê. |

## 3. Ferramenta de risco de viés por desenho

Use a ferramenta certa e nomeie-a na ficha. Escala de pontos resume; domínio explica.

| Desenho | Ferramenta | O que costuma decidir em fisioterapia |
|---|---|---|
| ECR | RoB 2 (cinco domínios) | Desfecho relatado pelo paciente sem cegamento; perdas desiguais; desvio do protocolo de exercício; desfecho trocado em relação ao registro |
| ECR, triagem rápida | PEDro (0 a 10) | Serve para ordenar, não para julgar: não pesa os itens nem avalia relato seletivo |
| Não randomizado de intervenção | ROBINS-I | Confusão por indicação; seleção de quem recebeu o tratamento |
| Coorte e caso-controle | Newcastle-Ottawa ou listas JBI | Comparabilidade dos grupos; seguimento |
| Fator prognóstico | QUIPS | Atrito e ajuste para confundidores |
| Modelo de predição | PROBAST | Sobreajuste; validação externa ausente |
| Acurácia diagnóstica | QUADAS-2 | Padrão de referência imperfeito; espectro de pacientes; teste lido sabendo o diagnóstico |
| Revisão sistemática | AMSTAR 2 (qualidade) ou ROBIS (viés) | Protocolo registrado; busca; risco de viés usado na síntese; heterogeneidade explicada |
| Meta-análise em rede | AMSTAR 2 mais transitividade e incoerência (CINeMA) | Comparações indiretas dominando a rede; ranking (SUCRA) sem olhar a certeza |
| Diretriz | AGREE II | Rigor do desenvolvimento; independência editorial |
| Propriedades de medida | COSMIN | Erro de medida diante da DMCI |
| Relato da intervenção | TIDieR, CERT | Dose replicável ou não |

Certeza do corpo de evidência: GRADE (risco de viés, inconsistência, evidência indireta,
imprecisão, viés de publicação). Uma revisão que não aplica GRADE deixa a certeza por sua conta:
diga isso na ficha.

## 4. Tamanho de efeito diante da diferença mínima clinicamente importante

A pergunta do slide é sempre a mesma: **o intervalo de confiança da diferença entre grupos está
de que lado da DMCI?**

| Situação | Leitura |
|---|---|
| IC inteiro acima da DMCI | Efeito importante, com boa precisão |
| Estimativa acima, IC cruza a DMCI | Provavelmente importante, impreciso |
| IC exclui zero, mas fica abaixo da DMCI | Diferença real e pequena: estatisticamente significativa, clinicamente discutível |
| IC cruza zero e a DMCI | Inconclusivo: não é prova de ausência de efeito |
| IC inteiro abaixo da DMCI, em torno de zero | Tratamentos equivalentes para fins práticos |

Cuidados:

- A DMCI foi derivada para mudança **individual** ao longo do tempo. Usá-la para a diferença
  **entre grupos** é convenção; diga isso. Alguns autores usam a metade como limiar entre grupos.
- Prefira o valor que o próprio artigo ou a diretriz da área adota, com a referência. A DMCI
  muda com a população, o valor de base e o método (âncora ou distribuição).
- Complemente com análise de respondedores quando houver: proporção que atingiu a DMCI em cada
  grupo, e daí o NNT.
- Mudança dentro de cada grupo inclui história natural, regressão à média e efeito de contexto.
  O efeito do tratamento é a diferença entre os grupos.

Valores usados com frequência, para orientar e não para citar sem conferir a fonte:

| Instrumento | Valor usual | Fonte a conferir |
|---|---|---|
| Escala numérica de dor (0 a 10) | 2 pontos ou 30% | Farrar 2001; Ostelo 2008 |
| Oswestry (0 a 100) | 10 pontos ou 30% | Ostelo 2008 |
| VISA-P (0 a 100) | 13 pontos | Hernandez-Sanchez 2014 |
| LEFS (0 a 80) | 9 pontos | Binkley 1999 |
| DASH (0 a 100) | cerca de 10 pontos | Franchignoni 2014 |

## 5. Como ler (e ensinar) forest plot

Leia nesta ordem, e ensine nesta ordem:

1. **Eixo e direção.** Que medida está no eixo (DM, DMP, RR, OR, HR) e para que lado fica o
   favorecimento. Os rótulos "Favours" ficam embaixo, e autores invertem. Erro de direção é o
   mais comum em aula.
2. **Linha de nulidade.** Zero para diferenças; um para razões (o eixo é logarítmico).
3. **Cada estudo.** O quadrado é a estimativa; o tamanho é o peso; a linha é o IC 95%. Estudo
   pequeno tem linha longa e quadrado pequeno.
4. **O losango.** O centro é a estimativa combinada; a largura é o IC. Se toca a nulidade, não
   há diferença estatisticamente demonstrada.
5. **Heterogeneidade.** I² diz quanto da variação entre estudos não é acaso; não diz o tamanho da
   dispersão. Para isso olhe tau² e, quando houver, o intervalo de predição, que mostra onde o
   efeito de um novo estudo (ou do seu serviço) deve cair. Com poucos estudos, I² é instável.
6. **Modelo.** Efeitos aleatórios dão mais peso relativo aos estudos pequenos. Confira se a
   conclusão muda com efeito fixo.
7. **Unidade de análise.** O mesmo estudo aparecendo em várias linhas (letras A, B, C) com o
   mesmo grupo controle conta os participantes mais de uma vez e estreita o IC de forma indevida.
8. **Tradução clínica.** DMP não é intuitiva: converta para a unidade de um instrumento conhecido
   (seção 8) e compare com a DMCI.

Para o slide: destaque um estudo, o losango e a linha de nulidade, nessa sequência. Pergunta boa
para enquete: "Para que lado está o favorecimento?" antes de mostrar a resposta.

## 6. Como ler curva de sobrevida

Aparece em retorno ao esporte, recidiva de lesão, tempo até cirurgia.

- **Eixos.** O vertical é a proporção ainda sem o evento (ou a incidência acumulada, que sobe).
  Confira qual das duas, e se o evento é bom (retorno ao esporte) ou ruim (relesão).
- **Degraus.** Cada degrau é um evento. Marcas verticais são censuras: gente que saiu do
  seguimento sem o evento.
- **Números em risco.** A tabela sob o eixo diz quantos sustentam cada trecho. A cauda direita,
  com poucos em risco, é a parte mais vistosa e a menos confiável.
- **Mediana.** O tempo em que a curva cruza 50%. Se não cruza, a mediana não foi atingida.
- **Hazard ratio.** Razão de taxas instantâneas, média ao longo do seguimento. Não é risco
  relativo e não diz quanto tempo se ganha. Curvas que se cruzam violam a proporcionalidade, e um
  HR único esconde isso.
- **Para decidir.** Leia a diferença absoluta em um tempo que importa (por exemplo, livre de
  relesão aos 12 meses) e, se couber, a diferença de medianas.
- **Risco competitivo.** Quem operou não pode mais "retornar sem cirurgia". Kaplan-Meier
  superestima a incidência quando há evento competitivo; o adequado é incidência acumulada.

## 7. Como ler gráfico de dispersão

- **O que é cada ponto.** Pessoa, membro, estudo? Correlação entre médias de estudos não vale
  para indivíduos (falácia ecológica).
- **r e r².** r mede associação linear; r² é a fração da variância explicada. r = 0,5 explica
  25%. Com n pequeno, o IC de r é largo: peça o IC.
- **Inclinação.** É ela que responde "quanto muda Y por unidade de X". Correlação alta com
  inclinação irrelevante não muda conduta.
- **Pontos influentes.** Um ou dois pontos extremos podem fabricar a reta. Cubra-os com o dedo.
- **Faixa de valores.** Restringir a amostra (só atletas de elite) achata a correlação;
  extrapolar além da faixa observada não tem base.
- **Mudança contra valor inicial.** Correlação entre o valor de base e a mudança é em parte
  artefato (acoplamento matemático e regressão à média).
- **Concordância não é correlação.** Para comparar dois métodos de medida, o gráfico certo é
  Bland-Altman: viés médio e limites de concordância, comparados com a DMCI.
- **Causalidade.** Dispersão de estudo transversal não sustenta "aumentar X melhora Y".

## 8. Conversões entre medidas, sem errar

Marque na ficha todo valor convertido como **calculado**, com a fórmula e os valores de entrada.
Φ é a distribuição normal padrão acumulada.

**Risco, redução absoluta e NNT**

- RAR = risco no controle − risco no tratamento. NNT = 1 / RAR, arredondado para cima.
- A partir do RR: RAR = risco no controle × (1 − RR).
- O NNT depende do risco de base e do tempo de seguimento. Informe os dois: "NNT 7 em 12 meses,
  para risco de base de 40%". O mesmo RR em população de risco menor dá NNT maior.
- IC do NNT: inverta os limites do IC da RAR. Se o IC da RAR cruza zero, o IC do NNT passa pelo
  infinito (de benefício a dano): não apresente só o número.

**OR para RR** (com o risco no controle p0)

- RR = OR / (1 − p0 + p0 × OR).
- OR só se aproxima do RR quando o evento é raro (até cerca de 10%). Com evento comum, ler OR
  como RR exagera o efeito.
- Exemplo: p0 = 0,40 e OR = 0,50. RR = 0,50 / (1 − 0,40 + 0,40 × 0,50) = 0,50 / 0,80 = 0,625.
  Risco no tratamento = 0,25. RAR = 0,15. NNT = 6,7, que se arredonda para 7.

**DMP (d de Cohen, g de Hedges)**

- Para unidades de um instrumento: DM ≈ DMP × DP de referência (o DP de base de um estudo
  representativo). Exemplo: DMP 0,42 com DP de 15 pontos no VISA-P equivale a cerca de 6 pontos,
  menos que a DMCI de 13.
- Probabilidade de superioridade: Φ(d / √2). Para d = 0,42: Φ(0,30) = 0,62. Em 62% dos pares, a
  pessoa tratada está melhor que a do controle.
- Para OR: ln(OR) = d × π / √3, ou seja, d × 1,81. Para d = 0,42: OR = e^0,76 = 2,1.
- Para NNT (Furukawa), com a taxa de resposta do controle (TRC):
  NNT = 1 / [Φ(d + Φ⁻¹(TRC)) − TRC].
  Exemplo: d = 0,42 e TRC = 30%. Φ⁻¹(0,30) = −0,52; somando 0,42 dá −0,10; Φ(−0,10) = 0,46;
  0,46 − 0,30 = 0,16; NNT = 6,3, que se arredonda para 7.
- Os rótulos "pequeno, médio, grande" (0,2; 0,5; 0,8) são convenção sem base clínica. Prefira a
  comparação com a DMCI.
- O sinal da DMP depende da direção da escala e de quem foi subtraído de quem. Confira antes de
  dizer quem ganhou.

**Dispersão e precisão**

- IC 95% de uma diferença = estimativa ± 1,96 × EP.
- DP = EP × √n. Barras de erro com EP parecem mais apertadas que com DP: leia a legenda.
- DP a partir do IC 95% de uma média: DP = √n × (limite superior − limite inferior) / 3,92
  (para n pequeno, troque 3,92 por 2 × t).
- Mediana e intervalo interquartil não viram média e DP sem supor normalidade: se converter,
  declare.
- O DP da mudança não é o DP do valor final: depende da correlação entre pré e pós. Não misture.

**Outros**

- Hazard ratio não é risco relativo.
- "Reduziu 50%" (relativo) e "reduziu 5 pontos percentuais" (absoluto) são frases diferentes.
  No slide, dê sempre o absoluto.
- Sensibilidade e especificidade viram razões de verossimilhança: RV+ = sens / (1 − espec);
  RV− = (1 − sens) / espec. Probabilidade pós-teste: passe por chances (odds), não some
  percentuais.

## 9. Erros de leitura que mais aparecem em aula

- Apresentar a melhora dentro do grupo como efeito do tratamento.
- Tratar p > 0,05 como "não funciona" quando o IC inclui efeito importante.
- Ler o ranking de uma meta-análise em rede sem olhar a certeza de cada comparação.
- Aceitar a análise por protocolo como principal em estudo de superioridade.
- Generalizar de atleta jovem para o paciente sedentário de 55 anos (ou o contrário).
- Ignorar a dose: "exercício" não é uma intervenção, é uma categoria.
- Desfecho substituto (espessura do tendão, ativação muscular) apresentado como desfecho clínico.
- Muitos desfechos secundários sem correção: um p < 0,05 entre vinte é esperado por acaso.
