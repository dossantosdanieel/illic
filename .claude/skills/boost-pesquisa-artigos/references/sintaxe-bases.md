# Sintaxe das bases: PubMed, Scopus, Crossref e site do JOSPT

Tabela de consulta para conferir as strings que `montar_strings.py` gera e para traduzir à mão quando preciso.

O que está marcado **[testado]** foi verificado na API do PubMed, da Crossref ou do OpenAlex em 24/11/2026. A sintaxe do Scopus vem da documentação da Elsevier e de guias de bibliotecas; o Scopus não pôde ser testado daqui (sem chave de API). Se uma string Scopus der erro ao colar, a mensagem do site aponta o trecho: corrija em `conceitos.json`, não na mão.

## Comparação

| Recurso | PubMed | Scopus (Advanced search) | Crossref (API) | Site do JOSPT |
|---|---|---|---|---|
| Lógica | AND, OR, NOT em maiúsculas; parênteses | AND, OR, AND NOT; parênteses | **não há**: palavras soltas, ordenadas por relevância | AND, OR, NOT básicos |
| Precedência sem parênteses | esquerda para a direita | OR primeiro, depois W/n e PRE/n, depois AND, depois AND NOT | não se aplica | incerta: use parênteses |
| Título + resumo | `termo[tiab]` | `TITLE-ABS(termo)` | `query.bibliographic=` (título, autor, revista, ano) | campo único `AllField` |
| Título, resumo e palavras-chave | `[tiab]` cobre também as palavras-chave do autor; `[tw]` inclui MeSH | `TITLE-ABS-KEY(termo)`: inclui palavras-chave do autor **e** termos de indexação (MeSH, Emtree) | não | não |
| Só título | `termo[ti]` | `TITLE(termo)` | `query.title=` | busca avançada do site |
| Vocabulário controlado | `"Descritor"[Mesh]` (explode); `[Mesh:NoExp]`; `[Majr]`; `"Descritor/subtítulo"[Mesh]` **[testado]** | não há tesauro próprio; `INDEXTERMS("descritor")` busca os termos MeSH/Emtree como texto, **sem explosão** | não | não |
| Frase | aspas: `"subacromial pain"[tiab]` | aspas = frase aproximada (ignora pontuação, pega plural); chaves `{...}` = frase exata | não garante frase | aspas |
| Truncagem | `*` no fim, com 4 letras ou mais antes; vale dentro de frase (`"rotator cuff tendin*"`) **[testado]** | `*` (zero ou mais caracteres) e `?` (um caractere), também dentro de aspas | não | `*` no fim |
| Proximidade | `"a b"[tiab:~n]`: só título e título/resumo, sem ordem, **ignorada se houver `*`** **[testado]** | `a W/n b` (qualquer ordem), `a PRE/n b` (a antes de b); aceita `*` e listas `(a OR b) W/3 (c OR d)`; não aceita AND dentro | não | não |
| Plural e grafia | não: `tendinopathy` não pega `tendinopathies` (use `*`) | singular pega plural e variantes de grafia na maioria dos casos | sim, por relevância | incerto |
| Ano | `2010:2026[dp]` **[testado]** | `PUBYEAR > 2009 AND PUBYEAR < 2027` | `filter=from-pub-date:2010-01-01,until-pub-date:2026-12-31` **[testado]** | `AfterYear=`, `BeforeYear=` na URL |
| Idioma | `english[la]` | `LANGUAGE(english)` | não há filtro confiável | não |
| Tipo de documento | `"randomized controlled trial"[pt]`, `"systematic review"[pt]`, `"practice guideline"[pt]`, `"consensus statement"[pt]` **[testado]** | `DOCTYPE(ar)` artigo, `re` revisão, `cp` congresso, `ed` editorial, `le` carta, `no` nota. Não há tipo "ensaio randomizado" | `filter=type:journal-article` | filtros na tela |
| Revista | `"J Orthop Sports Phys Ther"[jour]` ou `"0190-6011"[jour]` **[testado]** | `ISSN(0190-6011)`, `SRCTITLE(...)`, `EXACTSRCTITLE(...)` | `filter=issn:0190-6011` (vários ISSN somam) **[testado]** | já é o site da revista |
| Humanos | `NOT (animals[mh] NOT humans[mh])` | não há equivalente confiável | não | não |
| Identificadores | `12345678[uid]`, `"10.xxxx/yyy"[aid]` **[testado]** | `PMID(12345678)`, `DOI(10.xxxx/yyy)` | `/works/{doi}` | não |
| Limite de resultados | 10.000 por busca na API | exportação em lotes (ver SKILL.md) | cursor: sem limite; offset: 10.000 | só na tela |

## O que a Crossref é e o que não é

A Crossref é um registro de DOIs, não uma base bibliográfica. Serve aqui para três coisas: cobrir uma revista inteira por ISSN (o JOSPT, que bloqueia robôs no site), achar o que ainda não chegou ao PubMed, e contar citações.

- A consulta casa **qualquer** palavra e ordena por relevância. A consulta do exemplo do manguito devolveu 285 artigos só no JOSPT de 2010 em diante, a maioria apenas com "exercise" ou "loading"; depois do filtro pelos blocos sobraram poucas dezenas. Por isso o script baixa o conjunto e filtra localmente.
- **Com cursor a ordem não é a de relevância** **[testado]**: os primeiros resultados com `cursor=*` eram de 2010, sem relação com o tema. O script só usa cursor quando vai ler o conjunto inteiro; quando o conjunto passa de `--max`, usa offset, que respeita a relevância.
- O resumo só existe quando a editora deposita. JOSPT e BJSM depositam para a maioria dos artigos; cartas e editoriais vêm sem. Registro sem resumo é julgado só pelo título.
- A contagem de citações da Crossref é menor que a do Scopus e a do OpenAlex. A skill prefere a do OpenAlex.

## Site do JOSPT

`https://www.jospt.org/action/doSearch?AllField=<consulta>&AfterYear=2015` (plataforma Atypon). O site responde 403 a qualquer cliente automatizado; é para o usuário abrir no navegador, com o login dele, e conferir à vista se há algo que PubMed e Crossref não trouxeram (em geral não há: o JOSPT é integralmente indexado no MEDLINE). A URL não pôde ser testada daqui.

## Erros comuns ao traduzir entre bases

| Erro | O que acontece | Como evitar |
|---|---|---|
| Colar string PubMed no Scopus | `[tiab]` e `[Mesh]` não existem lá: erro de sintaxe ou busca em todos os campos | use a string Scopus gerada |
| Esperar que o Scopus exploda o MeSH | `"Exercise Therapy"` no Scopus não traz os descritores filhos | ponha os termos específicos em `livres` ou `scopus_extra` |
| Aspas "exatas" no Scopus | aspas no Scopus são frase aproximada; para exata, `{chaves}` | saiba que `"heavy load"` também pega "heavy loads" |
| `NOT` no Scopus | o operador é `AND NOT`, e vai no fim da string | o script já gera assim |
| Escrever `PUBYEAR >= 2010` | o Scopus não aceita `>=` | `PUBYEAR > 2009` |
| Usar `?` no PubMed | vira duas palavras soltas em `[All Fields]` **[testado]** | escreva as duas grafias |
| Proximidade com truncagem no PubMed | a proximidade some sem aviso **[testado]** | palavras inteiras na proximidade do PubMed; o script troca por AND e avisa |
| Truncar com menos de 4 letras no PubMed | o `*` é descartado **[testado]** | raiz mais longa |
| Termo de entrada como se fosse descritor | `"Rotator Cuff Tears"[Mesh]` devolve zero **[testado]** | `--verificar-mesh` |
| Tipo de publicação com nome antigo | `consensus development conference[pt]` devolve zero **[testado]** | `"consensus statement"[pt]` |
| Etiqueta de várias palavras sem aspas | o PubMed quebra a expressão **[testado]** | aspas sempre |
| Filtrar "humanos" no Scopus com `LIMIT-TO` copiado da tela | a sintaxe de refinamento muda entre versões | exclua animais na triagem |
| Contar com o resumo na Crossref | parte dos registros não tem | o filtro local cai para o título e marca `sem_resumo` |
| Comparar contagens entre bases | PubMed, Scopus e Crossref cobrem conjuntos diferentes | compare sentinelas recuperados, não totais |

## Códigos úteis do Scopus

`TITLE-ABS-KEY()`, `TITLE-ABS()`, `TITLE()`, `ABS()`, `AUTHKEY()`, `INDEXTERMS()`, `SRCTITLE()`, `EXACTSRCTITLE()`, `ISSN()`, `DOI()`, `PMID()`, `PUBYEAR`, `DOCTYPE()`, `LANGUAGE()`, `SRCTYPE(j)` (só periódicos), `AFFILCOUNTRY()`.

## Conferir antes de confiar

```bash
# total e tradução, sem baixar nada
python3 scripts/pubmed_busca.py --conceitos <...>/conceitos.json --variante base --so-contar

# contagem por bloco e por termo
python3 scripts/pubmed_busca.py --conceitos <...>/conceitos.json --diagnostico
```

No Scopus, a conferência é do usuário: o número de resultados aparece no topo da página. Peça que ele informe esse número junto com o arquivo exportado; ele tem de bater com o que `importar_scopus.py` leu.
