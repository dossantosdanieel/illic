# Planejar uma trilha de várias aulas

Uma trilha é uma sequência de aulas de 30 a 35 minutos sobre um mesmo território clínico (ex.: cotovelo e mão em 3
aulas). Cada aula continua sendo uma pasta completa do contrato; a trilha acrescenta um arquivo de plano e três
cuidados: sequência, pré-requisitos e recuperação espaçada.

Exemplo real nesta máquina: `aulas/trilha-cotovelo-e-mao.md` (3 aulas, a aula 2 usa a busca da aula 1 por link).

## 1. Escrever o plano antes da primeira pasta

Crie o plano a partir de `assets/trilha_modelo.md` (o `nova_aula.py --trilha aulas/trilha-<nome>.md` faz isso se o
arquivo não existir) e mostre ao usuário antes de buscar qualquer coisa. O plano tem:

- **Para quem e para quê:** as 2 a 4 decisões clínicas que a trilha inteira melhora.
- **Mapa:** uma linha por aula, com a pergunta clínica central, o pré-requisito, se a busca é própria ou
  compartilhada, e o que a abertura recupera.
- **Fio condutor:** o mesmo paciente atravessando aulas (com um revés por aula) dá continuidade e economiza tempo de
  apresentação do caso.
- **Calendário:** data de cada aula e do pós-teste (7 a 14 dias depois de cada uma).

Esse plano é uma checagem extra: aprovado o plano, cada aula segue as quatro checagens normais.

## 2. Sequência e pré-requisitos

- Ordene do raciocínio que sustenta para o que depende dele: **diagnóstico e prognóstico antes do tratamento**,
  mecanismo junto da primeira aula que precisa dele, condições raras ou de extrapolação no fim.
- Uma aula = uma pergunta clínica central. Se o tema pede duas decisões grandes (ex.: diagnóstico e dose de exercício),
  são duas aulas. A aula de 30 a 35 minutos não comporta mais que três decisões da turma.
- Pré-requisito é algo que a turma precisa **saber fazer** ao entrar (ex.: "interpretar razão de verossimilhança"), não
  "ter assistido". Escreva no briefing da aula seguinte e garanta que o pós-teste da anterior mede isso.
- Aulas de uma trilha devem ser **independentes o bastante** para quem faltou: a recuperação na abertura e o resumo do
  aluno da aula anterior bastam para acompanhar.

## 3. Recuperação espaçada na abertura da aula seguinte

Revisar depois de um intervalo retém mais que revisar em seguida (Cepeda et al. 2006), e tirar da memória ensina mais
que reouvir (Roediger & Karpicke 2006); ver `boost-aula-slides/references/desenho-instrucional.md`, seção 6.

Na prática, nos primeiros 3 minutos da aula N+1, antes do caso novo:

1. **Uma pergunta de recuperação, de memória**, sobre a decisão central da aula N (enquete de 1 min ou chat em
   cascata). Sem slide de revisão antes: a turma tenta lembrar, depois confere.
2. A pergunta sai do que a turma errou: a enquete mais errada da aula N, o bilhete de saída com respostas fracas ou a
   questão do pós-teste com pior acerto.
3. Prefira **intercalar**: a pergunta usa um caso novo que exige o raciocínio da aula N, em vez de repetir a enquete.
4. Na aula 3 de 3, recupere as aulas 1 e 2 misturadas (uma pergunta que precise das duas).
5. Conte esse minuto no tempo da abertura: a primeira interação continua antes dos 3 minutos, e o validador gosta.

O `nova_aula.py --aula-anterior <pasta>` já copia para o briefing o bilhete de saída, os objetivos e os pontos-chave da
aula anterior (de `04_aula/deck.json`, ou do briefing dela se o deck ainda não existir). Use como ponto de partida e
troque pelas respostas reais da turma quando houver.

## 4. Busca, artigos e figuras compartilhados

Aulas sobre a mesma condição (ex.: diagnóstico e tratamento da tendinopatia lateral) podem usar uma busca só:

```bash
python3 -I <skill>/scripts/nova_aula.py --tema "..." --trilha aulas/trilha-x.md --posicao "2 de 3" \
  --aula-anterior aulas/2026-11-x-1 --compartilhar-de aulas/2026-11-x-1
```

`01_busca`, `02_artigos` e `03_figuras` viram links simbólicos para a aula dona. Consequências:

- A seleção (`selecionados.json`) é a soma das duas aulas e pode passar de 12 artigos; o roteiro de cada aula usa só
  os seus. Diga isso ao usuário na checagem 2.
- Figuras aprovadas valem para as duas aulas; não repita a mesma figura nas duas sem motivo.
- `situacao.py` mostra "Compartilhado: ..." e acompanha o estado da pasta dona. As checagens 1 e 2 (busca e
  lista de artigos) são da aula dona: registre lá (`situacao.py <aula dona> --marcar 2`), e as aulas que usam a
  busca dela passam a ver a checagem feita.
- No claude.ai ou em sistema sem link simbólico, copie as pastas em vez de ligar.

Busca própria quando a pergunta clínica muda de condição (ex.: aula 3 sobre cotovelo medial e mão).

## 5. Acompanhar a trilha

`python3 -I <skill>/scripts/situacao.py aulas` lista todas as aulas e os planos de trilha com a etapa de cada uma.
Atualize a tabela "Calendário e pós-testes" e a seção "Decisões" do plano a cada aula dada.
