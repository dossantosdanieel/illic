---
name: boost-aula-slides
description: >-
  Desenha e monta a aula online da Boost Education (30 a 35 minutos, nível técnico alto, aprendizagem
  ativa) e gera o PowerPoint .pptx na marca illic ACADEMY · BOOST Education, idêntica ao deck de
  referência "Caso Marina": roteiro com linha do tempo, deck.json, slides de pergunta, enquete,
  revelação, salas, figura recortada do artigo com destaques, gráficos nativos, tabela, síntese,
  bilhete de saída e referências, notas do apresentador com tempo acumulado, validação pedagógica,
  render em PNG para conferir, e os materiais de apoio (enquetes para o Google Meet, pré e pós-teste
  para o Google Forms, resumo de 1 a 2 páginas para o aluno, verificação do que foi conferido). Use
  SEMPRE que o pedido envolver montar, fazer, criar, desenhar, revisar ou ajustar aula, slides,
  apresentação, PowerPoint, pptx, deck, roteiro de aula, plano de aula, enquete, quiz, pré-teste,
  pós-teste, questões, resumo para o aluno ou notas do apresentador da Boost ou da illic ACADEMY; quando
  o usuário disser "agora monta a aula", "transforma isso em slides", "faz a apresentação com as
  figuras", "ajusta o tempo da aula", "deixa mais interativo"; e logo depois da skill
  boost-leitura-figuras. Não improvise slides fora desta skill: a marca, o tempo e a interação só saem
  certos com os scripts dela.
---

# Aula Boost: do artigo ao .pptx

Esta skill transforma as fichas de leitura e o catálogo de figuras de uma aula em uma aula online de
**30 a 35 minutos** (alvo 32), desenhada para a turma decidir o tempo todo, e gera o .pptx na marca
Boost mais os materiais de apoio. O público são fisioterapeutas da equipe ILLIC em níveis diferentes;
a aula é uma só, em camadas, e é gravada para a equipe. Leia antes as preferências do Daniel em
`../boost-education/references/preferencias.md` (se existir): elas mandam quando o pedido não disser
outra coisa.

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

Dois ou três, em nível de aplicação, análise ou avaliação (decidir, interpretar, calcular, criticar),
cada um ligado a uma decisão que a turma vai tomar e a uma questão do pós-teste. Pelo menos um objetivo
exige raciocínio quantitativo (tamanho de efeito, IC, NNT, MCID, certeza, sensibilidade e
especificidade). O porquê e os exemplos estão em `references/desenho-instrucional.md`, seções 1 e 8.

### 3. Escrever `roteiro.md`

Use `assets/roteiro_modelo.md`. Monte o caso (um paciente fictício que atravessa a aula e sofre um
revés), escolha 3 a 5 figuras, e distribua o tempo:

- abertura de 3 a 4 min com a **primeira decisão da turma antes de 3 min**;
- 3 blocos de 7 a 9 min no ciclo **prever → ver a evidência → decidir → conferir**, com a pergunta sempre
  antes da figura;
- fechamento de 4 a 5 min: desfecho, recuperação de memória, síntese, bilhete de saída.

Cada bloco ganha uma âncora ("Para começar") e um desafio. Formatos de interação e como conduzir cada
um: `references/interacoes.md`. Corte conteúdo antes de cortar interação: o conteúdo cortado vai para o
resumo do aluno.

### 4. Escrever `deck.json` e `questoes.json`

Copie `assets/exemplo/deck.json` (aula completa de 32 min com todos os 16 tipos de slide) e reescreva.
O esquema campo a campo, com um exemplo por tipo, está em `references/deck-json.md`. Pontos que mais
erram:

- título de slide de evidência diz a **conclusão** ("Aos 9 meses quase todos passam no hop; metade
  falha no **quadríceps**"), com uma palavra-chave em negrito;
- até ~70 palavras visíveis por slide; o resto vai para `notas`;
- todo slide que afirma evidência tem `fonte`; dado do caso fictício leva `"origem": "caso"`;
- figura com `o_que_olhar` (2–3 pontos) e `destaques` numerados na mesma ordem;
- `bloco` e `papel` em todos os slides, para o validador conferir o ciclo;
- notas na voz do deck de referência (`references/voz-das-notas.md`): papel do slide, o que dizer com os
  números e a origem, o que não antecipar, "Interação: ..." com o roteiro, e "proposta clínica" onde
  nenhum ensaio testou.

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

O validador **reprova**: duração acima de 35 min, primeira interação depois de 3 min, mais de 7 min sem
interação, menos de 5 interações ou de 3 formatos, slide com mais de 100 palavras, slide de evidência
sem fonte, fonte do rodapé ausente das referências, figura inexistente, sem citação ou de baixa
resolução, slide sem notas, falta de bilhete de saída ou de referências, e figura mostrada antes de
qualquer pergunta no bloco. **Avisa**: duração abaixo de 28 min, 6 a 7 min sem interação, 70 a 100
palavras, menos de 25% do tempo em atividade, objetivos com verbo fraco, figura sem legenda, falta de
âncora/desafio, referências sem `conferido`. Corrija todo erro; decida conscientemente cada aviso.

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

Abra o .pptx com python-pptx e confira que toda nota começa com "Tempo: ... (acumulado M:SS)." e que os
gráficos são nativos:

```bash
python3 -c "from pptx import Presentation; p=Presentation('<slug>.pptx'); [print(i, [s.chart.chart_type for s in sl.shapes if s.has_chart], sl.notes_slide.notes_text_frame.text[:70]) for i, sl in enumerate(p.slides, 1)]"
```

### 9. Gerar os materiais

```bash
python3 SK/scripts/materiais.py aulas/<aula>/04_aula/deck.json            # lê questoes.json ao lado
python3 SK/scripts/materiais.py deck.json --questoes outro.json --saida pasta/
```

Gera `enquetes.md` (texto pronto para criar e salvar as enquetes no Meet antes da aula, com gabarito e o
roteiro de todas as interações), `pre_pos_teste.md` (questões em blocos prontos para colar no Google
Forms, mais o gabarito comentado) e `resumo_aluno.md` (objetivos, pontos-chave com números e fontes,
algoritmo de decisão, propostas clínicas, referências; a partir de `meta.resumo`). O script também
confere a forma das questões (pistas, gabarito concentrado, distrator sem explicação). Releia os três: o
script confere a forma, não o conteúdo clínico.

### 10. Escrever `verificacao.md`

Use `assets/verificacao_modelo.md`. Liste cada número da aula e onde foi conferido (texto completo com
página, só resumo, caso fictício), cada proposta clínica, cada figura com licença e as de direitos
reservados, o resultado das três checagens automáticas e o que ainda está pendente. A mesma honestidade
vai para as notas do slide de referências (geradas a partir do campo `conferido`).

### 11. Entregar

Diga ao usuário: caminho do .pptx, duração e número de slides, a linha do tempo resumida (minutos com e
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
- `scripts/materiais.py` — enquetes.md, pre_pos_teste.md, resumo_aluno.md.
- `scripts/_marca.py` — medidas, cores, interações canônicas e medição de texto (mude a marca aqui).
- `references/desenho-instrucional.md` — como desenhar a aula, com a base científica.
- `references/interacoes.md` — os cinco formatos, quando usar e como conduzir no Meet.
- `references/questoes.md` — enquetes e questões de alto nível, com exemplos bons e ruins.
- `references/deck-json.md` — esquema completo, um exemplo por tipo de slide.
- `references/marca-boost.md` — a marca medida no deck de referência.
- `references/voz-das-notas.md` — como escrever as notas, com trechos reais.
- `assets/` — logos, `exemplo/` (deck.json de 32 min, questoes.json, figuras e catálogo), modelos de
  roteiro e de verificação.
