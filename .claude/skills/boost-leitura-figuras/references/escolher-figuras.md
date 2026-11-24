# Escolher, recortar e citar figuras

## O que torna uma figura boa para ensinar

Uma figura entra na aula quando carrega **uma decisão clínica** que o aluno lê em até dez
segundos. Teste antes de aprovar: escreva `o_que_ensina` em uma frase. Se a frase sai genérica
("mostra os resultados"), a figura não está escolhida, está só disponível.

Sinais de figura boa:

- mostra o desfecho primário, com incerteza visível (IC, barras de erro) e os dois grupos;
- os eixos e a legenda se leem projetados (a altura da menor letra precisa ficar perto de 14 pt
  no slide; o `conferir_recortes.py` avisa da resolução, não da letra: olhe);
- tem um contraste que sustenta pergunta de enquete ("para que lado está o favorecimento?");
- traduz dose ou critério em algo aplicável na segunda-feira: tabela de prescrição, algoritmo de
  progressão, critérios de retorno.

Sinais de figura que só ocupa espaço:

- fluxograma CONSORT ou PRISMA (diga "76 randomizados, 9 perdas" em uma linha; mostre o
  fluxograma só se a perda desigual for o assunto);
- tabela de características de base inteira (recorte as três linhas que mudam a aplicabilidade);
- fotografia ilustrativa de exercício que o aluno já conhece;
- figura com seis painéis da qual a aula usa um.

## Quantas por aula de 30 a 35 minutos

Regra prática: **4 a 6 figuras de artigo**, no máximo 8, entre 12 e 18 slides. Cada figura
custa de 60 a 90 segundos de explicação se o aluno precisa mesmo lê-la. Mais do que isso, a
aula vira leitura de gráficos e a interação some. Por artigo central, uma ou duas; por artigo
de apoio, uma ou nenhuma. O catálogo pode ter mais aprovadas do que a aula usa: quem decide o
corte final é o roteiro.

## Recortar inteiro, só um painel, ou refazer

| Situação | Faça |
|---|---|
| A figura inteira é a mensagem e se lê projetada | Reproduza inteira (`<chave>/fig2.png`) |
| A mensagem está em um painel (A de A–D) | Recorte só o painel com `recortar.py`; diga "Fig. 2A" no rótulo e na citação |
| Dois painéis de páginas ou lugares diferentes se comparam | Junte com `--painel ... --juntar` |
| Tabela grande, mensagem em poucas linhas | Refaça como tabela nativa do slide, com 3 a 6 linhas, e cite "Adaptado de" |
| Gráfico com letras miúdas, baixa resolução ou cores que somem no projetor | Refaça como gráfico nativo com os mesmos números, e cite "Adaptado de" |
| Forest plot com 20 estudos | Mostre o original uma vez; para discutir, refaça só o losango e 2 ou 3 estudos |
| Legenda, cabeçalho da revista ou nota colados na figura | Apague com `--apagar` ou feche a caixa; a legenda vai no slide, em português |
| Licença não permite reprodução (ver abaixo) | Redesenhe os dados e cite "Adaptado de"; ou peça permissão |

Refazer exige que os números venham do texto ou de tabela do artigo, com página na ficha. Não
leia valores "no olho" a partir do gráfico; se for inevitável, marque como aproximado.

## Como citar no slide

- Rodapé à direita, 12 pt cinza: `Fonte: Breda SJ et al. Br J Sports Med. 2021;55(9):501-9. Fig. 4.`
  O campo `citacao` do catálogo já vem nesse formato.
- Figura modificada, painel isolado com reorganização ou gráfico refeito:
  `Adaptado de Breda SJ et al. ...`
- Tradução dos rótulos dentro da figura é modificação: use "Adaptado de". Legenda traduzida fora
  da figura não é.
- Figura com licença Creative Commons: acrescente a licença ao final quando houver espaço
  (`CC BY 4.0`), e sempre na lista de referências.
- O slide de referências traz a referência completa com PMID.

## Licença: o que registrar e o que avisar

Isto é informação prática, não parecer jurídico. O campo `licenca` do catálogo vem do
`manifest.json` (PMC, Unpaywall ou o texto do próprio PDF). Confira na primeira página do artigo
quando o valor for `desconhecida`.

| Licença | O que permite, em resumo | O que fazer |
|---|---|---|
| `cc-by`, `cc0`, `dominio publico` | Reproduzir e adaptar, inclusive em curso vendido, com atribuição | Citar autor, revista, ano e a licença |
| `cc-by-sa` | Idem, e o material derivado segue a mesma licença | Citar; atenção se o slide for redistribuído |
| `cc-by-nc`, `cc-by-nc-sa` | Reproduzir e adaptar sem fim comercial | Em aula interna gratuita, citar. Em curso vendido ou gravado para venda, pedir permissão ao editor ou redesenhar os dados |
| `cc-by-nd`, `cc-by-nc-nd` | Reproduzir sem alterar (e, com NC, sem fim comercial) | Usar a figura inteira, sem recortar painel nem traduzir por dentro; para adaptar, redesenhar a partir dos números |
| `todos os direitos reservados` | Nada além do uso pessoal de leitura | Registrar no catálogo e avisar o usuário: uso em curso vendido ou gravado pode exigir permissão do editor (em geral pelo link "Rights and permissions" da página do artigo). Alternativa: redesenhar os dados com "Adaptado de" |
| `desconhecida` | Não se sabe | Tratar como reservada até conferir |

Pontos que evitam surpresa:

- Artigo de acesso aberto pode trazer figura de terceiros com outra licença ("Reproduced with
  permission from..."): a legenda avisa. Registre em `legenda_original` e trate como reservada.
- Dados não têm direito autoral; a apresentação gráfica tem. Por isso redesenhar com os mesmos
  números, citando a fonte, é o caminho seguro quando a licença restringe.
- PDF baixado com a assinatura do usuário (JOSPT, acesso institucional) serve para leitura.
  Reproduzir figura em material vendido é outra autorização.
- Ao entregar o catálogo, liste para o usuário as figuras aprovadas que não são `cc-by`, com a
  alternativa para cada uma. O `conferir_recortes.py` imprime essa lista.
