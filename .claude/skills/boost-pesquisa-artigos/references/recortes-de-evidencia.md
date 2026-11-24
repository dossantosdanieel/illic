# Recortes de evidência

O recorte diz que tipo de literatura a aula quer. Ele muda três coisas: quais variantes da busca rodar, os limites de ano, e os pesos da pontuação. Fica em `"recorte"` de `conceitos.json`; `consolidar.py --recorte` sobrepõe para comparar.

Se o Daniel não disser nada, use `topo_mecanismos`. Na dúvida entre dois, pergunte em uma frase: "Você quer a melhor evidência com os mecanismos que a explicam (padrão), só a evidência de topo, ou o que saiu de novo nos últimos dois ou três anos?"

## Os três recortes

| | `topo_mecanismos` (padrão) | `so_topo` | `fronteira` |
|---|---|---|---|
| Para que aula | A maioria: o que funciona **e por quê**. Equipe com níveis diferentes precisa do mecanismo para transferir o achado ao paciente. | Aula de conduta ("o que a evidência manda fazer"), atualização de protocolo, tema com muita evidência de topo. | Atualização: o que mudou, controvérsias em aberto, tema que a equipe já domina. |
| Como o usuário pede | "aula sobre X", "evidência de X", sem qualificar | "só o que tem evidência forte", "revisões e diretrizes", "sem estudo de laboratório" | "o que tem de novo", "últimos anos", "atualização", "estado da arte" |
| Variantes no PubMed | `rs`, `diretriz`, `ecr`, `base`, `revistas` | `rs`, `diretriz`, `ecr`, `revistas` | `base`, `revistas` |
| Limite de ano | o de `conceitos.json` (sugestão: 10 a 15 anos) | o de `conceitos.json` | ano inicial forçado para os últimos 3 anos-calendário (em 2026: 2024 em diante) |
| Perseguição de citações | sentinelas, nas duas direções | opcional | **para a frente** a partir dos sentinelas: é o melhor jeito de achar o que saiu depois |
| Crossref | consulta + filtro local | consulta + filtro local | `--varrer --de-ano <ano>` nas revistas-alvo: o mais recente às vezes ainda não está no PubMed |

Por que a variante `base` entra no padrão: os estudos de mecanismo (biomecânica, eletromiografia, estrutura do tendão, sensibilidade à dor) não passam por nenhum filtro de desenho. Só a busca sem filtro os traz. No `so_topo` ela fica de fora de propósito.

## Pesos da pontuação

A pontuação vai de 0 a 100 e serve para **ordenar a leitura**, não para julgar qualidade. Tetos por componente:

| Componente | `topo_mecanismos` | `so_topo` | `fronteira` |
|---|---|---|---|
| Desenho do estudo | 35 | 45 | 25 |
| Atualidade | 20 | 20 | 35 |
| Citações por ano | 15 | 10 | 10 |
| Revista-alvo | 10 | 10 | 10 |
| Sentinela ou ligado a sentinela | 10 | 10 | 10 |
| Aderência ao tema | 10 | 5 | 10 |

Fração do teto de desenho que cada tipo recebe:

| Desenho | `topo_mecanismos` | `so_topo` | `fronteira` |
|---|---|---|---|
| Diretriz | 1,00 | 1,00 | 1,00 |
| Revisão sistemática/meta-análise | 1,00 | 1,00 | 1,00 |
| ECR | 0,85 | 0,80 | 0,95 |
| Consenso/Delphi | 0,70 | 0,55 | 0,75 |
| Laboratório/mecanístico | 0,70 | 0,10 | 0,70 |
| Coorte | 0,60 | 0,30 | 0,70 |
| Estudo de acurácia diagnóstica | 0,60 | 0,30 | 0,70 |
| Caso-controle | 0,45 | 0,20 | 0,50 |
| Transversal | 0,40 | 0,15 | 0,50 |
| Revisão narrativa | 0,40 | 0,15 | 0,45 |
| Relato/série de casos | 0,15 | 0,05 | 0,20 |
| Editorial/comentário | 0,10 | 0,05 | 0,25 |
| Outro | 0,15 | 0,05 | 0,25 |

Como ler: no padrão, um estudo de laboratório bem citado e recente fica perto de um ECR; no `so_topo`, ele afunda; na `fronteira`, um editorial recente sobe um pouco porque sinaliza debate em andamento.

Os outros componentes:

- **Atualidade.** Pontuação cheia até 2 anos (`topo_mecanismos`), 3 (`so_topo`) ou 1 (`fronteira`); cai em linha reta até zero aos 15 anos (aos 4, na `fronteira`).
- **Citações por ano.** Escala logarítmica; 25 citações por ano já dão o teto. Artigo com até 1 ano não leva menos de 40% do teto, porque ainda não teve tempo de ser citado. Sem dado de citação, valor neutro de 30%.
- **Revista-alvo.** Tudo ou nada: o ISSN está em `revistas_alvo` (o JOSPT conta sempre).
- **Sentinela.** Teto para o sentinela; 40% para quem cita ou é citado por um sentinela; 70% se a ligação for com dois ou mais.
- **Aderência.** Para cada bloco de conceito: 1 se aparece no título, 0,5 se só no resumo ou no MeSH. Média dos blocos vezes o teto.
- **Retratado.** Pontuação zerada e aviso na saída.

Cada linha da planilha traz a conta por extenso na coluna "Por que esta pontuação".

Os pesos são uma escolha de quem montou a skill, não um instrumento validado. Estão no dicionário `PESOS`, no topo de `scripts/consolidar.py`; se o Daniel quiser outra ênfase, mude ali e registre em `estrategia.md`.

## O que muda na triagem

**`topo_mecanismos`.** Monte a aula em camadas: uma ou duas diretrizes ou revisões como âncora; dois a quatro ensaios que sustentam ou contestam a âncora; dois ou três estudos de mecanismo que explicam o efeito; um contraponto. É a seleção que dá aula com nível técnico alto: o aluno vê a recomendação, o dado e a explicação.

**`so_topo`.** Fique com diretrizes, revisões sistemáticas e os ensaios que elas não alcançaram por serem mais novos. Quando houver várias revisões sobre a mesma pergunta, prefira a mais recente com meta-análise e use as outras só para mostrar concordância ou divergência (motivo de exclusão: "superado por evidência mais nova").

**`fronteira`.** Pré-prints, protocolos e resumos de congresso aparecem mais. Protocolo não tem resultado: vai para "sem resultados (protocolo)", mas anote em observações, porque diz o que vem por aí. Cuidado redobrado com artigo de um ano só: sem citações e sem replicação, o peso é da atualidade, não da solidez. Diga isso na aula.

## Ver o efeito de trocar o recorte

```bash
python3 scripts/consolidar.py --pasta aulas/<aula>/01_busca --recorte so_topo
python3 scripts/consolidar.py --pasta aulas/<aula>/01_busca --recorte fronteira
```

As decisões já preenchidas na planilha continuam lá; só a ordem das linhas muda. Para trocar de recorte de verdade (e não só a ordenação), mude `recorte` em `conceitos.json` e rode a busca de novo, porque variantes e limites também mudam.
