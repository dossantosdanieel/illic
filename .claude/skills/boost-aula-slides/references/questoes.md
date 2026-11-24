# Questões: enquetes da aula e pré/pós-teste

Dois produtos com o mesmo método:

- **Enquetes da aula** (`tipo: "enquete"` no deck): 3 a 4 por aula, para comprometer a turma com uma
  decisão antes da evidência. Votadas em 1 minuto, então curtas.
- **Pré/pós-teste** (`questoes.json`, lido por `materiais.py`): 5 a 8 questões que medem os objetivos
  da aula com **casos novos**, não os da aula. Se o pós-teste repetir a enquete, mede memória do slide, não
  transferência.

Ambos seguem as regras de redação de itens de múltipla escolha mais usadas em avaliação de profissões
da saúde (Haladyna et al. 2002; Paniagua & Swygert 2016, guia do NBME). O teste com feedback ensina, além
de medir (Roediger & Karpicke 2006; Butler & Roediger 2008): o comentário do gabarito é parte da aula.

## Anatomia de uma boa questão

1. **Cenário clínico** (cenario): paciente, tempo de evolução, os números que importam, o objetivo do
   paciente. 2 a 4 frases. Só o que é necessário para decidir, e tudo o que é necessário.
2. **Pergunta direta** (pergunta): "Qual conduta os dados sustentam melhor?", "Qual leitura do
   resultado é a mais correta?". Regra de cobrir as opções: quem domina o assunto consegue responder
   **antes** de ler as opções.
3. **Uma melhor resposta** e três distratores. Opções homogêneas em forma e tamanho, sem pista
   gramatical. Três opções plausíveis medem quase tão bem quanto quatro (Rodriguez 2005); prefira quatro
   na aula porque o layout é 2 × 2, mas nunca invente um distrator absurdo para completar.
4. **Distratores que são erros reais de raciocínio** (distratores): cada um corresponde a um engano que
   fisioterapeutas cometem de verdade. É isso que torna o resultado da enquete útil: a opção mais votada
   diz qual erro a turma tem.
5. **Gabarito comentado** (comentario): por que a certa é certa, **com o número e a fonte**, e o limite
   da evidência (desenho, imprecisão, o que é proposta clínica).
6. **Referência** (referencia): o `id` do artigo no deck.

## Erros de raciocínio que viram bons distratores

| Erro | Exemplo de distrator |
|---|---|
| Ler risco relativo como absoluto | "Passar corta o risco em 84%" (com 1 evento em 18); calcular o NNT com a redução relativa |
| Intervalo que cruza o nulo = "não funciona" | "Não há efeito: o intervalo cruza o 1" |
| Significância estatística = importância clínica | "p < 0,05, então o paciente vai sentir a diferença" (sem olhar a MCID) |
| Sensibilidade lida como valor preditivo | "Ele tem 85% de chance de não voltar" |
| Teste que todos passam é bom teste | "A bateria é adequada porque quase todos passam" |
| Simetria entre pernas = função normal | "96% de simetria, então o joelho está pronto" |
| Ausência de sintoma = tecido pronto | "Sem dor e sem derrame, o enxerto está pronto" |
| Desenho ignorado | "Está provado" (coorte) / "Não vale nada" (não randomizado, quando não existe ensaio possível) |
| Média do grupo aplicada ao indivíduo sem olhar a variação | "Todos os atletas ganham 20% de força em 8 semanas" |
| Calendário no lugar de critério | "Com 9 meses eu libero" |

## Níveis cognitivos

Escreva para aplicação, análise e avaliação (Anderson & Krathwohl 2001):

- **Aplicação**: usar o dado num caso novo ("Qual conduta para o Lucas?").
- **Análise**: decompor o número ou o estudo ("Quantos atletas seria preciso tratar?", "Por que os dois
  testes discordam?").
- **Avaliação**: julgar entre condutas defensáveis com critério explícito ("Qual plano é o mais
  defensável?").

"Qual é a definição de...", "Segundo Grindem, qual foi a taxa..." medem lembrança. Ficam fora.

## Exemplos

### Ruim

> Segundo Grindem et al. (2016), qual a redução da taxa de nova lesão por mês de espera até o 9º mês?
> A) 21%  B) 51%  C) 84%  D) Nenhuma das anteriores

Mede memória de um número; "nenhuma das anteriores" não testa nada; quem domina o tema mas não
decorou erra.

### Ruim (pista)

> Um atleta com LCA reconstruído há 7 meses quer voltar. O que fazer?
> A) Liberar. B) Liberar. C) Adiar o retorno, priorizar força de quadríceps e reavaliar depois dos 9
> meses com uma bateria completa. D) Não tratar.

A certa é a única longa e detalhada; dois distratores são absurdos. O `materiais.py` avisa quando a
certa é a mais longa em mais de um terço das questões.

### Bom (análise, quantitativa)

> **Cenário:** Na coorte Delaware-Oslo (106 atletas de esportes de pivô seguidos por 2 anos), entre os
> que voltaram ao esporte de nível I com quadríceps abaixo de 90% de simetria, 15 de 45 (33,3%) tiveram
> nova lesão no joelho; com quadríceps acima de 90%, 3 de 24 (12,5%).
> **Pergunta:** Supondo que a diferença fosse inteiramente causada pela força, de quantos atletas seria
> preciso levar o quadríceps acima de 90% para evitar uma nova lesão?
> A) Cerca de 2. B) Cerca de 21. C) Cerca de 5. D) Cerca de 3.
>
> **Gabarito:** C. Diferença absoluta 20,8 pontos; NNT = 1 ÷ 0,208 ≈ 5. A suposição de causa é forte:
> coorte, grupos pequenos, intervalo largo. **Distratores:** A usa a redução relativa do risco (62,5%) no lugar da absoluta; B confunde
> pontos percentuais com NNT; D usa o risco de um grupo só.

### Bom (enquete de aula, leitura de intervalo)

> **Título:** "Passar reduz a nova lesão em **84%**"
> **Pergunta:** Razão de risco 0,16; IC 95% de 0,02 a 1,20; 1 nova lesão entre os 18 que passaram. O que
> você pode afirmar?
> A) Está provado: passar corta o risco em 84%. B) Não há efeito: o intervalo cruza o 1. C) A direção é
> de proteção grande; a estimativa é imprecisa. D) Nada: o estudo não é randomizado.

As quatro opções são leituras que circulam de verdade. A revelação mostra a C em marinho e a justificativa
com o número de eventos.

## Regras de forma

- Sem "todas as anteriores", "nenhuma das anteriores", "exceto", NÃO em caixa alta, "sempre", "nunca"
  (o script avisa).
- Opções curtas para a enquete (até ~100 caracteres: são lidas no celular).
- Gabarito distribuído entre as letras (o script avisa se uma letra passa de metade).
- Números com vírgula decimal e unidade. Todo número do cenário tem origem (artigo ou caso fictício).
- Pré-teste sem nota e sem gabarito; pós-teste 7 a 14 dias depois, com feedback depois do envio (o
  intervalo usa o efeito de espaçamento: Cepeda et al. 2006). Se houver tempo para escrever, prefira um
  pós-teste paralelo (mesmo objetivo e mesmo nível, caso diferente) ao mesmo item do pré-teste: o item
  repetido mede em parte a lembrança da própria questão.
- Pelo menos uma questão por objetivo (o `materiais.py` avisa quando falta) e nenhuma cópia das enquetes.
- Questão sobre conduta que é proposta clínica: pergunte "qual é a mais defensável", não "o que a aula
  propôs" (o pré-teste vem antes da aula), e diga no comentário que é proposta clínica.

## Esquema do `questoes.json`

```json
{
  "questoes": [
    {
      "id": "q2",
      "objetivo": 2,
      "nivel": "análise",
      "cenario": "Na coorte Delaware-Oslo (...)",
      "pergunta": "Supondo que a diferença fosse inteiramente causada pela força, (...)?",
      "opcoes": {"A": "Cerca de 2.", "B": "Cerca de 21.", "C": "Cerca de 5.", "D": "Cerca de 3."},
      "gabarito": "C",
      "comentario": "Risco absoluto: 33,3% − 12,5% = 20,8 pontos (...)",
      "distratores": {"A": "Usar a redução relativa do risco no lugar da absoluta.", "B": "(...)", "D": "(...)"},
      "referencia": ["Grindem2016"]
    }
  ]
}
```

`objetivo` é o número do objetivo em `meta.objetivos` (1, 2, 3). `referencia` aceita um id ou uma lista.
O exemplo completo, com seis questões, está em `assets/exemplo/questoes.json`.

## Referências

- Anderson LW, Krathwohl DR (eds). A taxonomy for learning, teaching, and assessing. Longman; 2001.
- Butler AC, Roediger HL. Feedback enhances the positive effects and reduces the negative effects of multiple-choice testing. Mem Cognit. 2008;36(3):604-16. PMID 18491500.
- Cepeda NJ, Pashler H, Vul E, Wixted JT, Rohrer D. Distributed practice in verbal recall tasks. Psychol Bull. 2006;132(3):354-80. PMID 16719566.
- Haladyna TM, Downing SM, Rodriguez MC. A review of multiple-choice item-writing guidelines for classroom assessment. Appl Meas Educ. 2002;15(3):309-33.
- Paniagua MA, Swygert KA (eds). Constructing written test questions for the basic and clinical sciences. 4th ed. National Board of Medical Examiners; 2016.
- Rodriguez MC. Three options are optimal for multiple-choice items: a meta-analysis of 80 years of research. Educ Meas Issues Pract. 2005;24(2):3-13.
- Roediger HL, Karpicke JD. Test-enhanced learning. Psychol Sci. 2006;17(3):249-55. PMID 16507066.

As sem PMID estão fora do PubMed e foram citadas de memória bibliográfica.
