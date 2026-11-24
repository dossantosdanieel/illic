# Pendências da busca · cotovelo lateral (aulas 1 e 2)

Atualizado em 24/11/2026.

## 1. Exportação do Scopus (com o Daniel)

O Scopus só é acessível pelo site. A string `base` está pronta em `estrategia.md` (seção Scopus), com as instruções de
exportação. Quando o arquivo chegar, salvar como `01_busca/brutos/scopus.csv` e rodar:

```bash
python3 .claude/skills/boost-pesquisa-artigos/scripts/importar_scopus.py --pasta aulas/2026-11-cotovelo-lateral-1-diagnostico/01_busca
python3 .claude/skills/boost-pesquisa-artigos/scripts/consolidar.py --pasta aulas/2026-11-cotovelo-lateral-1-diagnostico/01_busca --lote 60
```

Até lá, a busca está fechada com PubMed + Crossref + OpenAlex, sem o Scopus.

## 2. PDFs do JOSPT fora do PMC (download manual, com a assinatura do Daniel)

O site do JOSPT bloqueia robôs. Artigos do JOSPT selecionados que não estão no PMC entram aqui para o Daniel baixar e
salvar em `02_artigos/manual/` (lista completa e conferida em `selecionados.json`, campo `acesso_aberto`):

- `Rio2021` · Sensory Processing in People With and Without Tendinopathy: A Systematic Review With Meta-analysis of Local, Regional, and Remote Sites in Upper- and Lower-Limb Conditions · J Orthop Sports Phys Ther 2021 · PMID 33383996 · DOI 10.2519/jospt.2021.9417
- `Coombes2015b` · Management of Lateral Elbow Tendinopathy: One Size Does Not Fit All · J Orthop Sports Phys Ther 2015 · PMID 26381484 · DOI 10.2519/jospt.2015.5841
- `Lucado2022` · Lateral Elbow Pain and Muscle Function Impairments · J Orthop Sports Phys Ther 2022 · PMID 36453071 · DOI 10.2519/jospt.2022.0302

## 3. Outros selecionados sem acesso aberto conhecido (OpenAlex)

Para a etapa de leitura: tentar PMC/Europe PMC/Unpaywall; se não houver, acesso institucional do Daniel.

- `Karanasios2022` · J Hand Ther 2022 · PMID 33814224 · DOI 10.1016/j.jht.2021.02.002
- `Karanasios2021` · Br J Sports Med 2021 · PMID 33148599 · DOI 10.1136/bjsports-2020-102525
- `Karanasios2021b` · Clin Rehabil 2021 · PMID 33813913 · DOI 10.1177/02692155211006860
- `Lucado2019` · J Hand Ther 2019 · PMID 29705077 · DOI 10.1016/j.jht.2018.01.010
- `Ma2024` · Arch Phys Med Rehabil 2024 · PMID 38484834 · DOI 10.1016/j.apmr.2024.02.713
- `Vuvan2020` · Med Sci Sports Exerc 2020 · PMID 31425384 · DOI 10.1249/mss.0000000000002128
- `Shahabi2020` · Prosthet Orthot Int 2020 · PMID 32635812 · DOI 10.1177/0309364620930618
- `Couppe2022` · Am J Sports Med 2022 · PMID 35867777 · DOI 10.1177/03635465221110214
- `Coombes2013` · JAMA 2013 · PMID 23385272 · DOI 10.1001/jama.2013.129
- `Expert2022` · J Am Coll Radiol 2022 · PMID 36436956 · DOI 10.1016/j.jacr.2022.09.022
- `Coombes2015` · Clin J Pain 2015 · PMID 24480912 · DOI 10.1097/ajp.0000000000000078
- `Waugh2004` · Arch Phys Med Rehabil 2004 · PMID 14966719 · DOI 10.1016/s0003-9993(03)00480-5
- `Krogh2020` · Am J Sports Med 2020 · PMID 32484714 · DOI 10.1177/0363546520921949
- `Bunata2007` · J Bone Joint Surg Am 2007 · PMID 17768192 · DOI 10.2106/jbjs.f.00727
- `Vicenzino2009` · Man Ther 2009 · PMID 18838330 · DOI 10.1016/j.math.2008.08.004
