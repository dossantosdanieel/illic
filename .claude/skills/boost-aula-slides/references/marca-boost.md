# Marca Boost Education (illic ACADEMY · BOOST Education)

Medidas tiradas do XML do deck de referência "Caso Marina" (32 slides, 80 min). Estão codificadas em
`scripts/_marca.py`; mude lá, nunca slide a slide. Unidades: polegadas para posição e tamanho, pontos
para tipografia.

## O que é fixo

### Página e grade

| Item | Valor |
|---|---|
| Formato | 16:9, 13,333 × 7,5 pol |
| Margem esquerda | 0,889 pol; largura útil 11,556 pol (borda direita do conteúdo em 12,445) |
| Olho (eyebrow) | y = 0,889; altura 0,228 |
| Título | y = 1,186; altura de uma linha 0,475 |
| Corpo | começa em y = 1,939 (desce 0,447 por linha extra de título) |
| Limite do corpo | y = 6,55: nada passa daqui (logo e fonte ficam embaixo) |
| Logo no rodapé (claro e escuro) | x 0,889, y 6,833, 2,194 × 0,278 |
| Logo na capa | no topo: x 0,889, y 0,889, 3,069 × 0,389 |
| "Fonte: ..." | caixa x 3,861, y 6,856, 8,583 × 0,228, alinhada à direita |
| Pílula de interação | y 0,792, altura 0,35, encostada na borda direita do conteúdo (12,445) |
| Vão entre cartões | 0,167 a 0,194 pol |
| Cantos dos cartões | raio constante de ~0,083 pol (6 pt), qualquer que seja o tamanho do cartão |

### Tipografia

Fonte única: **Lato**, regular e bold. Sem itálico, sem sublinhado, sem sombra.

| Elemento | Tamanho | Entrelinha | Estilo |
|---|---|---|---|
| Título da capa | 48 pt | 55,2 pt | regular + palavra-chave em bold, cor F7F9FA |
| Pergunta grande (fundo escuro) | 36 pt | 41,4 pt | idem |
| Título de slide claro | 28 pt | 32,2 pt | regular + **uma** palavra-chave em bold, cor 141A1A |
| Subtítulo da capa, instrução de pergunta | 18 pt | 24,3 pt | lavanda C7D0EE |
| Corpo de enquete e de lista numerada | 16 pt | 20,8 pt | |
| Corpo de cartão, faixa, tópicos | 14 pt | 19,6 pt | termo inicial em bold ("**Entrega:** ...") |
| Texto secundário, legenda, fonte, referências | 12 pt | 15,6 pt | |
| Olho e pílula | 12 pt bold, caixa alta | 14,4 pt | espaçamento entre letras 1,5 pt (olho) e 1 pt (pílula) |
| Número grande de cartão | 48 pt bold | 55,2 pt | petróleo 007A99 (branco no cartão marinho) |
| Letra A–D da enquete | 36 pt bold | 41,4 pt | petróleo |
| Número de lista | 22 pt bold (tarefa), 28 pt bold (cartões) | | petróleo |

O título destaca em bold a palavra que carrega a ideia, quase sempre a última: "O que os números
**dizem**", "Fase aguda e a **semana** dela", "A rotação lateral quase não **subiu**. Por quê?".

### Cores

| Nome | Hex | Uso |
|---|---|---|
| marinho | 202081 | fundo da capa e das perguntas; cabeçalho de tabela; cartão de destaque; faixas "Entrega"/"Combinado"; série principal dos gráficos |
| marinho escuro | 1D1D69 | borda do cabeçalho de tabela |
| petróleo | 007A99 | olho em fundo claro; letras A–D; números; pílula em fundo claro; cartão da fala em fundo escuro |
| ciano claro | 7FD4EA | pílula e olho em fundo escuro; olho dentro de cartão marinho |
| ciano | 009AC0 | barra de acento curta (0,833 × 0,042) acima do título escuro; terceira série de gráfico |
| lavanda | C7D0EE | texto secundário em fundo escuro |
| fundo | F7F9FA | fundo dos slides claros; texto em fundo escuro |
| cartão | EAEFF2 | cartões cinza |
| borda | D5DDE2 | borda de cartão branco (0,5 pt) |
| borda de tabela | CBCBCB | linhas internas de tabela (1 pt) |
| texto | 141A1A | texto principal |
| texto 2 | 4B5358 | texto secundário, olho de gráfico |
| texto da fonte | 5A5F63 | "Fonte: ..." |
| cinza de gráfico | 8A949A | série de comparação |
| eixo | 7D7D7D | linha de base do gráfico |
| alerta | B23A3A | destaque negativo (barra fora do critério, destaques sobre figuras) |

Ordem das séries em gráfico: marinho, cinza de gráfico, ciano, petróleo, lavanda.

### Fundos e o que vai em cada um

- **Escuro (marinho)**: capa e perguntas grandes, e a fala do revés (`citacao` com `fundo: escuro`).
  Pergunta na metade de baixo, com barra ciano curta 0,29 pol acima; instrução lavanda embaixo; logo
  branco no rodapé (na capa, logo branco no topo e sem rodapé).
- **Claro (F7F9FA)**: todo o resto. Logo escuro no rodapé à esquerda; "Fonte: ..." à direita.

### Componentes

- **Pílula**: retângulo de cantos totalmente arredondados; petróleo com texto branco em fundo claro,
  ciano claro com texto marinho em fundo escuro. Texto "FORMATO · DURAÇÃO" em caixa alta.
- **Cartão cinza** (EAEFF2, sem borda): opções de enquete, cartões numerados, pontos "o que olhar".
- **Cartão branco com borda** (FFFFFF, borda D5DDE2 0,5 pt): "Quem:", "Leitura:", dado novo, fala.
- **Cartão marinho**: destaque (a resposta revelada, o número que importa, "O que ela quer").
- **Faixa marinho de largura total**: "**Combinado:** ...", "**Entrega:** ...", "**Para segunda-feira:** ...".
- **Tabela**: cabeçalho marinho com texto branco bold 12 pt, primeira coluna em marinho, linhas brancas
  com borda CBCBCB 1 pt, margens 0,15 × 0,08 pol.
- **Gráfico**: sem título, sem eixo de valores nas barras, rótulos de valor em bold, linha de base 7D7D7D
  de 1 pt, legenda desenhada como quadradinho 0,167 pol + nome em 12 pt, olho cinza acima ("EM KG").
  No deck de referência os gráficos eram formas desenhadas; aqui são **gráficos nativos** (editáveis no
  PowerPoint, com os dados dentro), no mesmo visual.
- **Etapas**: cartões com seta marinho de 1,5 pt entre eles; o último passo em marinho.

## O que pode variar

- Quantidade de cartões, colunas e passos; largura relativa de colunas de tabela.
- Qual cartão é o destaque marinho (um por slide, no máximo dois).
- Cor de destaque sobre figuras de artigo (alerta, marinho, ciano ou petróleo), desde que distinguível
  das cores da própria figura.
- Fundo escuro em um slide de fala (revés), além da capa e das perguntas.
- Redução controlada de texto (até 3 pt, com piso) quando o conteúdo não cabe: o script avisa. Se
  precisar reduzir, primeiro corte palavras.

## O que nunca fazer

- Outra fonte, outra cor fora da tabela, gradiente, sombra, foto decorativa, clip-art, ícones de banco.
- Logo distorcido, recolorido ou em outra posição.
- Texto sobre a figura do artigo (exceto destaques e rótulos curtos).
- Título em caixa alta ou centralizado; corpo centralizado.
- Pílula com nome de formato fora dos canônicos.

## Render local

Lato não está instalada neste ambiente: o LibreOffice renderiza com Inter ou DejaVu, um pouco mais
largas. A diagramação confere, o desenho das letras não. O .pptx sempre pede Lato; no computador do
Daniel, com Lato instalada, o texto ocupa um pouco menos espaço. O medidor de texto usa a fonte mais
larga disponível, então o erro fica do lado seguro (nada vaza).

Os logos estão em `assets/logo_sobre_claro.png` (logo escuro, para fundo claro) e
`assets/logo_sobre_escuro.png` (logo branco, para fundo marinho).
