# Esquema de `conceitos.json`

`conceitos.json` é a fonte única da busca. As strings de PubMed, Scopus e Crossref saem dele, o filtro local da Crossref e do OpenAlex usa os mesmos blocos, e a pontuação de aderência também. Mudou a busca? Mude este arquivo e rode `montar_strings.py` de novo.

Exemplo real e testado: `exemplo-conceitos-manguito.json` (nesta pasta).

## Estrutura

```json
{
  "tema": "texto livre, aparece no topo de estrategia.md e da planilha",
  "pergunta": {"P": "...", "I": "...", "C": "...", "O": "...", "nota": "..."},
  "recorte": "topo_mecanismos",
  "blocos": [ { ...bloco... }, { ...bloco... } ],
  "excluir": {"mesh": [], "livres": ["..."], "campo": "ti"},
  "limites": {
    "ano_inicio": 2010, "ano_fim": null,
    "idiomas": ["english", "portuguese", "spanish"],
    "somente_humanos": true,
    "tipos_scopus": ["ar", "re"]
  },
  "revistas_alvo": [ {"nome": "J Orthop Sports Phys Ther", "issn": ["0190-6011", "1938-1344"]} ],
  "sentinelas": [ {"pmid": "40165544", "doi": "10.2519/jospt.2025.13182", "nota": "por que é sentinela"} ]
}
```

| Campo | Obrigatório | O que é |
|---|---|---|
| `tema` | não | Título da busca. |
| `pergunta` | não | PICO/PECO por extenso. Só documentação: **não** gera string. É onde se registra que comparador e desfecho ficaram de fora de propósito. |
| `recorte` | não | `topo_mecanismos` (padrão), `so_topo` ou `fronteira`. Ver `recortes-de-evidencia.md`. |
| `blocos` | sim | Lista de blocos de conceito. Dentro do bloco, OR; entre blocos, AND. Dois blocos é o normal; três só com motivo. |
| `excluir` | não | Bloco NOT. Use com muita parcimônia: NOT elimina artigos que citam o termo de passagem. `campo` padrão é `ti` (só título) por isso. |
| `limites` | não | Anos, idiomas (nomes em inglês), humanos (só PubMed) e tipos de documento do Scopus (`ar` artigo, `re` revisão, `cp` congresso, `ed` editorial, `le` carta, `no` nota). |
| `revistas_alvo` | não | Revistas que ganham pontos na priorização, entram na variante `revistas` e na busca da Crossref. ISSN impresso e eletrônico. Lista conferida em `assets/revistas_alvo.json`. |
| `sentinelas` | não, mas faça | Artigos que a busca tem de recuperar. PMID, DOI ou os dois. Sem sentinela não há teste de sensibilidade. |

## Bloco de conceito

```json
{
  "id": "condicao",
  "rotulo": "Tendinopatia do manguito rotador",
  "papel": "P",
  "campo": "tiab",
  "mesh": [
    "Rotator Cuff Injuries",
    {"termo": "Rotator Cuff", "explodir": false},
    {"termo": "Rotator Cuff Injuries", "subtitulos": ["rehabilitation", "therapy"]},
    {"termo": "Exercise Therapy", "principal": true}
  ],
  "livres": ["rotator cuff tendinopath*", "subacromial pain", "RCRSP"],
  "proximidade": [
    {"a": ["rotator cuff", "supraspinatus"], "b": ["tendinopathy", "pain"], "n": 3, "ordenado": false}
  ],
  "simples": ["rotator cuff", "subacromial"],
  "scopus_extra": ["rotator cuff rupture"]
}
```

| Campo | O que é | Vira o quê |
|---|---|---|
| `id` | Identificador curto, sem espaço. | Aparece nos relatórios e em `blocos_casados`. |
| `rotulo` | Nome legível. | Tabela de `estrategia.md`. |
| `papel` | `P`, `I`, `C`, `O` ou vazio. O bloco com `P` é a **âncora** do filtro local (Crossref, OpenAlex); sem `P`, vale o primeiro bloco. | Só controle. |
| `campo` | `tiab` (padrão), `ti` ou `tw`. | PubMed: `[tiab]`, `[ti]`, `[tw]`. Scopus: `TITLE-ABS-KEY` ou `TITLE`. |
| `mesh` | Descritores. Texto simples = explode, não é tópico principal. Objeto permite `explodir` (padrão `true`), `principal` (padrão `false`) e `subtitulos`. | PubMed: `[Mesh]`, `[Mesh:NoExp]`, `[Majr]`, `"Descritor/subtitulo"[Mesh]`. Scopus: o nome do descritor entra como frase em `TITLE-ABS-KEY` (o Scopus não explode). |
| `livres` | Termos de texto livre. `*` trunca. Escreva frases **sem aspas**: o script cita o que tiver espaço ou hífen. | PubMed: `termo[tiab]`. Scopus: dentro de `TITLE-ABS-KEY(...)`. |
| `proximidade` | Lista de pares: qualquer termo de `a` a até `n` palavras de qualquer termo de `b`. `ordenado: true` exige `a` antes de `b`. | PubMed: `"a b"[tiab:~n]` para cada par (sem ordem; com `*` vira AND, e o script avisa). Scopus: `(a1 OR a2) W/n (b1 OR b2)` ou `PRE/n`. |
| `simples` | Palavras sem sintaxe para buscadores fracos. Se faltar, o script deriva de `livres`. | Consulta da Crossref e URL de busca do site do JOSPT. |
| `scopus_extra` | Termos só para o Scopus (por exemplo vocabulário Emtree, que o MeSH não tem). | Só na string Scopus. |

## Regras que o script confere

- Cada bloco precisa de pelo menos um `mesh`, `livres` ou `proximidade`.
- `id` não pode repetir; `campo` só aceita `tiab`, `ti`, `tw`; `recorte` só aceita os três valores.
- Sentinela precisa de PMID ou DOI válido; revista-alvo precisa de ISSN válido.
- Avisa (sem parar) quando a truncagem tem menos de 4 letras, quando há `?` (o PubMed não entende) e quando a proximidade tem `*` (o PubMed ignora a proximidade).
- Com `--verificar-mesh`, confere cada descritor no NLM e sai com código 1 se algum não existir.

## Variantes geradas

A partir do mesmo arquivo saem: `base` (blocos + limites), `rs`, `ecr`, `diretriz` (base + filtro de desenho), `revistas` (base restrita aos ISSN de `revistas_alvo`) e, com `--ecr-sensivel`, `ecr_sensivel`. Quais rodar depende do recorte; `pubmed_busca.py --variante recorte` escolhe sozinho.
