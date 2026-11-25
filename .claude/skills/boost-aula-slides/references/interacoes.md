# Interações: os formatos canônicos

São os quatro formatos do deck de referência ("Caso Marina") mais o bilhete de saída. Use sempre estes
ids no `deck.json`; o script escreve a pílula no slide ("ENQUETE · 1 MIN") e o validador conta tempo,
quantidade e variedade a partir deles. A plataforma padrão é o **Google Meet**.

| id | Pílula no slide | Duração típica | Para que serve |
|---|---|---|---|
| `enquete` | ENQUETE · 1 MIN | 60 s de voto + 30 a 60 s de conversa | comprometer cada pessoa com uma decisão antes da evidência; ler o erro mais comum da turma |
| `chat_cascata` | CHAT EM CASCATA · 2 MIN | 45 s a 2 min | resposta aberta curta (um número, uma hipótese, três palavras) sem que a primeira resposta contamine as outras |
| `salas` | SALAS DE 3 · 4 MIN | 4 a 5 min de tarefa + 1 min para abrir, fechar e ouvir | aplicar ao caso com discussão; o produto volta escrito |
| `mao_camera` | MÃO NA CÂMERA | 15 a 30 s | termômetro rápido (sim/não, concordo/discordo) e mudança de estímulo |
| `chat` | CHAT · 2 MIN | 1 a 2 min | bilhete de saída: uma frase sobre o que muda na prática |

Por que esses e não outros: todos são **respostas comprometidas e individuais** (cada pessoa produz a
sua antes de ver a dos outros), que é o que faz a pergunta virar aprendizagem (Crouch & Mazur 2001;
Smith et al. 2009), e todos cabem no tempo de uma aula de 30 minutos. "Alguém tem alguma dúvida?" não é
interação: responde quem já sabe, e o silêncio parece consenso.

## Quantas e onde

- **Aula de caso:** 5 a 12 interações, em pelo menos 3 formatos, a primeira antes de 3 min e nunca mais de
  6 a 7 min sem nenhuma (o validador confere; a razão está em `desenho-instrucional.md`, seção 5).
- **Aula expositiva:** 6 a 10 checagens rápidas (seção seguinte) mais o bilhete de saída, em pelo menos
  3 formatos, a primeira antes de 5 min, uma a cada 5 a 7 min e nunca mais de 8 min sem nenhuma (aviso a
  partir de 7). Salas no máximo uma vez, e só se a tarefa valer os 5 min que ela custa.
- Uma sala de 3 por aula, no bloco em que a decisão é mais rica. Duas salas em 32 min comem 12 min.
- Mão na câmera é o tapa-buraco legítimo: se a linha do tempo mostrar um trecho longo de `·`, ponha uma
  no meio da figura (`"inicio_s"` faz a interação começar depois de a figura ser lida).
- O bilhete de saída é sempre o último slide cronometrado.

## Checagem rápida (aula expositiva)

A checagem é uma pergunta de compreensão no meio da explicação: curta, individual, com resposta
comprometida e feedback logo depois. Serve para a turma recuperar o que acabou de ouvir (é isso que
fixa) e para o professor saber se pode seguir. Usa os mesmos formatos canônicos, mais curtos:

| Formato | Duração | Quando | Exemplo |
|---|---|---|---|
| `enquete` | 30 a 45 s de voto (`"duracao_s": 40`) + 30 s de resultado | aplicar a ideia a um paciente novo, ler um número | "Um atleta passa no hop com 96%. O que dá para dizer da força de quadríceps dele?" |
| `chat_cascata` de uma linha | 30 a 60 s | recuperar um número, completar um passo de conta, escrever a frase para o paciente | "Sem voltar o slide: até que mês esperar reduziu o risco, e quanto por mês?" |
| `mao_camera` | 15 a 20 s, com `inicio_s` no fim da explicação | checar uma leitura de sim ou não sem sair do slide | "Polegar para cima: 5,6% é o risco de quem passou. Para baixo: é quanto o risco cai." |

**Exigir recuperar, não reconhecer.** A pergunta boa só se responde se a explicação ficou: pede o
número de memória, aplica a ideia num caso que não estava no slide ou faz o passo seguinte da conta.
"Ficou claro?", "Concordam?" e "O risco cai com o tempo, sim ou não?" medem educação, não compreensão.
Na enquete, os distratores são os erros que a explicação quis desfazer (`questoes.md`).

**Roteiro de condução:**
1. Termine a explicação e diga "checagem rápida": a turma reconhece o ritmo.
2. Leia a pergunta uma vez e diga o formato da resposta ("o mês e a porcentagem", "uma letra").
3. Silêncio no tempo da resposta (30 a 45 s). No chat, "3, 2, 1, enviem".
4. Mostre o resultado ou leia três ou quatro respostas com os nomes (no chat e na câmera; na enquete do
   Meet, só a contagem, então peça um voluntário da opção menos votada).
5. Dê a resposta e o porquê em 20 a 30 s, ligando com o slide de onde ela vem.
6. **Decida:** se mais da metade errou, volte 30 s ao slide da explicação antes de seguir; se quase todos
   acertaram, siga e diga isso ("todo mundo pegou; vamos para a parte difícil").

**Na gravação:** antes de abrir, diga "quem assiste à gravação, pause e responda antes de eu mostrar a
resposta". A checagem continua valendo para quem assiste depois.

**Preparar antes:** as enquetes de checagem também ficam salvas no Meet antes da aula (o `enquetes.md`
lista todas). Sem enquete na conta, a letra vai no chat em cascata.

## enquete

**Quando:** antes da evidência (prever, decidir) e na abertura (primeira decisão). Também para ler um
número ("O que você pode afirmar com este intervalo?").

**Roteiro de condução:**
1. Leia a pergunta em voz alta, uma vez. **Não comente as opções**: qualquer comentário vira pista.
2. Lance a enquete e diga o tempo: "1 minuto, ninguém fica sem votar".
3. Aos 45 s: "faltam 15 segundos". Feche no tempo.
4. Mostre o resultado na tela. A enquete do Google Meet mostra ao vivo **só a contagem** de cada opção,
   não quem votou em quê (conforme a edição do Workspace, um relatório com os nomes pode chegar por e-mail depois da aula). Por isso não
   se chama pelo voto: peça **um voluntário de cada opção** ("quem votou B, abre o microfone ou levanta
   a mão na câmera e defende em 15 segundos") e chame pelo nome quem se apresentar. Comece pela opção
   menos votada: quem está sozinho precisa de espaço. Se ninguém vier, dê voz à opção sem expor
   ninguém ("o que faria alguém votar B?") ou peça a justificativa em uma linha no chat, que mostra o
   nome.
5. **Não dê a resposta ainda** se a evidência vem nos próximos slides. Diga quando a turma vai conferir.
6. Revele no slide de revelação (`revela`), dizendo o que sustenta a resposta e de onde vem, e volte a
   quem votou nas outras: "o que mudaria seu voto?".

**Preparar antes:** entre na chamada 10 min antes, crie as enquetes em Atividades → Enquetes e salve
sem lançar (`materiais.py` gera o `enquetes.md` com o texto pronto). Opções com letra (A) a D)) para
bater com o slide. Enquetes não estão em todas as edições do Google Workspace: confira na conta antes da
aula. Sem enquete, use o chat em cascata com a letra.

## chat_cascata

**Quando:** a resposta é aberta, mas curta: um número de 0 a 10, uma hipótese em até seis palavras, três
medidas, a resposta ao áudio do paciente em três linhas. Excelente para a recuperação de memória no
fechamento.

**Roteiro de condução:**
1. Diga o formato da resposta com precisão ("um número", "até seis palavras").
2. "Escrevam e **não enviem**." Dê o tempo em silêncio (30 a 90 s). Silêncio é trabalho.
3. "3, 2, 1, enviem." Todo mundo ao mesmo tempo.
4. Leia em voz alta, agrupando as respostas repetidas e **citando os nomes**. Classifique em grupos
   ("o tendão, a paciente e a prescrição") e pergunte qual grupo quase ninguém escolheu.
5. Peça a duas pessoas que expliquem a resposta que escreveram.

**Preparar antes:** nada além de ter o chat visível (segunda tela ou um colega lendo). Na abertura,
faça um chat em cascata ou uma mão na câmera de teste: a turma descobre onde fica o chat e que hoje
participar é a regra.

## salas

**Quando:** uma vez por aula, na decisão que pede discussão (montar a bateria de testes, ajustar a
prescrição, responder ao revés). A tarefa cabe em 4 min e tem **produto escrito**.

**O slide (`tarefa`):** até 3 perguntas numeradas, a faixa "Entrega" dizendo exatamente o que volta pelo
chat, e os cartões "Para começar" e "Desafio".

**Roteiro de condução:**
1. Antes de abrir, diga quem é o porta-voz com um critério leve e rápido: "o nome que vem primeiro no
   alfabeto", "quem fez aniversário mais recentemente". Mude o critério a cada sala.
2. Leia a entrega em voz alta: "o porta-voz cola no chat as 4 medidas, com o corte, e a frase".
3. Abra as salas com o cronômetro ligado. Entre em duas salas para ouvir, sem resolver por elas.
4. Aviso de 1 minuto. Feche no tempo.
5. Na volta, peça a três porta-vozes que colem a resposta e compare duas diferentes lado a lado. Cobre a
   pergunta mais difícil, que é a que as salas pulam.

**Tempo no deck:** `duracao_s` é o tempo da tarefa (240 s); `tempo_s` do slide soma mais 60 s para abrir,
fechar e ouvir os porta-vozes (o validador avisa se faltar). **Preparar antes:** salas temáticas do Meet
configuradas com 3 pessoas (ou 2 a 4, `"tamanho"` na interação), com tempo limite. Salas também dependem
da edição do Workspace.

**Gravação e plano B (campos `gravacao` e `plano_b` da interação).** A aula é gravada para a equipe, e
a gravação do Meet registra só a sala principal: quem assiste depois vê minutos de sala vazia e não
ouve nada das salas. E a sala pode não abrir (conta sem salas temáticas, alguém que cai). As duas coisas
se resolvem no deck.json, não à mão no `enquetes.md` (que o `materiais.py` reescreve a cada execução):

```json
"interacao": {
  "tipo": "salas", "duracao_s": 240,
  "gravacao": "Antes de abrir, dizer: \"quem assiste à gravação, pause e faça a tarefa em 4 minutos\". Na edição, cortar o trecho de sala vazia.",
  "plano_b": "Sem salas: chat em cascata com a mesma entrega, 2 minutos, todos enviam no 3; ler duas respostas diferentes em voz alta. O bloco encolhe de 5 para 3 min."
}
```

- `gravacao`: o que quem assiste ao vídeo faz enquanto as salas acontecem (pausar e fazer a tarefa, com o
  tempo) e o que sai na edição. Vale a pena repetir a instrução na faixa de entrega do slide. Na volta,
  leia as entregas em voz alta: só assim elas entram na gravação.
- `plano_b`: o formato que substitui as salas, com a duração e o que acontece com a sobra de tempo.
  Escreva para a aula concreta (a mesma entrega, em outro formato), não um texto genérico.
- O `materiais.py` gera a seção "Plano B e gravação" do `enquetes.md` a partir desses campos e avisa
  quando uma sala não tem `gravacao` ou `plano_b`. Os dois campos valem para qualquer interação (por
  exemplo, `plano_b` de uma enquete: "sem enquete na conta, letra no chat em cascata").

## mao_camera

**Quando:** para medir a sala em 15 segundos ("polegar para cima quem mede força de quadríceps com
dinamômetro") e para mudar o estímulo no meio de uma explicação.

**Roteiro de condução:**
1. Pergunta de sim ou não, com os dois lados ditos: "para cima quem..., para baixo quem...".
2. Conte o que vê, sem julgar: "uns dois terços para cima".
3. Chame uma pessoa de cada lado pelo nome para uma frase, se houver tempo.

Funciona só com câmera aberta, por isso o combinado do começo da aula. Sem câmera, use a reação de
emoji do Meet (polegar).

## chat (bilhete de saída)

**Quando:** no último slide, sempre. Pergunta de transferência: "O que você vai mudar na próxima
liberação de LCA?". Instrução: "Uma frase no chat. Quem enviar, está liberado."

**Roteiro de condução:** leia cinco em voz alta, com os nomes; agradeça pelo nome quem mais participou;
**copie o chat antes de encerrar** (dependendo da edição e da gravação, o chat da chamada some quando
ela termina). As respostas abrem
a próxima aula e mostram o que ficou: é avaliação formativa (Black & Wiliam 1998).

## Erros comuns de condução

- Comentar as opções antes do voto ("a B é interessante...").
- Abrir a enquete e preencher o silêncio falando. Silêncio de 60 s é o tempo de pensar.
- Dar a resposta antes de a turma ver a evidência: mata o ciclo prever → ver.
- Chamar só quem acertou, ou perguntar "quem errou?". Chame por opção, não por acerto.
- Na enquete, chamar pelo nome alguém "que votou B": o Meet não mostra o voto de cada um ao vivo. Peça
  voluntários por opção (o validador avisa quando a nota de uma enquete manda chamar pelo nome).
- Sala sem entrega escrita: vira conversa solta e não volta nada.
- Deixar a interação crescer: o cronômetro é do professor. A discussão boa que não cabe vai para o
  chat ou para a próxima aula.

## Referências

- Black P, Wiliam D. Assessment and classroom learning. Assess Educ. 1998;5(1):7-74.
- Crouch CH, Mazur E. Peer Instruction: ten years of experience and results. Am J Phys. 2001;69(9):970-7.
- Smith MK, Wood WB, Adams WK, et al. Why peer discussion improves student performance on in-class concept questions. Science. 2009;323(5910):122-4. PMID 19119232.
- Ver também `desenho-instrucional.md` (atenção online, voto comprometido, chamar pelo nome).
