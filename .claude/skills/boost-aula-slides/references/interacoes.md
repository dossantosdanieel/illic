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

- 5 a 12 interações, em pelo menos 3 formatos, a primeira antes de 3 min e nunca mais de 6 a 7 min sem
  nenhuma (o validador confere; a razão está em `desenho-instrucional.md`, seção 5).
- Uma sala de 3 por aula, no bloco em que a decisão é mais rica. Duas salas em 32 min comem 12 min.
- Mão na câmera é o tapa-buraco legítimo: se a linha do tempo mostrar um trecho longo de `·`, ponha uma
  no meio da figura (`"inicio_s"` faz a interação começar depois de a figura ser lida).
- O bilhete de saída é sempre o último slide cronometrado.

## enquete

**Quando:** antes da evidência (prever, decidir) e na abertura (primeira decisão). Também para ler um
número ("O que você pode afirmar com este intervalo?").

**Roteiro de condução:**
1. Leia a pergunta em voz alta, uma vez. **Não comente as opções**: qualquer comentário vira pista.
2. Lance a enquete e diga o tempo: "1 minuto, ninguém fica sem votar".
3. Aos 45 s: "faltam 15 segundos". Feche no tempo.
4. Mostre o resultado na tela. Chame uma pessoa de cada opção pelo nome para justificar em 15 a 20 s.
   Comece pela opção menos votada: quem está sozinho precisa de espaço.
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
- Sala sem entrega escrita: vira conversa solta e não volta nada.
- Deixar a interação crescer: o cronômetro é do professor. A discussão boa que não cabe vai para o
  chat ou para a próxima aula.

## Referências

- Black P, Wiliam D. Assessment and classroom learning. Assess Educ. 1998;5(1):7-74.
- Crouch CH, Mazur E. Peer Instruction: ten years of experience and results. Am J Phys. 2001;69(9):970-7.
- Smith MK, Wood WB, Adams WK, et al. Why peer discussion improves student performance on in-class concept questions. Science. 2009;323(5910):122-4. PMID 19119232.
- Ver também `desenho-instrucional.md` (atenção online, voto comprometido, chamar pelo nome).
