# Voz das notas do apresentador

As notas são o roteiro de quem dá a aula. O padrão é o do deck de referência "Caso Marina": instruções
curtas, no infinitivo, que dizem **o que falar, o que perguntar, o que não antecipar e como conduzir a
interação**. Quem nunca viu o slide deve conseguir dar a aula só com elas.

O script escreve sozinho a primeira linha, `Tempo: 2 min 30 s (acumulado 12:00).`. No `deck.json`,
`notas` começa depois disso.

## As regras, com trechos reais

### 1. A primeira frase diz o papel do slide na aula

> "A primeira decisão da turma, logo depois da história."
>
> "O primeiro revés: o plano da turma encontra a vida real."
>
> "Uma resposta possível, para comparar com as das salas."
>
> "A armadilha do caso."

Uma frase nominal, sem verbo, situa o professor: onde estamos no arco da aula.

### 2. Instruções no infinitivo, uma ação por frase

> "Ler as duas falas em voz alta. Ainda sem perguntas."
>
> "Apresentar os achados sem interpretar."
>
> "Dizer apenas os números."

Nada de "você pode talvez considerar...". O infinitivo é instrução direta e serve para qualquer
apresentador.

### 3. O que **não** fazer vem escrito

> "Não comentar nem interpretar: a turma vai tirar as próprias conclusões mais adiante. Só contar."
>
> "Não dar a resposta agora: dizer que a turma vai conferir o voto no fim da primeira decisão."
>
> "Não comentar; a próxima sala responde."

O erro mais comum do professor experiente é explicar antes da hora e matar a previsão da turma. A nota
protege o ciclo prever → ver.

### 4. A interação é marcada com "Interação:" e tem roteiro completo

> "Interação: enquete 1, aberta por 1 minuto. Não comentar as opções antes do voto. Mostrar o resultado
> na tela e pedir um voluntário de cada opção, começando pela menos votada: quem votou nela abre o
> microfone ou levanta a mão na câmera e justifica em 20 segundos."
>
> "Interação: chat em cascata. Dar 60 segundos de silêncio para escrever, contar 3, 2, 1 e pedir que
> enviem juntos. Ler as hipóteses em voz alta agrupando as repetidas e citando os nomes."
>
> "Interação: salas de 3 por 5 minutos. Antes de abrir as salas, dizer quem é o porta-voz: a pessoa cujo
> nome vem primeiro no alfabeto. Avisar que a entrega é escrita e vai para o chat. Entrar em duas salas
> para ouvir."

Sempre: formato, duração, o que a turma faz, como o professor fecha. O validador avisa quando o slide
tem interação e a nota não diz "Interação:".

Na enquete do Google Meet o apresentador vê só a contagem de cada opção, não quem votou em quê: a nota
nunca manda "chamar pelo nome quem votou B" (o validador avisa). Pelo nome se chama quem se apresentou
como voluntário, quem escreveu no chat ou quem está com a mão na câmera.

### 5. Os números são ditos por inteiro, com unidade e origem

> "Rotação lateral 7 quilos à direita e 12 à esquerda; abdução 6 e 10; rotação medial 14 e 14,5."
>
> "Bases: a curva de síntese de colágeno de Magnusson, o inchaço do tendão doloroso depois de carga até
> a fadiga, de McCreesh, e a meta-regressão de Pavlova, em que frequência menor que diária teve efeito
> maior."

A fonte é falada pelo nome do autor e pelo que o estudo mostrou, não pela sigla da revista. Do exemplo
de LCA: "No estudo de Delaware-Oslo, 38,2% dos que voltaram ao esporte de pivô sem passar nos critérios
tiveram nova lesão no joelho em dois anos: 21 de 55."

### 6. O limite da evidência é dito com as mesmas palavras sempre

> "É uma hipótese: não há ensaio que compare tempos de isometria no manguito."
>
> "Os degraus são proposta clínica, não protocolo testado em ensaio."
>
> "A regra de retomar um ou dois degraus abaixo depois de uma pausa é proposta clínica nossa, sem ensaio
> que a teste."

"Proposta clínica" é o termo da casa para o que a equipe propõe sem estudo que teste. Aparece na nota do
slide e em `meta.propostas_clinicas`.

### 7. A nota liga o slide ao que a turma fez antes

> "Voltar à enquete do aquecimento e mostrar que a opção C venceu o caso. Perguntar a quem votou repouso
> total o que mudou de ideia."
>
> "Voltar ao resultado da enquete e perguntar a quem votou A ou B o que sentiu ao ouvir. Sem julgar: a
> maioria dos profissionais faria o mesmo."

O voto é a memória da aula. Retomá-lo, com respeito por quem errou, é o que transforma o feedback em
aprendizagem.

### 8. Indicação de tom quando importa

> "Ler o áudio em voz alta, devagar, com a entonação de quem está frustrada. Fazer uma pausa."
>
> "Ler a semana dia por dia, como quem conta a agenda de uma amiga."

### 9. Camadas de nível aparecem na nota

Do exemplo de LCA: "Para quem está começando, vale o palpite; para quem já conhece o estudo, pedir que
escreva também o número dos que passaram." e "Desafio para quem já domina: perguntar quantos eventos a
mais entre os 18 bastariam para mudar a conclusão."

### 10. Nota de abertura e de fechamento

A capa traz a logística da aula inteira:

> "Antes de abrir a sala: deixar as quatro enquetes prontas na plataforma, as salas simultâneas
> configuradas com 3 pessoas, um cronômetro visível e, se possível, um colega acompanhando o chat. Entrar
> 5 minutos antes e receber as pessoas pelo nome. Pedir câmera aberta logo no início, explicando o motivo:
> hoje ninguém assiste, todo mundo decide."

O bilhete de saída fecha com o que fazer depois:

> "Bilhete de saída. Interação: uma frase no chat, e só sai quem enviar. Ler cinco em voz alta, com os
> nomes. Copiar as respostas do chat antes de encerrar: servem para abrir a próxima aula e para saber o
> que ficou. Agradecer pelo nome quem mais participou."

O slide de referências leva a declaração honesta (o script gera a partir de `conferido`):

> "Os números dos artigos com PMID foram conferidos nos resumos do Europe PMC. O descritor do consenso
> Delphi (...) não foi conferido no texto completo. Os degraus do supino e a regra de retomada depois de
> pausa são propostas clínicas. A paciente e seus dados são fictícios."

## Tamanho e forma

- 50 a 150 palavras por slide; slides de interação longa (salas) podem chegar a 180.
- Texto corrido, sem tópicos, sem negrito (as notas são lidas no modo apresentador).
- Português do Brasil, frases curtas, sem jargão de palco ("pessoal", "galera", "bora").
- Sem "como vimos" ou "é importante ressaltar": se é importante, diga o quê.
- Cada número das notas está no slide ou na ficha de leitura, com a mesma origem.

## Modelo

```
<Papel do slide em uma frase nominal.> <O que dizer, com os números e de onde vêm.> <O que não antecipar.>
Interação: <formato>, <duração>. <Como abrir.> <Como fechar: quem chamar, o que ler, o que comparar.>
<Ligação com o voto anterior ou com o próximo slide.> <Limite da evidência, se houver.>
<Âncora ou desafio, se houver.>
```
