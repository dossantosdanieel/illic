#!/usr/bin/env python3
"""Extrai o texto de cada PDF, página por página, em 02_artigos/texto/<chave>.md.

Lê em ordem de leitura mesmo em duas colunas, tira cabeçalhos e rodapés repetidos,
desfaz a hifenização de fim de linha, marca onde começam Métodos, Resultados e
Discussão quando há um título reconhecível e lista no topo as legendas de figuras e
tabelas com a página (é o mapa para a leitura crítica e para o recorte).

Uso:
  python3 extrair_texto.py AULA
  python3 extrair_texto.py AULA --apenas Breda2021 --refazer
  python3 extrair_texto.py --pdf artigo.pdf --saida artigo.md     # um PDF avulso
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402
import _pdf as P  # noqa: E402


def log(msg: str) -> None:
    print(msg, flush=True)


def extrair(pdf: Path, titulo: str, cabecalho: list[str]) -> tuple[str, dict]:
    doc = P.DocLayout(pdf)
    corpo: list[str] = []
    secoes: list[tuple[str, int, str]] = []
    n_car = 0
    for pag in doc.paginas:
        corpo += ["", f"## Página {pag.numero}", ""]
        itens = P.texto_ordenado(doc, pag)
        if not itens:
            corpo.append("_(página sem texto extraível: provavelmente só imagem)_")
            continue
        if pag.frac_girado > 0.5:
            corpo.append("_(página com conteúdo girado, em geral tabela em paisagem: o texto abaixo pode vir "
                         "incompleto; confira na miniatura)_")
            corpo.append("")
        for it in itens:
            t = it["texto"].strip()
            if not t:
                continue
            n_car += len(t)
            if it["tipo"] == "secao":
                secoes.append((it["secao"], pag.numero, t))
                corpo += [f"### [{it['secao']}] {t}", ""]
            elif it["tipo"] == "legenda":
                corpo += [f"> **Legenda:** {t}", ""]
            elif it["tipo"] == "linha":
                corpo.append(t + "  ")
            else:
                corpo += [t, ""]
    legendas = doc.legendas
    topo = [f"# {titulo}", ""] + cabecalho + [""]
    topo += ["## Mapa do artigo", ""]
    topo.append(f"- Páginas: {len(doc.paginas)} · layout: {'duas colunas' if doc.duas_colunas else 'coluna única'}")
    if secoes:
        partes = []
        for nome, pg, _ in secoes:
            partes.append(f"{nome.capitalize()} p.{pg}")
        topo.append("- Seções encontradas (em ordem; títulos dentro do resumo também aparecem): " + " · ".join(partes))
    else:
        topo.append("- Seções: nenhum título de seção reconhecido (artigo sem estrutura IMRaD ou títulos fora do padrão).")
    if legendas:
        topo.append("- Legendas de figuras e tabelas:")
        for l in legendas:
            resumo = l.texto if len(l.texto) <= 220 else l.texto[:217].rstrip() + "..."
            cont = " (continuação)" if l.continuacao else ""
            topo.append(f"  - p.{l.pagina} — {l.rotulo}{cont}: {resumo}")
    else:
        topo.append("- Legendas de figuras e tabelas: nenhuma encontrada pelo texto.")
    avisos = list(doc.avisos)
    if n_car < 1500:
        avisos.append("quase nenhum texto extraído: o PDF parece digitalizado (sem camada de texto). "
                      "Leia pelas miniaturas das páginas.")
    for a in avisos:
        topo.append(f"- Aviso: {a}")
    info = {"paginas": len(doc.paginas), "caracteres": n_car, "duas_colunas": doc.duas_colunas,
            "secoes": [s[0] for s in secoes], "legendas": len(legendas), "avisos": avisos}
    return "\n".join(topo + corpo).rstrip() + "\n", info


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Extrai o texto dos PDFs por página, com mapa de seções e de legendas.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", nargs="?", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--apenas", nargs="+", metavar="CHAVE", help="processa só estas chaves")
    ap.add_argument("--refazer", action="store_true", help="extrai de novo mesmo que o .md já exista")
    ap.add_argument("--pdf", help="extrai um PDF avulso (fora do contrato de pastas)")
    ap.add_argument("--saida", help="arquivo .md de saída para --pdf (padrão: ao lado do PDF)")
    args = ap.parse_args()

    if args.pdf:
        pdf = Path(args.pdf)
        ok, motivo, _ = C.validar_pdf(pdf, 1000)
        if not ok:
            C.sair(f"{pdf}: {motivo}")
        md, info = extrair(pdf, pdf.stem, [f"Arquivo: `{pdf.name}`"])
        saida = Path(args.saida) if args.saida else pdf.with_suffix(".md")
        saida.write_text(md, encoding="utf-8")
        log(f"{saida}: {info['paginas']} pág., {info['caracteres']} caracteres, {info['legendas']} legendas")
        return 0
    if not args.aula:
        ap.error("informe a pasta da aula ou --pdf")

    aula = C.Aula(args.aula)
    aula.exigir()
    aula.criar_pastas()
    manifest = C.carregar_manifest(aula)
    try:
        registros, _ = C.carregar_registros(aula)
    except SystemExit:
        registros = []
    por_chave = {r["chave"]: r for r in registros}
    pdfs = sorted(aula.pdf.glob("*.pdf"))
    if args.apenas:
        pdfs = [p for p in pdfs if p.stem in set(args.apenas)]
    if not pdfs:
        log(f"Nenhum PDF em {aula.pdf}. Rode antes baixar_artigos.py e incorporar_manuais.py.")
        return 0
    feitos = pulados = falhas = 0
    for pdf in pdfs:
        chave = pdf.stem
        destino = aula.texto / f"{chave}.md"
        if destino.exists() and not args.refazer and destino.stat().st_mtime >= pdf.stat().st_mtime:
            pulados += 1
            continue
        ok, motivo, _ = C.validar_pdf(pdf, 1000)
        if not ok:
            log(f"  falhou  {chave}: {motivo}")
            falhas += 1
            continue
        reg = por_chave.get(chave, {"chave": chave})
        ent = manifest.get(chave, {})
        cab = [f"- Citação: {C.citacao_curta(reg, ent)}" if reg.get("autores") or reg.get("primeiro_autor") else None,
               f"- DOI: {reg['doi']}" if reg.get("doi") else None,
               f"- PDF: `02_artigos/pdf/{chave}.pdf` · origem {ent.get('origem') or '?'} · licença {ent.get('licenca') or '?'}",
               f"- Extraído em {C.agora()[:16].replace('T', ' ')} por extrair_texto.py. Citações textuais devem "
               "indicar a página deste arquivo."]
        try:
            md, info = extrair(pdf, f"{chave} — {reg.get('titulo') or '(título não informado)'}", [c for c in cab if c])
        except Exception as e:
            log(f"  falhou  {chave}: {type(e).__name__}: {e}")
            falhas += 1
            continue
        destino.write_text(md, encoding="utf-8")
        if chave in manifest:
            manifest[chave]["texto"] = f"texto/{chave}.md"
            manifest[chave]["texto_caracteres"] = info["caracteres"]
            C.salvar_manifest(aula, manifest)
        feitos += 1
        sec = ", ".join(dict.fromkeys(s.capitalize() for s in info["secoes"])) or "nenhuma seção reconhecida"
        log(f"  ok      {chave}: {info['paginas']} pág., {info['caracteres']} caracteres, "
            f"{'2 colunas' if info['duas_colunas'] else '1 coluna'}, {info['legendas']} legendas; {sec}")
        for a in info["avisos"]:
            log(f"          aviso: {a}")
    log("")
    log(f"Resumo: {feitos} extraído(s), {pulados} já em dia, {falhas} com falha. Saída em {aula.texto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
