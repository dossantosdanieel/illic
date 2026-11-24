# Paralelizar com subagentes (e como seguir em série sem eles)

Subagente vale a pena onde o trabalho é independente e longo: uma leitura por artigo, uma busca por base. Ele começa
sem o contexto da conversa, então o pedido precisa levar tudo (caminhos absolutos, chave, pergunta, regras) e dizer o
que devolver. Você continua dono das decisões, das checagens com o usuário e dos arquivos compartilhados.

## O que pode e o que não pode rodar ao mesmo tempo

| Trabalho | Paralelo? | Por quê |
|---|---|---|
| PubMed × Crossref | sim | gravam arquivos diferentes (`brutos/pubmed.json`, `brutos/crossref.json`) |
| Dois scripts que chamam o NCBI (montar_strings `--verificar-mesh`, pubmed_busca, teste_sentinela) | **não** | o NCBI aceita 3 requisições/s sem chave; dois ao mesmo tempo levam HTTP 429 |
| OpenAlex | depois de PubMed e Crossref | lê todos os `brutos/*.json` |
| `consolidar.py`, `exportar_selecionados.py` | só no agente principal | reescrevem `registros.json` e `triagem.xlsx` |
| `baixar_artigos.py`, `incorporar_manuais.py`, `extrair_texto.py`, `detectar_figuras.py` | **uma vez, no principal**, antes de distribuir | gravam `02_artigos/manifest.json` sem trava; dois ao mesmo tempo perdem entradas |
| Ficha de leitura de um artigo | sim, um subagente por artigo | cada um escreve só `02_artigos/leitura/<chave>.md` |
| `recortar.py` (recorte, ajuste, aprovação) | sim, cada subagente só nas chaves dele | `catalogo.json` tem trava de arquivo e mescla as mudanças |
| `conferir_recortes.py` | só no principal, no fim | regrava o catálogo inteiro e a folha de contato |
| roteiro, deck.json, montagem | só no principal | é uma peça só; dividir quebra o fio da aula |
| Revisão do render do deck | sim, um subagente revisor (só leitura) | olho novo acha texto encavalado e destaque fora do lugar |

## Busca: um subagente por base

Na etapa 1, com `conceitos.json` e as strings prontos:

- **PubMed** (um subagente): `pubmed_busca.py` (contar, diagnosticar, baixar), `teste_sentinela.py` e as voltas de
  ajuste. Devolve: contagens por variante, sentinelas recuperados, termos que mudou e por quê. Se ele mudar
  `conceitos.json`, só ele muda; os outros esperam.
- **Crossref** (outro): `crossref_busca.py --conceitos ...`. Devolve: total lido, total após filtro local, JOSPT achados.
- **Diretrizes fora das bases** (opcional, com ferramenta de busca web): sites da APTA/JOSPT CPG, NICE, AAOS, KNGF.
  Devolve título, ano, URL e DOI quando houver. Nunca PMID ou DOI de memória.

Você, enquanto isso, prepara a checagem 1 (estratégia + string Scopus). Depois: OpenAlex, consolidação e triagem no
principal.

## Leitura e figuras: um subagente por artigo

Antes de distribuir, no principal: `baixar_artigos.py`, `extrair_texto.py`, `detectar_figuras.py` (uma vez para a
aula toda). Depois, um subagente por artigo com PDF; os pendentes ganham ficha "só resumo" (pode ser um subagente só
para todos eles).

Modelo de pedido (troque o que está entre colchetes):

```
Você vai ler criticamente um artigo para uma aula da Boost Education (fisioterapeutas, nível técnico alto).
Pasta da aula: [/caminho/absoluto/aulas/2026-12-lca-retorno-esporte]
Artigo: [Grindem2016] · papel na aula: [âncora da aula] · por que entrou: [observacoes de selecionados.json]
Pergunta clínica da aula: [PICO de 00_briefing.md]

Leia antes, nesta ordem:
- [/caminho/.claude/skills/boost-leitura-figuras/SKILL.md], passos 4 e 5
- [/caminho/.claude/skills/boost-leitura-figuras/references/leitura-critica.md]
- [/caminho/.claude/skills/boost-leitura-figuras/references/escolher-figuras.md]

Faça:
1. Escreva 02_artigos/leitura/[Grindem2016].md a partir de assets/ficha_leitura_modelo.md, lendo
   02_artigos/texto/[Grindem2016].md. Todo número com página e tabela/figura. Calculado por você = marcado como
   calculado. O que não deu para conferir vai em "Pendências de verificação".
2. Para as 1 a 3 figuras ou tabelas que a ficha aponta como boas para slide: abra os PNGs (_candidatos.png, o
   recorte, a página _grade.png), ajuste com recortar.py e aprove com --aprovar --tipo --legenda-pt --ensina.
   Use só a chave [Grindem2016]. Não aprove sem ter aberto o PNG. Não rode conferir_recortes.py.
3. Não mexa em manifest.json, selecionados.json nem em arquivos de outros artigos. Não baixe nada.

Devolva em até 15 linhas: os 2 ou 3 números que importam para a aula (com página), o risco de viés em uma frase,
o que muda na conduta, os ids das figuras aprovadas com o que cada uma ensina, e as pendências de verificação.
```

Quando todos voltarem: `conferir_recortes.py`, abra a folha de contato, resolva os PROBLEMAS e, se a aula tiver muitos
artigos, junte os retornos num `00_mapa_evidencias.md` (o número, a página, a certeza, a figura) antes do roteiro.

## Revisor do deck (opcional)

Depois de `renderizar.py`, um subagente só de leitura: abre `04_aula/previa/folha-*.png` e cada `s-NN.png`, compara com
`boost-aula-slides/references/marca-boost.md` e devolve a lista de problemas por slide (texto cortado, destaque fora
do lugar, figura ilegível, título que quebrou feio). Quem corrige é você, no `deck.json`.

## Sem subagentes: a mesma ordem, em série

1. Busca: PubMed (com as voltas de sentinela), depois Crossref, depois OpenAlex. Apresente a checagem 1 assim que o
   teste de sentinelas passar e siga com a Crossref enquanto o usuário vai ao Scopus.
2. Leitura: comece pelos artigos de papel "âncora da aula" e "evidência principal", depois mecanismo e contraponto.
   Ficha e figuras do mesmo artigo de uma vez, enquanto o texto está fresco.
3. Se o tempo da sessão acabar no meio, tudo o que foi gravado fica na pasta; `situacao.py` mostra de onde retomar.
