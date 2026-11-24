# Estratégia de busca - Ramo 1a. Tendinopatia medial do cotovelo (epicondilite medial / cotovelo de golfista): diagnóstico e tratamento

Gerado em 2026-11-24 por `montar_strings.py` a partir de `conceitos.json`. Para mudar uma string, edite `conceitos.json` e rode o script de novo: assim PubMed, Scopus e Crossref continuam dizendo a mesma coisa.

## Pergunta e recorte

- **População/problema:** Adultos (trabalhadores e atletas) com tendinopatia medial do cotovelo
- **Intervenção/exposição:** Avaliação clínica e testes; tratamento conservador (exercício/carga, órtese, terapia manual, recursos), injeção de corticoide ou de outros agentes, cirurgia
- **Comparador:** Fora da string
- **Desfechos:** Fora da string: dor, função (DASH, PRTEE), força de preensão, retorno ao trabalho/esporte
- **Nota:** Comparador e desfecho ficam fora da string (muitos resumos não os citam) e entram como critério de triagem. O segundo bloco reúne diagnóstico e tratamento porque a aula cobre os dois; termos genéricos como 'treatment*', 'therap*' e 'diagnos*' ficaram de fora de propósito (casariam com quase tudo). Limite 1990+ para alcançar os clássicos de acurácia e os ensaios antigos de corticoide; citações da aula base anteriores a 1990 entram por PMID (pubmed_busca.py --pmids). Volta 2: o ramo 1a ficou com UM bloco (só a condição). O bloco de diagnóstico/tratamento eliminava epidemiologia e mecanismo (Shiri 2006 perdido) e a literatura da tendinopatia medial é pequena o bastante para triar inteira; proximidade 'medial ~3 epicondylitis' acrescentada para 'medial and lateral epicondylitis' (Dingemanse 2014 perdido).
- **Recorte:** topo da pirâmide + mecanismos (padrão)

## Blocos de conceito

Dentro do bloco os termos se somam (OR); os blocos se cruzam (AND).

| Bloco | Papel | MeSH | Termos livres | Proximidade |
|---|---|---|---|---|
| Tendinopatia medial do cotovelo (`condicao`) | P | Elbow Tendinopathy (sem explosão) | medial epicondylit*; medial epicondylos*; medial epicondylalg*; medial epicondylopath*; medial epicondyle tendin*; medial elbow tendinopath*; medial elbow tendinos*; medial elbow pain; golfer elbow; golfers elbow; golfer's elbow; flexor-pronator; flexor pronator; common flexor tendon*; medial tennis elbow | [medial epicondyle / medial elbow / flexor pronator / common flexor] W/3 [tendinopathy / tendinosis / tendinitis / tendonitis / pain / enthesopathy]; [medial] W/3 [epicondylitis / epicondylalgia / epicondylosis / epicondylopathy] |

## Limites

- Anos: 1990 a hoje
- Idiomas: english, portuguese, spanish
- Somente humanos (PubMed): sim
- Tipos de documento no Scopus: ar, re
- Revistas-alvo: J Orthop Sports Phys Ther (0190-6011, 1938-1344); J Hand Ther (0894-1130, 1545-004X); J Hand Surg Am (0363-5023, 1531-6564); J Hand Surg Eur Vol (1753-1934, 2043-6289); J Shoulder Elbow Surg (1058-2746, 1532-6500); Am J Sports Med (0363-5465, 1552-3365); Cochrane Database Syst Rev (1469-493X)

## PubMed

Cole em https://pubmed.ncbi.nlm.nih.gov/advanced/ ou rode `pubmed_busca.py --conceitos conceitos.json --variante <nome>`.

### Base (só os blocos e os limites) (`base`)

```
(("Elbow Tendinopathy"[Mesh:NoExp] OR "medial epicondylit*"[tiab] OR "medial epicondylos*"[tiab] OR "medial epicondylalg*"[tiab] OR "medial epicondylopath*"[tiab] OR "medial epicondyle tendin*"[tiab] OR "medial elbow tendinopath*"[tiab] OR "medial elbow tendinos*"[tiab] OR "medial elbow pain"[tiab] OR "golfer elbow"[tiab] OR "golfers elbow"[tiab] OR "golfer's elbow"[tiab] OR "flexor-pronator"[tiab] OR "flexor pronator"[tiab] OR "common flexor tendon*"[tiab] OR "medial tennis elbow"[tiab] OR "medial epicondyle tendinopathy"[tiab:~3] OR "medial epicondyle tendinosis"[tiab:~3] OR "medial epicondyle tendinitis"[tiab:~3] OR "medial epicondyle tendonitis"[tiab:~3] OR "medial epicondyle pain"[tiab:~3] OR "medial epicondyle enthesopathy"[tiab:~3] OR "medial elbow tendinopathy"[tiab:~3] OR "medial elbow tendinosis"[tiab:~3] OR "medial elbow tendinitis"[tiab:~3] OR "medial elbow tendonitis"[tiab:~3] OR "medial elbow pain"[tiab:~3] OR "medial elbow enthesopathy"[tiab:~3] OR "flexor pronator tendinopathy"[tiab:~3] OR "flexor pronator tendinosis"[tiab:~3] OR "flexor pronator tendinitis"[tiab:~3] OR "flexor pronator tendonitis"[tiab:~3] OR "flexor pronator pain"[tiab:~3] OR "flexor pronator enthesopathy"[tiab:~3] OR "common flexor tendinopathy"[tiab:~3] OR "common flexor tendinosis"[tiab:~3] OR "common flexor tendinitis"[tiab:~3] OR "common flexor tendonitis"[tiab:~3] OR "common flexor pain"[tiab:~3] OR "common flexor enthesopathy"[tiab:~3] OR "medial epicondylitis"[tiab:~3] OR "medial epicondylalgia"[tiab:~3] OR "medial epicondylosis"[tiab:~3] OR "medial epicondylopathy"[tiab:~3]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Revisões sistemáticas e meta-análises (`rs`)

```
(("Elbow Tendinopathy"[Mesh:NoExp] OR "medial epicondylit*"[tiab] OR "medial epicondylos*"[tiab] OR "medial epicondylalg*"[tiab] OR "medial epicondylopath*"[tiab] OR "medial epicondyle tendin*"[tiab] OR "medial elbow tendinopath*"[tiab] OR "medial elbow tendinos*"[tiab] OR "medial elbow pain"[tiab] OR "golfer elbow"[tiab] OR "golfers elbow"[tiab] OR "golfer's elbow"[tiab] OR "flexor-pronator"[tiab] OR "flexor pronator"[tiab] OR "common flexor tendon*"[tiab] OR "medial tennis elbow"[tiab] OR "medial epicondyle tendinopathy"[tiab:~3] OR "medial epicondyle tendinosis"[tiab:~3] OR "medial epicondyle tendinitis"[tiab:~3] OR "medial epicondyle tendonitis"[tiab:~3] OR "medial epicondyle pain"[tiab:~3] OR "medial epicondyle enthesopathy"[tiab:~3] OR "medial elbow tendinopathy"[tiab:~3] OR "medial elbow tendinosis"[tiab:~3] OR "medial elbow tendinitis"[tiab:~3] OR "medial elbow tendonitis"[tiab:~3] OR "medial elbow pain"[tiab:~3] OR "medial elbow enthesopathy"[tiab:~3] OR "flexor pronator tendinopathy"[tiab:~3] OR "flexor pronator tendinosis"[tiab:~3] OR "flexor pronator tendinitis"[tiab:~3] OR "flexor pronator tendonitis"[tiab:~3] OR "flexor pronator pain"[tiab:~3] OR "flexor pronator enthesopathy"[tiab:~3] OR "common flexor tendinopathy"[tiab:~3] OR "common flexor tendinosis"[tiab:~3] OR "common flexor tendinitis"[tiab:~3] OR "common flexor tendonitis"[tiab:~3] OR "common flexor pain"[tiab:~3] OR "common flexor enthesopathy"[tiab:~3] OR "medial epicondylitis"[tiab:~3] OR "medial epicondylalgia"[tiab:~3] OR "medial epicondylosis"[tiab:~3] OR "medial epicondylopathy"[tiab:~3]) AND (systematic[sb] OR "meta-analysis"[pt] OR "systematic review"[ti] OR meta-analy*[ti] OR "umbrella review"[ti]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Ensaios clínicos randomizados (`ecr`)

```
("Elbow Tendinopathy"[Mesh:NoExp] OR "medial epicondylit*"[tiab] OR "medial epicondylos*"[tiab] OR "medial epicondylalg*"[tiab] OR "medial epicondylopath*"[tiab] OR "medial epicondyle tendin*"[tiab] OR "medial elbow tendinopath*"[tiab] OR "medial elbow tendinos*"[tiab] OR "medial elbow pain"[tiab] OR "golfer elbow"[tiab] OR "golfers elbow"[tiab] OR "golfer's elbow"[tiab] OR "flexor-pronator"[tiab] OR "flexor pronator"[tiab] OR "common flexor tendon*"[tiab] OR "medial tennis elbow"[tiab] OR "medial epicondyle tendinopathy"[tiab:~3] OR "medial epicondyle tendinosis"[tiab:~3] OR "medial epicondyle tendinitis"[tiab:~3] OR "medial epicondyle tendonitis"[tiab:~3] OR "medial epicondyle pain"[tiab:~3] OR "medial epicondyle enthesopathy"[tiab:~3] OR "medial elbow tendinopathy"[tiab:~3] OR "medial elbow tendinosis"[tiab:~3] OR "medial elbow tendinitis"[tiab:~3] OR "medial elbow tendonitis"[tiab:~3] OR "medial elbow pain"[tiab:~3] OR "medial elbow enthesopathy"[tiab:~3] OR "flexor pronator tendinopathy"[tiab:~3] OR "flexor pronator tendinosis"[tiab:~3] OR "flexor pronator tendinitis"[tiab:~3] OR "flexor pronator tendonitis"[tiab:~3] OR "flexor pronator pain"[tiab:~3] OR "flexor pronator enthesopathy"[tiab:~3] OR "common flexor tendinopathy"[tiab:~3] OR "common flexor tendinosis"[tiab:~3] OR "common flexor tendinitis"[tiab:~3] OR "common flexor tendonitis"[tiab:~3] OR "common flexor pain"[tiab:~3] OR "common flexor enthesopathy"[tiab:~3] OR "medial epicondylitis"[tiab:~3] OR "medial epicondylalgia"[tiab:~3] OR "medial epicondylosis"[tiab:~3] OR "medial epicondylopathy"[tiab:~3]) AND (("randomized controlled trial"[pt] OR "controlled clinical trial"[pt] OR randomized[tiab] OR randomised[tiab] OR placebo[tiab] OR "clinical trials as topic"[mesh:noexp] OR randomly[tiab] OR trial[ti]) NOT (animals[mh] NOT humans[mh])) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])
```

### Diretrizes e consensos (`diretriz`)

```
(("Elbow Tendinopathy"[Mesh:NoExp] OR "medial epicondylit*"[tiab] OR "medial epicondylos*"[tiab] OR "medial epicondylalg*"[tiab] OR "medial epicondylopath*"[tiab] OR "medial epicondyle tendin*"[tiab] OR "medial elbow tendinopath*"[tiab] OR "medial elbow tendinos*"[tiab] OR "medial elbow pain"[tiab] OR "golfer elbow"[tiab] OR "golfers elbow"[tiab] OR "golfer's elbow"[tiab] OR "flexor-pronator"[tiab] OR "flexor pronator"[tiab] OR "common flexor tendon*"[tiab] OR "medial tennis elbow"[tiab] OR "medial epicondyle tendinopathy"[tiab:~3] OR "medial epicondyle tendinosis"[tiab:~3] OR "medial epicondyle tendinitis"[tiab:~3] OR "medial epicondyle tendonitis"[tiab:~3] OR "medial epicondyle pain"[tiab:~3] OR "medial epicondyle enthesopathy"[tiab:~3] OR "medial elbow tendinopathy"[tiab:~3] OR "medial elbow tendinosis"[tiab:~3] OR "medial elbow tendinitis"[tiab:~3] OR "medial elbow tendonitis"[tiab:~3] OR "medial elbow pain"[tiab:~3] OR "medial elbow enthesopathy"[tiab:~3] OR "flexor pronator tendinopathy"[tiab:~3] OR "flexor pronator tendinosis"[tiab:~3] OR "flexor pronator tendinitis"[tiab:~3] OR "flexor pronator tendonitis"[tiab:~3] OR "flexor pronator pain"[tiab:~3] OR "flexor pronator enthesopathy"[tiab:~3] OR "common flexor tendinopathy"[tiab:~3] OR "common flexor tendinosis"[tiab:~3] OR "common flexor tendinitis"[tiab:~3] OR "common flexor tendonitis"[tiab:~3] OR "common flexor pain"[tiab:~3] OR "common flexor enthesopathy"[tiab:~3] OR "medial epicondylitis"[tiab:~3] OR "medial epicondylalgia"[tiab:~3] OR "medial epicondylosis"[tiab:~3] OR "medial epicondylopathy"[tiab:~3]) AND ("practice guideline"[pt] OR "guideline"[pt] OR "consensus statement"[pt] OR guideline*[ti] OR "practice guideline*"[tiab] OR consensus[ti] OR "position statement*"[ti] OR "position stand"[ti] OR recommendation*[ti]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Somente revistas-alvo (`revistas`)

```
(("Elbow Tendinopathy"[Mesh:NoExp] OR "medial epicondylit*"[tiab] OR "medial epicondylos*"[tiab] OR "medial epicondylalg*"[tiab] OR "medial epicondylopath*"[tiab] OR "medial epicondyle tendin*"[tiab] OR "medial elbow tendinopath*"[tiab] OR "medial elbow tendinos*"[tiab] OR "medial elbow pain"[tiab] OR "golfer elbow"[tiab] OR "golfers elbow"[tiab] OR "golfer's elbow"[tiab] OR "flexor-pronator"[tiab] OR "flexor pronator"[tiab] OR "common flexor tendon*"[tiab] OR "medial tennis elbow"[tiab] OR "medial epicondyle tendinopathy"[tiab:~3] OR "medial epicondyle tendinosis"[tiab:~3] OR "medial epicondyle tendinitis"[tiab:~3] OR "medial epicondyle tendonitis"[tiab:~3] OR "medial epicondyle pain"[tiab:~3] OR "medial epicondyle enthesopathy"[tiab:~3] OR "medial elbow tendinopathy"[tiab:~3] OR "medial elbow tendinosis"[tiab:~3] OR "medial elbow tendinitis"[tiab:~3] OR "medial elbow tendonitis"[tiab:~3] OR "medial elbow pain"[tiab:~3] OR "medial elbow enthesopathy"[tiab:~3] OR "flexor pronator tendinopathy"[tiab:~3] OR "flexor pronator tendinosis"[tiab:~3] OR "flexor pronator tendinitis"[tiab:~3] OR "flexor pronator tendonitis"[tiab:~3] OR "flexor pronator pain"[tiab:~3] OR "flexor pronator enthesopathy"[tiab:~3] OR "common flexor tendinopathy"[tiab:~3] OR "common flexor tendinosis"[tiab:~3] OR "common flexor tendinitis"[tiab:~3] OR "common flexor tendonitis"[tiab:~3] OR "common flexor pain"[tiab:~3] OR "common flexor enthesopathy"[tiab:~3] OR "medial epicondylitis"[tiab:~3] OR "medial epicondylalgia"[tiab:~3] OR "medial epicondylosis"[tiab:~3] OR "medial epicondylopathy"[tiab:~3]) AND ("0190-6011"[jour] OR "1938-1344"[jour] OR "0894-1130"[jour] OR "1545-004X"[jour] OR "0363-5023"[jour] OR "1531-6564"[jour] OR "1753-1934"[jour] OR "2043-6289"[jour] OR "1058-2746"[jour] OR "1532-6500"[jour] OR "0363-5465"[jour] OR "1552-3365"[jour] OR "1469-493X"[jour]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

## Scopus

Cole em Scopus > Advanced document search (https://www.scopus.com/search/form.uri?display=advanced). Uma string por vez. Depois exporte o resultado (passo a passo no SKILL.md) e salve em `brutos/scopus.csv`.

### Base (só os blocos e os limites) (`base`)

```
(TITLE-ABS-KEY("medial epicondylit*" OR "medial epicondylos*" OR "medial epicondylalg*" OR "medial epicondylopath*" OR "medial epicondyle tendin*" OR "medial elbow tendinopath*" OR "medial elbow tendinos*" OR "medial elbow pain" OR "golfer elbow" OR "golfers elbow" OR "golfer's elbow" OR "flexor-pronator" OR "flexor pronator" OR "common flexor tendon*" OR "medial tennis elbow" OR "Elbow Tendinopathy") OR TITLE-ABS(("medial epicondyle" OR "medial elbow" OR "flexor pronator" OR "common flexor") W/3 (tendinopathy OR tendinosis OR tendinitis OR tendonitis OR pain OR enthesopathy)) OR TITLE-ABS((medial) W/3 (epicondylitis OR epicondylalgia OR epicondylosis OR epicondylopathy))) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Revisões sistemáticas e meta-análises (`rs`)

```
(TITLE-ABS-KEY("medial epicondylit*" OR "medial epicondylos*" OR "medial epicondylalg*" OR "medial epicondylopath*" OR "medial epicondyle tendin*" OR "medial elbow tendinopath*" OR "medial elbow tendinos*" OR "medial elbow pain" OR "golfer elbow" OR "golfers elbow" OR "golfer's elbow" OR "flexor-pronator" OR "flexor pronator" OR "common flexor tendon*" OR "medial tennis elbow" OR "Elbow Tendinopathy") OR TITLE-ABS(("medial epicondyle" OR "medial elbow" OR "flexor pronator" OR "common flexor") W/3 (tendinopathy OR tendinosis OR tendinitis OR tendonitis OR pain OR enthesopathy)) OR TITLE-ABS((medial) W/3 (epicondylitis OR epicondylalgia OR epicondylosis OR epicondylopathy))) AND TITLE-ABS-KEY("systematic review" OR "meta analy*" OR metaanaly* OR "umbrella review") AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Ensaios clínicos randomizados (`ecr`)

```
(TITLE-ABS-KEY("medial epicondylit*" OR "medial epicondylos*" OR "medial epicondylalg*" OR "medial epicondylopath*" OR "medial epicondyle tendin*" OR "medial elbow tendinopath*" OR "medial elbow tendinos*" OR "medial elbow pain" OR "golfer elbow" OR "golfers elbow" OR "golfer's elbow" OR "flexor-pronator" OR "flexor pronator" OR "common flexor tendon*" OR "medial tennis elbow" OR "Elbow Tendinopathy") OR TITLE-ABS(("medial epicondyle" OR "medial elbow" OR "flexor pronator" OR "common flexor") W/3 (tendinopathy OR tendinosis OR tendinitis OR tendonitis OR pain OR enthesopathy)) OR TITLE-ABS((medial) W/3 (epicondylitis OR epicondylalgia OR epicondylosis OR epicondylopathy))) AND (TITLE-ABS-KEY(randomized OR randomised OR randomly OR placebo OR "controlled trial" OR "clinical trial") OR TITLE(trial)) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Diretrizes e consensos (`diretriz`)

```
(TITLE-ABS-KEY("medial epicondylit*" OR "medial epicondylos*" OR "medial epicondylalg*" OR "medial epicondylopath*" OR "medial epicondyle tendin*" OR "medial elbow tendinopath*" OR "medial elbow tendinos*" OR "medial elbow pain" OR "golfer elbow" OR "golfers elbow" OR "golfer's elbow" OR "flexor-pronator" OR "flexor pronator" OR "common flexor tendon*" OR "medial tennis elbow" OR "Elbow Tendinopathy") OR TITLE-ABS(("medial epicondyle" OR "medial elbow" OR "flexor pronator" OR "common flexor") W/3 (tendinopathy OR tendinosis OR tendinitis OR tendonitis OR pain OR enthesopathy)) OR TITLE-ABS((medial) W/3 (epicondylitis OR epicondylalgia OR epicondylosis OR epicondylopathy))) AND (TITLE(guideline* OR consensus OR "position statement*" OR "position stand" OR recommendation*) OR TITLE-ABS-KEY("practice guideline*")) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Somente revistas-alvo (`revistas`)

```
(TITLE-ABS-KEY("medial epicondylit*" OR "medial epicondylos*" OR "medial epicondylalg*" OR "medial epicondylopath*" OR "medial epicondyle tendin*" OR "medial elbow tendinopath*" OR "medial elbow tendinos*" OR "medial elbow pain" OR "golfer elbow" OR "golfers elbow" OR "golfer's elbow" OR "flexor-pronator" OR "flexor pronator" OR "common flexor tendon*" OR "medial tennis elbow" OR "Elbow Tendinopathy") OR TITLE-ABS(("medial epicondyle" OR "medial elbow" OR "flexor pronator" OR "common flexor") W/3 (tendinopathy OR tendinosis OR tendinitis OR tendonitis OR pain OR enthesopathy)) OR TITLE-ABS((medial) W/3 (epicondylitis OR epicondylalgia OR epicondylosis OR epicondylopathy))) AND (ISSN(0190-6011) OR ISSN(1938-1344) OR ISSN(0894-1130) OR ISSN(1545-004X) OR ISSN(0363-5023) OR ISSN(1531-6564) OR ISSN(1753-1934) OR ISSN(2043-6289) OR ISSN(1058-2746) OR ISSN(1532-6500) OR ISSN(0363-5465) OR ISSN(1552-3365) OR ISSN(1469-493X)) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

## Crossref e site do JOSPT

A Crossref não aceita booleanos: recebe palavras e ordena por relevância. O script filtra depois, localmente, pelos blocos de conceito.

```
medial epicondylitis golfer's elbow
```

ISSNs consultados por padrão: 0190-6011, 1938-1344, 0894-1130, 1545-004X, 0363-5023, 1531-6564, 1753-1934, 2043-6289, 1058-2746, 1532-6500, 0363-5465, 1552-3365, 1469-493X.

Busca no site do JOSPT (abra no navegador; o site bloqueia acesso automatizado):

```
("medial epicondylitis" OR "golfer's elbow" OR "medial elbow")
```

<https://www.jospt.org/action/doSearch?AllField=%28%22medial+epicondylitis%22+OR+%22golfer%27s+elbow%22+OR+%22medial+elbow%22%29&AfterYear=1990>

## Filtros metodológicos usados

- **Revisões sistemáticas e meta-análises** (`rs`): PubMed: subconjunto systematic[sb] (filtro de revisões sistemáticas da NLM) somado ao tipo de publicação Meta-Analysis e a palavras de título. Scopus: tradução aproximada, sem validação. systematic[sb] é sensível e pouco preciso: traz revisões narrativas que dizem 'systematic'. A triagem resolve.
- **Ensaios clínicos randomizados** (`ecr`): PubMed: Cochrane Highly Sensitive Search Strategy, versão que maximiza sensibilidade e precisão (revisão de 2008; Cochrane Handbook, suplemento técnico do cap. 4). Scopus: tradução aproximada, sem validação. Acréscimo nosso ao filtro Cochrane: randomised[tiab] (grafia britânica), que só aumenta a sensibilidade.
- **Diretrizes e consensos** (`diretriz`): Filtro pragmático: tipos de publicação do PubMed (Practice Guideline, Guideline, Consensus Statement, nome atual do antigo Consensus Development Conference) e palavras de título, na linha do filtro de diretrizes do CADTH. Não é um filtro validado. Diretrizes de sociedades também ficam fora das bases (sites de APTA, NICE, AAOS). Complete com busca manual.

Todo filtro de desenho troca sensibilidade por precisão. Se um artigo-sentinela sumir quando o filtro entra, a perda é do filtro, não dos blocos: confira com `teste_sentinela.py --variante <nome>`.

## Avisos de tradução entre bases

- Scopus não tem filtro 'humanos' equivalente ao do PubMed; o limite foi deixado de fora na string Scopus. Exclua estudos em animais na triagem.

## Execuções e contagens

### PubMed

| Data | Variante | Total na base | Baixados | Avisos |
|---|---|---|---|---|
| 2026-11-24 | rs | 36 | 36 | - |
| 2026-11-24 | diretriz | 9 | 9 | - |
| 2026-11-24 | ecr | 61 | 61 | - |
| 2026-11-24 | base | 714 | 702 | 12 registro(s) de livro ignorado(s) |
| 2026-11-24 | revistas | 130 | 130 | - |

Registros únicos do PubMed: **702**.

Tradução que o PubMed fez da variante `base` (2026-11-24). Confira se cada termo virou o campo esperado; as traduções das outras variantes estão em `brutos/pubmed.json`.

```
(("Elbow Tendinopathy"[MeSH Terms:noexp] OR "medial epicondylit*"[Title/Abstract] OR "medial epicondylos*"[Title/Abstract] OR "medial epicondylalg*"[Title/Abstract] OR "medial epicondylopath*"[Title/Abstract] OR "medial epicondyle tendin*"[Title/Abstract] OR "medial elbow tendinopath*"[Title/Abstract] OR "medial elbow tendinos*"[Title/Abstract] OR "medial elbow pain"[Title/Abstract] OR "golfer elbow"[Title/Abstract] OR "golfers elbow"[Title/Abstract] OR "golfer's elbow"[Title/Abstract] OR "flexor-pronator"[Title/Abstract] OR "flexor-pronator"[Title/Abstract] OR "common flexor tendon*"[Title/Abstract] OR "medial tennis elbow"[Title/Abstract] OR "medial epicondyle tendinopathy"[Title/Abstract:~3] OR "medial epicondyle tendinosis"[Title/Abstract:~3] OR "medial epicondyle tendinitis"[Title/Abstract:~3] OR "medial epicondyle tendonitis"[Title/Abstract:~3] OR "medial epicondyle pain"[Title/Abstract:~3] OR "medial epicondyle enthesopathy"[Title/Abstract:~3] OR "medial elbow tendinopathy"[Title/Abstract:~3] OR "medial elbow tendinosis"[Title/Abstract:~3] OR "medial elbow tendinitis"[Title/Abstract:~3] OR "medial elbow tendonitis"[Title/Abstract:~3] OR "medial elbow pain"[Title/Abstract:~3] OR "medial elbow enthesopathy"[Title/Abstract:~3] OR "flexor pronator tendinopathy"[Title/Abstract:~3] OR "flexor pronator tendinosis"[Title/Abstract:~3] OR "flexor pronator tendinitis"[Title/Abstract:~3] OR "flexor pronator tendonitis"[Title/Abstract:~3] OR "flexor pronator pain"[Title/Abstract:~3] OR "flexor pronator enthesopathy"[Title/Abstract:~3] OR "common flexor tendinopathy"[Title/Abstract:~3] OR "common flexor tendinosis"[Title/Abstract:~3] OR "common flexor tendinitis"[Title/Abstract:~3] OR "common flexor tendonitis"[Title/Abstract:~3] OR "common flexor pain"[Title/Abstract:~3] OR "common flexor enthesopathy"[Title/Abstract:~3] OR "medial epicondylitis"[Title/Abstract:~3] OR "medial epicondylalgia"[Title/Abstract:~3] OR "medial epicondylosis"[Title/Abstract:~3] OR "medial epicondylopathy"[Title/Abstract:~3]) AND 1990/01/01:3000/12/31[Date - Publication] AND ("english"[Language] OR "portuguese"[Language] OR "spanish"[Language])) NOT ("animals"[MeSH Terms] NOT "humans"[MeSH Terms])
```

### Crossref

| Data | Consulta | ISSNs | Total na base | Lidos | Mantidos |
|---|---|---|---|---|---|
| 2026-11-24 | medial epicondylitis golfer's elbow | 0190-6011, 1938-1344, 0894-1130, 1545-004X, 0363-5023, 1531-6564, 1753-1934, 2043-6289, 1058-2746, 1532-6500, 0363-5465, 1552-3365, 1469-493X | 12896 | 2000 | 35 |

### Teste de sentinela

Variante testada: `base`. Recuperados: **8 de 8** (2026-11-24).

| Sentinela | Título | Resultado | Blocos que falharam |
|---|---|---|---|
| PMID 26001427 | Medial epicondylitis: evaluation and management | recuperado | - |
| PMID 14506342 | Medial epicondylitis in occupational settings: prevalence, incidence and associated risk f | recuperado | - |
| PMID 16518220 | Medial epicondylitis | recuperado | - |
| PMID 9384424 | The efficacy of an injection of steroids for medial epicondylitis. A prospective study of  | recuperado | - |
| PMID 16968862 | Prevalence and determinants of lateral and medial epicondylitis: a population study | recuperado | - |
| PMID 23335238 | Evidence for the effectiveness of electrophysical modalities for treatment of medial and l | recuperado | - |
| PMID 35658623 | Surgical Techniques and Clinical Outcomes for Medial Epicondylitis: A Systematic Review | recuperado | - |
| PMID 41887339 | Eccentric exercise therapy for medial epicondylitis: A systematic review of clinical outco | recuperado | - |


## Artigos-sentinela

- PMID 26001427 - Revisão JAAOS 2015 (Amin): fonte provável do texto da aula base sobre MET
- PMID 14506342 - Descatha 2003: prevalência e incidência ocupacional (citado na aula base, slide 141, que lhe atribui 'até 84%' de comorbidades: conferir no texto)
- PMID 16518220 - Ciccotti 2003 Tech Hand Up Extrem Surg (citado na aula base, slide 139)
- PMID 9384424 - ECR Stahl 1997: injeção de corticoide na epicondilite medial
- PMID 16968862 - Shiri 2006: prevalência populacional de epicondilite lateral e medial
- PMID 23335238 - RS Dingemanse 2014 BJSM: recursos eletrofísicos na epicondilite medial e lateral
- PMID 35658623 - RS Arevalo 2023 AJSM: cirurgia da epicondilite medial
- PMID 41887339 - RS See 2026: exercício excêntrico na epicondilite medial

## Decisões e histórico

<!-- MANUAL: tudo abaixo desta linha é seu e será preservado quando o arquivo for gerado de novo -->

- O histórico das voltas, a string Scopus e a triagem deste ramo estão em `01_busca/estrategia.md` (seção Decisões e histórico).
