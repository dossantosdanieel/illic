#!/usr/bin/env python3
"""Confere o .pptx montado por dentro, antes de entregar.

Uso:
    python conferir_pptx.py aulas/<aula>/04_aula/deck.json aulas/<aula>/04_aula/<slug>.pptx

O que confere:
- toda nota de slide cronometrado começa com "Tempo: X (acumulado M:SS)." e o acumulado bate com o deck.json;
- slides de apoio (referências) têm nota;
- gráficos são nativos (parte de gráfico com planilha embutida, editável no PowerPoint);
- nenhuma forma sai da página;
- a estrutura do pacote: toda relação aponta para uma parte que existe, toda parte tem tipo de conteúdo
  e não há id de forma repetido no mesmo slide;
- se houver esquemas XSD do OOXML no ambiente (variável BOOST_OOXML_XSD com a pasta que tem pml.xsd e
  dml-chart.xsd), valida slides, notas e gráficos contra eles. O PowerPoint é mais rígido que o
  LibreOffice: um arquivo que abre no LibreOffice pode pedir "reparo" no PowerPoint.

Saída 1 se algo falhar.
"""
from __future__ import annotations

import argparse
import os
import posixpath
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _marca as M  # noqa: E402

PASTAS_XSD = [
    os.environ.get("BOOST_OOXML_XSD", ""),
    "/mnt/skills/public/pptx/scripts/office/schemas/ISO-IEC29500-4_2016",
]


def achar_xsd() -> Path | None:
    for p in PASTAS_XSD:
        if p and (Path(p) / "pml.xsd").is_file() and (Path(p) / "dml-chart.xsd").is_file():
            return Path(p)
    return None


def conferir_pacote(arq: Path, problemas: list[str]) -> str:
    z = zipfile.ZipFile(arq)
    nomes = set(z.namelist())
    ct = z.read("[Content_Types].xml").decode("utf-8")
    for n in sorted(nomes):
        if n.endswith("/"):
            continue
        ext = n.rsplit(".", 1)[-1]
        if f'Extension="{ext}"' not in ct and f'PartName="/{n}"' not in ct:
            problemas.append(f"parte sem tipo de conteúdo: {n}")
        if n.endswith(".rels"):
            base = posixpath.dirname(posixpath.dirname(n))
            for alvo, modo in re.findall(rb'Target="([^"]+)"(?:\s+TargetMode="([^"]+)")?', z.read(n)):
                if modo == b"External":
                    continue
                cam = posixpath.normpath(posixpath.join(base, alvo.decode()))
                if cam.lstrip("/") not in nomes:
                    problemas.append(f"relação quebrada em {n}: {cam}")
        if re.match(r"ppt/slides/slide\d+\.xml$", n):
            ids = re.findall(rb'<p:cNvPr id="(\d+)"', z.read(n))
            if len(ids) != len(set(ids)):
                problemas.append(f"id de forma repetido em {n}")
    pasta = achar_xsd()
    if pasta is None:
        return "validação XSD não feita (esquemas OOXML não encontrados; defina BOOST_OOXML_XSD)"
    from lxml import etree
    esquemas = {nome: etree.XMLSchema(etree.parse(str(pasta / nome))) for nome in ("pml.xsd", "dml-chart.xsd")}
    alvos = [(r"ppt/slides/slide\d+\.xml$", "pml.xsd"), (r"ppt/notesSlides/notesSlide\d+\.xml$", "pml.xsd"),
             (r"ppt/presentation\.xml$", "pml.xsd"), (r"ppt/charts/chart\d+\.xml$", "dml-chart.xsd")]
    n_ok = 0
    for n in sorted(nomes):
        for pad, nome in alvos:
            if re.search(pad, n):
                esq = esquemas[nome]
                if esq.validate(etree.fromstring(z.read(n))):
                    n_ok += 1
                else:
                    for e in list(esq.error_log)[:3]:
                        problemas.append(f"XML fora do esquema em {n} (linha {e.line}): {e.message}")
    return f"validação XSD: {n_ok} parte(s) conferidas contra {pasta}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Confere notas, gráficos nativos e estrutura do .pptx da aula.")
    ap.add_argument("deck", help="deck.json usado na montagem")
    ap.add_argument("pptx", help="arquivo .pptx montado")
    a = ap.parse_args(argv)
    try:
        from pptx import Presentation
    except ImportError:
        M.sair("falta a biblioteca python-pptx (pip install python-pptx).")
    deck = M.carregar_json(Path(a.deck))
    prs = Presentation(a.pptx)
    W, H = prs.slide_width, prs.slide_height
    problemas: list[str] = []

    esperado: list[str | None] = []
    acum = 0
    for s in M.como_lista(deck.get("slides")):
        if not isinstance(s, dict) or s.get("tipo") not in M.TIPOS:
            continue
        if s.get("apoio") or s.get("tipo") == "referencias" or not int(s.get("tempo_s") or 0):
            esperado.append(None)
        else:
            acum += int(s["tempo_s"])
            esperado.append(f"Tempo: {M.tempo_extenso(int(s['tempo_s']))} (acumulado {M.relogio(acum)}).")
    slides = list(prs.slides)
    # o slide de referências pode virar vários: os extras são apoio
    esperado += [None] * max(0, len(slides) - len(esperado))
    n_graf = 0
    print("== Conferência do .pptx ==")
    for i, sl in enumerate(slides, 1):
        nota = sl.notes_slide.notes_text_frame.text.strip() if sl.has_notes_slide else ""
        exp = esperado[i - 1]
        if exp and not nota.startswith(exp):
            problemas.append(f"slide {i}: a nota deveria começar com \"{exp}\" e começa com \"{nota[:50]}\".")
        if not nota:
            problemas.append(f"slide {i}: sem notas do apresentador.")
        for sh in sl.shapes:
            if sh.left < -9525 or sh.top < -9525 or sh.left + sh.width > W + 9525 or sh.top + sh.height > H + 9525:
                problemas.append(f"slide {i}: a forma \"{sh.name}\" sai da página.")
            if sh.has_chart:
                n_graf += 1
                parte = sh.chart.part
                tem_planilha = any("embeddings" in str(r.target_ref) for r in parte.rels.values())
                if not tem_planilha:
                    problemas.append(f"slide {i}: gráfico sem planilha embutida (não será editável).")
    print(f"Slides: {len(slides)} | notas conferidas: {sum(1 for e in esperado if e)} cronometradas | "
          f"gráficos nativos: {n_graf} | duração no deck.json: {M.relogio(acum)}")
    print(conferir_pacote(Path(a.pptx), problemas))
    if problemas:
        print(f"\nPROBLEMAS ({len(problemas)}):")
        for p in problemas:
            print(f"  ✗ {p}")
        return 1
    print("Nenhum problema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
