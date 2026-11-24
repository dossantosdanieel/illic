#!/usr/bin/env python3
"""Renderiza o .pptx em PDF, PNGs por slide e folhas de contato, para o modelo OLHAR o resultado.

Uso:
    python renderizar.py aulas/2026-11-lca/04_aula/lca.pptx
    python renderizar.py lca.pptx --saida previa --dpi 110 --colunas 4

Gera em <saida>/ (padrao: pasta 'previa' ao lado do .pptx):
    <nome>.pdf, s-01.png ... s-NN.png, folha-1.png, folha-2.png ...
Precisa do LibreOffice (soffice) e do pdftoppm (poppler). Sem a fonte Lato instalada,
o render usa uma fonte parecida: a diagramacao confere, o desenho das letras nao.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def achar(*nomes: str) -> str | None:
    for n in nomes:
        p = shutil.which(n)
        if p:
            return p
    for p in ("/Applications/LibreOffice.app/Contents/MacOS/soffice",
              "C:/Program Files/LibreOffice/program/soffice.exe"):
        if Path(p).exists() and any("office" in n for n in nomes):
            return p
    return None


def para_pdf(pptx: Path, destino: Path, tempo: int) -> Path:
    soffice = achar("soffice", "libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) não encontrado. Instale-o ou abra o .pptx no PowerPoint e exporte "
                           "em PDF; depois rode: pdftoppm -r 110 -png arquivo.pdf previa/s")
    with tempfile.TemporaryDirectory(prefix="lo_perfil_") as perfil:
        cmd = [soffice, f"-env:UserInstallation=file://{perfil}", "--headless", "--convert-to", "pdf",
               "--outdir", str(destino), str(pptx)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=tempo)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"o LibreOffice não terminou em {tempo} s. Tente de novo ou aumente --tempo.")
    pdf = destino / (pptx.stem + ".pdf")
    if not pdf.is_file():
        raise RuntimeError("o LibreOffice não gerou o PDF.\n" + (r.stderr or r.stdout)[-800:])
    return pdf


def para_png(pdf: Path, destino: Path, dpi: int) -> list[Path]:
    for velho in destino.glob("s-*.png"):
        velho.unlink()
    pdftoppm = achar("pdftoppm")
    if pdftoppm:
        r = subprocess.run([pdftoppm, "-r", str(dpi), "-png", str(pdf), str(destino / "s")],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError("pdftoppm falhou: " + r.stderr[-500:])
    else:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            raise RuntimeError("nem pdftoppm nem pypdfium2 disponíveis para converter o PDF em imagens.")
        doc = pdfium.PdfDocument(str(pdf))
        for i in range(len(doc)):
            doc[i].render(scale=dpi / 72).to_pil().save(destino / f"s-{i + 1}.png")
    pngs = sorted(destino.glob("s-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    largura = max(2, len(str(len(pngs))))
    saida = []
    for p in pngs:  # normaliza para s-01.png, s-02.png ...
        n = int(p.stem.split("-")[-1])
        novo = destino / f"s-{n:0{largura}d}.png"
        if novo != p:
            p.rename(novo)
        saida.append(novo)
    return saida


def folhas(pngs: list[Path], destino: Path, colunas: int, por_folha: int, largura_mini: int) -> list[Path]:
    from PIL import Image, ImageDraw, ImageFont
    for velho in destino.glob("folha-*.png"):
        velho.unlink()
    try:
        fonte = ImageFont.load_default(size=20)
    except TypeError:  # Pillow antigo
        fonte = ImageFont.load_default()
    saida = []
    margem, rot = 14, 26
    for f, ini in enumerate(range(0, len(pngs), por_folha), 1):
        lote = pngs[ini:ini + por_folha]
        minis = []
        for p in lote:
            im = Image.open(p).convert("RGB")
            h = round(im.height * largura_mini / im.width)
            minis.append(im.resize((largura_mini, h), Image.LANCZOS))
        hm = max(m.height for m in minis)
        linhas = (len(minis) + colunas - 1) // colunas
        W = colunas * largura_mini + (colunas + 1) * margem
        H = linhas * (hm + rot) + (linhas + 1) * margem
        folha = Image.new("RGB", (W, H), (120, 126, 130))
        d = ImageDraw.Draw(folha)
        for i, m in enumerate(minis):
            x = margem + (i % colunas) * (largura_mini + margem)
            y = margem + (i // colunas) * (hm + rot + margem)
            d.text((x + 2, y), f"slide {ini + i + 1}", fill=(255, 255, 255), font=fonte)
            folha.paste(m, (x, y + rot))
        cam = destino / f"folha-{f}.png"
        folha.save(cam)
        saida.append(cam)
    return saida


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Renderiza o .pptx em PDF, PNGs e folhas de contato.")
    ap.add_argument("pptx")
    ap.add_argument("--saida", help="pasta de saída (padrão: 'previa' ao lado do .pptx)")
    ap.add_argument("--dpi", type=int, default=110, help="resolução dos PNGs (padrão 110: 1467 px de largura)")
    ap.add_argument("--colunas", type=int, default=4, help="colunas da folha de contato")
    ap.add_argument("--por-folha", type=int, default=12, help="slides por folha de contato")
    ap.add_argument("--largura-mini", type=int, default=640, help="largura de cada miniatura na folha, em px")
    ap.add_argument("--tempo", type=int, default=240, help="limite de tempo do LibreOffice, em segundos")
    a = ap.parse_args(argv)

    pptx = Path(a.pptx).expanduser().resolve()
    if not pptx.is_file():
        print(f"ERRO: arquivo não encontrado: {pptx}", file=sys.stderr)
        return 2
    destino = Path(a.saida).expanduser().resolve() if a.saida else pptx.parent / "previa"
    destino.mkdir(parents=True, exist_ok=True)
    try:
        pdf = para_pdf(pptx, destino, a.tempo)
        pngs = para_png(pdf, destino, a.dpi)
        fls = folhas(pngs, destino, a.colunas, a.por_folha, a.largura_mini)
    except RuntimeError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    print(f"PDF: {pdf}")
    print(f"Slides renderizados: {len(pngs)} ({pngs[0].name} … {pngs[-1].name}) em {destino}")
    for f in fls:
        print(f"Folha de contato: {f}")
    print("Agora OLHE: primeiro as folhas (ritmo, alternância claro/escuro, slides carregados), depois cada "
          "slide em tamanho cheio (texto cortado, sobreposição, figura ilegível, destaque fora do lugar).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
