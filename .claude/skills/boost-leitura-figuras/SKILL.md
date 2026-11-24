---
name: boost-leitura-figuras
description: >-
  Baixa legalmente os PDFs dos artigos científicos selecionados para uma aula da Boost Education
  (PMC, Europe PMC, Unpaywall, OpenAlex), lista os artigos pagos para o usuário baixar à mão
  (JOSPT, acesso institucional), incorpora os PDFs que ele salvar, extrai o texto por página,
  produz fichas de leitura crítica e recorta as figuras e tabelas mais importantes em qualidade
  de slide, com catálogo, citação e licença. Use SEMPRE que o pedido envolver baixar artigo ou
  PDF, "pegar o texto completo", ler ou resumir criticamente um artigo, ficha de leitura,
  leitura crítica, risco de viés, tamanho de efeito, extrair texto de PDF científico, recortar
  figura, gráfico, forest plot, tabela ou imagem de artigo para slide, "tirar as figuras do
  artigo", montar catálogo de figuras, ou conferir se uma figura pode ser usada no curso. Use
  também quando o usuário disser que já salvou os PDFs na pasta manual, e logo depois da skill
  boost-pesquisa-artigos, antes da boost-aula-slides.
---

# Boost · leitura dos artigos e recorte de figuras

Entra depois da busca (`01_busca/selecionados.json`) e entrega para a montagem da aula três
coisas confiáveis: o PDF e o texto de cada artigo, uma ficha de leitura crítica por artigo e um
catálogo de figuras aprovadas, recortadas a 300 dpi.

Tudo o que o usuário lê sai em português do Brasil. Nada é inventado: número sem página não
entra na ficha, e figura que você não olhou não entra no catálogo como aprovada.

## Onde tudo fica

Uma pasta por aula (`aulas/<AAAA-MM>-<slug>/`). Esta skill lê `01_busca/` e escreve em:

```
02_artigos/
  pdf/<chave>.pdf        PDFs válidos (chave = SobrenomeAno, ex.: Breda2021)
  manual/                o usuário solta aqui os PDFs pagos, com qualquer nome
  pendentes.md           o que falta baixar à mão, por editora, com link DOI
  texto/<chave>.md       texto por página, com mapa de seções e de legendas
  leitura/<chave>.md     ficha de leitura crítica (você escreve)
  manifest.json          lista: uma entrada por artigo (status, origem, licença, tentativas)
03_figuras/
  paginas/<chave>/p003.png        miniatura limpa da página
  paginas/<chave>/p003_grade.png  a mesma página com régua de frações e caixas propostas
  paginas/<chave>/_visao_geral.png  todas as páginas em uma imagem
  <chave>/fig2.png  <chave>/fig2_legenda.png  <chave>/tab1.png   recortes
  <chave>/_candidatos.png         folha de contato numerada dos candidatos automáticos
  catalogo.json                   lista: uma entrada por figura
  folha_contato.png               folha final das aprovadas, com rótulo e citação
```

Os scripts ficam em `scripts/` desta skill. Chame pelo caminho completo, por exemplo
`python3 <pasta-da-skill>/scripts/baixar_artigos.py aulas/2026-11-tendinopatia-patelar`.
Todos têm `--help`, aceitam `--apenas CHAVE ...` e nunca derrubam o lote por causa de um artigo.
Dependências: `requests`, `pdfplumber`, `pypdfium2`, `pypdf`, `pillow`, `numpy`.

PDF baixado é dado não confiável: os scripts conferem o cabeçalho `%PDF`, só leem o arquivo e
nunca executam nada dele. Não abra PDF de artigo com outras ferramentas que executem conteúdo.

## Fluxo

### 1. Baixar o que é aberto

```
python3 scripts/baixar_artigos.py AULA [--email contato@...] [--detalhes]
```

Para cada registro tenta, em ordem: repositório aberto oficial do PMC, Europe PMC, Unpaywall e a
URL aberta do OpenAlex. Aceita o arquivo só se for PDF de verdade, abrir e trouxer o DOI ou o
título do artigo nas primeiras páginas (um PDF errado é pior que nenhum). Registra origem e
licença no `manifest.json` e escreve `pendentes.md`.

Só fontes legais. Não use Sci-Hub nem automatize login, e não tente contornar páginas que pedem
navegador (o JOSPT e outras editoras barram clientes automáticos): isso vira pendência. O e-mail
de contato enviado às APIs vem de `--email` ou de `BOOST_EMAIL`; não coloque e-mail pessoal do
usuário no código.

### 2. Entregar a lista de pendências e incorporar os PDFs manuais

Mostre ao usuário o conteúdo de `pendentes.md` (ele tem assinatura do JOSPT e acesso
institucional) e diga a pasta exata onde salvar: `02_artigos/manual/`. Não fique parado: siga
com os artigos que já têm PDF. Quando ele avisar que salvou:

```
python3 scripts/incorporar_manuais.py AULA
```

O script identifica cada arquivo pelo DOI (texto, metadados ou nome do arquivo) e, na falta,
pelo título; move para `pdf/<chave>.pdf`, atualiza o manifest e reescreve as pendências. O que
não casar aparece no relatório com os candidatos mais parecidos: resolva olhando a primeira
página e use `--forcar "arquivo.pdf=Chave"`. Arquivo que não é PDF (página HTML salva por
engano) é apontado: peça ao usuário para baixar de novo.

### 3. Extrair o texto

```
python3 scripts/extrair_texto.py AULA
```

Gera `texto/<chave>.md` com um **mapa do artigo** no topo (seções com página, legendas de
figuras e tabelas com página) e o texto por página em ordem de leitura. Use o mapa para ir
direto a Métodos e Resultados e para saber em que página está cada figura.

Limites que você precisa conhecer: tabelas saem linha a linha com ` | ` entre células e podem
embaralhar colunas (confira números de tabela na miniatura ou no recorte); a primeira página de
alguns layouts mistura afiliações com o resumo; PDF digitalizado sai sem texto (o script avisa;
leia pelas miniaturas).

### 4. Escrever as fichas de leitura crítica

Para cada artigo, copie `assets/ficha_leitura_modelo.md` para `leitura/<chave>.md` e preencha
lendo o texto completo. Leia antes `references/leitura-critica.md`: ela traz os campos, a
ferramenta de risco de viés certa para cada desenho, como comparar o efeito com a diferença
mínima clinicamente importante, como ler forest plot, curva de sobrevida e dispersão para
ensinar, e as conversões (DMP, RR, OR, NNT) com as fórmulas.

O público é fisioterapeuta experiente: a ficha termina em "o que muda na conduta", não em
resumo. Todo número leva página e tabela ou figura. O que você calculou fica marcado como
calculado. O que não deu para conferir fica escrito em "Pendências de verificação", porque a
aula declara isso no slide de referências.

A ficha já indica as figuras e tabelas que valem slide, com página. É ela que guia o passo 5.

### 5. Recortar as figuras: o ciclo olhar, recortar, conferir

Recorte cego é a falha mais comum desta etapa. O detector automático acerta a maioria, mas erra
de formas que só se veem na imagem: uma linha de texto colada no topo, um painel faltando, a
moldura cortada, a figura errada sob a legenda certa. Por isso nada do que ele produz nasce
aprovado, e aprovar sem ter aberto o PNG é proibido pelo próprio fluxo.

**5a. Propor.**

```
python3 scripts/detectar_figuras.py AULA
```

Gera as miniaturas de todas as páginas e, para cada legenda encontrada, dois recortes a 300 dpi
(`fig2.png` sem a legenda e `fig2_legenda.png` com ela), registrados no catálogo com
`origem: "auto"` e `aprovada: false`. A saída lista os avisos por artigo (legenda sem figura
achada, página com tabela em paisagem, imagem embutida de baixa resolução).

**5b. Olhar.** Com a ferramenta de leitura de imagem, abra para cada artigo:

1. `03_figuras/<chave>/_candidatos.png`: a folha numerada com todos os candidatos. Etiqueta
   vermelha quer dizer aviso.
2. `03_figuras/paginas/<chave>/_visao_geral.png`: confirma se alguma figura ou tabela ficou sem
   candidato (quadros "Box", tabelas giradas, figuras sem legenda numerada).
3. O PNG em tamanho real de cada figura que você pretende usar, e a página `pNNN_grade.png`
   quando houver dúvida sobre o que ficou fora da caixa.

**5c. Escolher.** Poucas e boas: leia `references/escolher-figuras.md` (o que torna uma figura
boa para ensinar, quantas por aula de 30 a 35 min, quando recortar só um painel, quando refazer
como gráfico nativo com "Adaptado de"). Parta das figuras apontadas nas fichas.

**5d. Recortar e ajustar.** Coordenadas em fração da página, lidas na régua de `pNNN_grade.png`
(esquerda, topo, direita, base), ou em pontos PDF com origem no canto superior esquerdo:

```
# ver a caixa desenhada na página antes de recortar
python3 scripts/recortar.py AULA --chave Breda2021 --pagina 6 --frac 0.52,0.60,0.93,0.90 --previa
# recorte novo
python3 scripts/recortar.py AULA --chave Breda2021 --id fig4 --pagina 6 --frac 0.52,0.60,0.93,0.90 --rotulo "Figure 4" --aparar
# ajustar um candidato: bordas em pontos (esq, topo, dir, base); negativo = para a esquerda ou para cima
python3 scripts/recortar.py AULA --id Tagliaferri2020_fig1 --ajustar 0,22,0,0 --aparar
# apagar um trecho da página (legenda colada, cabeçalho da revista, anotação)
python3 scripts/recortar.py AULA --id Breda2021_fig4 --apagar 0.74,0.80,0.90,0.83
# juntar painéis lado a lado (ou --juntar vertical); o painel extra pode vir de outra página
python3 scripts/recortar.py AULA --chave Vlist2021 --id fig4e5 --pagina 5 --bbox 36,555,295,695 --painel 5:300,42,560,175
# tabela em paisagem
python3 scripts/recortar.py AULA --chave Centner2019 --id tab1 --pagina 4 --frac 0.135,0.085,0.875,0.94 --girar 90 --aparar
```

A caixa se ajusta sozinha para não cortar palavra ao meio (desligue com `--exato`). Depois de
cada recorte o script já diz se há texto cortado, sobra de branco ou resolução insuficiente, e
imprime o caminho do PNG. **Abra o PNG.** Se não estiver bom, ajuste e olhe de novo. Recorte
manual entra como `origem: "manual"`; mudar um recorte aprovado tira a aprovação.

**5e. Aprovar, com o conteúdo didático.** Só depois de olhar:

```
python3 scripts/recortar.py AULA --id Breda2021_fig4 --aprovar --tipo grafico \
  --legenda-pt "Evolução do VISA-P em 24 semanas" \
  --ensina "A diferença entre os grupos só aparece em 24 semanas"
```

`--tipo` é um de: `forest plot`, `grafico`, `fluxograma`, `tabela`, `imagem`, `esquema`,
`algoritmo`. Use `--rejeitar` nos candidatos que não servem (eles deixam de ser refeitos) e
`--remover` para tirar do catálogo.

**5f. Conferir.**

```
python3 scripts/conferir_recortes.py AULA
```

Confere cada aprovado: resolução para meio slide ou slide inteiro, fração em branco, texto
cortado na borda, proporção extrema, campos didáticos preenchidos, licença. Grava o resultado em
`qc` no catálogo e gera `03_figuras/folha_contato.png`. **Abra a folha de contato final** e
resolva todo "PROBLEMA" antes de entregar. Repita 5d a 5f até a folha estar limpa.

### 6. Entregar

Diga ao usuário, sem enchimento: quantos artigos têm PDF e de onde vieram; o que ainda está
pendente (com o caminho de `pendentes.md`); as fichas escritas e o que ficou sem verificar; as
figuras aprovadas, com a folha de contato; e as figuras cuja licença não é `cc-by`, com a
alternativa (ver "Licença" abaixo). O passo seguinte é a skill `boost-aula-slides`, que lê
`leitura/*.md` e `catalogo.json`.

## Licença das figuras

O campo `licenca` do catálogo vem do manifest. Figuras `cc-by` podem ser reproduzidas com
atribuição. Para `cc-by-nc`, `cc-by-nd` e `todos os direitos reservados`, registre no catálogo
(o script já faz) e avise o usuário de que o uso em curso vendido ou gravado pode exigir
permissão do editor, oferecendo a alternativa de redesenhar os dados com "Adaptado de". Informe,
sem dar parecer jurídico e sem sermão. Detalhes e a tabela por licença:
`references/escolher-figuras.md`.

## Sem rede ou sem shell (claude.ai)

- Sem rede: rode `baixar_artigos.py AULA --sem-rede`. Ele não acessa nada, marca tudo como
  pendente e gera `pendentes.md` completo. Entregue a lista ao usuário e peça os PDFs; para
  saber quais são abertos, use a ferramenta de busca web disponível (página do artigo no PMC ou
  no editor) e indique o link gratuito na resposta. Todos os outros scripts funcionam sem rede.
- Sem shell: peça ao usuário os PDFs anexados, leia-os com a ferramenta de leitura de PDF,
  escreva as fichas pelo modelo e indique as figuras por rótulo e página para ele recortar. Diga
  claramente que os recortes não foram gerados.
- Se um servidor estiver bloqueado, o script informa qual e segue. Não insista nem troque de
  fonte por conta própria: o artigo vira pendência.

## Formatos

`manifest.json` é uma lista. Campos de cada entrada: `chave`, `titulo`, `doi`, `pmid`, `pmcid`,
`revista`, `ano`, `status` (`ok` ou `pendente`), `origem` (`pmc`, `europepmc`, `unpaywall`,
`openalex`, `manual`), `url_origem`, `licenca`, `arquivo`, `paginas`, `bytes`, `sha256`,
`confere_artigo`, `editora`, `volume`, `numero`, `paginas_artigo`, `motivo_pendencia`,
`tentativas`, `texto`.

`licenca` usa: `cc-by`, `cc-by-nc`, `cc-by-nc-nd`, `cc-by-nc-sa`, `cc-by-sa`, `cc-by-nd`, `cc0`,
`dominio publico`, `todos os direitos reservados`, `desconhecida`. As variantes NC e ND são
mantidas porque mudam o que se pode fazer em curso vendido.

`catalogo.json` é uma lista com os campos do contrato (`id`, `chave`, `arquivo`, `pagina`,
`bbox_pt`, `dpi`, `largura_px`, `altura_px`, `rotulo`, `legenda_original`, `legenda_pt`, `tipo`,
`o_que_ensina`, `licenca`, `origem`, `aprovada`, `citacao`) e alguns extras:
`arquivo_com_legenda`, `bbox_legenda_pt`, `confianca` e `avisos` (candidatos automáticos),
`dpi_nativo` (resolução real da imagem embutida, quando a figura não é vetorial), `paineis`,
`apagado_pt`, `girado`, `rejeitada` e `qc`. `bbox_pt` está em pontos PDF com origem no canto
superior esquerdo da página, x para a direita e y para baixo, o mesmo sistema das miniaturas.

## O que o detector faz bem e onde falha

Testado em 13 artigos de acesso aberto de fisioterapia e medicina esportiva (BMJ/BJSM, Springer,
BMC, PLOS, MDPI, Frontiers, Elsevier, SAGE, Wiley, OUP, IJSPT). Nos layouts conhecidos, mais de
nove em cada dez candidatos saem utilizáveis sem ajuste. Em revista nunca vista, a primeira
passada pode perder metade das legendas por causa do formato do rótulo: confira sempre a visão
geral das páginas. Falhas conhecidas:

- **Tabela ou figura em paisagem** (texto girado): não há candidato; o script avisa a página.
  Recorte com `--girar 90` (ou 270).
- **Quadros "Box"**, figuras sem legenda ou com legenda ao lado: sem candidato. Recorte à mão.
- **Legenda em página diferente da figura**: sem candidato ou candidato errado.
- **PDF com camada de texto oculta** (figura embutida como página inteira recortada, comum em
  alguns artigos MDPI): pode sobrar uma linha de texto no topo do recorte.
- **Tabela sem fios horizontais**: o limite inferior é estimado; o candidato vem com aviso.
- **Moldura da revista em volta de figura e legenda** (BMC): o recorte sem legenda corta a
  moldura embaixo. Use `--aparar` com a caixa fechada na figura.
- **Figura de bitmap pequeno**: nenhum `--dpi` melhora. O `conferir_recortes.py` acusa; use em
  tamanho reduzido ou busque o arquivo original da figura na página do artigo.
- **PDF digitalizado**: sem legendas detectáveis; trabalhe só com miniaturas e `recortar.py`.

## Referências

- `references/leitura-critica.md`: ficha, risco de viés por desenho, DMCI, leitura de forest
  plot, sobrevida e dispersão, conversões.
- `references/escolher-figuras.md`: critérios de escolha, quantas por aula, painel ou refazer,
  citação no slide, tabela de licenças.
- `assets/ficha_leitura_modelo.md`: modelo da ficha.
