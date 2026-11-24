# Pontos de checagem: o que mostrar, o que pedir, o que registrar

São quatro paradas com o usuário. Cada uma existe porque, depois dela, errar custa caro: o trabalho seguinte é
longo e é construído em cima da decisão. Entre as paradas, siga sozinho.

Regras gerais:

- Apresente a checagem **assim que ela aparecer** em `situacao.py` (na etapa atual ou em "Esperando o usuário") e
  continue o que não depende dela. Exemplo: mostre a estratégia e a string do Scopus e, enquanto o usuário cola no
  site, rode a Crossref e o OpenAlex.
- Uma mensagem por checagem, curta, com a decisão pedida no fim em uma pergunta fechada ("Aprovo assim?" ou "Quer trocar
  algum?"). Nada de despejar arquivos: resuma e diga o caminho.
- Quando ele aprovar (na conversa, na planilha ou com um "pode seguir"), registre na hora:
  `python3 -I <skill>/scripts/situacao.py AULA --marcar N --nota "o que ele disse, em poucas palavras"`.
  A próxima sessão começa do zero e só sabe da aprovação por esse registro.
- Se ele pedir mudança, faça, mostre só o que mudou e registre a decisão em `--registrar`.
- Sem resposta e com trabalho que não depende dela, siga. Sem resposta e com o próximo passo travado, pare e diga o
  que está esperando, em uma linha.

## 1. Estratégia de busca e string do Scopus

**Por quê.** Toda a triagem, a leitura e a aula saem da busca. Mudar a pergunta depois da triagem obriga a refazer
tudo. E o Scopus só entra pelas mãos do usuário (não há API): quanto antes ele receber a string, antes a exportação
volta.

**Quando.** Depois do teste de sentinelas (`sentinelas.json`) e das contagens no PubMed, com `estrategia.md`
regravado por `montar_strings.py` para trazer as contagens e os sentinelas (`situacao.py` pede esse passo).

**O que mostrar** (de `01_busca/estrategia.md` e `sentinelas.json`):

1. A pergunta (PICO) e o recorte, em duas linhas.
2. Os blocos, um por linha, com 3 a 5 termos de exemplo cada ("Condição: MeSH Anterior Cruciate Ligament Injuries +
   'ACL reconstruct*', 'ACLR', ...").
3. Contagens por variante no PubMed e quantos sentinelas a busca recuperou (meta: todos na `base`). Se algum ficou de
   fora, diga qual e por quê.
4. A string Scopus `base` em bloco de código, com o passo a passo de exportação do passo 8 da skill
   `boost-pesquisa-artigos` (CSV com resumo, palavras-chave, DOI, PMID e EID).

**O que pedir.** "A busca cobre o que você quer na aula? Se sim, cole a string no Scopus e me mande o CSV (ou salve
em `01_busca/brutos/scopus.csv`) com o número de resultados que apareceu."

**Depois.** A exportação não trava nada: siga sem ela e, quando chegar, rode `importar_scopus.py` e `consolidar.py`
de novo (`situacao.py` aponta). Decisões de triagem já tomadas são preservadas.

## 2. Lista de artigos e PDFs pagos

**Por quê.** A leitura crítica é a etapa mais cara (uma ficha por artigo, texto completo). Ler o artigo errado é a
perda maior do pipeline. E os pagos dependem da assinatura do usuário (JOSPT) ou do acesso institucional: só ele baixa.

**Quando.** Depois de `exportar_selecionados.py` e de `baixar_artigos.py` (que separa abertos e pendentes).

**O que mostrar:**

1. Tabela curta: chave, desenho, ano, revista, papel na aula, PDF (baixado / pago / gratuito que o servidor recusou).
   Seis a doze linhas.
2. Uma frase sobre o que ficou de fora e por quê (ex.: "deixei as 3 revisões de 2015 porque a de 2023 as incorpora").
3. O conteúdo de `02_artigos/pendentes.md` agrupado por editora, com a pasta exata onde salvar:
   `aulas/<aula>/02_artigos/manual/` (qualquer nome de arquivo serve). Lembre que a seção "Gratuitos" abre no
   navegador sem login.

**O que pedir.** "Quer trocar algum artigo? E pode baixar os pagos para a pasta manual quando puder; eu sigo com os
abertos enquanto isso."

**Depois.** Siga com extração, fichas e figuras dos que já têm PDF. Quando ele avisar que salvou, rode
`incorporar_manuais.py`. O que não chegar até o roteiro entra como "só resumo", e isso aparece em `verificacao.md`,
nas notas do slide de referências e no relatório final.

## 3. Roteiro com a linha do tempo

**Por quê.** O roteiro decide o que a aula ensina, o caso, as decisões da turma e o tempo de cada minuto. Montar o
deck é trabalho longo (deck.json, render, ajuste slide a slide); refazer o desenho depois do deck pronto custa o dobro.

**Quando.** Depois de `04_aula/roteiro.md` escrito, antes do `deck.json`.

**O que mostrar** (de `roteiro.md`):

1. Os 2 ou 3 objetivos e o caso em uma linha (paciente, objetivo dele, revés previsto).
2. A linha do tempo condensada: início, bloco, slide, interação. Marque onde ficam as figuras e as salas.
3. O dado que contraria ou refina um hábito comum, em uma frase: é o que faz a aula valer para os especialistas.
4. O que ficou de fora (vai para o resumo do aluno) e as propostas clínicas sem ensaio que as teste.

**O que pedir.** "O caso e as três decisões fazem sentido para a equipe? Mudo algum tempo ou alguma figura?"

## 4. Revisão do deck

**Por quê.** É a aula que ele vai dar e que fica gravada. Só ele sabe se o caso soa real, se o tom é o dele e se algum
número contradiz a prática da clínica. Revisar antes de gerar os materiais finais evita refazer enquetes e testes.

**Quando.** Depois de montar, renderizar, olhar cada slide e rodar `conferir_pptx.py` e `materiais.py`.

**O que mostrar:**

1. Caminho do `.pptx`, número de slides e duração; a linha do tempo resumida (minutos com e sem interação).
2. A folha de contato do deck (`04_aula/previa/folha-1.png`) e um ou dois slides de figura.
3. O que não foi conferido no texto completo, as propostas clínicas e os avisos do validador que ficaram de pé.
4. Os materiais: enquetes para cadastrar no Meet antes da aula, pré/pós-teste para o Forms, resumo do aluno.

**O que pedir.** "Revise o deck e me diga o que mudar; se estiver bom, eu fecho o relatório de entrega."

## Modo sem parar

Quando o usuário disser "segue sem parar", "não precisa me perguntar", "faz tudo e me mostra no fim":

- `situacao.py AULA --modo sem-parar --nota "pediu para seguir sem parar"`.
- Use só acesso aberto: PDFs pendentes não esperam, os artigos entram como "só resumo" e ficam listados.
- Scopus fica fora; a string fica pronta em `estrategia.md` para ele colar depois.
- Nas checagens, tome a decisão padrão (preferências e recorte padrão), escreva a suposição em
  `00_briefing.md` (seção "Decisões e perguntas em aberto") e siga.
- No fim, o relatório de entrega lista as checagens não feitas. Apresente as quatro de uma vez, na entrega: a revisão
  dele continua necessária, só mudou de hora.

Nada muda nos padrões: nada inventado, `verificacao.md` honesto, figuras com citação e licença.
