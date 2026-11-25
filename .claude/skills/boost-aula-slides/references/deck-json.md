# Esquema do deck.json

O `deck.json` é a única fonte da aula: `montar_deck.py` gera o .pptx a partir dele, `validar_aula.py`
confere o desenho pedagógico e `materiais.py` tira dele as enquetes, o pré/pós-teste e o resumo do aluno.
Há dois exemplos completos, um por formato (`meta.formato`), sobre volta ao esporte depois do LCA:

- `assets/exemplo_expositiva/deck.json`: aula **expositiva com checagens**, 45 min 30 s, em 4 partes, com
  mapa, "onde estamos", exemplo resolvido e parcialmente resolvido, comparação em colunas e caso só como
  aplicação no fim de cada parte. É o ponto de partida quando as preferências pedem expositiva.
- `assets/exemplo/deck.json`: aula **guiada por caso**, 32 min, ciclo prever → ver → decidir → conferir,
  com os outros tipos de slide (salas, revés, desfecho). Para aulas de aplicação ou discussão de casos.

Copie o do formato escolhido como ponto de partida.

Regras de escrita que valem para todos os campos de texto:

- `**negrito**` marca negrito em qualquer texto visível. No título, a marca pede **uma** palavra-chave
  em negrito, normalmente a última ideia ("O que os números **dizem**"). Sem marcação, o script põe em
  negrito a última palavra; use `"titulo_sem_destaque": true` para desligar.
- Uma ideia por slide e até ~70 palavras visíveis (o validador avisa acima de 70 e reprova acima de 100).
  O detalhe vai para `notas`.
- Números com vírgula decimal (38,2%), unidades por extenso na fala e abreviadas no slide.
- Nada de número sem origem: todo slide que afirma evidência tem `fonte`.

## Estrutura geral

```json
{
  "meta": { ... },
  "referencias": [ ... ],
  "slides": [ ... ]
}
```

### meta

| Campo | Obrigatório | O que é |
|---|---|---|
| `titulo` | sim | Título da aula (vai para a capa e para os materiais). Aceita `**negrito**`. |
| `formato` | não | `"expositiva"` (expositiva com checagens, 40 a 50 min) ou `"caso"` (guiada por caso, 30 a 35 min). **Sem o campo, vale `"caso"`**, para os decks antigos continuarem válidos. O validador aplica as regras do formato (ver "Regras por formato", no fim). |
| `partes` | sim, na expositiva | As 3 a 5 partes da aula, na ordem da linha de raciocínio: strings ou `{"titulo", "texto"}` (o texto é a pergunta ou o que a parte responde, em uma linha). Alimentam os slides `mapa` e o "O caminho da aula" do resumo do aluno. |
| `subtitulo` | não | Uma linha na capa: o que a turma vai decidir. |
| `autor` | não | Apresentador; padrão da casa: "Daniel Santos". |
| `slug` | sim | Nome do arquivo .pptx (`<slug>.pptx`). |
| `publico` | não | Para quem é a aula. |
| `duracao_alvo_min` | não | Só informativo; a duração real é a soma de `tempo_s`. |
| `catalogo` | não | Caminho do `catalogo.json` das figuras, relativo ao deck.json. Padrão: `../03_figuras/catalogo.json`. |
| `caso_ficticio` | não | `true` quando o paciente é inventado; o script declara isso nas notas das referências e no resumo. |
| `objetivos` | sim | 2 ou 3 objetivos com verbo de decisão (decidir, interpretar, calcular, criticar, escolher, justificar). |
| `propostas_clinicas` | não | Lista do que a aula propõe sem ensaio que teste. Sai nas notas das referências e no resumo do aluno. |
| `resumo.pontos_chave` | sim, para o resumo | 4 a 6 frases com o número e a fonte entre parênteses. |
| `resumo.algoritmo` | sim, para o resumo | Passos de decisão em forma de pergunta e ação ("Menos de 9 meses? Não libera..."). |
| `resumo.para_praticar` | não | 1 a 3 ações para a semana seguinte. |
| `referencias_com_doi` | não | `true` para mostrar DOI também nas referências que têm PMID. |
| `referencias_formato` | não | `auto` (padrão: se alguma referência quebra a linha, todas saem sem volume e páginas, como no deck de referência), `curto` ou `completo`. |

### referencias

Uma entrada por artigo citado em qualquer slide.

```json
{"id": "Grindem2016", "curta": "Grindem et al. 2016",
 "texto": "Grindem H et al. Br J Sports Med 2016;50(13):804-8",
 "pmid": "27162233", "doi": "10.1136/bjsports-2016-096031", "conferido": "texto completo"}
```

- `id` é a chave do contrato de pastas (SobrenomeAno). Nos slides, `fonte` usa o `id`; o rodapé mostra a `curta`.
- `conferido`: `texto completo`, `resumo` ou `nao conferido`. O slide de referências escreve nas notas, a
  partir desse campo, o que foi conferido onde. Seja honesto: se só leu o resumo, é `resumo`.

## Campos comuns a todos os slides

| Campo | O que é |
|---|---|
| `tipo` | Um dos 18 tipos abaixo. |
| `tempo_s` | Tempo previsto do slide em segundos, **incluindo** a interação. Obrigatório, exceto em slides de apoio. |
| `notas` | O que falar e como conduzir, na voz de `voz-das-notas.md`. Não escreva a linha "Tempo:": o script põe `Tempo: 1 min 30 s (acumulado 12:00).` na frente. |
| `interacao` | `{"tipo": "...", "duracao_s": 60}`. Tipos: `enquete`, `chat_cascata`, `salas`, `mao_camera`, `chat`. Opcionais: `inicio_s` (segundos depois do início do slide em que a interação começa), `pedido` (o que a turma faz, em uma frase, para o roteiro de `enquetes.md`), `tamanho` (salas de 2, 3, 4...), `rotulo` (troca o texto da pílula), `gravacao` (o que quem assiste à gravação faz nesse trecho; as salas não aparecem no vídeo do Meet) e `plano_b` (o que fazer se o formato falhar no Meet: sala que não abre, conta sem enquete). Os dois últimos são texto ou lista de frases e geram a seção "Plano B e gravação" do `enquetes.md`; o `materiais.py` avisa quando uma sala não tem os dois (ver `interacoes.md`, salas). A pílula aparece sozinha no canto superior direito. |
| `olho` | Linha pequena em caixa alta acima do título ("Bloco 2 · A evidência"). Uma linha só, antes da pílula: se não couber, é erro de layout (a segunda linha cai em cima do título). |
| `titulo` | Título do slide. Em slides de evidência, a **conclusão** em uma frase, não o assunto. |
| `fonte` | Lista de `id` de referência e/ou textos livres ("degraus: proposta clínica da equipe"). Sai no rodapé, à direita. Texto livre que parece citação (Sobrenome ... 2021) precisa estar em `referencias`. |
| `bloco` | Aula de caso: nome do bloco ("abertura", "tempo e critérios", "fechamento"). O validador confere o ciclo dentro de cada bloco. Na expositiva é opcional e não é usado. |
| `parte` | Aula expositiva: número da parte em `meta.partes` (1, 2, ...). Abertura e fechamento ficam sem. O validador confere, por parte, o "onde estamos" no começo, a síntese no fim, a aplicação, as checagens e a âncora/desafio. |
| `papel` | Caso: `gancho`, `prever`, `evidencia`, `decidir`, `conferir`, `recuperar`, `saida` (torna exata a checagem "pergunta antes da evidência"). Expositiva: `explicar`, `exemplo`, `checar`, `conferir`, `aplicacao` (o caso, no fim da parte; obrigatório em ao menos um slide), `sintese` (fecha a parte), `recuperar`, `saida`. |
| `origem` | `"caso"` quando os números do slide são do paciente fictício (dispensa `fonte`). |
| `evidencia` | `true`/`false` para forçar ou dispensar a exigência de fonte quando a detecção automática errar. |
| `ancora`, `desafio` | Linha "Para começar:" e linha "Desafio:" (slides `pergunta`, `tarefa` e `exemplo`). É assim que a aula atende níveis diferentes sem baixar o nível. |
| `apoio` | `true` tira o slide da contagem do tempo (slide de reserva). |

## Tipos de slide

### capa

Fundo marinho, logo branco no topo, barra ciano curta, título 48 pt (reduz até 36 pt se precisar),
subtítulo lavanda 18 pt, autor em caixa alta ciano. Sem rodapé. Campos: `titulo`, `subtitulo`, `autor`
(os três caem para `meta` se faltarem).

```json
{
  "tipo": "capa",
  "bloco": "abertura",
  "tempo_s": 30,
  "notas": "Aula online de 32 minutos. …"
}
```

### pergunta

A pergunta grande em fundo marinho, na metade de baixo do slide, com a instrução embaixo e a pílula da
interação. É o slide do "prever" e do bilhete de saída. Campos: `pergunta` (ou `titulo`), `instrucao`,
`ancora`, `desafio`, `bilhete_saida` (`true` no último slide da aula).

```json
{
  "tipo": "pergunta",
  "bloco": "tempo e critérios",
  "papel": "prever",
  "olho": "Bloco 1 · Tempo e critérios",
  "titulo": "De cada 10 atletas que voltam ao esporte de pivô **sem passar nos critérios**, quantos se machucam de novo em 2 anos?",
  "instrucao": "Um número de 0 a 10. Escreva e só envie quando eu contar até 3.",
  "tempo_s": 90,
  "interacao": {
    "tipo": "chat_cascata",
    "duracao_s": 60
  },
  "notas": "Interação: chat em cascata. …"
}
```

### enquete

Pergunta + opções A–D em cartões cinza 2 × 2, letra grande em petróleo. Campos: `pergunta`, `opcoes`
(objeto `{"A": ..., "D": ...}` ou lista), `gabarito` (letra sustentada pela evidência, só para as notas e os
materiais), `sem_gabarito: true` para enquete de opinião.

**Variante revelação:** o mesmo slide repetido com `revela` (letra) e `justificativa`. A opção sustentada
fica em cartão marinho com texto branco em negrito; as outras ficam apagadas. Não leva `interacao`. Use
o mesmo texto de opções da enquete original, para o `materiais.py` ligar as duas.

```json
{
  "tipo": "enquete",
  "bloco": "abertura",
  "papel": "gancho",
  "olho": "Agora é com vocês",
  "titulo": "A sua **primeira** resposta",
  "tempo_s": 90,
  "interacao": {
    "tipo": "enquete",
    "duracao_s": 60
  },
  "pergunta": "Você libera o Rafael para a final?",
  "opcoes": {
    "A": "Sim: o hop está em 96% e ele não sente nada.",
    "B": "Não agora: com 9 meses eu libero.",
    "C": "Não: faltam tempo, força de quadríceps e treino com o time.",
    "D": "Depende dele: se está confiante, joga."
  },
  "gabarito": "C",
  "notas": "A primeira decisão da turma, antes de qualquer conteúdo. …"
}
```

```json
{
  "tipo": "enquete",
  "bloco": "tempo e critérios",
  "papel": "conferir",
  "olho": "Bloco 1 · Conferindo o voto",
  "titulo": "Direção forte, precisão **baixa**",
  "tempo_s": 60,
  "pergunta": "Razão de risco 0,16; intervalo de confiança de 95% de 0,02 a 1,20.",
  "opcoes": {
    "A": "Está provado: passar corta o risco em 84%.",
    "B": "Não há efeito: o intervalo cruza o 1.",
    "C": "A direção é de proteção grande; a estimativa é imprecisa.",
    "D": "Nada: o estudo não é randomizado."
  },
  "revela": "C",
  "justificativa": "**O que sustenta:** 1 nova lesão em 18 contra 21 em 55: 33 pontos de diferença. Com um evento só, o intervalo vai de 98% menos a 20% mais.",
  "fonte": [
    "Grindem2016"
  ],
  "notas": "A resposta que o estudo sustenta é a C. …"
}
```

### tarefa

Lista numerada (números 22 pt petróleo) + faixa marinho "Entrega:", para salas. Campos: `dado`
(cartão branco opcional antes da lista), `itens` (até 3), `entrega` (obrigatória com salas), `ancora`,
`desafio` (dois cartões lado a lado embaixo).

```json
{
  "tipo": "tarefa",
  "bloco": "simetria",
  "papel": "decidir",
  "olho": "Bloco 2 · Decisão",
  "titulo": "Monte a **bateria** do Rafael",
  "tempo_s": 300,
  "interacao": {
    "tipo": "salas",
    "duracao_s": 240,
    "gravacao": "Antes de abrir, dizer: \"quem assiste à gravação, pause e faça a tarefa em 4 minutos\". Na edição, cortar o trecho de sala vazia.",
    "plano_b": "Sem salas: chat em cascata com as 4 medidas e o corte, 2 minutos, todos enviam no 3. Ler duas baterias diferentes em voz alta."
  },
  "itens": [
    "Quais 4 medidas entram na liberação dele, e com que ponto de corte?",
    "Quadríceps em 84%: o que muda no treino das próximas 8 semanas?",
    "O que você responde sobre a final, em uma frase?"
  ],
  "entrega": "o porta-voz cola no chat as 4 medidas, com o corte, e a frase.",
  "ancora": "use só o que a sua clínica já mede.",
  "desafio": "sem medida de antes da lesão, como estimar a perna sã?",
  "notas": "Interação: salas de 3 por 4 minutos. …"
}
```

### topicos

Parágrafos curtos com o termo inicial em negrito, coluna de ~7 pol, e cartão lateral opcional. Campos:
`itens` (strings com `**Termo:** texto` ou objetos `{"termo", "texto"}`), `lateral` (lista de cartões).

Cartões laterais (`lateral`, também aceito em `figura`, `tabela`, `barras`, `linha`):
`{"estilo": "escuro|claro|cinza|petroleo|fala", "olho": "...", "texto": "...", "itens": [...], "nota": "..."}`.
`fala` é a fala do paciente em 18 pt.

```json
{
  "tipo": "topicos",
  "bloco": "cabeça",
  "papel": "decidir",
  "olho": "Bloco 3 · O que fazer",
  "titulo": "O que fazer com o **medo**",
  "tempo_s": 60,
  "itens": [
    "**Acolher:** “Faz sentido ter medo de girar. Vamos treinar exatamente isso.”",
    "**Expor aos poucos:** o giro entra no treino em degraus, do previsível ao reativo.",
    "**Medir de novo:** ACL-RSI a cada 3 ou 4 semanas, com força e salto.",
    "**Decidir junto:** ele escolhe a data do jogo dentro dos degraus."
  ],
  "lateral": [
    {
      "estilo": "escuro",
      "olho": "O que não fazer",
      "texto": "Liberar porque o físico passou, ou vetar porque a escala deu 42."
    }
  ],
  "fonte": [
    "Faleide2021",
    "conduta: proposta clínica da equipe"
  ],
  "notas": "Uma conduta possível, em quatro verbos. …"
}
```

### cartoes

Grade numerada (2 ou 3 colunas) com faixa marinho de combinado embaixo. Campos: `itens`
(`{"titulo", "texto", "destaque", "numero"}`), `colunas`, `faixa`.

```json
{
  "tipo": "cartoes",
  "bloco": "abertura",
  "olho": "Combinados",
  "titulo": "Como vamos trabalhar **hoje**",
  "tempo_s": 45,
  "interacao": {
    "tipo": "mao_camera",
    "duracao_s": 20,
    "pedido": "Polegar para cima: já liberou um atleta de LCA antes dos 9 meses. Para baixo: nunca liberou."
  },
  "itens": [
    {
      "titulo": "Enquete",
      "texto": "Voto em 1 minuto. Ninguém fica sem votar."
    },
    {
      "titulo": "Chat em cascata",
      "texto": "Todo mundo escreve; só envia quando eu contar até 3."
    },
    {
      "titulo": "Salas de 3",
      "texto": "Tarefa curta, com porta-voz. A resposta volta pelo chat."
    },
    {
      "titulo": "Mão na câmera",
      "texto": "Polegar para cima ou para baixo, na frente da câmera."
    }
  ],
  "faixa": "**Combinado:** câmera aberta, resposta antes da explicação e erro bem-vindo. O paciente é fictício; as decisões são reais.",
  "notas": "Explicar as quatro formas de participar em 20 segundos, sem ler os cartões. …"
}
```

### figura

A figura recortada do artigo em moldura branca, com o título dizendo a conclusão, a coluna "O que
olhar" com 2–3 pontos numerados na ordem em que o olho deve percorrer a figura, destaques opcionais por
cima da imagem, legenda curta em português e a citação completa no rodapé.

| Campo | O que é |
|---|---|
| `figura` | `{"id": "Welling2018_fig2"}` (entrada do `catalogo.json`) ou `{"arquivo": "...", "citacao": "...", "ref": "Welling2018", "legenda": "..."}`. |
| `legenda` | Sobrescreve a `legenda_pt` do catálogo. Uma ou duas linhas: o que os eixos, as cores e os painéis mostram. |
| `o_que_olhar` | 2 ou 3 frases. Cada uma aponta um lugar da figura e diz o que se vê ali. |
| `rotulo_pontos` | Troca o olho "O que olhar". |
| `layout` | `auto` (padrão: escolhe o que deixa a figura maior), `meia` (figura à esquerda, coluna à direita) ou `total` (figura na largura toda, pontos numa faixa embaixo; legenda vai para a direita quando a figura é limitada pela altura). |
| `largura_figura` | Largura máxima da moldura no layout `meia`, em polegadas (padrão 7). |
| `destaques` | Lista de marcas sobre a figura, em coordenadas **relativas à imagem** (0 a 1, origem no canto superior esquerdo). |
| `lateral` | Cartões embaixo da coluna "O que olhar" (só no layout `meia`). |

Destaques:

```json
{"tipo": "retangulo", "x": 0.56, "y": 0.10, "w": 0.09, "h": 0.52, "texto": "1", "rotulo_pos": "sup-dir", "cor": "alerta"}
{"tipo": "elipse", "x": 0.30, "y": 0.40, "w": 0.10, "h": 0.10}
{"tipo": "seta", "de": [0.80, 0.20], "para": [0.62, 0.35], "texto": "corte 47", "cor": "alerta"}
{"tipo": "rotulo", "x": 0.50, "y": 0.05, "texto": "9 meses", "cor": "marinho"}
```

Coordenadas fora de 0 a 1 são erro de layout (o destaque sai da figura). `cor`: `alerta` (padrão), `ciano`, `marinho`, `petroleo`. `rotulo_pos`: `sup-esq` (padrão), `sup-dir`,
`inf-esq`, `inf-dir`. Numere os destaques com o mesmo número do ponto "o que olhar" correspondente.
Para acertar as coordenadas: abra o PNG, meça em pixels e divida pela largura e pela altura; depois
renderize e confira.

A imagem nunca é distorcida (a proporção vem do arquivo) e nunca é ampliada além de 110 px por
polegada de slide: um recorte pequeno aparece pequeno, e o script avisa para recortar de novo em 300 dpi.

```json
{
  "tipo": "figura",
  "bloco": "tempo e critérios",
  "papel": "evidencia",
  "olho": "Bloco 1 · E quem passa?",
  "titulo": "Aos 9 meses quase todos passam no hop; metade falha no **quadríceps**",
  "tempo_s": 105,
  "interacao": {
    "tipo": "mao_camera",
    "duracao_s": 20,
    "inicio_s": 80,
    "pedido": "Polegar para cima: mede força de quadríceps com dinamômetro. Para baixo: libera só com hop."
  },
  "figura": {
    "id": "Welling2018_fig2"
  },
  "o_que_olhar": [
    "Barras vermelhas, 9 meses: no hop simples e no triplo, 97% e 94% passam.",
    "Quadríceps a 60°/s, o primeiro par de barras: só 53% passam.",
    "Passar em tudo: 11% aos 9 meses (dado do texto)."
  ],
  "destaques": [
    {
      "tipo": "retangulo",
      "x": 0.183,
      "y": 0.33,
      "w": 0.05,
      "h": 0.29,
      "texto": "2"
    },
    {
      "tipo": "retangulo",
      "x": 0.562,
      "y": 0.105,
      "w": 0.092,
      "h": 0.515,
      "texto": "1",
      "rotulo_pos": "sup-dir"
    }
  ],
  "notas": "Outro estudo, outra pergunta: quantos conseguem passar? …"
}
```

### tabela

Tabela nativa com cabeçalho marinho e texto branco em negrito, primeira coluna em marinho, bordas
cinza finas. Campos: `colunas`, `linhas`, `larguras` (proporções), `destaque_linhas` (índices a partir
de 0, fundo cinza), `nota` (12 pt embaixo), `lateral`.

```json
{
  "tipo": "tabela",
  "bloco": "simetria",
  "papel": "conferir",
  "olho": "Bloco 2 · Uma resposta possível",
  "titulo": "A bateria do Rafael, **hoje**",
  "tempo_s": 60,
  "colunas": [
    "Medida",
    "Para liberar",
    "Rafael, 7 meses"
  ],
  "linhas": [
    [
      "Tempo de cirurgia",
      "9 meses ou mais",
      "7 meses"
    ],
    [
      "Força de quadríceps",
      "90% ou mais da outra perna",
      "84%"
    ],
    [
      "Altura do salto em uma perna",
      "90% ou mais",
      "79%"
    ],
    [
      "Hop em distância",
      "90% ou mais",
      "96%"
    ],
    [
      "ACL-RSI",
      "conversa se abaixo de 47",
      "52"
    ]
  ],
  "larguras": [
    3,
    3.2,
    2.2
  ],
  "destaque_linhas": [
    0,
    1,
    2
  ],
  "nota": "Em cinza, o que ele ainda não cumpre. Altura do salto e ACL-RSI: dados do caso.",
  "fonte": [
    "Grindem2016",
    "Kotsifaki2022",
    "Faleide2021",
    "corte da altura do salto: proposta clínica"
  ],
  "notas": "Uma resposta possível, para comparar com as das salas. …"
}
```

### numeros

Cartões com número grande (48 pt, reduz até 28 pt se o número for longo; se nem assim couber, é erro: deixe só o número e passe intervalo e unidade para o rótulo) e rótulo; `destaque` deixa o cartão
marinho. Campos: `itens` (`{"numero", "rotulo", "destaque"}`, 2 a 4), `linhas` (cartões brancos de
largura total embaixo, para "Quem:" e "Leitura:").

```json
{
  "tipo": "numeros",
  "bloco": "tempo e critérios",
  "papel": "evidencia",
  "olho": "Bloco 1 · A evidência",
  "titulo": "Sem critério, quase **4 em 10** se machucam de novo",
  "tempo_s": 90,
  "itens": [
    {
      "numero": "38,2%",
      "rotulo": "tiveram nova lesão no joelho ao voltar sem passar nos critérios (21 de 55)"
    },
    {
      "numero": "5,6%",
      "rotulo": "entre os que passaram em tudo (1 de 18)",
      "destaque": true
    },
    {
      "numero": "51%",
      "rotulo": "a menos na taxa de nova lesão por mês de espera, até o 9º"
    }
  ],
  "linhas": [
    "**Quem:** 106 atletas de esportes de pivô, seguidos por 2 anos. Passar: mais de 90 em força de quadríceps, quatro hop tests e duas escalas."
  ],
  "fonte": [
    "Grindem2016"
  ],
  "notas": "Conferir os palpites. …"
}
```

### barras

Gráfico nativo de colunas (ou barras horizontais com `"orientacao": "horizontal"`), editável no
PowerPoint, com rótulos de valor em negrito e sem eixo de valores (como no deck de referência). Várias
séries viram barras agrupadas com legenda desenhada (quadradinho + nome). Campos: `categorias`,
`series` (`{"nome", "valores", "cor"}`; cores da marca na ordem marinho, cinza, ciano, petróleo,
lavanda), `formato` (formato numérico do Excel: `"0"`, `"0.0"`, `"0\"%\""`), `rotulo` (olho acima do
gráfico, em uma linha; o script avisa se quebrar), `destaque_categorias` (índices pintados em vermelho-alerta, só com uma série),
`legenda_destaque`, `minimo`, `maximo`, `rotulos` (`false` tira os valores), `vao`, `altura`, `nota`, `lateral`.

Na série, `intervalo` desenha **barras de erro** (IC, faixa observada): uma entrada por categoria, `null`
ou `[inferior, superior]` em valores absolutos (`"intervalo": [null, [70, 84], null]`). O validador
reprova lista do tamanho errado ou intervalo que não contém o valor. Nas colunas o traço sai em cinza
escuro (`cor_intervalo` troca) e, com intervalo, os rótulos de valor vão para a base da coluna, em
branco, para não ficar sob o traço. Os limites ficam no XML do gráfico (editáveis em *Formatar barras de
erro* no PowerPoint), não na planilha embutida: anote a fonte do IC nas notas.

```json
{
  "tipo": "barras",
  "bloco": "simetria",
  "papel": "evidencia",
  "olho": "Bloco 2 · O mesmo atleta, três testes",
  "titulo": "Na distância ele parece pronto; na **altura**, não",
  "tempo_s": 60,
  "interacao": {
    "tipo": "mao_camera",
    "duracao_s": 20,
    "inicio_s": 35,
    "pedido": "Polegar para cima: mede altura de salto em uma perna. Para baixo: mede só distância."
  },
  "rotulo": "Simetria entre as pernas, em % (26 atletas já liberados)",
  "categorias": [
    "Hop em distância",
    "Salto vertical unipodal",
    "Drop jump unipodal"
  ],
  "series": [
    {
      "nome": "Simetria (%)",
      "valores": [
        97,
        83,
        77
      ]
    }
  ],
  "destaque_categorias": [
    1,
    2
  ],
  "legenda_destaque": "Abaixo de 90%",
  "formato": "0",
  "lateral": [
    {
      "estilo": "escuro",
      "olho": "E a perna de referência?",
      "texto": "Aos 6 meses, 57,1% atingiram 90% de simetria. Só 28,6% atingiram 90% da perna sã de antes da cirurgia.",
      "nota": "70 atletas, força e quatro hop tests."
    },
    {
      "estilo": "claro",
      "texto": "**Leitura:** simetria alta pode ser duas pernas fracas."
    }
  ],
  "fonte": [
    "Kotsifaki2022",
    "Wellsandt2017"
  ],
  "notas": "Os mesmos 26 atletas em três testes: 97% de simetria na distância do hop, 83% na altura do salto vertical unipodal e 77% na altura do drop jump unipodal. …"
}
```

### linha

Gráfico nativo de linha com marcadores, linhas de grade cinza claras e eixo de valores à esquerda.
Mesmos campos de `barras`; `destaque_categorias` aumenta e pinta de vermelho o ponto daquele índice (no PowerPoint; no render do LibreOffice o ponto sai maior, mas na cor da série: isso é esperado).

Campos da série só da linha: `tracejado` (`true`: linha tracejada, marcador vazado e amostra tracejada na
legenda) e `marcadores` (`false` tira os pontos). **Conta ilustrativa, projeção ou modelo vai sempre
tracejada**, e o dado observado em linha cheia ou ponto com `intervalo` (barras de erro na cor da
série): quem olha o gráfico precisa separar o que foi medido do que foi calculado sem ler a nota. No
render do LibreOffice o marcador vazado sai cheio; o tracejado e as barras de erro saem certos.

```json
"series": [
  {"nome": "Conta: meia-vida de 3 meses (não é dado)", "valores": [0, 50, 75, 88, null],
   "cor": "cinza_grafico", "tracejado": true},
  {"nome": "Observado em 1 ano: 89 (IC 80 a 97)", "valores": [null, null, null, null, 89],
   "cor": "alerta", "intervalo": [null, null, null, null, [80, 97]]}
]
```

```json
{
  "tipo": "linha",
  "bloco": "fechamento",
  "olho": "Fechamento",
  "titulo": "O que **aconteceu** com o Rafael",
  "tempo_s": 45,
  "origem": "caso",
  "rotulo": "Do 7º ao 11º mês de cirurgia",
  "categorias": [
    "7 meses",
    "8 meses",
    "9 meses",
    "10 meses",
    "11 meses"
  ],
  "series": [
    {
      "nome": "Quadríceps (% da outra perna)",
      "valores": [
        84,
        88,
        92,
        94,
        95
      ]
    },
    {
      "nome": "Altura do salto (%)",
      "valores": [
        79,
        85,
        90,
        92,
        94
      ],
      "cor": "ciano"
    },
    {
      "nome": "ACL-RSI (0 a 100)",
      "valores": [
        52,
        47,
        42,
        58,
        71
      ],
      "cor": "alerta"
    }
  ],
  "minimo": 30,
  "maximo": 100,
  "rotulos": false,
  "formato": "0",
  "lateral": [
    {
      "estilo": "claro",
      "texto": "**Mês 9:** físico pronto, cabeça não."
    },
    {
      "estilo": "claro",
      "texto": "**Mês 10:** treino completo com o time."
    },
    {
      "estilo": "escuro",
      "texto": "**Mês 11:** jogou, com minutos controlados."
    }
  ],
  "nota": "Dados fictícios.",
  "notas": "O desfecho, em 30 segundos. …"
}
```

### etapas

Passos em cartões com setas entre eles; o último pode ser marinho (`destaque`). Campos: `passos`
(`{"titulo", "texto", "destaque"}`, 3 a 5), `numerar`, `cartoes_baixo` (strings ou
`{"texto", "estilo": "escuro"}`).

```json
{
  "tipo": "etapas",
  "bloco": "cabeça",
  "papel": "decidir",
  "olho": "Bloco 3 · A volta",
  "titulo": "A volta em **degraus**",
  "tempo_s": 60,
  "interacao": {
    "tipo": "mao_camera",
    "duracao_s": 20,
    "inicio_s": 35,
    "pedido": "Polegar para cima: põe o Rafael no degrau 2 hoje. Para baixo: deixa no degrau 1."
  },
  "numerar": true,
  "passos": [
    {
      "titulo": "Treino individual",
      "texto": "Corrida, mudança de direção e bola."
    },
    {
      "titulo": "Coletivo sem contato",
      "texto": "Treino do time; giro previsível."
    },
    {
      "titulo": "Coletivo completo",
      "texto": "Contato e giro reativo."
    },
    {
      "titulo": "Jogo",
      "texto": "Minutos controlados.",
      "destaque": true
    }
  ],
  "cartoes_baixo": [
    {
      "texto": "**Para subir:** critérios cumpridos e duas semanas no degrau sem dor, sem derrame e sem travar no giro."
    },
    {
      "estilo": "escuro",
      "texto": "**Para o Rafael:** entra hoje no degrau 2. O jogo fica para daqui a 6 semanas, se os degraus andarem."
    }
  ],
  "fonte": [
    "degraus e prazos: proposta clínica da equipe"
  ],
  "notas": "Quatro degraus: treino individual, coletivo sem contato, coletivo completo e jogo com minutos controlados. …"
}
```

### comparacao

Antes/depois em duas faixas de cartões, cada faixa com olho próprio; cartões `destaque` ficam marinho.
Campos: `faixas` (`{"rotulo", "itens": [{"titulo", "texto", "etiqueta", "destaque"}]}`), `nota`.

```json
{
  "tipo": "comparacao",
  "bloco": "simetria",
  "olho": "Bloco 2 · O que muda na bateria",
  "titulo": "Da bateria que tranquiliza à que **expõe**",
  "tempo_s": 60,
  "faixas": [
    {
      "rotulo": "Antes: o que costuma liberar",
      "itens": [
        {
          "titulo": "Tempo",
          "texto": "6 meses",
          "etiqueta": "Cedo"
        },
        {
          "titulo": "Hop simples",
          "texto": "90% da distância",
          "etiqueta": "Quadril compensa"
        },
        {
          "titulo": "Hop triplo",
          "texto": "90% da distância",
          "etiqueta": "Quadril compensa"
        },
        {
          "titulo": "Sintoma",
          "texto": "“Não sinto nada”",
          "etiqueta": "Não mede função"
        }
      ]
    },
    {
      "rotulo": "Agora: o que expõe o joelho",
      "itens": [
        {
          "titulo": "Tempo",
          "texto": "9 meses ou mais",
          "etiqueta": "Grindem 2016",
          "destaque": true
        },
        {
          "titulo": "Quadríceps",
          "texto": "90% da outra perna",
          "etiqueta": "Grindem 2016",
          "destaque": true
        },
        {
          "titulo": "Salto vertical",
          "texto": "Altura, em uma perna",
          "etiqueta": "Kotsifaki 2022",
          "destaque": true
        },
        {
          "titulo": "Cabeça",
          "texto": "ACL-RSI e conversa",
          "etiqueta": "Bloco 3",
          "destaque": true
        }
      ]
    }
  ],
  "fonte": [
    "Grindem2016",
    "Kotsifaki2022",
    "seleção dos testes: proposta clínica da equipe"
  ],
  "notas": "Comparar as duas baterias em 40 segundos, sem ler cartão por cartão. …"
}
```

**Variante colunas (`"layout": "colunas"`):** comparação lado a lado, para a aula expositiva (duas
condições, dois testes, duas doses). Cada faixa vira uma coluna; os cartões da mesma posição ficam na
mesma altura nas colunas, então escreva os itens na mesma ordem de atributos ("O que mede", "Nos
estudos", "Na prática"). A faixa com `"destaque": true` (a que a aula defende) ganha cabeçalho marinho;
as outras, cabeçalho cinza com texto marinho (sem nenhuma em destaque, todas saem marinho). Um item com
`destaque` vira cartão marinho: use em um, no máximo dois. Campos: `faixas` (2 ou 3, cada uma com
`rotulo`, `destaque`, `itens`), `nota` (cartão branco) e `faixa` (faixa marinho de conclusão).

```json
{
  "tipo": "comparacao",
  "parte": 2,
  "papel": "explicar",
  "layout": "colunas",
  "olho": "Parte 2 · Lado a lado",
  "titulo": "Dois saltos, duas **leituras**",
  "tempo_s": 90,
  "faixas": [
    {"rotulo": "Hop em distância", "itens": [
      {"titulo": "O que mede", "texto": "Até onde o corpo vai; o quadril pode empurrar."},
      {"titulo": "Atletas já liberados", "texto": "97% de simetria."},
      {"titulo": "Na liberação", "texto": "Tranquiliza: quase todos passam."}]},
    {"rotulo": "Altura do salto em uma perna", "destaque": true, "itens": [
      {"titulo": "O que mede", "texto": "Quanto o membro empurra para cima."},
      {"titulo": "Os mesmos atletas", "texto": "83% no vertical, 77% no drop jump."},
      {"titulo": "Na liberação", "texto": "Expõe o déficit do joelho.", "destaque": true}]}
  ],
  "fonte": ["Kotsifaki2022", "Welling2018"],
  "notas": "A comparação que fecha a explicação da parte, linha a linha. …"
}
```

### citacao

A fala do paciente em cartão (branco com borda em fundo claro; petróleo em fundo escuro), com contexto
acima e cartão lateral "O que você sabe". Campos: `fundo` (`"escuro"` para o revés), `contexto`,
`rotulo`, `fala`, `quem`, `fala2` (segundo cartão cinza), `cartao` (`{"estilo", "olho", "itens", "texto"}`).

```json
{
  "tipo": "citacao",
  "bloco": "abertura",
  "olho": "O caso",
  "titulo": "Rafael quer jogar a **final**",
  "tempo_s": 60,
  "origem": "caso",
  "rotulo": "No consultório, hoje",
  "fala": "“Sete meses de cirurgia e não sinto nada. A final é daqui a três semanas. Estou liberado, né?”",
  "fala2": "Rafael, 22 anos, ala de futsal. LCA direito reconstruído com enxerto de isquiotibiais.",
  "cartao": {
    "olho": "O que você mediu",
    "itens": [
      "Hop simples: 96% da distância da outra perna",
      "Quadríceps no dinamômetro: 84%",
      "Sem dor e sem derrame",
      "Ainda não treina com o time"
    ]
  },
  "notas": "Começar pela pessoa. …"
}
```

### sintese

Até 3 ou 4 pontos em cartões cinza com número grande, e faixa marinho final ("Para segunda-feira:").
Campos: `pontos` (strings ou `{"titulo", "texto"}`), `faixa`.

```json
{
  "tipo": "sintese",
  "bloco": "fechamento",
  "papel": "conferir",
  "olho": "Fechamento",
  "titulo": "Três coisas para **levar**",
  "tempo_s": 60,
  "pontos": [
    {
      "titulo": "Antes de 9 meses, cada mês conta",
      "texto": "Taxa de nova lesão 51% menor por mês de espera, até o 9º."
    },
    {
      "titulo": "Força e altura do salto expõem o joelho",
      "texto": "A distância do hop chega a 97% com o joelho trabalhando menos."
    },
    {
      "titulo": "Número é estimativa, não veredito",
      "texto": "Leia o intervalo de confiança e os alarmes falsos."
    }
  ],
  "faixa": "**Para segunda-feira:** em um paciente de LCA, meça força de quadríceps e altura do salto em uma perna.",
  "fonte": [
    "Grindem2016",
    "Kotsifaki2022",
    "Faleide2021"
  ],
  "notas": "Comparar com o que a turma escreveu. …"
}
```

### referencias

Duas colunas de 5,72 pol, 12 pt, uma referência por linha no formato "Autor et al. Revista Ano. PMID n"
(com volume e páginas quando todas cabem em uma linha; ver `meta.referencias_formato`). As duas colunas ficam com alturas parecidas, como no deck de referência; até 8 linhas ficam numa coluna só. Se não couber, o script abre outro slide sozinho ("Referências (2)"). As referências vêm do
bloco `referencias` do deck, em ordem alfabética. Campos: `outras` (linhas extras "Também: ..."),
`notas` (se vazio, o script escreve a declaração do que foi conferido no texto completo, no resumo e o
que é proposta clínica). É slide de apoio: não entra no tempo.

```json
{
  "tipo": "referencias",
  "outras": [
    "testes, cortes e degraus marcados como proposta clínica da equipe"
  ]
}
```

### mapa

O organizador prévio da aula expositiva e o divisor "onde estamos". As partes de `meta.partes` em
cartões cinza de largura total, numeradas de cima para baixo (número 28 pt petróleo, título 18 pt bold,
linha de texto 13 pt). Sem `atual` (ou `0`), é o **mapa da aula**, mostrado na abertura. Com `"atual": k`,
abre a parte k: o cartão dela fica marinho com "AGORA" à direita, as partes já vistas ficam apagadas
(cinza) e as que faltam, normais. Olho e título saem sozinhos ("Mapa da aula" / "O caminho de hoje";
"Onde estamos · Parte k de n" / o título da parte); escreva `olho` e `titulo` só para trocar. Campos:
`atual`, `faixa` (no mapa geral sai marinho, "**Ao fim:** ..."; no divisor sai branca com borda, para
não competir com a parte em destaque), `partes` (troca `meta.partes` só neste slide, raro).

Na expositiva, o validador **exige** um `mapa` sem `atual` antes da parte 1 e um `mapa` com
`"atual": k` como primeiro slide de cada parte k. Tempo típico: 60 a 90 s no mapa geral (ler as partes
como perguntas), 20 a 40 s no divisor.

```json
{"tipo": "mapa", "olho": "Mapa da aula", "titulo": "Quatro perguntas, nesta **ordem**", "tempo_s": 90,
 "faixa": "**Ao fim:** decidir a liberação com tempo, força, salto e prontidão, e ler o número que sustenta cada critério.",
 "notas": "O organizador prévio: a turma vê o caminho inteiro antes de começar. …"}
```

```json
{"tipo": "mapa", "parte": 3, "atual": 3, "tempo_s": 30,
 "notas": "Onde estamos: parte 3 de 4. As duas primeiras partes disseram quando e o que medir. …"}
```

### exemplo

Exemplo resolvido passo a passo: o problema num cartão branco à esquerda (`dado`), os passos numerados
à direita em cartões cinza, cada um com o nome do passo em bold e a operação com o resultado em
marinho 16 pt (`conta`, com o resultado em `**negrito**`), e a conclusão numa faixa marinho (`resposta`).
Passos listados em `lacunas` (números a partir de 1) saem em cartão branco com borda e "**Sua vez:**"
seguido de `lacuna` em petróleo: é o **exemplo parcialmente resolvido**, que a turma completa (dê a ele
uma interação, chat em cascata ou enquete, com `inicio_s` depois de explicar os passos feitos). Campos:
`dado` (texto ou `{"olho", "texto", "itens", "nota"}`; olho padrão "O problema"), `largura_dado` (pol,
padrão 4,2; sem `dado`, os passos ocupam a largura toda), `rotulo_passos` (padrão "Passo a passo"),
`passos` (2 a 5: `{"titulo", "conta", "texto", "lacuna"}`), `lacunas`, `resposta`, `ancora`, `desafio`
(cartões embaixo, como na `tarefa`).

Conta feita a partir de um estudo é dado derivado: ponha a conta inteira nas notas e "contas: calc. a
partir de Autor ano" na `fonte`. Diga no slide quando a conta não equivale ao que parece ("1 ÷ 0,326 ≈ 3
(não é NNT)" para uma diferença de risco de coorte).

```json
{
  "tipo": "exemplo",
  "parte": 3,
  "papel": "exemplo",
  "olho": "Parte 3 · Exemplo resolvido",
  "titulo": "Do risco relativo ao **absoluto**",
  "tempo_s": 180,
  "dado": {"olho": "Nova lesão em 2 anos", "itens": ["Sem passar: 21 de 55", "Passando: 1 de 18", "Razão de risco 0,16 (IC 0,02 a 1,20)"]},
  "passos": [
    {"titulo": "Risco em cada grupo", "conta": "21 ÷ 55 = **38,2%**  ·  1 ÷ 18 = **5,6%**"},
    {"titulo": "Diferença absoluta", "conta": "38,2 − 5,6 = **32,6 pontos**"},
    {"titulo": "Quantos para um a menos", "conta": "1 ÷ 0,326 ≈ **3** (não é NNT)"},
    {"titulo": "Precisão", "conta": "o IC **cruza o 1**"}
  ],
  "resposta": "**Leitura:** diferença grande; com 1 evento em 18, tamanho incerto.",
  "fonte": ["Grindem2016", "contas: calc. a partir de Grindem 2016"],
  "notas": "Exemplo resolvido: eu faço a conta inteira, a turma acompanha. Passo 1, …"
}
```

Parcialmente resolvido (o passo 2 fica para a turma):

```json
{
  "tipo": "exemplo", "parte": 4, "papel": "checar",
  "olho": "Parte 4 · Exemplo parcialmente resolvido",
  "titulo": "Quanto um ACL-RSI abaixo de 47 muda a **chance**?",
  "tempo_s": 150,
  "interacao": {"tipo": "chat_cascata", "duracao_s": 60, "inicio_s": 45},
  "dado": {"olho": "O dado", "texto": "Corte de 47 aos 9 meses, para não voltar ao nível de antes.", "itens": ["Sensibilidade: 85%", "Especificidade: 45%"]},
  "passos": [
    {"titulo": "Razão de verossimilhança positiva", "conta": "0,85 ÷ (1 − 0,45) ≈ **1,5**"},
    {"titulo": "Razão de verossimilhança negativa", "lacuna": "(1 − 0,85) ÷ 0,45 = ?"},
    {"titulo": "Leitura", "conta": "RV+ abaixo de 2 muda **pouco** a chance"}
  ],
  "lacunas": [2],
  "ancora": "RV− = (1 − sensibilidade) ÷ especificidade.",
  "desafio": "RV− perto de 0,3: o que um escore alto permite dizer?",
  "fonte": ["Faleide2021", "contas: calc. a partir de Faleide 2021"],
  "notas": "Exemplo parcialmente resolvido: o primeiro passo está feito, o segundo é da turma. …"
}
```

### Receitas para a aula expositiva com os tipos que já existem

- **Conceito com 2 a 4 pontos e um destaque:** `cartoes` (2 a 4 itens, `colunas` 2, com a ideia central
  na `faixa` marinho) ou `topicos` com um cartão `lateral` de estilo `escuro`. Título = a ideia em uma frase.
- **Sequência ou processo:** `etapas` (3 a 5 passos com seta; o último em marinho).
- **Comparação lado a lado:** `comparacao` com `"layout": "colunas"`; atributos com muitas linhas vão para
  `tabela`.
- **Checagem rápida:** `enquete` com `duracao_s` de 30 a 45 (revelação no slide seguinte, `revela`),
  `pergunta` com `chat_cascata` de uma linha, ou `mao_camera` com `inicio_s` em qualquer slide de
  explicação (ver `interacoes.md`, "Checagem rápida").
- **Aplicação a caso:** `citacao` (o paciente fala), `pergunta` ou `tabela`, com `"papel": "aplicacao"`, no
  fim da parte, depois da explicação.
- **Síntese da parte:** `sintese` com 2 ou 3 pontos e a faixa "**Na prática:** ...", `"papel": "sintese"`.

## Regras por formato (o que `validar_aula.py` confere)

| Regra | `caso` (padrão sem `meta.formato`) | `expositiva` |
|---|---|---|
| Duração (soma de `tempo_s`) | erro acima de 35 min; aviso abaixo de 28 | erro acima de 50 min; aviso abaixo de 42 e acima de 48 |
| Tempo estimado pela fala das notas | aviso acima de 35 min | aviso acima de 50 min, e abaixo de 65% do `tempo_s` (nota que não é a explicação completa) |
| Primeira interação | até 3 min | até 5 min |
| Tempo sem interação | aviso acima de 6 min, erro acima de 7 | aviso a partir de 7 min, erro acima de 8 |
| Interações | 5 ou mais, 3 formatos | 6 checagens ou mais antes do bilhete, 3 formatos |
| Tempo em atividade | aviso abaixo de 25% | aviso abaixo de 12% |
| Pergunta antes da figura, ciclo prever/decidir por `bloco` | exige | não exige |
| Mapa da aula no início (`mapa` sem `atual`) | — | exige |
| Cada parte abre com `mapa` `"atual": k` e fecha com síntese | — | exige |
| Aplicação a caso (`"papel": "aplicacao"`) | — | exige ao menos uma; avisa a parte sem |
| Exemplo resolvido (`exemplo` ou `"papel": "exemplo"`) | — | avisa se não houver |
| Âncora/desafio e checagem em cada parte; parte acima de 14 min | — | avisa |
| Bilhete de saída no último slide cronometrado; slide de referências | exige | exige |

## O que o script faz sozinho

- Pílula de interação, logo no rodapé (claro ou branco conforme o fundo) e "Fonte: ..." à direita.
- Linha "Tempo: X (acumulado M:SS)." no começo de cada nota.
- Texto que não cabe: reduz 1 pt por vez, até 3 pt a menos, com piso de 10 a 12 pt conforme o elemento, e avisa. Se ainda
  não couber, gera o slide mesmo assim, marca **erro de layout** e o código de saída é 1. Título com
  mais de 2 linhas em 24 pt também é erro.
- Fonte do rodapé longa demais: cai para 11 e 10 pt; acima de 2 linhas é erro (use a `curta`).
- Um slide com problema não derruba o deck: o erro é relatado e os outros slides saem.
