# Estratégia de busca: o método

Como um bibliotecário de revisão sistemática monta uma busca, adaptado ao objetivo daqui: achar a melhor evidência para uma aula de 30 a 35 minutos, sem deixar passar o artigo que todo especialista conhece. Não é uma revisão sistemática; é uma busca reprodutível, com sensibilidade testada.

Os números do exemplo (tendinopatia do manguito rotador e exercício com carga) são reais, obtidos com os scripts desta skill em 24/11/2026.

## Índice

1. Da pergunta aos blocos
2. O que NÃO entra na string
3. Dentro do bloco: vocabulário controlado e texto livre
4. Truncagem e proximidade
5. Armadilhas do PubMed
6. Filtros de desenho e o preço deles
7. Artigos-sentinela e teste de sensibilidade
8. Pearl growing e perseguição de citações
9. Iterar, e quando parar
10. Como documentar
11. Exemplo trabalhado

## 1. Da pergunta aos blocos

Escreva a pergunta em PICO (ou PECO, quando é exposição): população ou problema, intervenção, comparador, desfecho. O PICO serve para **pensar** e para definir os critérios de triagem. Ele não é o molde da string.

A string é feita de **blocos de conceito**. Dentro do bloco, sinônimos somados com OR; entre blocos, AND. Cada bloco a mais é um AND a mais, e cada AND corta artigos: um registro só é recuperado se tiver pelo menos um termo de **todos** os blocos no título, no resumo ou na indexação.

Regra prática: **dois blocos**, quase sempre condição + intervenção (ou condição + exposição). Um terceiro bloco só entra quando os dois primeiros devolvem volume intratável e o terceiro conceito é daqueles que todo resumo cita (por exemplo a população "athletes" numa pergunta sobre esporte).

## 2. O que NÃO entra na string

- **Desfecho.** Resumos citam o desfecho principal e esquecem os secundários; muitos falam em "outcomes" sem nomear dor, função ou força. Um bloco de desfecho elimina artigos pertinentes de forma silenciosa. Desfecho vira critério de triagem.
- **Comparador.** "Usual care", "placebo", "wait and see" raramente estão no resumo de forma buscável. Mesma lógica.
- **Desenho do estudo dentro dos blocos.** Desenho entra por filtro separado (seção 6), que pode ser ligado e desligado para medir o que se perde.
- **Termos em português.** PubMed e Scopus indexam título e resumo em inglês mesmo quando o artigo é em português; limite de idioma se faz no campo de idioma.
- **NOT.** Excluir "surgery" tira também o ensaio que compara exercício com cirurgia. Se precisar, só no título (`excluir` com `campo: "ti"`), e com teste de sentinela depois.

Anote em `pergunta.nota` de `conceitos.json` o que ficou de fora e por quê. Quem ler a estratégia depois precisa saber que foi decisão, não esquecimento.

## 3. Dentro do bloco: vocabulário controlado e texto livre

Use **os dois**, sempre.

- **MeSH** pega o artigo pelo assunto, mesmo quando o autor usou outra palavra. `[Mesh]` explode: traz também os descritores mais específicos da árvore.
- **Texto livre** em título e resumo (`[tiab]`) pega o que o MeSH não alcança: artigos recentes ainda não indexados, revistas fora do MEDLINE (que chegam ao PubMed sem MeSH), conceitos sem descritor próprio e nomenclatura nova.

No exemplo, 207 dos 1.551 registros do PubMed (13%) não tinham nenhum MeSH. Uma busca só com MeSH nunca os veria; um dos sentinelas (Ingwersen 2017, Orthop J Sports Med) está nesse grupo.

Para montar a lista de sinônimos:

1. Abra dois ou três artigos-sentinela no PubMed e copie os MeSH que eles receberam e as palavras dos títulos.
2. Olhe os termos de entrada do descritor no banco MeSH: são os sinônimos que o próprio NLM reconhece.
3. Inclua a nomenclatura antiga. A literatura de ombro anterior a 2015 fala em "subacromial impingement"; a atual, em "rotator cuff related shoulder pain". Quem busca só o nome novo perde uma década.
4. Inclua grafia britânica e americana quando a raiz muda, e siglas consagradas (RCRSP, ACL).
5. Descritor criado há pouco pode não alcançar o artigo antigo. Depende do descritor: "Rotator Cuff Injuries" (2017) foi aplicado para trás e traz 1.212 artigos de 2005-2010; "Return to Sport" (2016) não tem nenhum desse período. Como não dá para saber sem medir, mantenha o descritor antigo e o texto livre. A tabela está em `vocabulario-fisioterapia.md`.

Explosão: desligue (`"explodir": false`) quando o descritor é uma estrutura anatômica ou um termo-guarda-chuva cujos filhos não interessam. Tópico principal (`[Majr]`) aumenta a precisão e derruba a sensibilidade; reserve para buscas exploratórias.

## 4. Truncagem e proximidade

**Truncagem** (`*`) recupera as variações de uma raiz: `tendinopath*` pega tendinopathy, tendinopathies, tendinopathic. Trunque depois de uma raiz longa o bastante: `tend*` traz 616 mil registros. No PubMed são exigidas 4 letras antes do `*`; com menos, o asterisco é descartado sem aviso (`str*[tiab]` foi traduzido como `"str"[Title/Abstract]`).

**Frase** (`"subacromial pain"`) exige as palavras juntas e nessa ordem. É precisa e frágil: não pega "pain in the subacromial region".

**Proximidade** fica no meio: as palavras a até *n* palavras uma da outra, em qualquer ordem. É a ferramenta certa para conceitos que aparecem em muitas construções ("progressive loading", "loading was progressed", "progressive resistance"). No exemplo, `"rotator cuff pain"[tiab]` como frase achou 14 registros; `"rotator cuff pain"[tiab:~3]` achou 753.

Limites: no PubMed a proximidade só existe em título e título/resumo, não respeita ordem e **é ignorada se houver truncagem** (`"rotator cuff tendinopath*"[tiab:~3]` foi traduzido como frase simples). No Scopus, `W/n` e `PRE/n` aceitam truncagem e listas com OR. O script traduz os dois lados e avisa do que se perde.

## 5. Armadilhas do PubMed

1. **Mapeamento automático de termos.** Termo digitado sem etiqueta de campo é reinterpretado: `rotator cuff tendinopathy exercise` virou uma expressão com `[MeSH Terms]` e `[All Fields]` para cada palavra. Às vezes ajuda; nunca é controlável. Aspas, truncagem ou etiqueta de campo desligam o mapeamento. Por isso todo termo gerado aqui tem etiqueta.
2. **Descritor errado devolve zero, em silêncio.** `"Rotator Cuff Tears"[Mesh]` é termo de entrada, não descritor: devolveu 0 registros, com um aviso que só aparece na resposta da API. O bloco continua funcionando pelos outros termos e ninguém nota. Defesa: `--verificar-mesh` e `--diagnostico`.
3. **Frase não encontrada.** Uma frase entre aspas que não existe no índice devolve zero (`quotedphrasesnotfound`). O script mostra como AVISO.
4. **Tipos de publicação mudam de nome.** `consensus development conference[pt]` não existe mais; hoje é `"consensus statement"[pt]`, com 30 mil registros. O filtro de diretrizes desta skill já usa o nome atual, mas a lição vale para qualquer filtro copiado de artigo antigo.
5. **Etiqueta de várias palavras sem aspas.** `consensus development conference[pt]` sem aspas foi quebrado e a palavra "conference" virou termo solto. Cite sempre.
6. **Curinga `?`.** Não existe no PubMed: `stabili?ation[ti]` virou `"stabili"[All Fields] AND "ation"[Title]`.

A defesa comum a todas: **ler a tradução** (`querytranslation`) que `pubmed_busca.py` imprime e grava. Cada termo tem de aparecer com o campo que você quis. `[All Fields]` onde você não pediu é sinal de problema, e o script avisa.

## 6. Filtros de desenho e o preço deles

Filtro metodológico é um bloco pronto, validado contra um padrão-ouro, que seleciona um desenho de estudo. Os desta skill:

| Variante | Filtro no PubMed | Origem |
|---|---|---|
| `rs` | `systematic[sb]` + tipo Meta-Analysis + palavras de título | Subconjunto de revisões sistemáticas da NLM. Sensível, pouco preciso. |
| `ecr` | Cochrane Highly Sensitive Search Strategy, versão sensibilidade e precisão (2008) | Cochrane Handbook, suplemento técnico do capítulo 4. Acrescentamos `randomised[tiab]`. |
| `ecr_sensivel` | A versão de máxima sensibilidade do mesmo filtro | Idem. Para quando o padrão perde um ensaio. |
| `diretriz` | Tipos Practice Guideline, Guideline, Consensus Statement + palavras de título | Pragmático, na linha do filtro CADTH. **Não validado.** |

As versões Scopus são traduções aproximadas, sem validação: o Scopus não tem tipo de publicação "Randomized Controlled Trial".

O preço: todo filtro perde artigos. No exemplo, o filtro `ecr` reduziu 2.317 para 894 e manteve os 6 ensaios-sentinela; o `rs` reduziu para 209 e manteve as 3 revisões; o `diretriz`, para 46, com a diretriz-sentinela dentro. Se algum sentinela do desenho certo sumir quando o filtro entra, a perda é do filtro: troque pela versão sensível ou rode sem filtro e classifique depois (o `consolidar.py` classifica o desenho de todo jeito).

Diretrizes merecem busca à parte: muitas saem em sites de sociedades (APTA, NICE, AAOS) e não em revista indexada.

## 7. Artigos-sentinela e teste de sensibilidade

Antes de montar a busca, liste 5 a 10 artigos que **têm** de aparecer: a diretriz mais recente, as revisões que todo mundo cita, os ensaios que mudaram a prática. Fontes: a lista de referências de uma diretriz, o que o próprio Daniel já conhece, uma busca rápida de reconhecimento.

Escolha sentinelas variados: desenhos diferentes, anos diferentes, nomenclaturas diferentes. Dez sentinelas iguais testam pouco.

Depois de montar a busca, rode `teste_sentinela.py`. Para cada sentinela perdido o script diz **qual bloco** o eliminou (ou qual limite, ou qual filtro) e mostra os MeSH e as palavras do título do artigo que não estão no bloco. É dali que saem os termos que faltam.

Leitura do resultado:

- Perdido por um **bloco**: falta sinônimo. Acrescente e teste de novo.
- Perdido por **limite de ano ou idioma**: decida se o limite está certo. Às vezes está, e o sentinela é que era antigo.
- **Sem MeSH** (registro `PubMed-not-MEDLINE` ou ainda em processamento): só texto livre resolve.
- **Fora do PubMed**: é para isso que existem Crossref, Scopus e a perseguição de citações.
- Recuperado pela string mas **fora de `brutos/pubmed.json`**: o total passou de `--max` e ele ficou no corte. Aumente `--max`.

A meta é 100% na variante `base`. Com filtro de desenho, cada sentinela deve ser recuperado por pelo menos um dos filtros; a matriz no fim do relatório mostra isso.

## 8. Pearl growing e perseguição de citações

**Pearl growing** é usar um artigo bom (a pérola) para achar outros: tirar dele descritores e vocabulário e devolver à busca. O relatório do teste de sentinela já entrega essa matéria-prima.

**Perseguição de citações** sai do vocabulário: parte de um sentinela e pega quem ele cita (para trás) e quem o cita (para a frente). Acha artigos que nenhuma string acharia porque usam outras palavras. `openalex_enriquecer.py --perseguir` faz isso e filtra pelo bloco da condição.

No exemplo, perseguir uma revisão de 2020 e a diretriz de 2025 trouxe 152 registros pertinentes à condição; 85 deles não estavam em nenhuma outra fonte, entre eles uma revisão sistemática do JOSPT de 2025 sobre achados de imagem em ombros assintomáticos, que não fala em exercício e por isso nunca passaria pelo bloco da intervenção. É material de contexto e mecanismo que enriquece a aula.

Para a frente, a perseguição é a melhor forma de achar o que saiu **depois** de um artigo-chave.

## 9. Iterar, e quando parar

O ciclo: montar, contar, ler a tradução, testar sentinelas, ajustar, anotar. Duas ou três voltas costumam bastar.

Olhe o `--diagnostico` (contagem por termo):

- Termo com **zero**: erro de grafia ou descritor inexistente.
- Termo que sozinho responde por quase todo o bloco: é a fonte do ruído. Veja se ele é necessário (no exemplo, `exercis*` traz 286 mil registros, mas sem ele o ensaio GRASP, que fala só em "progressive exercise", se perde; ficou, e a decisão foi anotada).
- Termo que não acrescenta nada depois dos outros: pode sair.

Pare quando: (a) todos os sentinelas voltam; (b) um termo novo acrescenta só ruído nos primeiros 20 a 30 resultados; (c) a perseguição de citações devolve quase só o que você já tem; (d) o volume cabe na triagem. Para uma aula, triar os 60 a 100 primeiros da planilha por pontuação, mais todas as diretrizes e revisões recentes, é suficiente. Volume alto na variante `base` não é problema: a priorização cuida da ordem.

Se o volume estiver intratável, aperte nesta ordem: limite de ano, texto livre só no título para o termo mais ruidoso, filtro de desenho. Bloco extra é o último recurso.

## 10. Como documentar

`estrategia.md` é gerado e guarda: pergunta, blocos, limites, cada string, a data, as contagens por base, a tradução do PubMed, o resultado dos sentinelas e os números da consolidação. Falta só a parte humana, na seção "Decisões e histórico" (que o script preserva):

- o que mudou em cada volta e por quê;
- o efeito na contagem e nos sentinelas;
- o que ficou de fora de propósito;
- a data da exportação do Scopus e a string exata que foi colada lá.

Com isso a busca pode ser refeita daqui a um ano para atualizar a aula, e qualquer colega entende de onde vieram os artigos.

## 11. Exemplo trabalhado

**Tema:** tendinopatia do manguito rotador, exercício resistido com carga. Arquivo completo: `exemplo-conceitos-manguito.json`.

**Pergunta.** P: adultos com tendinopatia do manguito ou dor no ombro relacionada ao manguito. I: exercício resistido com carga. C e O: fora da string, na triagem.

**Primeira tentativa (o que se faz por instinto).** Um MeSH e uma frase por bloco: `"Rotator Cuff Injuries"[Mesh] OR "rotator cuff tendinopathy"[tiab]` AND `"Resistance Training"[Mesh] OR "resistance training"[tiab] OR "strength training"[tiab]`, de 2015 em diante. Teste de sentinela: **2 de 10**. O relatório mostrou por quê:

- 6 perdidos pelo bloco do exercício: os artigos estão indexados como **Exercise Therapy** (não Resistance Training) e falam em "strengthening", "progressive exercise", "therapeutic exercise".
- 4 perdidos pelo bloco da condição: indexados como **Shoulder Impingement Syndrome**, com "subacromial impingement" e "subacromial pain" no título.
- 2 perdidos pelo limite de ano (2012 e 2013).

**Versão final.** Condição: 4 MeSH (dois sem explosão), 12 termos livres com a nomenclatura antiga e a nova, uma proximidade (manguito, supraespinal ou subacromial a até 3 palavras de tendinopatia, dor ou impacto). Intervenção: 3 MeSH, 12 termos livres, uma proximidade (progressive, graded, heavy ou high a até 2 palavras de load, loading ou resistance). Limites: 2010 em diante; inglês, português, espanhol; humanos.

| Variante | Registros no PubMed | Sentinelas recuperados |
|---|---|---|
| `base` | 2.317 | 10 de 10 |
| `ecr` | 894 | os 6 ensaios (e 2 revisões) |
| `rs` | 209 | as 3 revisões |
| `diretriz` | 46 | a diretriz |
| `revistas` (JOSPT + BJSM) | 89 | não se aplica |

**O que as outras fontes acrescentaram.** Crossref (JOSPT e BJSM, 1.276 resultados lidos por cursor e filtrados pelos blocos): 84 registros, 11 só dela. A diretriz JOSPT de 2025 quase ficou de fora, porque o resumo fala em "rehabilitation" e não em exercício; por isso o filtro local deixa passar diretrizes e consensos só com o bloco da condição. Perseguição de citações: 85 registros exclusivos.

**Consolidação.** 1.902 identificados, 246 duplicatas, 1.656 únicos. No topo da planilha: a diretriz JOSPT 2025, a revisão com meta-análise pelo princípio FITT (2024), o ensaio de três braços do BJSM (2023), a diretriz de 2022 e a atualização de revisões do JOSPT (2020). Entre os 40 primeiros: 29 revisões sistemáticas, 9 ensaios, 2 diretrizes.
