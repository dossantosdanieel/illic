---
name: boost-aula-slides
description: >-
  Desenha e monta a aula online da Boost Education, expositiva com checagens (45 a 50 min, o padrão:
  mapa da aula, "onde estamos", exemplo resolvido, caso como aplicação) ou guiada por caso (30 a 35
  min), com nível técnico alto, e gera o .pptx na marca illic ACADEMY · BOOST Education do deck "Caso
  Marina": roteiro, deck.json, notas do apresentador, validação por formato, render em PNG e materiais
  (enquetes do Meet, pré e pós-teste, resumo do aluno, verificação).
  Use SEMPRE que o pedido for montar os slides a partir das fichas e figuras já prontas, ou revisar ou
  ajustar aula, slides, apresentação, PowerPoint, pptx, deck, roteiro, enquete, quiz, pré ou pós-teste,
  resumo do aluno ou notas do apresentador da Boost ("transforma isso em slides", "ajusta o tempo da
  aula", "deixa mais interativo"), e logo depois da boost-leitura-figuras. Pedido de aula inteira a
  partir de um tema vai antes para boost-education. Não improvise slides fora desta skill.
---

# Aula Boost: do artigo ao .pptx

Esta skill transforma as fichas de leitura e o catálogo de figuras de uma aula em uma aula online e
gera o .pptx na marca Boost mais os materiais de apoio. O público são fisioterapeutas da equipe ILLIC
em níveis diferentes; a aula é uma só, em camadas, e é gravada para a equipe. Leia antes as preferências
do Daniel em `../boost-education/references/preferencias.md` (se existir): elas mandam quando o pedido
não disser outra coisa.

**Dois formatos** (`meta.formato` no deck.json; o porquê e quando usar cada um em
`references/desenho-instrucional.md`, seção 11):

| | `expositiva` (padrão das preferências hoje) | `caso` |
|---|---|---|
| Duração | 40 a 50 min, alvo 45 a 48 (erro acima de 50) | 30 a 35 min, alvo 32 (erro acima de 35) |
| Espinha | a linha lógica do tema em 3 a 5 partes (`meta.partes`), com mapa e "onde estamos" | um caso que evolui, em 3 blocos prever → ver → decidir → conferir |
| Interação | checagem rápida a cada 5 a 7 min (6 ou mais), a primeira até 5 min | decisão da turma antes da evidência, a primeira até 3 min |
| O caso | só como aplicação, no fim de cada parte | atravessa a aula, com revés |
| Exemplo | `assets/exemplo_expositiva/deck.json` | `assets/exemplo/deck.json` |

Escolha: o que o pedido ou o `00_briefing.md` disser ("Formato pedagógico"); senão, as preferências
(hoje: expositiva). Caso fica para aulas de aplicação ou discussão de casos, quando pedido. Deck sem
`meta.formato` é validado como caso, para os decks antigos continuarem valendo.

Os scripts ficam em `scripts/` desta skill; nos comandos abaixo, `SK` é o diretório desta skill.
Rodam com Python 3, `python-pptx` e `pillow`; o render usa LibreOffice (`soffice`) e `pdftoppm`.

## Entradas e saídas (contrato de pastas)

Tudo da aula mora em `aulas/<AAAA-MM>-<slug>/`. Esta skill lê:

- `00_briefing.md` (tema, público, objetivos, pergunta clínica)
- `02_artigos/leitura/<chave>.md` (fichas de leitura crítica) e `02_artigos/texto/<chave>.md` (texto por página)
- `03_figuras/catalogo.json` e `03_figuras/folha_contato.png`
- `01_busca/selecionados.json` (papel de cada artigo)

e escreve em `04_aula/`: `roteiro.md`, `deck.json`, `questoes.json`, `<slug>.pptx`, `previa/`,
`enquetes.md`, `pre_pos_teste.md`, `resumo_aluno.md`, `verificacao.md`.

Se faltarem fichas ou figuras, pare e rode antes `boost-leitura-figuras`: uma aula sem a leitura do
texto completo vira repetição de resumo, e o padrão da casa é "nada inventado".

## Fluxo

### 1. Ler as fichas e o catálogo

Leia todas as fichas e olhe a folha de contato das figuras. Para cada artigo, anote o número que pode
entrar na aula, a página de onde ele vem, o desenho do estudo, a certeza e o limite. Separe o que foi
conferido no texto completo do que veio só do resumo: isso vai para o campo `conferido` das referências
e para `verificacao.md`.

### 2. Definir os objetivos

Dois ou três (na expositiva, até quatro), em nível de aplicação, análise ou avaliação (decidir, interpretar, calcular, criticar),
cada um ligado a uma decisão que a turma vai tomar e a uma questão do pós-teste. Pelo menos um objetivo
exige raciocínio quantitativo (tamanho de efeito, IC, NNT, MCID, certeza, sensibilidade e
especificidade). O porquê e os exemplos estão em `references/desenho-instrucional.md`, seções 1 e 8.
Antes de seguir, leia em `desenho-instrucional.md` a parte "O que torna a aula de nível alto": a turma
tem especialistas, e a aula que só confirma o que eles já fazem é tempo perdido. Procure nas
fichas o dado que contraria ou refina um hábito comum (o ranking citado por todos com certeza baixa, o
preditor popular que não ficou no modelo, a melhora que não passa da MCID) e construa a decisão em torno
dele.

### 3. Escrever `roteiro.md`

Use `assets/roteiro_modelo.md` (modelo A, expositiva; modelo B, caso).

**Expositiva.** Escreva primeiro a linha de raciocínio em 3 a 5 partes, como perguntas na ordem do tema
(o que é → por que acontece → como diagnosticar → o que esperar → como tratar, ou um recorte). Abertura
de 3 a 4 min (capa, combinados com mão na câmera, **mapa da aula**); cada parte de 8 a 12 min com
"onde estamos" → explicação com uma ideia por slide → exemplo resolvido → checagem → aplicação ao caso →
síntese; fechamento de 3 min (recuperação na ordem do mapa e bilhete de saída). Uma checagem a cada 5
a 7 min, que exige recuperar e não reconhecer (`references/interacoes.md`, "Checagem rápida"); exemplo
resolvido, depois parcialmente resolvido, depois aplicação; âncora e desafio por parte; salas no máximo
uma vez. O nível não baixa: cada parte tem o número com IC, DMCI, NNT/NNH, RV, dose prescritível e
certeza quando couber (`desenho-instrucional.md`, seções 8 e 11).

**Caso.** Monte o caso (um paciente fictício que atravessa a aula e sofre um
revés), escolha 3 a 5 figuras, e distribua o tempo:

- abertura de 3 a 4 min com a **primeira decisão da turma antes de 3 min**;
- 3 blocos de 7 a 9 min no ciclo **prever → ver a evidência → decidir → conferir**, com a pergunta sempre
  antes da figura;
- fechamento de 4 a 5 min: desfecho, recuperação de memória, síntese, bilhete de saída.

Cada bloco ganha uma âncora ("Para começar") e um desafio. Formatos de interação e como conduzir cada
um: `references/interacoes.md`. Corte conteúdo antes de cortar interação: o conteúdo cortado vai para o
resumo do aluno.

### 4. Escrever `deck.json` e `questoes.json`

Copie o exemplo do formato e reescreva: `assets/exemplo_expositiva/deck.json` (expositiva de 45 min 30 s
em 4 partes, com `mapa`, `exemplo` e `comparacao` em colunas) ou `assets/exemplo/deck.json` (caso de 32
min, com os outros tipos). Mantenha `meta.formato`. Apague `meta.catalogo` da cópia: nos exemplos ele
aponta para as figuras do exemplo, e na pasta da aula o padrão (`../03_figuras/catalogo.json`) já é o
certo. Na expositiva, escreva `meta.partes` e ponha `"parte": k` em cada slide das partes (abertura e
fechamento ficam sem). O esquema campo a campo, com um exemplo por tipo,
está em `references/deck-json.md` (longo: leia a parte geral e só os tipos que vai usar). Pontos que mais
erram:

- título de slide de evidência diz a **conclusão** ("Aos 9 meses quase todos passam no hop; metade
  falha no **quadríceps**"), com uma palavra-chave em negrito;
- até ~70 palavras visíveis por slide; o resto vai para `notas`;
- todo slide que afirma evidência tem `fonte`; dado do caso fictício leva `"origem": "caso"`;
- figura com `o_que_olhar` (2–3 pontos) e `destaques` numerados na mesma ordem;
- caso: `bloco` e `papel` em todos os slides, para o validador conferir o ciclo; expositiva: `parte` e
  `papel` (`explicar`, `exemplo`, `checar`, `aplicacao`, `sintese`);
- `olho` curto (cabe em uma linha antes da pílula), `numero` só com o número (o intervalo vai no
  `rotulo`), `rotulo` de gráfico em uma linha e destaques com coordenadas entre 0 e 1: o script
  reprova o que passar disso, porque no slide vira texto encavalado;
- em gráfico de linha, conta ilustrativa ou projeção vai com `"tracejado": true` e o dado observado com
  `intervalo` (barras de erro), para não desenhar conta igual a dado (`references/deck-json.md`, linha);
- notas na voz do deck de referência (`references/voz-das-notas.md`): papel do slide, o que dizer com os
  números e a origem, o que não antecipar, "Interação: ..." com o roteiro, e "proposta clínica" onde
  nenhum ensaio testou. Na expositiva a nota é a explicação completa, com a transição entre partes;
- conta feita a partir de um estudo ("calc.") vai com a conta inteira nas notas e "contas: calc. a partir
  de Autor ano" na `fonte`.

As enquetes e as questões do pré/pós-teste seguem `references/questoes.md`: cenário clínico, uma melhor
resposta, distratores que são erros reais de raciocínio, gabarito comentado com a referência. O
pós-teste usa casos **novos**, não as enquetes da aula. Modelo: `assets/exemplo/questoes.json`.

### 5. Montar e validar

```bash
python3 SK/scripts/montar_deck.py aulas/<aula>/04_aula/deck.json
```

O script roda a validação pedagógica (`validar_aula.py`), imprime a **linha do tempo minuto a minuto**
(`●` com interação, `·` sem), monta o .pptx e lista o texto que precisou ser reduzido ou não coube.
Saída 1 quando há erro; o arquivo sai mesmo assim para você ver. Use `--estrito` para não gerar com erro.

Para validar sem montar: `python3 SK/scripts/validar_aula.py deck.json` (ou `--json`).

As regras de tempo e de estrutura dependem do formato; a tabela completa está no fim de
`references/deck-json.md`. **Expositiva:** reprova acima de 50 min, primeira checagem depois de 5 min,
mais de 8 min sem interação, menos de 6 checagens, falta do mapa da aula no início, parte que não abre
com o `mapa` "onde estamos" ou não fecha com síntese, aula sem nenhuma aplicação a caso; avisa abaixo
de 42 e acima de 48 min, 7 a 8 min sem interação, parte sem aplicação, sem âncora/desafio ou acima de
14 min, falta de exemplo resolvido, e notas que cobrem menos de 65% do tempo. Não exige pergunta antes
da figura nem o ciclo prever/decidir. **Caso:** o validador **reprova** duração acima de 35 min,
primeira interação depois de 3 min, mais de 7 min sem interação, menos de 5 interações ou de 3 formatos.
Nos dois formatos, reprova slide com mais de 100 palavras, slide de
evidência sem fonte, fonte do rodapé ausente das referências, figura inexistente, sem citação ou de baixa
resolução, slide sem notas, último slide cronometrado que não é o bilhete de saída (`chat`) e falta de
referências; no caso, também figura mostrada antes de qualquer pergunta no bloco. **Avisa**, no caso,
duração abaixo de 28 min, 6 a 7 min sem interação e menos de 25% do tempo em atividade (12% na
expositiva); nos dois, 70 a 100 palavras, objetivos com verbo fraco, figura sem legenda, falta de
âncora/desafio, referências sem `conferido`, nota de enquete que manda chamar pelo nome quem votou (o
Meet não mostra o voto de cada um) e deck com partes ou mapa mas sem `meta.formato`. Corrija todo erro; decida conscientemente cada aviso.

Além da soma de `tempo_s`, o validador **estima o tempo real**: palavras faladas das notas a ~130 por
minuto (sem "Tempo:", sem a rubrica "Interação:" e as ordens de condução, sem o pré-aula da capa) mais a
`duracao_s` da interação; avisa (não reprova) se o total passa do teto do formato (35 ou 50 min) ou um
slide passa de 1,5 × o seu `tempo_s` com 30 s ou mais de sobra.

### 6. Renderizar e OLHAR cada slide

```bash
python3 SK/scripts/renderizar.py aulas/<aula>/04_aula/<slug>.pptx
```

Gera `previa/<slug>.pdf`, `previa/s-01.png ...` e as folhas de contato `previa/folha-N.png`. Abra
primeiro as folhas (ritmo: alternância escuro/claro, slides carregados, sequência de figuras) e depois
**cada PNG em tamanho cheio**. O script mede o texto, mas só o olho pega: destaque fora do lugar na
figura, figura ilegível, rótulo cobrindo dado, gráfico com escala enganosa, título que quebrou feio,
cartão vazio, olho encostando na pílula. Compare com a marca em `references/marca-boost.md` (hierarquia,
margens, cartões, pílula, rodapé). Lato não está instalada no ambiente de render: as letras saem em Inter,
um pouco mais largas; isso é esperado.

Para acertar destaques sobre a figura, meça no PNG do recorte (pixels ÷ largura e ÷ altura) e confira de
novo no render.

### 7. Corrigir e repetir

Volte ao `deck.json`, monte, valide e renderize de novo até não haver erro e todos os slides estarem
limpos. Prefira cortar palavras a aceitar texto reduzido.

### 8. Conferir o .pptx por dentro

```bash
python3 SK/scripts/conferir_pptx.py aulas/<aula>/04_aula/deck.json aulas/<aula>/04_aula/<slug>.pptx
```

Confere que toda nota começa com "Tempo: ... (acumulado M:SS)." com o acumulado certo, que os gráficos
são nativos (com planilha embutida, editáveis), que nenhuma forma sai da página e que o pacote está
íntegro; se houver esquemas OOXML no ambiente, valida o XML contra eles. Isso importa porque o
PowerPoint é mais rígido que o LibreOffice: um arquivo que renderiza bem aqui pode abrir com "reparo" lá.

### 9. Gerar os materiais

```bash
python3 SK/scripts/materiais.py aulas/<aula>/04_aula/deck.json            # lê questoes.json ao lado
python3 SK/scripts/materiais.py deck.json --questoes outro.json --saida pasta/
```

Gera `enquetes.md` (texto pronto para criar e salvar as enquetes no Meet antes da aula, com gabarito, o
roteiro de todas as interações e a seção "Plano B e gravação", feita de `interacao.plano_b` e
`interacao.gravacao`: escreva esses campos no deck.json, nunca à mão no .md, que é reescrito), `pre_pos_teste.md` (questões em blocos prontos para colar no Google
Forms, mais o gabarito comentado) e `resumo_aluno.md` (objetivos, pontos-chave com números e fontes,
algoritmo de decisão, propostas clínicas, referências; a partir de `meta.resumo`; avisa acima de 900
palavras de texto corrido, sem contar a lista de referências, DOI, PMID e URLs). O script também
confere a forma das questões (pistas, gabarito concentrado, distrator sem explicação), se cada objetivo
tem questão e se alguma questão repete uma enquete da aula. Releia os três: o
script confere a forma, não o conteúdo clínico.

### 10. Escrever `verificacao.md`

Use `assets/verificacao_modelo.md`. Liste cada número da aula e onde foi conferido (texto completo com
página, só resumo, caso fictício), cada proposta clínica, cada figura com licença e as de direitos
reservados, o resultado das três checagens automáticas e o que ainda está pendente. A mesma honestidade
vai para as notas do slide de referências (geradas a partir do campo `conferido`).

### 11. Entregar

Diga ao usuário: caminho do .pptx, formato, duração e número de slides, a linha do tempo resumida (minutos com e
sem interação), o que foi conferido no texto completo e o que não foi, as propostas clínicas, avisos que
ficaram de pé e por quê, e os arquivos de apoio. Mostre duas ou três prévias (a folha de contato e um
slide de figura).

## Sem rede, sem LibreOffice ou no claude.ai

- Sem rede esta skill funciona inteira: ela só lê arquivos locais. Se as fichas e figuras não existirem,
  peça os PDFs ou as figuras ao usuário, ou use a ferramenta de busca disponível para achar o artigo e
  diga o que veio só do resumo.
- Sem `soffice`: monte o .pptx, peça ao usuário para abrir e exportar em PDF, ou renderize com outra
  ferramenta disponível; não entregue sem olhar.
- Sem `python-pptx`: `pip install python-pptx pillow`.

## Arquivos desta skill

- `scripts/montar_deck.py` — deck.json → .pptx (valida antes).
- `scripts/validar_aula.py` — regras pedagógicas e linha do tempo minuto a minuto.
- `scripts/renderizar.py` — .pptx → PDF → PNGs + folhas de contato.
- `scripts/conferir_pptx.py` — notas com tempo acumulado, gráficos nativos, formas fora da página, XML.
- `scripts/materiais.py` — enquetes.md, pre_pos_teste.md, resumo_aluno.md.
- `scripts/_marca.py` — medidas, cores, interações canônicas e medição de texto (mude a marca aqui).
- `references/desenho-instrucional.md` — como desenhar a aula, com a base científica; seção 11: expositiva
  de nível alto e quando escolher cada formato.
- `references/interacoes.md` — os cinco formatos, a checagem rápida da expositiva e como conduzir no Meet.
- `references/questoes.md` — enquetes e questões de alto nível, com exemplos bons e ruins.
- `references/deck-json.md` — esquema completo, um exemplo por tipo de slide.
- `references/marca-boost.md` — a marca medida no deck de referência.
- `references/voz-das-notas.md` — como escrever as notas, com trechos reais.
- `assets/` — logos, `exemplo_expositiva/` (deck.json expositivo de 45 min em 4 partes e questoes.json;
  usa as figuras de `exemplo/`), `exemplo/` (deck.json de caso de 32 min, questoes.json, figuras e
  catálogo), modelos de roteiro (expositiva e caso) e de verificação.
