---
name: boost-education
description: >-
  Orquestrador das aulas da Boost Education (illic ACADEMY · BOOST Education): leva o pedido "monta uma aula sobre X"
  até o PowerPoint pronto (busca de artigos no PubMed, Scopus e JOSPT, leitura crítica, recorte de figuras, roteiro,
  deck .pptx na marca, enquetes, pré e pós-teste, resumo do aluno, relatório do que foi conferido), com quatro pontos
  de checagem com o usuário. Cria a pasta da aula e diz em que etapa ela parou e qual o próximo passo. Use SEMPRE que
  o usuário pedir para montar, preparar, criar ou planejar uma aula, curso, módulo, capacitação, treinamento ou trilha
  de aulas para a equipe ou para a Boost ("monta uma aula sobre...", "prepara a aula de...", "quero uma aula de 30
  minutos sobre...", "planeja uma sequência de aulas"); quando quiser retomar ou saber em que pé está uma aula ("onde
  paramos?", "continua a aula do LCA", "o que falta?"); e quando disser "segue sem parar". Para uma etapa isolada
  bastam as skills boost-pesquisa-artigos, boost-leitura-figuras e boost-aula-slides.
---

# Boost Education · orquestrador da aula

Esta skill não faz a busca, a leitura nem os slides: ela decide **o que vem agora**, chama a skill certa, para nos
quatro pontos em que o usuário precisa decidir e segue sozinha entre eles. A memória do trabalho é a pasta da aula:
cada sessão começa do zero, e `situacao.py` lê a pasta e diz onde parou.

Leia primeiro `references/preferencias.md`. São as respostas que o Daniel já deu (Google Meet, aula única em camadas,
gravada para a equipe, recorte padrão, apresentador). Elas valem como padrão; o pedido da aula ganha delas. Não
pergunte de novo o que está lá.

Scripts desta skill em `scripts/` (chame com `python3 -I <caminho>/scripts/...`). Nos comandos abaixo:
`E` = `scripts/` desta skill, `P` = `../boost-pesquisa-artigos/scripts`, `L` = `../boost-leitura-figuras/scripts`,
`D` = `../boost-aula-slides/scripts`, `AULA` = `aulas/<AAAA-MM>-<slug>`.

## O pipeline

```
pedido ─► 0 briefing ─► 1 busca ─►(C1)─► 2 seleção ─► 3 artigos ─►(C2)─► 4 figuras ─► 5 roteiro ─►(C3)─► 6 deck ─►(C4)─► 7 entrega
          nova_aula     boost-pesquisa-artigos         boost-leitura-figuras                boost-aula-slides           relatorio_final
```

| Etapa | Skill | Produz (na pasta da aula) |
|---|---|---|
| 0 Briefing | esta (`nova_aula.py`) | `00_briefing.md`, `00_andamento.md`, subpastas |
| 1 Busca | boost-pesquisa-artigos, passos 2 a 8 | `01_busca/conceitos.json`, `estrategia.md`, `brutos/` |
| 2 Seleção | boost-pesquisa-artigos, passos 9 a 11 | `registros.json`, `triagem.xlsx`, `selecionados.json` |
| 3 Artigos | boost-leitura-figuras, passos 1 a 4 | `02_artigos/pdf/`, `pendentes.md`, `texto/`, `leitura/` |
| 4 Figuras | boost-leitura-figuras, passo 5 | `03_figuras/<chave>/*.png`, `catalogo.json`, `folha_contato.png` |
| 5 Roteiro | boost-aula-slides, passos 1 a 3 | `04_aula/roteiro.md` (opcional antes: `00_mapa_evidencias.md`) |
| 6 Deck e materiais | boost-aula-slides, passos 4 a 10 | `deck.json`, `<slug>.pptx`, `previa/`, materiais, `verificacao.md` |
| 7 Entrega | esta (`relatorio_final.py`) | `04_aula/entrega.md` |

Ao entrar em cada etapa, leia o SKILL.md da skill dela: os comandos e as armadilhas estão lá. Não improvise a etapa
de outra skill.

## Onde ficam as aulas

Uma pasta por aula em `aulas/<AAAA-MM>-<slug>/`, na raiz do projeto (aqui: `/home/user/illic/aulas/`; o
`.gitignore` já deixa PDFs, textos, recortes e prévias fora do git por direito autoral e tamanho). Outra raiz:
`--raiz` ou a variável `BOOST_AULAS`. Cada skill escreve só na sua parte, e as outras leem dali:

```
aulas/2026-12-lca-retorno-esporte/
  00_briefing.md  00_andamento.md  [00_mapa_evidencias.md]
  01_busca/    conceitos.json estrategia.md brutos/ registros.json triagem.xlsx selecionados.json
  02_artigos/  pdf/ manual/ pendentes.md texto/ leitura/ manifest.json
  03_figuras/  paginas/ <chave>/fig2.png catalogo.json folha_contato.png
  04_aula/     roteiro.md deck.json questoes.json <slug>.pptx previa/ enquetes.md pre_pos_teste.md
               resumo_aluno.md verificacao.md entrega.md
```

`00_andamento.md` guarda o modo (com checagens ou sem parar), as quatro checagens com data e o registro do que
aconteceu; `situacao.py` lê e escreve, e você pode editar à mão. Chave de artigo = SobrenomeAno (vira nome de arquivo
em todas as etapas; não renomeie).

## Começar ou retomar: sempre por `situacao.py`

```bash
python3 -I E/situacao.py aulas                  # todas as aulas e trilhas, com a etapa de cada uma
python3 -I E/situacao.py AULA                   # etapas, próximo passo com o comando, esperas e avisos
```

Rode no início de toda sessão que toque numa aula e depois de cada etapa. Ele lê só arquivos (e roda o validador
pedagógico se houver `deck.json`), não usa rede e não muda nada, exceto com `--marcar`, `--modo` ou `--registrar`.
Ele percebe arquivo velho (planilha editada depois de `selecionados.json`, deck mudado depois do .pptx, seleção nova
sem download) e manda refazer só o que mudou.

Leia a saída assim: "Próximo passo" é o que fazer agora; "Esperando o usuário" são coisas que não travam o trabalho
(exportação do Scopus, PDFs pagos) a menos que sejam a checagem que bloqueia o passo; "Atenção" são decisões suas
(sentinela perdido, seleção grande demais, figura sem CC BY). Se uma pasta antiga não tiver checagens registradas mas
o trabalho já passou delas, ele avisa em vez de travar: confirme com o usuário e registre.

## Aula nova: perguntas mínimas, depois `nova_aula.py`

Antes de criar a pasta, confira no pedido e em `preferencias.md` o que já está respondido. Pergunte **só o que faltar,
em uma única mensagem**, cada pergunta com o padrão entre parênteses, para que "pode seguir" seja resposta suficiente:

1. **Tema e recorte clínico:** qual condição, qual decisão (diagnóstico, prognóstico, tratamento, retorno ao esporte),
   qual população. Muda a busca inteira; é a única que não tem padrão.
2. **Nível da turma:** (padrão: equipe ILLIC em níveis diferentes, aula única em camadas, nível técnico alto).
3. **Quem apresenta:** (padrão: Daniel Santos). Vai para a capa e para a voz das notas.
4. **Formatos de interação disponíveis na plataforma:** (padrão: Google Meet com enquete, chat em cascata, salas de 3,
   mão na câmera e bilhete de saída no chat). Sem salas ou sem enquete, o desenho muda.
5. **Gravada ou vendida fora da empresa:** (padrão: gravada para a equipe). Vendida muda o que se pode fazer com
   figuras de direitos reservados, NC ou ND e exige revisão ética do material de divulgação.
6. **Artigos que ele já quer na aula:** viram sentinelas da busca. E se existe aula, apostila ou slide antigo que sirva
   de base (veja `aulas/_base-*`).

Pergunte também o recorte de evidência só se o pedido sugerir outro que o padrão (`topo_mecanismos`): "o que tem de
novo" é `fronteira`, "só evidência forte" é `so_topo`. Sem resposta, siga com os padrões e diga que seguiu.

```bash
python3 -I E/nova_aula.py --tema "Retorno ao esporte após reconstrução do LCA" --slug lca-retorno-esporte \
  --objetivo "Decidir se libera para o esporte de pivô, justificando com tempo, força, salto e prontidão psicológica" \
  --p "atletas após reconstrução do LCA" --i "cumprir critérios de retorno" --c "não cumprir" --o "segunda lesão" \
  --artigo 27162233 [--recorte so_topo] [--uso venda] [--formatos enquete,chat_cascata,chat] [--sem-parar]
```

Cria as subpastas, o briefing (padrões lidos de `preferencias.md`) e o `00_andamento.md`. Não sobrescreve nada (o
briefing só com `--forcar-briefing`, guardando o anterior). Campo não informado sai como "A PREENCHER" e
`situacao.py` cobra; preencha com o que a conversa já disse antes de perguntar. Objetivos em nível de aplicação,
análise ou avaliação; pelo menos um quantitativo (`boost-aula-slides/references/desenho-instrucional.md`, seção 1).
Para trilha: `--trilha`, `--posicao`, `--aula-anterior` e `--compartilhar-de` (ver "Trilha" abaixo). `--simular`
mostra o que faria.

## Os quatro pontos de checagem

Entre eles, siga sozinho: não peça licença para rodar o próximo script nem para decisões técnicas que as skills já
regulam. Neles, pare, porque depois de cada um vem trabalho longo construído em cima da decisão.

| # | Quando | O usuário decide | Por que parar aqui |
|---|---|---|---|
| 1 | sentinelas testados | aprova a estratégia e cola a string no Scopus, devolvendo a exportação | triagem, leitura e aula saem da busca; e o Scopus só entra pelas mãos dele |
| 2 | seleção exportada e PDFs abertos baixados | aprova a lista; baixa os pagos de `pendentes.md` para `02_artigos/manual/` (JOSPT com a assinatura dele) | ler o artigo errado é a maior perda do pipeline; só ele acessa os pagos |
| 3 | `roteiro.md` escrito | aprova objetivos, caso e linha do tempo | o deck é longo de montar e refazer o desenho depois custa o dobro |
| 4 | deck montado, renderizado e conferido | revisa o deck | é a aula dele, gravada; só ele sabe se o caso e o tom soam reais |

Apresente a checagem assim que ela aparecer e continue o que não depende dela (a Crossref enquanto ele vai ao Scopus;
as fichas dos abertos enquanto ele baixa os pagos). O que mostrar em cada uma, com modelos de mensagem:
`references/checagens.md`. Aprovou? Registre na hora, senão a próxima sessão não sabe:

```bash
python3 -I E/situacao.py AULA --marcar 2 --nota "aprovou a lista; vai baixar Wellsandt2017 e Grindem2016"
python3 -I E/situacao.py AULA --registrar "trocou Kyritsis2016 por Webster2016"
```

**Modo sem parar.** Se ele disser para seguir sem parar: `situacao.py AULA --modo sem-parar --nota "..."`. Use só
acesso aberto, deixe o Scopus para depois, transforme cada checagem numa suposição escrita no briefing e registre as
pendências. No fim, as quatro revisões vão juntas com a entrega (o relatório lista as checagens não feitas).

## Subagentes: quando existirem, uma leitura por artigo e uma busca por base

- **Busca:** um subagente para o PubMed (com as voltas de sentinela) e outro para a Crossref, ao mesmo tempo; OpenAlex,
  consolidação e triagem no principal. Nunca dois scripts que chamam o NCBI juntos (limite de 3 requisições/s).
- **Leitura:** rode `baixar_artigos.py`, `extrair_texto.py` e `detectar_figuras.py` uma vez no principal (gravam o
  manifest sem trava). Depois, um subagente por artigo escreve a ficha e recorta e aprova as figuras daquela chave
  (o catálogo tem trava). `conferir_recortes.py` no fim, no principal.
- **Slides:** em série no principal; um subagente revisor pode olhar o render.

Sem subagentes, a mesma ordem em série, começando pelos artigos âncora e de evidência principal. Modelo de pedido para
o subagente de leitura e a tabela do que pode rodar junto: `references/subagentes.md`.

## Padrões que valem para o curso inteiro

- **Nível técnico alto.** A turma tem especialistas: cada aula traz o número que sustenta a decisão (efeito com IC,
  DMCI, NNT, acurácia, certeza) e pelo menos um dado que contraria ou refina um hábito comum. Iniciante entra pela
  âncora de cada bloco, não por uma aula mais fraca.
- **Nada inventado.** Número em slide tem artigo e página. PMID, DOI e descritor só valem se vieram de API ou arquivo.
  O que veio só do resumo é dito como tal. Proposta clínica sem ensaio que a teste é chamada de proposta.
- **`verificacao.md` honesto.** Cada número, onde foi conferido; o que veio só do resumo; propostas; dados do caso
  fictício; figuras e licenças; o que falta conferir. A mesma honestidade nas notas do slide de referências.
- **Figuras com citação e licença.** Recorte só aprovado depois de aberto; citação completa no rodapé; licença no
  catálogo. Aula gravada para a equipe usa a figura com citação; o relatório final lista as de direitos reservados,
  NC e ND. Se a aula for vendida, essas viram gráfico próprio "Adaptado de" ou pedido de permissão ao editor.
- **Ética na divulgação.** Aula para a equipe não é publicidade. Mas qualquer material de divulgação (post, anúncio,
  página de venda, chamada para o curso, depoimento) passa pela skill `etica-fisioterapia` (COFFITO 424/2013) antes
  de sair: sem promessa de resultado, sem sensacionalismo, sem antes e depois.
- **Uma aula, 30 a 35 minutos.** O validador da skill de slides reprova acima de 35. Tema grande vira trilha, não
  aula longa.

## Trilha de várias aulas

Quando o pedido for um curso ou uma sequência: escreva primeiro o plano da trilha (`assets/trilha_modelo.md`) e
aprove com o usuário. Ordem: diagnóstico e prognóstico antes do tratamento; uma pergunta clínica central por aula;
pré-requisito escrito como algo que a turma sabe fazer. A aula N+1 abre com uma pergunta de recuperação de memória
sobre a aula N, tirada do que a turma errou (bilhete de saída, enquete, pós-teste), antes do caso novo; o pós-teste de
cada aula vai 7 a 14 dias depois. Aulas da mesma condição podem dividir a busca (`--compartilhar-de`). Detalhes e o
exemplo da trilha do cotovelo: `references/trilha.md`.

## Sem rede, sem shell ou no claude.ai

- Sem rede: `nova_aula.py`, `situacao.py` e `relatorio_final.py` funcionam (só leem e escrevem arquivos). Cada skill
  irmã diz o que fazer sem rede: strings para o usuário colar no PubMed e no Scopus e importar o arquivo; PDFs pedidos
  a ele; slides funcionam inteiros. Use a ferramenta de busca web disponível para achar artigos e versões gratuitas,
  nunca para completar PMID ou DOI de memória.
- Sem shell: siga a mesma ordem e os mesmos pontos de checagem, escrevendo os arquivos à mão pelos modelos das skills,
  e diga claramente o que não foi gerado (recortes, .pptx).
- Sem as outras skills instaladas: `situacao.py` imprime `<skill ...>/scripts` no lugar do caminho; peça ao usuário
  para instalá-las.

## Entrega

Quando `situacao.py` disser que só falta a entrega (checagem 4 feita ou modo sem parar):

```bash
python3 -I E/relatorio_final.py AULA
```

Gera `04_aula/entrega.md`: a lista de arquivos (com o que falta), a **tabela de evidências** (chave, desenho, ano,
revista, papel, PDF, licença, como foi lido, slides em que aparece, o que o deck declara como conferido), as figuras
do deck com licença e as de direitos reservados, e **o que não foi conferido** (PDFs que não chegaram, fichas só do
resumo, referências não conferidas, Scopus ausente, checagens não feitas, mais as seções de resumo, propostas e
pendências de `verificacao.md`). Releia antes de mandar: ele junta o que está nos arquivos, não julga.

Mensagem final ao usuário, sem enchimento:

1. O `.pptx` (caminho), duração e número de slides, e a folha de contato do deck (`04_aula/previa/folha-1.png`).
2. Os materiais: `enquetes.md` (cadastrar no Meet antes da aula), `pre_pos_teste.md` (Forms; pós-teste 7 a 14 dias
   depois), `resumo_aluno.md`.
3. A tabela de evidências (de `entrega.md`, as colunas que couberem) e a folha de contato das figuras.
4. O que não foi conferido e as figuras de direitos reservados, em lista curta.
5. O que ainda depende dele (PDFs, Scopus, revisão), se houver.

## Scripts desta skill

| Script | Faz |
|---|---|
| `nova_aula.py` | cria `aulas/<AAAA-MM>-<slug>/`, subpastas, `00_briefing.md` e `00_andamento.md`; trilha, aula anterior, busca compartilhada |
| `situacao.py` | etapa atual, próximo passo com comando, esperas e avisos; lista as aulas; marca checagens, modo e registro (`--json` para máquina) |
| `relatorio_final.py` | `04_aula/entrega.md`: arquivos, tabela de evidências, figuras e licenças, o que não foi conferido |

Referências: `references/preferencias.md` (padrões do Daniel; não apague), `references/checagens.md` (o que mostrar em
cada parada), `references/subagentes.md` (paralelismo e modelo de pedido), `references/trilha.md` (várias aulas).
Modelo: `assets/trilha_modelo.md`.

## Limites

- `situacao.py` julga pelo que está nos arquivos: sabe que `folha-1.png` existe, não que alguém olhou; sabe que a
  ficha tem "Texto lido: completo", não se a leitura foi boa. Os passos de olhar continuam sendo seus.
- `conferir_pptx.py` não deixa rastro em arquivo; por isso `situacao.py` pede `--registrar "conferir_pptx: OK"`.
- Pasta compartilhada por link simbólico some no claude.ai e em alguns sistemas; lá, copie.
