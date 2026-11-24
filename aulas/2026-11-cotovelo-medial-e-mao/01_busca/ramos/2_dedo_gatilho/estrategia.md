# Estratégia de busca - Ramo 2. Dedo em gatilho (tenossinovite estenosante dos flexores): graduação, órtese, injeção, cirurgia

Gerado em 2026-11-24 por `montar_strings.py` a partir de `conceitos.json`. Para mudar uma string, edite `conceitos.json` e rode o script de novo: assim PubMed, Scopus e Crossref continuam dizendo a mesma coisa.

## Pergunta e recorte

- **População/problema:** Adultos com dedo ou polegar em gatilho
- **Intervenção/exposição:** Graduação da gravidade (Quinnell/Green e variações); órtese, injeção de corticoide, exercício/terapia da mão, cirurgia (aberta, percutânea)
- **Comparador:** Fora da string
- **Desfechos:** Fora da string: resolução do gatilho, recidiva, dor, função, necessidade de cirurgia
- **Nota:** Comparador e desfecho ficam fora da string (muitos resumos não os citam) e entram como critério de triagem. O segundo bloco reúne diagnóstico e tratamento porque a aula cobre os dois; termos genéricos como 'treatment*', 'therap*' e 'diagnos*' ficaram de fora de propósito (casariam com quase tudo). Limite 1990+ para alcançar os clássicos de acurácia e os ensaios antigos de corticoide; citações da aula base anteriores a 1990 entram por PMID (pubmed_busca.py --pmids). Trigger finger pediátrico entra na busca e sai na triagem (população diferente).
- **Recorte:** topo da pirâmide + mecanismos (padrão)

## Blocos de conceito

Dentro do bloco os termos se somam (OR); os blocos se cruzam (AND).

| Bloco | Papel | MeSH | Termos livres | Proximidade |
|---|---|---|---|---|
| Dedo em gatilho (`condicao`) | P | Trigger Finger Disorder | trigger finger*; trigger digit*; trigger thumb*; stenosing tenosynovitis; stenosing flexor tenosynovitis; stenosing tenovaginitis; flexor tenosynovitis; A1 pulley | - |
| Diagnóstico (testes, acurácia, graduação) ou tratamento (`dx_tx`) | I | Diagnosis, Differential; Physical Examination; Sensitivity and Specificity; Predictive Value of Tests; Severity of Illness Index; Orthotic Devices; Splints; Braces; Injections; Glucocorticoids; Adrenal Cortex Hormones; Exercise Therapy; Physical Therapy Modalities; Musculoskeletal Manipulations; Conservative Treatment; Orthopedic Procedures; Remission, Spontaneous | differential diagnos*; physical exam*; clinical exam*; clinical test*; provocative test*; sensitivity; specificity; likelihood ratio*; diagnostic accuracy; classification; grading; conservative; nonoperative; non-operative; nonsurgical; non-surgical; splint*; orthos*; orthotic*; brace*; immobili*; corticosteroid*; steroid*; glucocorticoid*; triamcinolone; methylprednisolone; injection*; exercis*; eccentric*; physiotherap*; physical therap*; hand therap*; manual therap*; mobilization; mobilisation; massage; surgery; surgical; release; natural history; spontaneous resolution; randomized; randomised; Quinnell; Green classification; severity; percutaneous; A1 pulley release | - |

## Limites

- Anos: 1990 a hoje
- Idiomas: english, portuguese, spanish
- Somente humanos (PubMed): sim
- Tipos de documento no Scopus: ar, re
- Revistas-alvo: J Orthop Sports Phys Ther (0190-6011, 1938-1344); J Hand Ther (0894-1130, 1545-004X); J Hand Surg Am (0363-5023, 1531-6564); J Hand Surg Eur Vol (1753-1934, 2043-6289); J Shoulder Elbow Surg (1058-2746, 1532-6500); Am J Sports Med (0363-5465, 1552-3365); Cochrane Database Syst Rev (1469-493X)

## PubMed

Cole em https://pubmed.ncbi.nlm.nih.gov/advanced/ ou rode `pubmed_busca.py --conceitos conceitos.json --variante <nome>`.

### Base (só os blocos e os limites) (`base`)

```
(("Trigger Finger Disorder"[Mesh] OR "trigger finger*"[tiab] OR "trigger digit*"[tiab] OR "trigger thumb*"[tiab] OR "stenosing tenosynovitis"[tiab] OR "stenosing flexor tenosynovitis"[tiab] OR "stenosing tenovaginitis"[tiab] OR "flexor tenosynovitis"[tiab] OR "A1 pulley"[tiab]) AND ("Diagnosis, Differential"[Mesh] OR "Physical Examination"[Mesh] OR "Sensitivity and Specificity"[Mesh] OR "Predictive Value of Tests"[Mesh] OR "Severity of Illness Index"[Mesh] OR "Orthotic Devices"[Mesh] OR "Splints"[Mesh] OR "Braces"[Mesh] OR "Injections"[Mesh] OR "Glucocorticoids"[Mesh] OR "Adrenal Cortex Hormones"[Mesh] OR "Exercise Therapy"[Mesh] OR "Physical Therapy Modalities"[Mesh] OR "Musculoskeletal Manipulations"[Mesh] OR "Conservative Treatment"[Mesh] OR "Orthopedic Procedures"[Mesh] OR "Remission, Spontaneous"[Mesh] OR "differential diagnos*"[tiab] OR "physical exam*"[tiab] OR "clinical exam*"[tiab] OR "clinical test*"[tiab] OR "provocative test*"[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "likelihood ratio*"[tiab] OR "diagnostic accuracy"[tiab] OR classification[tiab] OR grading[tiab] OR conservative[tiab] OR nonoperative[tiab] OR "non-operative"[tiab] OR nonsurgical[tiab] OR "non-surgical"[tiab] OR splint*[tiab] OR orthos*[tiab] OR orthotic*[tiab] OR brace*[tiab] OR immobili*[tiab] OR corticosteroid*[tiab] OR steroid*[tiab] OR glucocorticoid*[tiab] OR triamcinolone[tiab] OR methylprednisolone[tiab] OR injection*[tiab] OR exercis*[tiab] OR eccentric*[tiab] OR physiotherap*[tiab] OR "physical therap*"[tiab] OR "hand therap*"[tiab] OR "manual therap*"[tiab] OR mobilization[tiab] OR mobilisation[tiab] OR massage[tiab] OR surgery[tiab] OR surgical[tiab] OR release[tiab] OR "natural history"[tiab] OR "spontaneous resolution"[tiab] OR randomized[tiab] OR randomised[tiab] OR Quinnell[tiab] OR "Green classification"[tiab] OR severity[tiab] OR percutaneous[tiab] OR "A1 pulley release"[tiab]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Revisões sistemáticas e meta-análises (`rs`)

```
(("Trigger Finger Disorder"[Mesh] OR "trigger finger*"[tiab] OR "trigger digit*"[tiab] OR "trigger thumb*"[tiab] OR "stenosing tenosynovitis"[tiab] OR "stenosing flexor tenosynovitis"[tiab] OR "stenosing tenovaginitis"[tiab] OR "flexor tenosynovitis"[tiab] OR "A1 pulley"[tiab]) AND ("Diagnosis, Differential"[Mesh] OR "Physical Examination"[Mesh] OR "Sensitivity and Specificity"[Mesh] OR "Predictive Value of Tests"[Mesh] OR "Severity of Illness Index"[Mesh] OR "Orthotic Devices"[Mesh] OR "Splints"[Mesh] OR "Braces"[Mesh] OR "Injections"[Mesh] OR "Glucocorticoids"[Mesh] OR "Adrenal Cortex Hormones"[Mesh] OR "Exercise Therapy"[Mesh] OR "Physical Therapy Modalities"[Mesh] OR "Musculoskeletal Manipulations"[Mesh] OR "Conservative Treatment"[Mesh] OR "Orthopedic Procedures"[Mesh] OR "Remission, Spontaneous"[Mesh] OR "differential diagnos*"[tiab] OR "physical exam*"[tiab] OR "clinical exam*"[tiab] OR "clinical test*"[tiab] OR "provocative test*"[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "likelihood ratio*"[tiab] OR "diagnostic accuracy"[tiab] OR classification[tiab] OR grading[tiab] OR conservative[tiab] OR nonoperative[tiab] OR "non-operative"[tiab] OR nonsurgical[tiab] OR "non-surgical"[tiab] OR splint*[tiab] OR orthos*[tiab] OR orthotic*[tiab] OR brace*[tiab] OR immobili*[tiab] OR corticosteroid*[tiab] OR steroid*[tiab] OR glucocorticoid*[tiab] OR triamcinolone[tiab] OR methylprednisolone[tiab] OR injection*[tiab] OR exercis*[tiab] OR eccentric*[tiab] OR physiotherap*[tiab] OR "physical therap*"[tiab] OR "hand therap*"[tiab] OR "manual therap*"[tiab] OR mobilization[tiab] OR mobilisation[tiab] OR massage[tiab] OR surgery[tiab] OR surgical[tiab] OR release[tiab] OR "natural history"[tiab] OR "spontaneous resolution"[tiab] OR randomized[tiab] OR randomised[tiab] OR Quinnell[tiab] OR "Green classification"[tiab] OR severity[tiab] OR percutaneous[tiab] OR "A1 pulley release"[tiab]) AND (systematic[sb] OR "meta-analysis"[pt] OR "systematic review"[ti] OR meta-analy*[ti] OR "umbrella review"[ti]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Ensaios clínicos randomizados (`ecr`)

```
("Trigger Finger Disorder"[Mesh] OR "trigger finger*"[tiab] OR "trigger digit*"[tiab] OR "trigger thumb*"[tiab] OR "stenosing tenosynovitis"[tiab] OR "stenosing flexor tenosynovitis"[tiab] OR "stenosing tenovaginitis"[tiab] OR "flexor tenosynovitis"[tiab] OR "A1 pulley"[tiab]) AND ("Diagnosis, Differential"[Mesh] OR "Physical Examination"[Mesh] OR "Sensitivity and Specificity"[Mesh] OR "Predictive Value of Tests"[Mesh] OR "Severity of Illness Index"[Mesh] OR "Orthotic Devices"[Mesh] OR "Splints"[Mesh] OR "Braces"[Mesh] OR "Injections"[Mesh] OR "Glucocorticoids"[Mesh] OR "Adrenal Cortex Hormones"[Mesh] OR "Exercise Therapy"[Mesh] OR "Physical Therapy Modalities"[Mesh] OR "Musculoskeletal Manipulations"[Mesh] OR "Conservative Treatment"[Mesh] OR "Orthopedic Procedures"[Mesh] OR "Remission, Spontaneous"[Mesh] OR "differential diagnos*"[tiab] OR "physical exam*"[tiab] OR "clinical exam*"[tiab] OR "clinical test*"[tiab] OR "provocative test*"[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "likelihood ratio*"[tiab] OR "diagnostic accuracy"[tiab] OR classification[tiab] OR grading[tiab] OR conservative[tiab] OR nonoperative[tiab] OR "non-operative"[tiab] OR nonsurgical[tiab] OR "non-surgical"[tiab] OR splint*[tiab] OR orthos*[tiab] OR orthotic*[tiab] OR brace*[tiab] OR immobili*[tiab] OR corticosteroid*[tiab] OR steroid*[tiab] OR glucocorticoid*[tiab] OR triamcinolone[tiab] OR methylprednisolone[tiab] OR injection*[tiab] OR exercis*[tiab] OR eccentric*[tiab] OR physiotherap*[tiab] OR "physical therap*"[tiab] OR "hand therap*"[tiab] OR "manual therap*"[tiab] OR mobilization[tiab] OR mobilisation[tiab] OR massage[tiab] OR surgery[tiab] OR surgical[tiab] OR release[tiab] OR "natural history"[tiab] OR "spontaneous resolution"[tiab] OR randomized[tiab] OR randomised[tiab] OR Quinnell[tiab] OR "Green classification"[tiab] OR severity[tiab] OR percutaneous[tiab] OR "A1 pulley release"[tiab]) AND (("randomized controlled trial"[pt] OR "controlled clinical trial"[pt] OR randomized[tiab] OR randomised[tiab] OR placebo[tiab] OR "clinical trials as topic"[mesh:noexp] OR randomly[tiab] OR trial[ti]) NOT (animals[mh] NOT humans[mh])) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])
```

### Diretrizes e consensos (`diretriz`)

```
(("Trigger Finger Disorder"[Mesh] OR "trigger finger*"[tiab] OR "trigger digit*"[tiab] OR "trigger thumb*"[tiab] OR "stenosing tenosynovitis"[tiab] OR "stenosing flexor tenosynovitis"[tiab] OR "stenosing tenovaginitis"[tiab] OR "flexor tenosynovitis"[tiab] OR "A1 pulley"[tiab]) AND ("Diagnosis, Differential"[Mesh] OR "Physical Examination"[Mesh] OR "Sensitivity and Specificity"[Mesh] OR "Predictive Value of Tests"[Mesh] OR "Severity of Illness Index"[Mesh] OR "Orthotic Devices"[Mesh] OR "Splints"[Mesh] OR "Braces"[Mesh] OR "Injections"[Mesh] OR "Glucocorticoids"[Mesh] OR "Adrenal Cortex Hormones"[Mesh] OR "Exercise Therapy"[Mesh] OR "Physical Therapy Modalities"[Mesh] OR "Musculoskeletal Manipulations"[Mesh] OR "Conservative Treatment"[Mesh] OR "Orthopedic Procedures"[Mesh] OR "Remission, Spontaneous"[Mesh] OR "differential diagnos*"[tiab] OR "physical exam*"[tiab] OR "clinical exam*"[tiab] OR "clinical test*"[tiab] OR "provocative test*"[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "likelihood ratio*"[tiab] OR "diagnostic accuracy"[tiab] OR classification[tiab] OR grading[tiab] OR conservative[tiab] OR nonoperative[tiab] OR "non-operative"[tiab] OR nonsurgical[tiab] OR "non-surgical"[tiab] OR splint*[tiab] OR orthos*[tiab] OR orthotic*[tiab] OR brace*[tiab] OR immobili*[tiab] OR corticosteroid*[tiab] OR steroid*[tiab] OR glucocorticoid*[tiab] OR triamcinolone[tiab] OR methylprednisolone[tiab] OR injection*[tiab] OR exercis*[tiab] OR eccentric*[tiab] OR physiotherap*[tiab] OR "physical therap*"[tiab] OR "hand therap*"[tiab] OR "manual therap*"[tiab] OR mobilization[tiab] OR mobilisation[tiab] OR massage[tiab] OR surgery[tiab] OR surgical[tiab] OR release[tiab] OR "natural history"[tiab] OR "spontaneous resolution"[tiab] OR randomized[tiab] OR randomised[tiab] OR Quinnell[tiab] OR "Green classification"[tiab] OR severity[tiab] OR percutaneous[tiab] OR "A1 pulley release"[tiab]) AND ("practice guideline"[pt] OR "guideline"[pt] OR "consensus statement"[pt] OR guideline*[ti] OR "practice guideline*"[tiab] OR consensus[ti] OR "position statement*"[ti] OR "position stand"[ti] OR recommendation*[ti]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

### Somente revistas-alvo (`revistas`)

```
(("Trigger Finger Disorder"[Mesh] OR "trigger finger*"[tiab] OR "trigger digit*"[tiab] OR "trigger thumb*"[tiab] OR "stenosing tenosynovitis"[tiab] OR "stenosing flexor tenosynovitis"[tiab] OR "stenosing tenovaginitis"[tiab] OR "flexor tenosynovitis"[tiab] OR "A1 pulley"[tiab]) AND ("Diagnosis, Differential"[Mesh] OR "Physical Examination"[Mesh] OR "Sensitivity and Specificity"[Mesh] OR "Predictive Value of Tests"[Mesh] OR "Severity of Illness Index"[Mesh] OR "Orthotic Devices"[Mesh] OR "Splints"[Mesh] OR "Braces"[Mesh] OR "Injections"[Mesh] OR "Glucocorticoids"[Mesh] OR "Adrenal Cortex Hormones"[Mesh] OR "Exercise Therapy"[Mesh] OR "Physical Therapy Modalities"[Mesh] OR "Musculoskeletal Manipulations"[Mesh] OR "Conservative Treatment"[Mesh] OR "Orthopedic Procedures"[Mesh] OR "Remission, Spontaneous"[Mesh] OR "differential diagnos*"[tiab] OR "physical exam*"[tiab] OR "clinical exam*"[tiab] OR "clinical test*"[tiab] OR "provocative test*"[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "likelihood ratio*"[tiab] OR "diagnostic accuracy"[tiab] OR classification[tiab] OR grading[tiab] OR conservative[tiab] OR nonoperative[tiab] OR "non-operative"[tiab] OR nonsurgical[tiab] OR "non-surgical"[tiab] OR splint*[tiab] OR orthos*[tiab] OR orthotic*[tiab] OR brace*[tiab] OR immobili*[tiab] OR corticosteroid*[tiab] OR steroid*[tiab] OR glucocorticoid*[tiab] OR triamcinolone[tiab] OR methylprednisolone[tiab] OR injection*[tiab] OR exercis*[tiab] OR eccentric*[tiab] OR physiotherap*[tiab] OR "physical therap*"[tiab] OR "hand therap*"[tiab] OR "manual therap*"[tiab] OR mobilization[tiab] OR mobilisation[tiab] OR massage[tiab] OR surgery[tiab] OR surgical[tiab] OR release[tiab] OR "natural history"[tiab] OR "spontaneous resolution"[tiab] OR randomized[tiab] OR randomised[tiab] OR Quinnell[tiab] OR "Green classification"[tiab] OR severity[tiab] OR percutaneous[tiab] OR "A1 pulley release"[tiab]) AND ("0190-6011"[jour] OR "1938-1344"[jour] OR "0894-1130"[jour] OR "1545-004X"[jour] OR "0363-5023"[jour] OR "1531-6564"[jour] OR "1753-1934"[jour] OR "2043-6289"[jour] OR "1058-2746"[jour] OR "1532-6500"[jour] OR "0363-5465"[jour] OR "1552-3365"[jour] OR "1469-493X"[jour]) AND 1990:3000[dp] AND (english[la] OR portuguese[la] OR spanish[la])) NOT (animals[mh] NOT humans[mh])
```

## Scopus

Cole em Scopus > Advanced document search (https://www.scopus.com/search/form.uri?display=advanced). Uma string por vez. Depois exporte o resultado (passo a passo no SKILL.md) e salve em `brutos/scopus.csv`.

### Base (só os blocos e os limites) (`base`)

```
TITLE-ABS-KEY("trigger finger*" OR "trigger digit*" OR "trigger thumb*" OR "stenosing tenosynovitis" OR "stenosing flexor tenosynovitis" OR "stenosing tenovaginitis" OR "flexor tenosynovitis" OR "A1 pulley" OR "Trigger Finger Disorder") AND TITLE-ABS-KEY("differential diagnos*" OR "physical exam*" OR "clinical exam*" OR "clinical test*" OR "provocative test*" OR sensitivity OR specificity OR "likelihood ratio*" OR "diagnostic accuracy" OR classification OR grading OR conservative OR nonoperative OR "non-operative" OR nonsurgical OR "non-surgical" OR splint* OR orthos* OR orthotic* OR brace* OR immobili* OR corticosteroid* OR steroid* OR glucocorticoid* OR triamcinolone OR methylprednisolone OR injection* OR exercis* OR eccentric* OR physiotherap* OR "physical therap*" OR "hand therap*" OR "manual therap*" OR mobilization OR mobilisation OR massage OR surgery OR surgical OR release OR "natural history" OR "spontaneous resolution" OR randomized OR randomised OR Quinnell OR "Green classification" OR severity OR percutaneous OR "A1 pulley release" OR "Diagnosis, Differential" OR "Physical Examination" OR "Sensitivity and Specificity" OR "Predictive Value of Tests" OR "Severity of Illness Index" OR "Orthotic Devices" OR Splints OR Braces OR Injections OR Glucocorticoids OR "Adrenal Cortex Hormones" OR "Exercise Therapy" OR "Physical Therapy Modalities" OR "Musculoskeletal Manipulations" OR "Conservative Treatment" OR "Orthopedic Procedures" OR "Remission, Spontaneous") AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Revisões sistemáticas e meta-análises (`rs`)

```
TITLE-ABS-KEY("trigger finger*" OR "trigger digit*" OR "trigger thumb*" OR "stenosing tenosynovitis" OR "stenosing flexor tenosynovitis" OR "stenosing tenovaginitis" OR "flexor tenosynovitis" OR "A1 pulley" OR "Trigger Finger Disorder") AND TITLE-ABS-KEY("differential diagnos*" OR "physical exam*" OR "clinical exam*" OR "clinical test*" OR "provocative test*" OR sensitivity OR specificity OR "likelihood ratio*" OR "diagnostic accuracy" OR classification OR grading OR conservative OR nonoperative OR "non-operative" OR nonsurgical OR "non-surgical" OR splint* OR orthos* OR orthotic* OR brace* OR immobili* OR corticosteroid* OR steroid* OR glucocorticoid* OR triamcinolone OR methylprednisolone OR injection* OR exercis* OR eccentric* OR physiotherap* OR "physical therap*" OR "hand therap*" OR "manual therap*" OR mobilization OR mobilisation OR massage OR surgery OR surgical OR release OR "natural history" OR "spontaneous resolution" OR randomized OR randomised OR Quinnell OR "Green classification" OR severity OR percutaneous OR "A1 pulley release" OR "Diagnosis, Differential" OR "Physical Examination" OR "Sensitivity and Specificity" OR "Predictive Value of Tests" OR "Severity of Illness Index" OR "Orthotic Devices" OR Splints OR Braces OR Injections OR Glucocorticoids OR "Adrenal Cortex Hormones" OR "Exercise Therapy" OR "Physical Therapy Modalities" OR "Musculoskeletal Manipulations" OR "Conservative Treatment" OR "Orthopedic Procedures" OR "Remission, Spontaneous") AND TITLE-ABS-KEY("systematic review" OR "meta analy*" OR metaanaly* OR "umbrella review") AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Ensaios clínicos randomizados (`ecr`)

```
TITLE-ABS-KEY("trigger finger*" OR "trigger digit*" OR "trigger thumb*" OR "stenosing tenosynovitis" OR "stenosing flexor tenosynovitis" OR "stenosing tenovaginitis" OR "flexor tenosynovitis" OR "A1 pulley" OR "Trigger Finger Disorder") AND TITLE-ABS-KEY("differential diagnos*" OR "physical exam*" OR "clinical exam*" OR "clinical test*" OR "provocative test*" OR sensitivity OR specificity OR "likelihood ratio*" OR "diagnostic accuracy" OR classification OR grading OR conservative OR nonoperative OR "non-operative" OR nonsurgical OR "non-surgical" OR splint* OR orthos* OR orthotic* OR brace* OR immobili* OR corticosteroid* OR steroid* OR glucocorticoid* OR triamcinolone OR methylprednisolone OR injection* OR exercis* OR eccentric* OR physiotherap* OR "physical therap*" OR "hand therap*" OR "manual therap*" OR mobilization OR mobilisation OR massage OR surgery OR surgical OR release OR "natural history" OR "spontaneous resolution" OR randomized OR randomised OR Quinnell OR "Green classification" OR severity OR percutaneous OR "A1 pulley release" OR "Diagnosis, Differential" OR "Physical Examination" OR "Sensitivity and Specificity" OR "Predictive Value of Tests" OR "Severity of Illness Index" OR "Orthotic Devices" OR Splints OR Braces OR Injections OR Glucocorticoids OR "Adrenal Cortex Hormones" OR "Exercise Therapy" OR "Physical Therapy Modalities" OR "Musculoskeletal Manipulations" OR "Conservative Treatment" OR "Orthopedic Procedures" OR "Remission, Spontaneous") AND (TITLE-ABS-KEY(randomized OR randomised OR randomly OR placebo OR "controlled trial" OR "clinical trial") OR TITLE(trial)) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Diretrizes e consensos (`diretriz`)

```
TITLE-ABS-KEY("trigger finger*" OR "trigger digit*" OR "trigger thumb*" OR "stenosing tenosynovitis" OR "stenosing flexor tenosynovitis" OR "stenosing tenovaginitis" OR "flexor tenosynovitis" OR "A1 pulley" OR "Trigger Finger Disorder") AND TITLE-ABS-KEY("differential diagnos*" OR "physical exam*" OR "clinical exam*" OR "clinical test*" OR "provocative test*" OR sensitivity OR specificity OR "likelihood ratio*" OR "diagnostic accuracy" OR classification OR grading OR conservative OR nonoperative OR "non-operative" OR nonsurgical OR "non-surgical" OR splint* OR orthos* OR orthotic* OR brace* OR immobili* OR corticosteroid* OR steroid* OR glucocorticoid* OR triamcinolone OR methylprednisolone OR injection* OR exercis* OR eccentric* OR physiotherap* OR "physical therap*" OR "hand therap*" OR "manual therap*" OR mobilization OR mobilisation OR massage OR surgery OR surgical OR release OR "natural history" OR "spontaneous resolution" OR randomized OR randomised OR Quinnell OR "Green classification" OR severity OR percutaneous OR "A1 pulley release" OR "Diagnosis, Differential" OR "Physical Examination" OR "Sensitivity and Specificity" OR "Predictive Value of Tests" OR "Severity of Illness Index" OR "Orthotic Devices" OR Splints OR Braces OR Injections OR Glucocorticoids OR "Adrenal Cortex Hormones" OR "Exercise Therapy" OR "Physical Therapy Modalities" OR "Musculoskeletal Manipulations" OR "Conservative Treatment" OR "Orthopedic Procedures" OR "Remission, Spontaneous") AND (TITLE(guideline* OR consensus OR "position statement*" OR "position stand" OR recommendation*) OR TITLE-ABS-KEY("practice guideline*")) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

### Somente revistas-alvo (`revistas`)

```
TITLE-ABS-KEY("trigger finger*" OR "trigger digit*" OR "trigger thumb*" OR "stenosing tenosynovitis" OR "stenosing flexor tenosynovitis" OR "stenosing tenovaginitis" OR "flexor tenosynovitis" OR "A1 pulley" OR "Trigger Finger Disorder") AND TITLE-ABS-KEY("differential diagnos*" OR "physical exam*" OR "clinical exam*" OR "clinical test*" OR "provocative test*" OR sensitivity OR specificity OR "likelihood ratio*" OR "diagnostic accuracy" OR classification OR grading OR conservative OR nonoperative OR "non-operative" OR nonsurgical OR "non-surgical" OR splint* OR orthos* OR orthotic* OR brace* OR immobili* OR corticosteroid* OR steroid* OR glucocorticoid* OR triamcinolone OR methylprednisolone OR injection* OR exercis* OR eccentric* OR physiotherap* OR "physical therap*" OR "hand therap*" OR "manual therap*" OR mobilization OR mobilisation OR massage OR surgery OR surgical OR release OR "natural history" OR "spontaneous resolution" OR randomized OR randomised OR Quinnell OR "Green classification" OR severity OR percutaneous OR "A1 pulley release" OR "Diagnosis, Differential" OR "Physical Examination" OR "Sensitivity and Specificity" OR "Predictive Value of Tests" OR "Severity of Illness Index" OR "Orthotic Devices" OR Splints OR Braces OR Injections OR Glucocorticoids OR "Adrenal Cortex Hormones" OR "Exercise Therapy" OR "Physical Therapy Modalities" OR "Musculoskeletal Manipulations" OR "Conservative Treatment" OR "Orthopedic Procedures" OR "Remission, Spontaneous") AND (ISSN(0190-6011) OR ISSN(1938-1344) OR ISSN(0894-1130) OR ISSN(1545-004X) OR ISSN(0363-5023) OR ISSN(1531-6564) OR ISSN(1753-1934) OR ISSN(2043-6289) OR ISSN(1058-2746) OR ISSN(1532-6500) OR ISSN(0363-5465) OR ISSN(1552-3365) OR ISSN(1469-493X)) AND PUBYEAR > 1989 AND (DOCTYPE(ar) OR DOCTYPE(re)) AND (LANGUAGE(english) OR LANGUAGE(portuguese) OR LANGUAGE(spanish))
```

## Crossref e site do JOSPT

A Crossref não aceita booleanos: recebe palavras e ordena por relevância. O script filtra depois, localmente, pelos blocos de conceito.

```
trigger finger digit stenosing tenosynovitis diagnosis treatment injection
```

ISSNs consultados por padrão: 0190-6011, 1938-1344, 0894-1130, 1545-004X, 0363-5023, 1531-6564, 1753-1934, 2043-6289, 1058-2746, 1532-6500, 0363-5465, 1552-3365, 1469-493X.

Busca no site do JOSPT (abra no navegador; o site bloqueia acesso automatizado):

```
("trigger finger" OR "trigger digit" OR "stenosing tenosynovitis") AND (diagnosis OR treatment OR injection OR orthosis OR exercise)
```

<https://www.jospt.org/action/doSearch?AllField=%28%22trigger+finger%22+OR+%22trigger+digit%22+OR+%22stenosing+tenosynovitis%22%29+AND+%28diagnosis+OR+treatment+OR+injection+OR+orthosis+OR+exercise%29&AfterYear=1990>

## Filtros metodológicos usados

- **Revisões sistemáticas e meta-análises** (`rs`): PubMed: subconjunto systematic[sb] (filtro de revisões sistemáticas da NLM) somado ao tipo de publicação Meta-Analysis e a palavras de título. Scopus: tradução aproximada, sem validação. systematic[sb] é sensível e pouco preciso: traz revisões narrativas que dizem 'systematic'. A triagem resolve.
- **Ensaios clínicos randomizados** (`ecr`): PubMed: Cochrane Highly Sensitive Search Strategy, versão que maximiza sensibilidade e precisão (revisão de 2008; Cochrane Handbook, suplemento técnico do cap. 4). Scopus: tradução aproximada, sem validação. Acréscimo nosso ao filtro Cochrane: randomised[tiab] (grafia britânica), que só aumenta a sensibilidade.
- **Diretrizes e consensos** (`diretriz`): Filtro pragmático: tipos de publicação do PubMed (Practice Guideline, Guideline, Consensus Statement, nome atual do antigo Consensus Development Conference) e palavras de título, na linha do filtro de diretrizes do CADTH. Não é um filtro validado. Diretrizes de sociedades também ficam fora das bases (sites de APTA, NICE, AAOS). Complete com busca manual.

Todo filtro de desenho troca sensibilidade por precisão. Se um artigo-sentinela sumir quando o filtro entra, a perda é do filtro, não dos blocos: confira com `teste_sentinela.py --variante <nome>`.

## Avisos de tradução entre bases

- Bloco 'condicao': o Scopus não explode MeSH. Os descritores mais específicos só entram se estiverem em 'livres' ou 'scopus_extra'.
- Bloco 'dx_tx': o Scopus não explode MeSH. Os descritores mais específicos só entram se estiverem em 'livres' ou 'scopus_extra'.
- Scopus não tem filtro 'humanos' equivalente ao do PubMed; o limite foi deixado de fora na string Scopus. Exclua estudos em animais na triagem.

## Execuções e contagens

### PubMed

| Data | Variante | Total na base | Baixados | Avisos |
|---|---|---|---|---|
| 2026-11-24 | base | 1831 | só contagem | - |
| 2026-11-24 | rs | 82 | só contagem | - |
| 2026-11-24 | ecr | 217 | só contagem | - |
| 2026-11-24 | diretriz | 13 | só contagem | - |
| 2026-11-24 | revistas | 352 | só contagem | - |
| 2026-11-24 | base | 1831 | só contagem | - |
| 2026-11-24 | rs | 82 | só contagem | - |
| 2026-11-24 | ecr | 217 | só contagem | - |
| 2026-11-24 | diretriz | 13 | só contagem | - |
| 2026-11-24 | revistas | 352 | só contagem | - |

Registros únicos do PubMed: **0**.

Tradução que o PubMed fez da variante `base` (2026-11-24). Confira se cada termo virou o campo esperado; as traduções das outras variantes estão em `brutos/pubmed.json`.

```
(("Trigger Finger Disorder"[MeSH Terms] OR "trigger finger*"[Title/Abstract] OR "trigger digit*"[Title/Abstract] OR "trigger thumb*"[Title/Abstract] OR "stenosing tenosynovitis"[Title/Abstract] OR "stenosing flexor tenosynovitis"[Title/Abstract] OR "stenosing tenovaginitis"[Title/Abstract] OR "flexor tenosynovitis"[Title/Abstract] OR "A1 pulley"[Title/Abstract]) AND ("diagnosis, differential"[MeSH Terms] OR "Physical Examination"[MeSH Terms] OR "Sensitivity and Specificity"[MeSH Terms] OR "Predictive Value of Tests"[MeSH Terms] OR "Severity of Illness Index"[MeSH Terms] OR "Orthotic Devices"[MeSH Terms] OR "Splints"[MeSH Terms] OR "Braces"[MeSH Terms] OR "Injections"[MeSH Terms] OR "Glucocorticoids"[MeSH Terms] OR "Adrenal Cortex Hormones"[MeSH Terms] OR "Exercise Therapy"[MeSH Terms] OR "Physical Therapy Modalities"[MeSH Terms] OR "Musculoskeletal Manipulations"[MeSH Terms] OR "Conservative Treatment"[MeSH Terms] OR "Orthopedic Procedures"[MeSH Terms] OR "remission, spontaneous"[MeSH Terms] OR "differential diagnos*"[Title/Abstract] OR "physical exam*"[Title/Abstract] OR "clinical exam*"[Title/Abstract] OR "clinical test*"[Title/Abstract] OR "provocative test*"[Title/Abstract] OR "sensitivity"[Title/Abstract] OR "specificity"[Title/Abstract] OR "likelihood ratio*"[Title/Abstract] OR "diagnostic accuracy"[Title/Abstract] OR "classification"[Title/Abstract] OR "grading"[Title/Abstract] OR "conservative"[Title/Abstract] OR "nonoperative"[Title/Abstract] OR "non-operative"[Title/Abstract] OR "nonsurgical"[Title/Abstract] OR "non-surgical"[Title/Abstract] OR "splint*"[Title/Abstract] OR "orthos*"[Title/Abstract] OR "orthotic*"[Title/Abstract] OR "brace*"[Title/Abstract] OR "immobili*"[Title/Abstract] OR "corticosteroid*"[Title/Abstract] OR "steroid*"[Title/Abstract] OR "glucocorticoid*"[Title/Abstract] OR "triamcinolone"[Title/Abstract] OR "methylprednisolone"[Title/Abstract] OR "injection*"[Title/Abstract] OR "exercis*"[Title/Abstract] OR "eccentric*"[Title/Abstract] OR "physiotherap*"[Title/Abstract] OR "physical therap*"[Title/Abstract] OR "hand therap*"[Title/Abstract] OR "manual therap*"[Title/Abstract] OR "mobilization"[Title/Abstract] OR "mobilisation"[Title/Abstract] OR "massage"[Title/Abstract] OR "surgery"[Title/Abstract] OR "surgical"[Title/Abstract] OR "release"[Title/Abstract] OR "natural history"[Title/Abstract] OR "spontaneous resolution"[Title/Abstract] OR "randomized"[Title/Abstract] OR "randomised"[Title/Abstract] OR "Quinnell"[Title/Abstract] OR "Green classification"[Title/Abstract] OR "severity"[Title/Abstract] OR "percutaneous"[Title/Abstract] OR "A1 pulley release"[Title/Abstract]) AND 1990/01/01:3000/12/31[Date - Publication] AND ("english"[Language] OR "portuguese"[Language] OR "spanish"[Language])) NOT ("animals"[MeSH Terms] NOT "humans"[MeSH Terms])
```

### Teste de sentinela

Variante testada: `base`. Recuperados: **10 de 10** (2026-11-24).

| Sentinela | Título | Resultado | Blocos que falharam |
|---|---|---|---|
| PMID 24810861 | Multidisciplinary consensus guideline for managing trigger finger: results from the Europe | recuperado | - |
| PMID 19160256 | Corticosteroid injection for trigger finger in adults | recuperado | - |
| PMID 29460276 | Surgery for trigger finger | recuperado | - |
| PMID 33849080 | Non-steroidal anti-inflammatory drugs (NSAIDs) for trigger finger | recuperado | - |
| PMID 21816888 | Outcome of corticosteroid injection versus physiotherapy in the treatment of mild trigger  | recuperado | - |
| PMID 22039269 | Treatment of trigger finger: randomized clinical trial comparing the methods of corticoste | recuperado | - |
| PMID 1538090 | Trigger fingers and thumb: when to splint, inject, or operate | recuperado | - |
| PMID 29290504 | Conservative management of trigger finger: A systematic review | recuperado | - |
| PMID 37391318 | Orthotic intervention options to non-surgically manage adult and pediatric trigger finger: | recuperado | - |
| PMID 41691955 | Evidence-based management strategies for adult trigger digits: a systematic review and net | recuperado | - |


## Artigos-sentinela

- PMID 24810861 - Diretriz de consenso HANDGUIDE para dedo em gatilho (Huisstede 2014, Phys Ther)
- PMID 19160256 - Cochrane 2009: injeção de corticoide no dedo em gatilho
- PMID 29460276 - Cochrane 2018: cirurgia no dedo em gatilho
- PMID 33849080 - Cochrane 2021: AINE no dedo em gatilho
- PMID 21816888 - ECR Salim 2012: corticoide x fisioterapia no gatilho leve
- PMID 22039269 - ECR Sato 2012: injeção x liberação percutânea x cirurgia aberta
- PMID 1538090 - Patel 1992: quando imobilizar, injetar ou operar (graduação clássica)
- PMID 29290504 - RS Lunsford 2019 J Hand Ther: manejo conservador
- PMID 37391318 - RS Leong 2023 J Hand Ther: órteses
- PMID 41691955 - RS com meta-análise em rede Chiang 2026: manejo do dedo em gatilho em adultos

## Decisões e histórico

<!-- MANUAL: tudo abaixo desta linha é seu e será preservado quando o arquivo for gerado de novo -->

- O histórico das voltas, a string Scopus e a triagem deste ramo estão em `01_busca/estrategia.md` (seção Decisões e histórico).
