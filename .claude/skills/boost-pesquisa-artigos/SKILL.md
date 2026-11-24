---
name: boost-pesquisa-artigos
description: "Busca de artigos científicos de fisioterapia no nível de um pesquisador experiente, para as aulas da Boost Education. Monta a estratégia (PICO, blocos de conceito, MeSH + texto livre, filtros de desenho), roda no PubMed e na Crossref (onde entra o JOSPT), gera a string para a busca avançada do Scopus e importa o CSV/RIS/BibTeX exportado, testa a busca com artigos-sentinela, remove duplicatas, prioriza e entrega a planilha de triagem e os artigos selecionados para a aula. Use SEMPRE que o usuário pedir para buscar, pesquisar, levantar ou atualizar artigos, evidências, referências, literatura, revisões, ensaios ou diretrizes sobre um tema clínico (ombro, joelho, coluna, tendinopatia, dor, exercício); quando falar em PubMed, Scopus, JOSPT, MeSH, palavras-chave, descritores ou estratégia de busca; quando for preparar aula baseada em evidência; e quando quiser importar uma exportação do Scopus. Vale também para pedidos vagos como 'ache os melhores artigos sobre X': busca improvisada perde os artigos importantes."
---

# Boost · pesquisa de artigos

Transforma um tema clínico em uma busca reprodutível e testada, e entrega os artigos que vão sustentar uma aula de 30 a 35 minutos. A diferença para uma busca improvisada é mensurável: no tema de exemplo, a string "de instinto" recuperou 2 de 10 artigos obrigatórios; a string montada com este método, 10 de 10.

Tudo fica na pasta da aula, em `aulas/<AAAA-MM>-<slug>/01_busca/`. As próximas etapas (leitura e figuras, slides) leem `selecionados.json` dessa pasta.

## Antes de começar

- Scripts em `scripts/` desta skill. Nos comandos abaixo, `S` é essa pasta e `B` é `aulas/<aula>/01_busca`.
- Todos têm `--help`, falam português e aceitam ser rodados de novo sem perder trabalho.
- E-mail de contato para as APIs: `--email` ou a variável `BOOST_EMAIL`. Nunca escreva o e-mail pessoal do usuário em arquivo.
- **Nada inventado.** PMID, DOI, ISSN e descritor MeSH só valem se vieram de uma API ou de um arquivo. Se não conseguiu conferir, diga que não conferiu.
- O site do JOSPT bloqueia acesso automatizado. Não tente contornar: o JOSPT entra pelo PubMed e pela Crossref.

## Fluxo

### 1. Entender o tema e escrever o briefing

Se `aulas/<aula>/00_briefing.md` já existir, leia. Se não, crie a pasta e escreva, em meia página: tema, público, 2 a 4 objetivos de aprendizagem, pergunta clínica em PICO e o recorte.

Pergunte ao usuário só o que muda a busca e ele ainda não disse: o foco dentro do tema, o recorte e se há artigos que ele já quer ver na aula. O recorte tem três opções (`references/recortes-de-evidencia.md`): `topo_mecanismos` (padrão: melhor evidência + os mecanismos que a explicam), `so_topo` (só diretrizes, revisões sistemáticas e ensaios) e `fronteira` (últimos 3 anos). Sem resposta, siga com o padrão e diga que seguiu.

### 2. Escolher os artigos-sentinela

Liste 5 a 10 artigos que a busca **tem** de recuperar: a diretriz mais recente, as revisões mais citadas, os ensaios que mudaram a prática, e os que o usuário indicou. Varie desenho, ano e nomenclatura. Confirme cada um no PubMed e anote o PMID verdadeiro:

```bash
python3 $S/pubmed_busca.py --consulta 'Desmeules[au] AND rotator cuff tendinopathy AND guideline[ti]' --listar 5
```

Sentinela citado de memória, sem conferir, é o erro mais comum: o teste passa a medir a sua memória, não a busca.

### 3. Montar os blocos em `conceitos.json`

Leia `references/estrategia-de-busca.md` (o método) e use `references/vocabulario-fisioterapia.md` (descritores e sinônimos já conferidos). Esquema e exemplo: `references/esquema-conceitos.md` e `references/exemplo-conceitos-manguito.json`.

O essencial:

- Dois blocos, condição e intervenção. **Desfecho e comparador ficam fora da string** (muitos resumos não os citam) e viram critério de triagem; registre isso em `pergunta.nota`.
- Em cada bloco, MeSH **e** texto livre. No tema de exemplo, 1 em cada 8 registros do PubMed não tinha MeSH (artigos recentes e revistas fora do MEDLINE): só o texto livre os alcança.
- Inclua a nomenclatura antiga da condição, grafia britânica e siglas.
- Use `proximidade` para conceitos que aparecem em várias construções ("progressive loading", "loading was progressed").
- Revistas-alvo: escolha em `assets/revistas_alvo.json` (61 revistas com ISSN conferido) as 3 a 8 que importam para o tema; não copie a lista inteira, porque todas entram na busca da Crossref. JOSPT já é padrão.

### 4. Gerar as strings e conferir os descritores

```bash
python3 $S/montar_strings.py $B/conceitos.json --verificar-mesh
```

Grava `estrategia.md` (strings prontas para colar, uma por variante: `base`, `rs`, `ecr`, `diretriz`, `revistas`) e `strings.json`. Com `--verificar-mesh`, cada descritor é conferido no NLM. Corrija todo descritor recusado antes de seguir: no PubMed um MeSH inexistente devolve zero **sem avisar**, e o bloco fica mais fraco sem ninguém notar.

### 5. Rodar o PubMed e ler a tradução

```bash
python3 $S/pubmed_busca.py --conceitos $B/conceitos.json --variante base --so-contar   # quanto dá, sem baixar
python3 $S/pubmed_busca.py --conceitos $B/conceitos.json --diagnostico                 # contagem por termo
python3 $S/pubmed_busca.py --conceitos $B/conceitos.json                               # roda as variantes do recorte
```

O script imprime a **tradução** que o PubMed fez da consulta. Leia: cada termo tem de aparecer com o campo que você pediu. `[All Fields]` onde você não pediu, um termo truncado que perdeu o asterisco ou um AVISO de frase não encontrada indicam erro na string. No diagnóstico, termo com zero é grafia errada ou descritor inexistente; termo que domina o bloco é a fonte do ruído.

Volume alto na variante `base` é aceitável: a priorização ordena a leitura. Se passar de `--max` (1000 por variante), o script avisa e baixa os primeiros pela relevância do PubMed. Relevância não é importância: no tema do LCA (5.286 na `base`), a coorte mais citada do assunto estava na posição 1.503. Com `base` até uns 5.000, rode de novo só ela com `--variante base --max 5000` (cerca de 1 minuto); acima disso, aperte a busca (seção 9 de `references/estrategia-de-busca.md`). Se a saída terminar com ATENÇÃO de variante incompleta (falha de rede no meio), rode de novo só aquela variante: o resultado se soma ao que já foi baixado.

### 6. Testar os sentinelas

```bash
python3 $S/teste_sentinela.py --conceitos $B/conceitos.json --variante base,rs,ecr,diretriz
```

Meta: 100% na `base`. Para cada perdido o relatório diz o que o eliminou (bloco, limite ou filtro) e mostra os MeSH e as palavras do título que faltam no bloco. "A string recupera, mas o registro não está em brutos/pubmed.json" quer dizer corte por `--max`: aumente o `--max` da variante (passo 5). Sentinela mais amplo que a pergunta (um consenso geral de retorno ao esporte numa busca sobre LCA, a diretriz de outra condição) não justifica alargar os blocos: acrescente-o com `python3 $S/pubmed_busca.py --pmids 27226389 --saida $B/brutos/pubmed.json` e anote a decisão. Acrescente os termos, rode os passos 4 a 6 de novo e anote a mudança em "Decisões e histórico" de `estrategia.md` (essa seção é preservada). Duas ou três voltas bastam. Com filtros de desenho, o que importa é a matriz no fim: nenhum sentinela pode ficar fora de todos.

### 7. Crossref (JOSPT e revistas-alvo) e OpenAlex

```bash
python3 $S/crossref_busca.py --conceitos $B/conceitos.json
python3 $S/openalex_enriquecer.py --pasta $B --perseguir sentinelas --de-ano 2018
```

A Crossref cobre o JOSPT e as revistas-alvo por ISSN e filtra localmente pelos blocos (ela não entende booleanos). O OpenAlex traz citações, acesso aberto, licença e URL de PDF aberto para tudo que já foi baixado, e com `--perseguir` segue as citações dos sentinelas: quem os cita e o que eles citam. É assim que aparecem artigos que usam outro vocabulário. Escolha 2 ou 3 sentinelas bons (`--perseguir 32571081,40165544`) se a lista for longa. No recorte `fronteira`, acrescente `--varrer --de-ano <ano>` na Crossref e `--direcao citam` no OpenAlex.

### 8. Pedir a exportação do Scopus

O usuário não tem API do Scopus, só o site. Rode `montar_strings.py` de novo (para registrar as contagens em `estrategia.md`) e mande a ele a string **Scopus `base`** em bloco de código, com estas instruções:

> 1. Entre em **scopus.com** pelo acesso da instituição e abra **Advanced document search**.
> 2. Cole a string inteira no campo de busca e clique em **Search**.
> 3. Anote o número de documentos que aparece no topo.
> 4. Marque **All** (selecionar todos) e clique em **Export**. Escolha **CSV**.
> 5. Na janela de campos, marque tudo em **Citation information** e **Bibliographical information** (precisa incluir DOI, PubMed ID, ISSN, EID, Document type, Abbreviated source title) e, em **Abstract & keywords**, marque **Abstract**, **Author keywords** e **Indexed keywords**. Pode desmarcar referências e financiamento.
> 6. Clique em **Export** e me envie o arquivo (ou salve como `01_busca/brutos/scopus.csv`). Diga também o número do passo 3.
> 7. Se o Scopus limitar a quantidade por exportação, exporte em partes por faixa de ano e salve como `scopus_1.csv`, `scopus_2.csv`.

Se o número for grande demais para ele (mais de uns 2.000), ofereça as strings `rs`, `ecr` e `diretriz` no lugar da `base`. RIS e BibTeX também servem. Depois:

```bash
python3 $S/importar_scopus.py --pasta $B      # lê todos os brutos/scopus*.csv|.ris|.bib
```

Confira se o total lido bate com o número que o usuário informou e leia os avisos (coluna `Abstract` ausente significa refazer a exportação). **Não espere parado**: se o usuário não puder exportar agora, siga sem o Scopus, diga isso em `estrategia.md` e rode a importação e a consolidação de novo quando o arquivo chegar. Nada se perde.

### 9. Consolidar

```bash
python3 $S/consolidar.py --pasta $B --lote 60
```

Une as fontes, remove duplicatas (DOI, PMID, EID, título + ano com tolerância de 1 ano), classifica o desenho do estudo, cria a chave `SobrenomeAno` (estável entre rodadas, porque vira nome de arquivo nas próximas etapas), pontua de 0 a 100 com os motivos por extenso e grava:

- `registros.json`: os registros únicos, em ordem de prioridade;
- `triagem.xlsx`: aba **Triagem** (colunas azuis para decisão, motivo, papel na aula e observações), aba **Fluxo** (números tipo PRISMA, que se atualizam sozinhos) e aba **Leia-me**;
- `triagem_lote.md`: os 60 primeiros sem decisão, com resumo, para você ler;
- `duplicatas.json` e `fluxo.json`: auditoria.

Leia a saída: sentinela ausente ou artigo retratado aparecem como ATENÇÃO. O desenho é inferido de metadados e erra em casos limítrofes; a coluna "Por que esta pontuação" mostra de onde veio.

### 10. Triar por título e resumo

Leia `triagem_lote.md` e decida. Cobertura mínima: todas as diretrizes e revisões sistemáticas recentes do topo, mais os 60 a 100 primeiros da lista. Critérios: o PICO do briefing (é aqui que desfecho e comparador entram), o recorte, e o que cabe em 30 a 35 minutos. Uma aula sustenta de 6 a 12 artigos: 1 ou 2 âncoras, 3 a 5 de evidência principal, 2 ou 3 de mecanismo, 1 contraponto.

Grave as decisões em `$B/decisoes.json`:

```json
[
  {"chave": "Desmeules2025", "decisao": "incluir", "papel": "âncora da aula", "observacoes": "diretriz mais recente; estrutura a aula"},
  {"chave": "Sanders2025", "decisao": "excluir", "motivo": "fora do tema"},
  {"chave": "Liaghat2023", "decisao": "talvez", "observacoes": "ver texto completo"}
]
```

`decisao`: `incluir`, `excluir` ou `talvez` (decidir no texto completo). `motivo` (para excluídos): fora do tema; população diferente; intervenção diferente; desenho inadequado; sem resultados (protocolo); duplicata ou republicação; superado por evidência mais nova; qualidade insuficiente; idioma; sem acesso ao texto; outro. `papel` (para incluídos): âncora da aula; evidência principal; mecanismo; contraponto; aplicação clínica; contexto; leitura complementar. Em `observacoes`, uma frase sobre **por que** o artigo entra: é o que orienta a leitura e os slides.

Aplique e mostre ao usuário:

```bash
python3 $S/consolidar.py --pasta $B --decisoes $B/decisoes.json
```

A planilha passa a trazer a sua proposta. O que o usuário digitar nela **vale mais** que `decisoes.json` nas rodadas seguintes, e artigos que saírem da busca têm a decisão guardada na aba "Fora da busca atual". Apresente a seleção ao usuário em uma tabela curta (chave, desenho, ano, revista, papel, acesso aberto ou pago) e pergunte se quer trocar algo, na conversa ou direto na planilha.

### 11. Entregar os selecionados

```bash
python3 $S/exportar_selecionados.py --pasta $B
python3 $S/montar_strings.py $B/conceitos.json      # atualiza estrategia.md com contagens, sentinelas e fluxo
```

`selecionados.json` é a lista dos incluídos, cada um com o registro completo mais `papel`, `decisao` e `observacoes`. O script avisa de incluído sem papel. Feche com um resumo ao usuário: quantos identificados, duplicatas, triados e incluídos; os sentinelas recuperados; o que é pago (ele baixa com a assinatura dele); e as limitações (Scopus pendente, o que não pôde ser conferido).

## Sem rede

No claude.ai, ou quando o proxy bloquear as APIs, os scripts falham com mensagem clara ("sem acesso a ..."). O que continua funcionando e o que pedir:

1. `montar_strings.py` (sem `--verificar-mesh`) funciona offline. Entregue as strings para o usuário colar no PubMed e no Scopus. Use só descritores de `references/vocabulario-fisioterapia.md`, que já foram conferidos.
2. PubMed: peça que ele rode a string em pubmed.ncbi.nlm.nih.gov, clique em **Save**, escolha **All results** e **Format: PubMed**, e envie o arquivo. Importe com `pubmed_busca.py --importar arquivo.txt --saida $B/brutos/pubmed.json`. Peça também que cole a "Search details" (a tradução), para você conferir.
3. Scopus: igual ao passo 8.
4. `importar_scopus.py`, `consolidar.py` e `exportar_selecionados.py` não usam rede. Sem OpenAlex, a planilha sai sem citações nem acesso aberto, e a pontuação usa valor neutro: diga isso.
5. Teste de sentinela sem API: confira se cada sentinela está nos arquivos importados (a consolidação lista os ausentes).
6. Se houver ferramenta de busca na web, use para achar candidatos a sentinela e conferir títulos, nunca para completar PMID ou DOI de cabeça.

## Scripts

| Script | Faz | Grava em `01_busca/` |
|---|---|---|
| `montar_strings.py` | strings de PubMed, Scopus, Crossref e URL do JOSPT; confere MeSH | `estrategia.md`, `strings.json` |
| `pubmed_busca.py` | esearch + efetch, tradução da consulta, diagnóstico por termo, importação de arquivo do site | `brutos/pubmed.json` |
| `crossref_busca.py` | busca por ISSN (JOSPT por padrão), filtro local pelos blocos | `brutos/crossref.json` |
| `openalex_enriquecer.py` | citações, acesso aberto, licença, PDF aberto; perseguição de citações | `brutos/openalex.json` |
| `importar_scopus.py` | lê CSV, RIS e BibTeX do Scopus | `brutos/scopus.json` |
| `teste_sentinela.py` | sensibilidade da busca e diagnóstico das perdas | `sentinelas.json` |
| `consolidar.py` | deduplicação, desenho, chave, pontuação, planilha | `registros.json`, `triagem.xlsx`, `fluxo.json`, `duplicatas.json` |
| `exportar_selecionados.py` | lê as decisões da planilha | `selecionados.json` |

## Referências

- `references/estrategia-de-busca.md`: o método completo, com o exemplo do manguito rotador. Leia antes de montar os blocos.
- `references/esquema-conceitos.md` e `references/exemplo-conceitos-manguito.json`: formato de `conceitos.json`.
- `references/vocabulario-fisioterapia.md`: 335 descritores MeSH conferidos, os termos que parecem MeSH e não são, sinônimos por tema, siglas de instrumentos e as revistas-alvo com ISSN.
- `references/sintaxe-bases.md`: PubMed x Scopus x Crossref x site do JOSPT, e os erros de tradução entre elas. Consulte quando uma string der erro ou resultado estranho.
- `references/recortes-de-evidencia.md`: os três recortes e os pesos da pontuação.

## Limites que você deve dizer ao usuário

- O Scopus não é consultado por aqui: depende da exportação dele. A sintaxe Scopus vem da documentação e não foi testada no site.
- O desenho do estudo e a pontuação são triagem automática para ordenar a leitura. Quem decide é a leitura do resumo e, depois, do texto completo.
- Diretrizes de sociedades (APTA, NICE, AAOS) podem estar fora das bases; vale uma busca manual nos sites.
- Resumo não é artigo: nenhum número vai para slide a partir do resumo. Isso é trabalho da etapa de leitura.
