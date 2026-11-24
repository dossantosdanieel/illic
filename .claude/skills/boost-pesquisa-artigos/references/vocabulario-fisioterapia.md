# Vocabulário de busca para fisioterapia musculoesquelética, esportiva, dor e exercício

Use este arquivo para montar os blocos de `conceitos.json`: descritores MeSH para o campo `mesh`, sinônimos para o campo `livres`, e ISSN das revistas para `revistas_alvo`.

Tudo que é MeSH ou ISSN aqui foi conferido nas APIs em 24/11/2026 (banco MeSH do NLM via E-utilities; NLM Catalog; Crossref). O MeSH muda todo ano. Antes de usar um descritor que não está nesta lista, ou depois de alguns meses, confira de novo com `montar_strings.py conceitos.json --verificar-mesh`.

## Índice

1. Termos que parecem MeSH e não são
2. Descritores novos e onde está o artigo antigo
3. Descritores MeSH por tema
4. Sinônimos em texto livre por tema
5. Instrumentos e desfechos (siglas)
6. Revistas-alvo com ISSN
7. Como reconferir

## 1. Termos que parecem MeSH e não são

No PubMed, um descritor inexistente entre aspas com `[Mesh]` devolve **zero sem dar erro** e o bloco fica mais fraco sem ninguém perceber. Estes foram testados e recusados pelo NLM:

| Você escreveria | Situação no MeSH | O que usar |
|---|---|---|
| Frozen Shoulder, Adhesive Capsulitis | termos de entrada de **Bursitis** | `"Bursitis"[Mesh]` + `frozen shoulder`, `adhesive capsulitis` em texto livre |
| Plantar Fasciitis | o descritor é invertido | `"Fasciitis, Plantar"[Mesh]` |
| Kinesio Tape | termo de entrada | `"Athletic Tape"[Mesh]` + `kinesio tap*`, `kinesiotap*` |
| Pain, Postoperative | nome mudou | `"Postoperative Pain"[Mesh]` |
| Osgood-Schlatter Disease | termo de entrada | `"Osteochondrosis"[Mesh]` + texto livre |
| Achilles Tendinopathy, Patellar Tendinopathy, Gluteal Tendinopathy | não existem | `"Tendinopathy"[Mesh]` cruzado com `"Achilles Tendon"[Mesh]` ou `"Patellar Ligament"[Mesh]`; texto livre para o glúteo |
| Greater Trochanteric Pain Syndrome | não existe | só texto livre: `greater trochanteric pain`, `gluteal tendinopath*`, `trochanteric bursitis` |
| Hamstring Injuries, Muscle Strain | não existem | `"Hamstring Muscles/injuries"[Mesh]`, `"Sprains and Strains"[Mesh]` + `hamstring strain*`, `hamstring injur*` |
| Chronic Ankle Instability | não existe | `"Ankle Injuries"[Mesh]`, `"Joint Instability"[Mesh]`, `"Lateral Ligament, Ankle"[Mesh]` + `chronic ankle instability` |
| Scapular Dyskinesis | não existe | `"Scapula"[Mesh]` + `scapular dyskines*`, `scapular kinematic*` |
| Delayed Onset Muscle Soreness | não existe | `"Myalgia"[Mesh]` + `delayed onset muscle soreness`, `DOMS` |
| Eccentric Exercise, Isometric Strength, Stretching | não existem | `"Resistance Training"[Mesh]`, `"Isometric Contraction"[Mesh]`, `"Muscle Stretching Exercises"[Mesh]` + texto livre |
| Pilates | não existe | `"Exercise Movement Techniques"[Mesh]` + `pilates` |
| Pain Neuroscience Education, Graded Exposure, Graded Motor Imagery | não existem | `"Patient Education as Topic"[Mesh]`, `"Imagery, Psychotherapy"[Mesh]` + texto livre |
| Shoulder Pain and Disability Index | não existe (instrumento) | texto livre: `SPADI`, `shoulder pain and disability index` |
| Handball | não existe | `"Team Sports"[Mesh]`, `"Athletes"[Mesh]` + `handball` |
| Randomized Controlled Trial, Systematic Review, Meta-Analysis, Practice Guideline com `[Mesh]` | são **tipos de publicação** | use `[pt]`. Com `[Mesh]` existem só as versões "as Topic" (artigos *sobre* o método) |
| Consensus Development Conference `[pt]` | o tipo de publicação hoje se chama **Consensus Statement** | `"consensus statement"[pt]` |

## 2. Descritores novos e onde está o artigo antigo


Descritor criado depois de 2010 só indexa artigos a partir daquele ano. Para pegar os anteriores, some o descritor antigo ou o texto livre.

| Descritor MeSH | Desde | Antes disso, indexado como |
|---|---|---|
| Anterior Cruciate Ligament Injuries | 2017 | Anterior Cruciate Ligament/injuries (1990-2016); Knee Injuries (1974-2016) |
| Anterior Cruciate Ligament Reconstruction | 2012 | Anterior Cruciate Ligament/surgery (1990-2011) |
| Aquatic Therapy | 2022 | Hydrotherapy (1966-2021) |
| Blood Flow Restriction Therapy | 2022 | Exercise (2007-2021) |
| Cardiac Rehabilitation | 2017 | Cardiovascular Diseases (1963-2016) |
| Catastrophization | 2011 | Anxiety (1984-2010) |
| Central Nervous System Sensitization | 2012 | Pain (1998-2011) |
| Chronic Pain | 2012 | Pain (1993-2011) |
| Clinical Decision Rules | 2020 | Decision Support Techniques (1991-2019) |
| Clinical Decision-Making | 2016 | Decision Making (1972-2015) |
| Clinical Reasoning | 2021 | Thinking (1985-2020) |
| Cognitive Behavioral Therapy | 2019 | Behavior Therapy (1967-1989); Cognition (1967-1989) |
| Decision Making, Shared | 2020 | Decision Making (2000-2019) |
| Diffuse Noxious Inhibitory Control | 2012 | Pain (1994-2011) |
| Elbow Tendinopathy | 2017 | Tennis Elbow (1987-2016) |
| Endurance Training | 2019 | Physical Endurance (1975-2018) |
| Exergaming | 2022 | Video Games (2009-2021) |
| Extracorporeal Shockwave Therapy | 2018 | High-Energy Shock Waves/therapeutic use (1989-2017) |
| Femoracetabular Impingement | 2011 | Acetabulum (1999-2010); Hip Joint (2001-2010) |
| Foot Orthoses | 2013 | Orthotic Devices (1973-2012) |
| Frailty | 2018 | Frail Elderly (1990-2017) |
| Gait Analysis | 2019 | Gait (1981-2018) |
| Glenoid Cavity | 2012 | Scapula (1963-2011) |
| Hamstring Muscles | 2017 | Muscle, Skeletal (1965-2016) |
| Hamstring Tendons | 2017 | Tendons (1970-2016) |
| High-Intensity Interval Training | 2017 | Exercise (1995-2016) |
| Iliotibial Band Syndrome | 2011 | Cumulative Trauma Disorders (1992-2010); Knee Injuries (1993-2010) |
| Imagery, Psychotherapy | 2020 | Relaxation Techniques (1980-1995) |
| Kinesiophobia | 2023 | Phobic Disorders (2003-2022) |
| Medial Tibial Stress Syndrome | 2011 | Leg Injuries (1967-2010); Tibia (1967-2010) |
| Minimal Clinically Important Difference | 2017 | Treatment Outcome (2001-2016) |
| Mirror Movement Therapy | 2022 | Physical Therapy Modalities (2010-2021) |
| Motivational Interviewing | 2013 | Nondirective Therapy (1996-2012) |
| Musculoskeletal Pain | 2012 | Pain (1963-2011) |
| Neurofeedback | 2011 | Biofeedback, Psychology (1995-2010) |
| Neurological Rehabilitation | 2016 | Rehabilitation (1963-2015) |
| Nociception | 2012 | Pain (1966-2011) |
| Nociceptive Pain | 2012 | Pain (1963-2011) |
| Outcome Assessment, Health Care | 2020 | Outcome and Process Assessment (Health Care) (1979-1991) |
| Pain Management | 2012 | Pain (1966-2011) |
| Pain Perception | 2011 | Pain (1963-2010) |
| Paraspinal Muscles | 2014 | Muscle, Skeletal (1972-2013) |
| Patient Reported Outcome Measures | 2017 | Patient Outcome Assessment (2013-2016) |
| Peripheral Nerve Injuries | 2012 | Peripheral Nerves/injuries (1965-2011) |
| Physical Therapy Specialty | 2012 | Physical Therapy Techniques (1963-2001) |
| Plyometric Exercise | 2012 | Exercise (1992-2011); Muscle Stretching Exercises (2006-2011) |
| Preoperative Exercise | 2021 | Exercise (1996-2020) |
| Reinjuries | 2021 | Wounds and Injuries (1992-2020) |
| Rotator Cuff Injuries | 2017 | Rotator Cuff/injuries (1991-2016); Shoulder Joint/injuries (1982-2016) |
| Self-Management | 2018 | Self Care (2015-2017) |
| Shoulder Injuries | 2017 | Shoulder (1966-2016) |
| Stroke Rehabilitation | 2017 | Cerebrovascular Disorders/rehabilitation (1969-2016); Stroke/rehabilitation (1982-2016) |
| Team Sports | 2021 | Sports (1975-2020) |
| Telerehabilitation | 2016 | Telemedicine (1996-2015) |
| Tibial Meniscus Injuries | 2017 | Leg Injuries (1963-2016); Menisci, Tibial/injuries (1967-2016) |
| Treatment Adherence and Compliance | 2018 | Patient Compliance (1963-2017) |
| Trigger Points | 2012 | Myofascial Pain Syndromes (1984-2011) |
| Visual Analog Scale | 2014 | Pain Measurement (1986-2013) |
| Walk Test | 2017 | Exercise Test (1986-2016) |
| Warm-Up Exercise | 2014 | Exercise (1977-2013) |
| Youth Sports | 2016 | Sports (1970-2014) |


## 3. Descritores MeSH por tema

Todos confirmados como descritores. O ano entre parênteses aparece só para os criados de 2011 em diante. Lembre que `[Mesh]` explode (inclui os descritores mais específicos); use `"explodir": false` quando o descritor for uma estrutura anatômica ou um termo muito largo.

### Condições clínicas (118 descritores confirmados)

Accidental Falls; Achilles Tendon; Achilles Tendon; Acromioclavicular Joint; Ankle Injuries; Anterior Cruciate Ligament Injuries (2017); Anterior Cruciate Ligament Reconstruction (2012); Arthralgia; Arthritis, Rheumatoid; Arthroplasty, Replacement, Hip; Arthroplasty, Replacement, Knee; Athletic Injuries; Back Pain; Brain Concussion; Bursitis; Calcinosis; Carpal Tunnel Syndrome; Central Nervous System Sensitization (2012); Chronic Pain (2012); Complex Regional Pain Syndromes; Cumulative Trauma Disorders; Elbow Joint; Elbow Tendinopathy (2017); Fascia; Fasciitis, Plantar; Femoracetabular Impingement (2011); Fibromyalgia; Flatfoot; Foot Diseases; Fractures, Stress; Frailty (2018); Glenoid Cavity (2012); Groin; Growth Plate; Hallux Valgus; Hamstring Muscles (2017); Hamstring Tendons (2017); Hand Injuries; Headache; Hip Dislocation, Congenital (2026); Hip Injuries; Hyperalgesia; Iliotibial Band Syndrome (2011); Intervertebral Disc Displacement; Joint Capsule; Joint Diseases; Joint Instability; Knee Injuries; Kyphosis; Lateral Ligament, Ankle; Leg Injuries; Lordosis; Low Back Pain; Medial Collateral Ligament, Knee; Medial Tibial Stress Syndrome (2011); Muscle Cramp; Muscle, Skeletal; Musculoskeletal Diseases; Musculoskeletal Pain (2012); Myalgia (2014); Myofascial Pain Syndromes; Neck Pain; Nerve Compression Syndromes; Neuralgia; Nociceptive Pain (2012); Osteoarthritis (2013); Osteoarthritis, Hip; Osteoarthritis, Knee; Osteochondritis; Osteoporosis; Overtraining Syndrome (2023); Patella; Patellar Dislocation; Patellar Ligament; Patellar Ligament; Patellofemoral Pain Syndrome; Pelvic Floor; Peripheral Nerve Injuries (2012); Piriformis Muscle Syndrome; Post-Concussion Syndrome; Posterior Cruciate Ligament; Postoperative Pain; Pubic Symphysis; Radiculopathy; Reinjuries (2021); Relative Energy Deficiency in Sport (2020); Rotator Cuff; Rotator Cuff Injuries (2017); Sacroiliac Joint; Sarcopenia; Sciatica; Scoliosis; Shoulder; Shoulder Dislocation; Shoulder Dislocation; Shoulder Fractures; Shoulder Impingement Syndrome; Shoulder Injuries (2017); Shoulder Pain; Spinal Curvatures; Spinal Stenosis; Spondylolisthesis; Sprains and Strains; Stroke Rehabilitation (2017); Temporomandibular Joint Disorders; Tendinopathy; Tendon Injuries; Tennis Elbow; Tension-Type Headache; Thoracic Outlet Syndrome; Thoracic Vertebrae; Tibial Meniscus Injuries (2017); Torticollis; Trigger Points (2012); Ulnar Neuropathies; Urinary Incontinence; Whiplash Injuries; Wrist Injuries.

### Intervenções (84 descritores confirmados)

Acupuncture Therapy; Adrenal Cortex Hormones; Anti-Inflammatory Agents, Non-Steroidal; Aquatic Therapy (2022); Arthroscopy; Athletic Tape; Biofeedback, Psychology; Blood Flow Restriction Therapy (2022); Braces; Breathing Exercises; Cardiac Rehabilitation (2017); Circuit-Based Exercise (2015); Cognitive Behavioral Therapy (2019); Conservative Treatment (2017); Cryotherapy; Decision Making, Shared (2020); Dry Needling (2020); Electric Stimulation Therapy; Endurance Training (2019); Exercise; Exercise Movement Techniques; Exercise Therapy (2026); Exergaming (2022); Extracorporeal Shockwave Therapy (2018); Feedback, Sensory; Foot Orthoses (2013); Health Behavior; Health Education; High-Intensity Interval Training (2017); Hydrotherapy; Hyperthermia, Induced; Imagery, Psychotherapy (2020); Injections, Intra-Articular; Isometric Contraction; Low-Level Light Therapy; Manipulation, Orthopedic; Manipulation, Spinal; Massage; Mirror Movement Therapy (2022); Mobile Applications (2014); Motivational Interviewing (2013); Motor Activity; Motor Skills; Muscle Contraction; Muscle Stretching Exercises; Musculoskeletal Manipulations; Neurofeedback (2011); Neurological Rehabilitation (2016); Nocebo Effect (2014); Occupational Therapy; Orthopedic Procedures; Orthotic Devices; Pain Management (2012); Patient Education as Topic; Physical Conditioning, Human (2014); Physical Exertion; Physical Fitness; Physical Therapy Modalities; Physical Therapy Specialty (2012); Placebo Effect; Platelet-Rich Plasma; Plyometric Exercise (2012); Preoperative Exercise (2021); Professional-Patient Relations; Rehabilitation; Resistance Training; Return to Sport (2016); Return to Work (2013); Self Care; Self-Management (2018); Tai Ji; Telemedicine; Telerehabilitation (2016); Therapeutic Alliance (2019); Therapy, Soft Tissue (2014); Transcutaneous Electric Nerve Stimulation; Ultrasonic Therapy; Virtual Reality (2018); Virtual Reality Exposure Therapy (2013); Warm-Up Exercise (2014); Wearable Electronic Devices (2018); Weight Lifting; Weight-Bearing; Yoga.

### Desfechos, medidas e fatores psicossociais (59 descritores confirmados)

Activities of Daily Living; Anxiety; Catastrophization (2011); Clinical Decision-Making (2016); Clinical Reasoning (2021); Depression; Disability Evaluation; Exercise Test; Exercise Tolerance; Fatigue; Fear; Gait; Gait Analysis (2019); Hand Strength; Health Status; Incidence; Kinesiophobia (2023); Kinesthesis; Minimal Clinically Important Difference (2017); Movement; Muscle Strength; Muscle Strength Dynamometer; Muscle Tonus; Outcome Assessment, Health Care (2020); Oxygen Consumption; Pain Measurement; Pain Perception (2011); Pain Threshold; Patient Acuity (2013); Patient Compliance; Patient Outcome Assessment (2014); Patient Reported Outcome Measures (2017); Patient Satisfaction; Physical Examination; Physical Functional Performance (2019); Postural Balance; Posture; Predictive Value of Tests; Prognosis; Proprioception; Psychometrics; Quality of Life; Range of Motion, Articular; Recovery of Function; Recurrence; Reproducibility of Results; Risk Factors; Self Efficacy; Sensitivity and Specificity; Sick Leave; Sleep (2026); Surveys and Questionnaires (2016); Torque; Treatment Adherence and Compliance (2018); Treatment Outcome; Visual Analog Scale (2014); Walk Test (2017); Work Capacity Evaluation; Workload.

### Mecanismos, anatomia, esporte e população (59 descritores confirmados)

Adaptation, Physiological; Adolescent; Aged; Ankle Joint; Athletes; Athletic Performance; Baseball; Basketball; Bicycling; Biomechanical Phenomena; Central Nervous System; Cervical Vertebrae; Collagen; Dancing; Diffuse Noxious Inhibitory Control (2012); Elasticity Imaging Techniques; Electromyography; Evoked Potentials, Motor; Football; Gymnastics; Hip Joint; Hypertrophy; Inflammation; Kinetics; Knee Joint; Lumbar Vertebrae; Magnetic Resonance Imaging; Martial Arts; Mechanotransduction, Cellular; Motor Cortex; Motor Neurons; Muscle Fatigue; Muscle Weakness; Muscular Atrophy; Neuronal Plasticity; Nociception (2012); Pain; Paraspinal Muscles (2014); Quadriceps Muscle; Regeneration; Rugby (2022); Running; Scapula; Shoulder Joint; Soccer; Sports; Sports for Persons with Disabilities (2014); Sports Medicine; Stress, Mechanical; Swimming; Team Sports (2021); Tendon Transfer; Tendons; Tennis; Transcranial Magnetic Stimulation; Ultrasonography; Volleyball; Wound Healing; Youth Sports (2016).

### Desenho e método (22 descritores confirmados)

Animals; Cadaver; Case-Control Studies; Clinical Decision Rules (2020); Cohort Studies; Consensus; Cross-Sectional Studies; Delphi Technique; Evidence-Based Practice; Follow-Up Studies; Humans; Longitudinal Studies; Meta-Analysis as Topic; Practice Guidelines as Topic; Prospective Studies; Randomized Controlled Trials as Topic; Retrospective Studies; Systematic Reviews as Topic (2019).

## 4. Sinônimos em texto livre por tema

Listas para o campo `livres`. Truncagem com `*`; frases sem aspas (o script põe). Sempre inclua a grafia britânica quando ela muda a raiz (`mobilisation`, `randomised`, `tumour`) e os nomes antigos da condição, porque a literatura anterior a 2015 usa outra nomenclatura.

**Ombro, manguito rotador.** rotator cuff tendinopath*; rotator cuff tendin*; rotator cuff related shoulder pain; RCRSP; rotator cuff disease*; rotator cuff disorder*; subacromial pain; subacromial impingement; shoulder impingement; subacromial pain syndrome; supraspinatus tendinopath*; painful arc; rotator cuff tear*; partial thickness tear*; calcific tendin*; frozen shoulder; adhesive capsulitis; shoulder instability; scapular dyskines*; GIRD; glenohumeral internal rotation deficit; overhead athlete*; throwing shoulder.

**Cotovelo, punho e mão.** lateral epicondyl*; tennis elbow; lateral elbow tendinopath*; medial epicondyl*; golfer* elbow; carpal tunnel; de Quervain*; ulnar collateral ligament.

**Quadril e virilha.** femoroacetabular impingement; FAI syndrome; hip-related pain; groin pain; adductor-related; athletic pubalgia; greater trochanteric pain; gluteal tendinopath*; hip osteoarthritis; labral tear*.

**Joelho.** patellofemoral pain; anterior knee pain; chondromalacia; patellar tendinopath*; jumper* knee; anterior cruciate ligament; ACL reconstruction; ACL injur*; meniscal tear*; meniscus; knee osteoarthritis; iliotibial band; total knee arthroplasty; total knee replacement.

**Perna, tornozelo e pé.** Achilles tendinopath*; Achilles tendin*; midportion; insertional; calf strain*; medial tibial stress syndrome; shin splint*; ankle sprain*; lateral ankle sprain*; chronic ankle instability; plantar fasciitis; plantar heel pain; plantar fasciopath*; bone stress injur*; stress fracture*.

**Posterior de coxa e músculo.** hamstring strain*; hamstring injur*; muscle injur*; muscle strain*; Nordic hamstring; proximal hamstring tendinopath*.

**Coluna.** low back pain; non-specific low back pain; nonspecific low back pain; chronic low back pain; lumbar radiculopathy; sciatica; lumbar disc herniation; lumbar spinal stenosis; neck pain; cervical radiculopathy; whiplash; cervicogenic headache; thoracic spine.

**Dor: mecanismos e fatores psicossociais.** central sensiti*; nociplastic; nociceptive; neuropathic; pain sensitiv*; pressure pain threshold*; quantitative sensory testing; conditioned pain modulation; temporal summation; pain catastrophi*; kinesiophobia; fear avoidance; fear of movement; self-efficacy; pain beliefs; illness perception*; placebo; nocebo; contextual factor*; therapeutic alliance; expectation*.

**Exercício e carga.** exercis*; exercise therap*; therapeutic exercise*; resistance training; resistance exercise*; strength training; strengthening; resisted; progressive loading; load management; loading program*; heavy slow resistance; eccentric*; isometric*; isotonic; concentric; plyometric*; neuromuscular training; motor control; stabilization exercise*; stabilisation exercise*; blood flow restriction; dose-response; exercise dos*; training volume; training intensity; repetition maximum; adherence.

**Terapia manual e recursos.** manual therap*; mobilization; mobilisation; manipulation; thrust; soft tissue; massage; dry needling; taping; kinesio tap*; shockwave; shock wave; ESWT; laser therap*; photobiomodulation; ultrasound therap*; TENS; electrical stimulation; NMES; cryotherap*; heat therap*.

**Educação e autogestão.** patient education; pain education; pain neuroscience education; therapeutic neuroscience education; explain pain; self-management; advice; reassurance; shared decision; telerehabilitation; telehealth; digital health; app-based.

**Esporte e retorno.** return to sport*; return to play; return to competition; return to run*; injury prevention; prevention program*; FIFA 11+; workload; training load; acute chronic workload; reinjur*; recurren*; athlete*; handball; volleyball; overhead sport*.

**Cirurgia e alternativas (para comparadores, se entrarem na busca).** surg*; arthroscop*; decompression; acromioplasty; repair; corticosteroid injection*; platelet-rich plasma; PRP; wait and see; usual care; sham; placebo surgery.

O PubMed não tem curinga de um caractere (`?`): escreva as duas grafias, como acima. No Scopus `?` funciona.

## 5. Instrumentos e desfechos (siglas)

Desfecho quase nunca entra como bloco (ver `estrategia-de-busca.md`), mas as siglas servem para reconhecer artigos na triagem e para buscas específicas de propriedades de medida.

| Região ou construto | Instrumentos |
|---|---|
| Ombro | SPADI (Shoulder Pain and Disability Index); DASH e QuickDASH (Disabilities of the Arm, Shoulder and Hand); WORC (Western Ontario Rotator Cuff Index); Constant-Murley; ASES; Penn Shoulder Score; KJOC (atletas de arremesso) |
| Cotovelo | PRTEE (Patient-Rated Tennis Elbow Evaluation) |
| Quadril e virilha | HAGOS (Copenhagen Hip and Groin Outcome Score); iHOT-33 e iHOT-12; HOOS; VISA-G |
| Joelho | KOOS; IKDC; Lysholm; Tegner; ACL-RSI; Kujala ou AKPS (dor patelofemoral); VISA-P; WOMAC |
| Tornozelo e pé | FAAM; FAOS; CAIT (Cumberland Ankle Instability Tool); VISA-A; LEFS (membro inferior em geral) |
| Coluna | ODI (Oswestry); RMDQ (Roland-Morris); NDI (Neck Disability Index); STarT Back; Örebro |
| Dor | NPRS; VAS; BPI (Brief Pain Inventory); PPT (limiar de dor à pressão); CPM; soma temporal |
| Psicossocial | TSK (Tampa Scale of Kinesiophobia); FABQ; PCS (Pain Catastrophizing Scale); PSEQ; CSI (Central Sensitization Inventory) |
| Função e mudança | PSFS (Patient-Specific Functional Scale); GROC ou GRoC (Global Rating of Change); MCID ou MIC; PASS; SF-36; EQ-5D |
| Desempenho | hop tests; Y-Balance ou SEBT; LSI (limb symmetry index); dinamometria isocinética e manual; 1RM; CKCUEST (membro superior) |

No MeSH, os conceitos correspondentes são gerais: Disability Evaluation, Pain Measurement, Patient Reported Outcome Measures (2017), Surveys and Questionnaires, Psychometrics, Reproducibility of Results, Minimal Clinically Important Difference (2017).

## 6. Revistas-alvo com ISSN

Conferidas no NLM Catalog (tipo do ISSN e situação de indexação) e na Crossref (se o ISSN resolve em `/journals/{issn}`). A mesma lista está em `assets/revistas_alvo.json`, pronta para copiar para `revistas_alvo` de `conceitos.json`.

Três coisas que esta tabela ensina:

- Na Crossref, várias revistas da Elsevier só respondem pelo ISSN impresso. Passe sempre os dois ISSN; o script usa os que funcionarem.
- A Crossref às vezes rotula o tipo do ISSN ao contrário do NLM (por exemplo Braz J Phys Ther e Musculoskelet Sci Pract). O tipo desta tabela é o do NLM.
- Revista fora do MEDLINE (IJSPT, Orthop J Sports Med, BMJ Open Sport Exerc Med, JOSPT Cases) pode estar no PubMed via PMC, mas o registro vem **sem MeSH**. Só texto livre alcança esses artigos; é o caso do ensaio de Ingwersen 2017 no exemplo trabalhado.

| Abreviatura (use em `[jour]`) | ISSN impresso | ISSN eletrônico | MEDLINE hoje | Resolve na Crossref |
|---|---|---|---|---|
| J Orthop Sports Phys Ther | 0190-6011 | 1938-1344 | sim | 0190-6011, 1938-1344 |
| JOSPT Open | - | 2832-8280 | sim | 2832-8280 |
| JOSPT Cases | 2767-293X | 2767-2921 | não (sem MeSH) | 2767-2921 |
| Br J Sports Med | 0306-3674 | 1473-0480 | sim | 0306-3674, 1473-0480 |
| Phys Ther | 0031-9023 | 1538-6724 | sim | 0031-9023, 1538-6724 |
| J Physiother | 1836-9553 | 1836-9561 | sim | 1836-9553 |
| Braz J Phys Ther | 1413-3555 | 1809-9246 | sim | 1413-3555, 1809-9246 |
| Musculoskelet Sci Pract | 2468-8630 | 2468-7812 | sim | 2468-7812 |
| Phys Ther Sport | 1466-853X | 1873-1600 | sim | 1466-853X |
| Physiotherapy | 0031-9406 | 1873-1465 | sim | 0031-9406 |
| Physiother Theory Pract | 0959-3985 | 1532-5040 | sim | 0959-3985, 1532-5040 |
| J Man Manip Ther | 1066-9817 | 2042-6186 | sim | 1066-9817, 2042-6186 |
| Int J Sports Phys Ther | - | 2159-2896 | não (sem MeSH) | 2159-2896 |
| Arch Phys Med Rehabil | 0003-9993 | 1532-821X | sim | 0003-9993 |
| Clin Rehabil | 0269-2155 | 1477-0873 | sim | 0269-2155, 1477-0873 |
| Am J Phys Med Rehabil | 0894-9115 | 1537-7385 | sim | 0894-9115, 1537-7385 |
| Disabil Rehabil | 0963-8288 | 1464-5165 | sim | 0963-8288, 1464-5165 |
| J Rehabil Med | 1650-1977 | 1651-2081 | sim | 1650-1977, 1651-2081 |
| Eur J Phys Rehabil Med | 1973-9087 | 1973-9095 | sim | 1973-9087, 1973-9095 |
| Ann Phys Rehabil Med | 1877-0657 | 1877-0665 | sim | 1877-0657 |
| Am J Sports Med | 0363-5465 | 1552-3365 | sim | 0363-5465, 1552-3365 |
| Sports Med | 0112-1642 | 1179-2035 | sim | 0112-1642, 1179-2035 |
| Med Sci Sports Exerc | 0195-9131 | 1530-0315 | sim | 0195-9131, 1530-0315 |
| Scand J Med Sci Sports | 0905-7188 | 1600-0838 | sim | 0905-7188, 1600-0838 |
| J Sci Med Sport | 1440-2440 | 1878-1861 | sim | 1440-2440 |
| J Athl Train | 1062-6050 | 1938-162X | sim | 1062-6050, 1938-162X |
| Sports Health | 1941-7381 | 1941-0921 | sim | 1941-7381, 1941-0921 |
| Orthop J Sports Med | - | 2325-9671 | não (sem MeSH) | 2325-9671 |
| BMJ Open Sport Exerc Med | - | 2055-7647 | não (sem MeSH) | 2055-7647 |
| Clin J Sport Med | 1050-642X | 1536-3724 | sim | 1050-642X, 1536-3724 |
| Int J Sports Med | 0172-4622 | 1439-3964 | sim | 0172-4622, 1439-3964 |
| J Strength Cond Res | 1064-8011 | 1533-4287 | sim | 1064-8011, 1533-4287 |
| Knee Surg Sports Traumatol Arthrosc | 0942-2056 | 1433-7347 | sim | 0942-2056, 1433-7347 |
| J Shoulder Elbow Surg | 1058-2746 | 1532-6500 | sim | 1058-2746 |
| Arthroscopy | 0749-8063 | 1526-3231 | sim | 0749-8063, 1526-3231 |
| J Bone Joint Surg Am | 0021-9355 | 1535-1386 | sim | 0021-9355, 1535-1386 |
| Bone Joint J | 2049-4394 | 2049-4408 | sim | 2049-4394, 2049-4408 |
| Osteoarthritis Cartilage | 1063-4584 | 1522-9653 | sim | 1063-4584, 1522-9653 |
| Ann Rheum Dis | 0003-4967 | 1468-2060 | sim | 0003-4967, 1468-2060 |
| Arthritis Care Res (Hoboken) | 2151-464X | 2151-4658 | sim | 2151-464X, 2151-4658 |
| BMC Musculoskelet Disord | - | 1471-2474 | sim | 1471-2474 |
| Pain | 0304-3959 | 1872-6623 | sim | 0304-3959, 1872-6623 |
| J Pain | 1526-5900 | 1528-8447 | sim | 1526-5900 |
| Eur J Pain | 1090-3801 | 1532-2149 | sim | 1090-3801, 1532-2149 |
| Clin J Pain | 0749-8047 | 1536-5409 | sim | 0749-8047, 1536-5409 |
| Pain Med | 1526-2375 | 1526-4637 | sim | 1526-2375, 1526-4637 |
| Spine (Phila Pa 1976) | 0362-2436 | 1528-1159 | sim | 0362-2436, 1528-1159 |
| Spine J | 1529-9430 | 1878-1632 | sim | 1529-9430 |
| Eur Spine J | 0940-6719 | 1432-0932 | sim | 0940-6719, 1432-0932 |
| J Electromyogr Kinesiol | 1050-6411 | 1873-5711 | sim | 1050-6411 |
| Clin Biomech (Bristol) | 0268-0033 | 1879-1271 | sim | 0268-0033 |
| J Biomech | 0021-9290 | 1873-2380 | sim | 0021-9290 |
| Gait Posture | 0966-6362 | 1879-2219 | sim | 0966-6362 |
| J Appl Physiol (1985) | 8750-7587 | 1522-1601 | sim | 8750-7587, 1522-1601 |
| Eur J Appl Physiol | 1439-6319 | 1439-6327 | sim | 1439-6319, 1439-6327 |
| J Hand Ther | 0894-1130 | 1545-004X | sim | 0894-1130 |
| Cochrane Database Syst Rev | - | 1469-493X | sim | 1469-493X |
| BMJ | 0959-8138 | 1756-1833 | sim | 0959-8138, 1756-1833 |
| JAMA | 0098-7484 | 1538-3598 | sim | 0098-7484, 1538-3598 |
| Lancet | 0140-6736 | 1474-547X | sim | 0140-6736, 1474-547X |
| N Engl J Med | 0028-4793 | 1533-4406 | sim | 0028-4793, 1533-4406 |

JOSPT: prefixo DOI 10.2519. O site (www.jospt.org) bloqueia acesso automatizado; a busca entra por PubMed (`"J Orthop Sports Phys Ther"[jour]` ou `"0190-6011"[jour]`) e pela Crossref.

## 7. Como reconferir

```bash
# descritores de um conceitos.json (pára com código 1 se algum não existir)
python3 scripts/montar_strings.py aulas/<aula>/01_busca/conceitos.json --verificar-mesh

# quanto cada termo recupera (zero = erro de grafia ou descritor inexistente)
python3 scripts/pubmed_busca.py --conceitos aulas/<aula>/01_busca/conceitos.json --diagnostico
```

ISSN de uma revista nova: procure a abreviatura no NLM Catalog (https://www.ncbi.nlm.nih.gov/nlmcatalog) e confira em `https://api.crossref.org/journals/<issn>`. Não copie ISSN de memória nem de site de terceiros.
