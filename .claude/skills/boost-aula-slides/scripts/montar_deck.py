#!/usr/bin/env python3
"""Monta o .pptx da aula a partir do deck.json, na marca Boost Education.

Uso:
    python montar_deck.py aulas/2026-11-lca/04_aula/deck.json
    python montar_deck.py deck.json -o saida.pptx --estrito

O esquema do deck.json esta em references/deck-json.md. O script valida a aula
(validar_aula.py), monta os slides, escreve as notas do apresentador com o tempo
acumulado e avisa quando um texto precisou ser reduzido ou nao coube.
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _marca as M  # noqa: E402

try:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_MARK, XL_MARKER_STYLE
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Inches, Pt
    from lxml import etree
except ImportError as e:  # pragma: no cover
    print(f"ERRO: falta a biblioteca python-pptx ({e}). Instale com: pip install python-pptx pillow", file=sys.stderr)
    raise SystemExit(2)

C = M.COR
ALIN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
ANC = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def rgb(nome_ou_hex: str) -> RGBColor:
    return RGBColor.from_string(C.get(nome_ou_hex, nome_ou_hex).upper())


def par(texto, pt, cor="texto", ls=None, neg=False, alin="l", spc=0, cor_neg=None, antes=0.0, alta=False):
    """Um paragrafo: texto com **negrito**, tamanho em pt, entrelinha exata em pt, espaco antes em pt."""
    texto = "" if texto is None else str(texto)
    if alta:
        texto = texto.upper()
    return {"texto": texto, "pt": float(pt), "cor": cor, "ls": float(ls if ls else round(pt * 1.4, 1)),
            "neg": neg, "alin": alin, "spc": spc, "cor_neg": cor_neg, "antes": float(antes)}


def olho_par(texto, cor="petroleo"):
    return par(texto, 12, cor, ls=14.4, neg=True, spc=1.5, alta=True)


class Construtor:
    def __init__(self, deck: dict, base: Path):
        self.deck = deck
        self.base = base
        self.meta = deck.get("meta") or {}
        self.refs = M.indice_referencias(deck)
        self.catalogo, self.pasta_cat = M.carregar_catalogo(deck, base)
        self.med = M.Medidor()
        self.prs = Presentation()
        self.prs.slide_width = Inches(M.LARGURA)
        self.prs.slide_height = Inches(M.ALTURA)
        self.branco = self.prs.slide_layouts[6]
        self.seco = False
        self.avisos: list[tuple[int, str, str]] = []   # (n do slide no json, nivel, mensagem)
        self.n_atual = 0
        self.acumulado = 0
        self.n_slides_pptx = 0

    # ------------------------------------------------------------------ infraestrutura
    def aviso(self, msg: str, nivel: str = "aviso") -> None:
        if not self.seco:
            self.avisos.append((self.n_atual, nivel, msg))

    def novo_slide(self, escuro: bool = False):
        sl = self.prs.slides.add_slide(self.branco)
        f = sl.background.fill
        f.solid()
        f.fore_color.rgb = rgb("marinho" if escuro else "fundo")
        self.n_slides_pptx += 1
        return sl

    def h_pars(self, pars: list[dict], w: float) -> float:
        total = 0.0
        for i, p in enumerate(pars):
            n = self.med.n_linhas(p["texto"], p["pt"], w, p["neg"], p["spc"])
            total += max(n, 1) * p["ls"] / 72.0
            if i:
                total += p["antes"] / 72.0
        return total

    def n_linhas(self, p: dict, w: float) -> int:
        return max(1, self.med.n_linhas(p["texto"], p["pt"], w, p["neg"], p["spc"]))

    @staticmethod
    def _limpar_estilo(shape) -> None:
        st = shape._element.find(qn("p:style"))
        if st is not None:
            shape._element.remove(st)

    def caixa(self, sl, x, y, w, h, pars=None, fill=None, borda=None, ins=(0, 0, 0, 0), ancora="t",
              forma="ret", esp_borda=0.5, nome=None, raio=None):
        """Desenha um retangulo, cartao arredondado ou pilula, com paragrafos dentro. Devolve o shape."""
        if self.seco or sl is None:
            return None
        w = max(w, 0.01)
        h = max(h, 0.01)
        if fill is None and borda is None and forma == "ret":
            sh = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        else:
            tipo = MSO_SHAPE.RECTANGLE if forma == "ret" else (MSO_SHAPE.OVAL if forma == "elipse" else MSO_SHAPE.ROUNDED_RECTANGLE)
            sh = sl.shapes.add_shape(tipo, Inches(x), Inches(y), Inches(w), Inches(h))
            self._limpar_estilo(sh)
            if forma == "cartao":
                sh.adjustments[0] = min(0.5, (raio if raio is not None else M.RAIO) / min(w, h))
            elif forma == "pilula":
                sh.adjustments[0] = 0.5
            if fill:
                sh.fill.solid()
                sh.fill.fore_color.rgb = rgb(fill)
            else:
                sh.fill.background()
            if borda:
                sh.line.color.rgb = rgb(borda)
                sh.line.width = Pt(esp_borda)
            else:
                sh.line.fill.background()
        if nome:
            sh.name = nome
        tf = sh.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (Inches(v) for v in ins)
        tf.vertical_anchor = ANC[ancora]
        for i, p in enumerate(pars or []):
            pg = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            pg.alignment = ALIN[p["alin"]]
            pg.line_spacing = Pt(p["ls"])
            if i and p["antes"]:
                pg.space_before = Pt(p["antes"])
            for texto, neg in M.partes(p["texto"], p["neg"]):
                r = pg.add_run()
                r.text = texto
                f = r.font
                f.size = Pt(p["pt"])
                f.bold = bool(neg)
                f.name = M.FONTE
                f.color.rgb = rgb(p["cor_neg"] if (neg and p["cor_neg"]) else p["cor"])
                rpr = r._r.get_or_add_rPr()
                rpr.set("lang", "pt-BR")
                if p["spc"]:
                    rpr.set("spc", str(int(round(p["spc"] * 100))))
                lat = rpr.find(qn("a:latin"))
                for tag in ("a:cs", "a:ea"):
                    el = etree.SubElement(rpr, qn(tag))
                    el.set("typeface", M.FONTE)
                    if lat is not None:
                        lat.addnext(el)
        return sh

    def cartao(self, sl, x, y, w, pars, fill="cartao", borda=None, ins=(0.23, 0.14, 0.15, 0.13), h=None):
        """Cartao arredondado com a altura calculada pelo texto. Devolve a altura."""
        alt = ins[1] + self.h_pars(pars, w - ins[0] - ins[2]) + ins[3]
        if h is not None:
            alt = max(alt, h)
        # Altura calculada pelo texto: a medida usa a fonte mais larga disponível, então no PowerPoint
        # (com Lato) pode sobrar uma linha. Centralizar evita a faixa com espaço vazio embaixo.
        self.caixa(sl, x, y, w, alt, pars, fill=fill, borda=borda, ins=ins, forma="cartao",
                   ancora="m" if h is None else "t")
        return alt

    def h_cartao(self, w, pars, ins=(0.23, 0.14, 0.15, 0.13)) -> float:
        return ins[1] + self.h_pars(pars, w - ins[0] - ins[2]) + ins[3]

    def imagem(self, sl, caminho, x, y, w=None, h=None):
        if self.seco or sl is None:
            return None
        kw = {}
        if w is not None:
            kw["width"] = Inches(w)
        if h is not None:
            kw["height"] = Inches(h)
        return sl.shapes.add_picture(str(caminho), Inches(x), Inches(y), **kw)

    def linha(self, sl, x1, y1, x2, y2, cor="texto2", esp=1.0, seta=False):
        if self.seco or sl is None:
            return None
        cn = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        self._limpar_estilo(cn)
        cn.line.color.rgb = rgb(cor)
        cn.line.width = Pt(esp)
        if seta:
            ln = cn.line._get_or_add_ln()
            fim = etree.SubElement(ln, qn("a:tailEnd"))
            fim.set("type", "triangle")
            fim.set("w", "med")
            fim.set("len", "med")
        return cn

    # ------------------------------------------------------------------ partes fixas
    def pilula(self, sl, inter: dict | None, escuro: bool) -> float:
        """Pilula de interacao no canto superior direito. Devolve o x da borda esquerda (ou MD)."""
        if not inter:
            return M.MD
        rot = M.rotulo_interacao(inter)
        w = self.med.largura(rot, 12, True, 1.0) + 0.52
        x = M.MD - w
        self.caixa(sl, x, M.Y_PILULA, w, M.H_PILULA,
                   [par(rot, 12, "marinho" if escuro else "branco", ls=14.4, neg=True, alin="c", spc=1.0)],
                   fill="ciano_claro" if escuro else "petroleo", forma="pilula", ancora="m", nome="Pilula de interacao")
        return x

    def cabecalho(self, sl, s: dict, escuro: bool = False, r: int = 0) -> float:
        """Olho + titulo + pilula. Devolve o y em que o corpo comeca."""
        x_pil = self.pilula(sl, s.get("interacao"), escuro)
        olho = s.get("olho")
        if olho:
            p = olho_par(olho, "ciano_claro" if escuro else "petroleo")
            if self.med.largura(p["texto"], 12, True, 1.5) > x_pil - M.ME - 0.25:
                self.aviso("o olho (texto pequeno acima do título) não cabe em uma linha antes da pílula e cai "
                           "em cima do título: encurte para poucas palavras (\"Bloco 2 · A evidência\").", "erro")
            self.caixa(sl, M.ME, M.Y_OLHO, x_pil - M.ME - 0.2, 0.228, [p])
        tit = s.get("titulo")
        if not tit:
            return M.Y_CORPO
        tit = tit if s.get("titulo_sem_destaque") else M.titulo_com_destaque(tit)
        cor = "fundo" if escuro else "texto"
        for pt in (28, 26, 24):
            p = par(tit, pt, cor, ls=round(pt * 1.15, 1))
            n = self.n_linhas(p, M.LC)
            if n <= 2:
                break
        if n > 2:
            self.aviso(f"título com {n} linhas mesmo em 24 pt: reescreva em até 2 linhas.", "erro")
        elif pt < 28:
            self.aviso(f"título reduzido para {pt} pt para caber em 2 linhas.")
        h = n * p["ls"] / 72.0
        self.caixa(sl, M.ME, M.Y_TITULO, M.LC, h, [p], nome="Titulo")
        return M.Y_CORPO + (n - 1) * p["ls"] / 72.0

    def texto_fonte(self, s: dict) -> str:
        itens = []
        for f in M.como_lista(s.get("fonte")):
            f = str(f)
            ref = self.refs.get(f)
            itens.append(ref.get("curta") or ref.get("texto") or f if ref else f)
        return "; ".join(i for i in itens if i)

    def rodape(self, sl, s: dict, escuro: bool = False, fonte: str | None = None) -> None:
        if self.seco or sl is None:
            return
        x, y, w, h = M.LOGO_RODAPE
        self.imagem(sl, M.LOGO_ESCURO if escuro else M.LOGO_CLARO, x, y, w, h)
        txt = fonte if fonte is not None else self.texto_fonte(s)
        if not txt:
            return
        txt = "Fonte: " + txt
        fx, fy, fw, fh = M.CAIXA_FONTE
        cor = "lavanda" if escuro else "texto_fonte"
        for pt in (12, 11, 10):
            if self.med.largura(txt, pt) <= fw:
                self.caixa(sl, fx, fy + (12 - pt) * 0.012, fw, fh, [par(txt, pt, cor, ls=pt * 1.2, alin="r")], nome="Fonte")
                return
        p = par(txt, 10, cor, ls=12.5, alin="r")
        n = self.n_linhas(p, fw)
        if n > 2:
            self.aviso("a fonte no rodapé passa de 2 linhas: use a forma curta e deixe a citação completa nas referências.", "erro")
        hh = n * 12.5 / 72.0
        self.caixa(sl, fx, fy + fh - hh, fw, hh, [p], nome="Fonte")

    def notas(self, sl, s: dict) -> None:
        if self.seco or sl is None:
            return
        txt = (s.get("notas") or "").strip()
        t = int(s.get("tempo_s") or 0)
        if s.get("apoio") or t <= 0:
            cab = "Slide de apoio, sem tempo previsto."
        else:
            cab = f"Tempo: {M.tempo_extenso(t)} (acumulado {M.relogio(self.acumulado)})."
        sl.notes_slide.notes_text_frame.text = f"{cab} {txt}".strip()

    def pt_r(self, base: float, r: int, minimo: float = 11) -> float:
        return max(minimo, base - r)

    # ------------------------------------------------------------------ pilha lateral de cartoes
    def pilha(self, sl, cartoes: list, x: float, y: float, w: float, r: int = 0) -> float:
        """Cartoes empilhados (coluna lateral). Estilos: escuro, claro, cinza, fala. Devolve o y final."""
        for c in M.como_lista(cartoes):
            if isinstance(c, str):
                c = {"estilo": "claro", "texto": c}
            est = c.get("estilo", "claro")
            pt = self.pt_r(13, r)
            if est == "escuro":
                fill, borda, cor, cor_olho, cor_nota = "marinho", None, "branco", "ciano_claro", "lavanda"
            elif est == "cinza":
                fill, borda, cor, cor_olho, cor_nota = "cartao", None, "texto", "petroleo", "texto2"
            elif est == "petroleo":
                fill, borda, cor, cor_olho, cor_nota = "petroleo", None, "branco", "ciano_claro", "lavanda"
            else:
                fill, borda, cor, cor_olho, cor_nota = "branco", "borda", "texto", "petroleo", "texto2"
            pars = []
            if c.get("olho"):
                pars.append(olho_par(c["olho"], cor_olho))
            if est == "fala":
                pars.append(par(c.get("texto"), self.pt_r(18, r, 14), cor, ls=self.pt_r(18, r, 14) * 1.3, antes=4))
            elif c.get("texto"):
                pars.append(par(c["texto"], pt, cor, ls=pt * 1.35, antes=4))
            for it in M.como_lista(c.get("itens")):
                pars.append(par(it, pt, cor, ls=pt * 1.35, antes=6 if len(pars) > 1 else 4))
            if c.get("nota"):
                pars.append(par(c["nota"], 12, cor_nota, ls=15.6, antes=5))
            ins = (0.23, 0.2, 0.15, 0.19) if (c.get("olho") or est == "fala") else (0.2, 0.15, 0.12, 0.14)
            h = self.cartao(sl, x, y, w, pars, fill=fill, borda=borda, ins=ins)
            y += h + 0.14
        return y - 0.14

    # ------------------------------------------------------------------ tipos de slide
    def t_capa(self, sl, s, r):
        titulo = s.get("titulo") or self.meta.get("titulo") or ""
        sub = s.get("subtitulo") or self.meta.get("subtitulo")
        autor = s.get("autor") or self.meta.get("autor")
        if sl is not None and not self.seco:
            self.imagem(sl, M.LOGO_ESCURO, *M.LOGO_CAPA)
        y = 6.64
        if autor:
            y -= 0.228
            self.caixa(sl, M.ME, y, M.LC, 0.228, [olho_par(autor, "ciano_claro")])
            y -= 0.222
        if sub:
            p = par(sub, 18, "lavanda", ls=24.3)
            h = self.h_pars([p], 10.014)
            y -= h
            self.caixa(sl, M.ME, y, 10.014, h, [p])
            y -= 0.2
        pt = (48, 44, 40, 36)[min(r, 3)]
        p = par(titulo if s.get("titulo_sem_destaque") else M.titulo_com_destaque(titulo), pt, "fundo", ls=round(pt * 1.15, 1))
        h = self.h_pars([p], 11.158)
        y -= h
        self.caixa(sl, M.ME, y, 11.158, h, [p], nome="Titulo")
        y -= 0.268
        self.caixa(sl, M.ME, y, 0.833, 0.042, fill="ciano", nome="Barra de acento")
        return y - 1.75      # folga: o bloco nao pode subir ate o logo

    def t_pergunta(self, sl, s, r):
        x_pil = self.pilula(sl, s.get("interacao"), True)
        if s.get("olho"):
            self.caixa(sl, M.ME, M.Y_OLHO, x_pil - M.ME - 0.2, 0.228, [olho_par(s["olho"], "ciano_claro")])
        y = 6.42
        linhas_extra = []
        # mesma ordem do slide de tarefa: primeiro o degrau de entrada, depois o desafio
        if s.get("ancora"):
            linhas_extra.append(par(f"**Para começar:** {s['ancora']}", 14, "lavanda", ls=19.6, cor_neg="ciano_claro"))
        if s.get("desafio"):
            linhas_extra.append(par(f"**Desafio:** {s['desafio']}", 14, "lavanda", ls=19.6, cor_neg="ciano_claro"))
        for p in reversed(linhas_extra):
            h = self.h_pars([p], 10.014)
            y -= h
            self.caixa(sl, M.ME, y, 10.014, h, [p])
            y -= 0.06
        if linhas_extra:
            y -= 0.1
        if s.get("instrucao"):
            p = par(s["instrucao"], 18, "lavanda", ls=24.3)
            h = self.h_pars([p], 10.014)
            y -= h
            self.caixa(sl, M.ME, y, 10.014, h, [p])
            y -= 0.222
        pt = (36, 32, 28, 26)[min(r, 3)]
        tit = s.get("pergunta") or s.get("titulo") or ""
        p = par(tit if s.get("titulo_sem_destaque") else M.titulo_com_destaque(tit), pt, "fundo", ls=round(pt * 1.15, 1))
        h = self.h_pars([p], 11.158)
        y -= h
        self.caixa(sl, M.ME, y, 11.158, h, [p], nome="Titulo")
        y -= 0.29
        self.caixa(sl, M.ME, y, 0.833, 0.042, fill="ciano", nome="Barra de acento")
        return y - 1.5

    def t_enquete(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        pt = self.pt_r(16, r, 13)
        if s.get("pergunta"):
            p = par(s["pergunta"], pt, "texto", ls=pt * 1.35)
            h = self.h_pars([p], M.LC)
            self.caixa(sl, M.ME, y, M.LC, h, [p])
            y += h + 0.16
        ops = s.get("opcoes") or {}
        if isinstance(ops, list):
            ops = {chr(65 + i): t for i, t in enumerate(ops)}
        letras = list(ops.keys())
        revela = str(s.get("revela") or "").strip().upper() or None
        wc = (M.LC - M.ESPACO_COLUNAS) / 2
        wt = wc - 0.82 - 0.2
        for i in range(0, len(letras), 2):
            linha = letras[i:i + 2]
            hs = []
            for L in linha:
                p = par(ops[L], pt, "texto", ls=pt * 1.3)
                hs.append(self.h_pars([p], wt))
            hc = max(0.889, max(hs) + 0.36)
            for j, L in enumerate(linha):
                x = M.ME + j * (wc + M.ESPACO_COLUNAS)
                certa = revela is not None and L.upper() == revela
                if revela is None:
                    fill, cl, ct, neg = "cartao", "petroleo", "texto", False
                elif certa:
                    fill, cl, ct, neg = "marinho", "ciano_claro", "branco", True
                else:
                    fill, cl, ct, neg = "cartao", "cinza_grafico", "texto2", False
                self.caixa(sl, x, y, wc, hc, fill=fill, forma="cartao", nome=f"Opcao {L}")
                self.caixa(sl, x + 0.222, y + (hc - 0.575) / 2, 0.5, 0.575, [par(L, 36, cl, ls=41.4, neg=True)])
                p = par(ops[L], pt, ct, ls=pt * 1.3, neg=neg)
                ht = self.h_pars([p], wt)
                self.caixa(sl, x + 0.82, y + (hc - ht) / 2, wt, ht, [p])
            y += hc + M.ESPACO_COLUNAS
        y -= M.ESPACO_COLUNAS
        if s.get("justificativa"):
            y += 0.2
            p14 = self.pt_r(14, r, 12)
            y += self.cartao(sl, M.ME, y, M.LC, [par(s["justificativa"], p14, "texto", ls=p14 * 1.4)],
                             fill="branco", borda="borda")
        return M.Y_LIMITE - y

    def _numerados(self, sl, itens, x, y, w, r, pt_base=16, cor_num="petroleo", cor="texto"):
        pt = self.pt_r(pt_base, r, 13)
        for i, it in enumerate(itens, 1):
            p = par(it, pt, cor, ls=pt * 1.3)
            h = self.h_pars([p], w - 0.5)
            self.caixa(sl, x, y - 0.02, 0.4, 0.38, [par(str(i), 22, cor_num, ls=25.3, neg=True)])
            self.caixa(sl, x + 0.5, y + 0.025, w - 0.5, h, [p])
            y += max(h, 0.32) + 0.14
        return y

    def t_tarefa(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        if s.get("dado"):
            pt = self.pt_r(14, r, 12)
            y += self.cartao(sl, M.ME, y, M.LC, [par(s["dado"], pt, "texto", ls=pt * 1.4)], fill="branco", borda="borda") + 0.2
        y = self._numerados(sl, M.como_lista(s.get("itens")), M.ME, y, M.LC, r)
        y += 0.03
        pt = self.pt_r(14, r, 12)
        if s.get("entrega"):
            y += self.cartao(sl, M.ME, y, M.LC, [par(f"**Entrega:** {s['entrega']}", pt, "branco", ls=pt * 1.4)],
                             fill="marinho", ins=(0.2, 0.14, 0.15, 0.13))
        extras = []
        if s.get("ancora"):
            extras.append(f"**Para começar:** {s['ancora']}")
        if s.get("desafio"):
            extras.append(f"**Desafio:** {s['desafio']}")
        if extras:
            y += 0.16
            wc = (M.LC - M.ESPACO_COLUNAS * (len(extras) - 1)) / len(extras)
            pars = [[par(e, self.pt_r(13, r), "texto", ls=self.pt_r(13, r) * 1.35)] for e in extras]
            hmax = max(self.h_cartao(wc, p, (0.2, 0.14, 0.12, 0.13)) for p in pars)
            for j, p in enumerate(pars):
                self.cartao(sl, M.ME + j * (wc + M.ESPACO_COLUNAS), y, wc, p, fill="branco", borda="borda",
                            ins=(0.2, 0.14, 0.12, 0.13), h=hmax)
            y += hmax
        return M.Y_LIMITE - y

    def t_topicos(self, sl, s, r):
        y0 = self.cabecalho(sl, s, r=r)
        lateral = M.como_lista(s.get("lateral"))
        w = 7.01 if lateral else min(M.LC, 9.2)
        pt = self.pt_r(14, r, 11.5)
        y = y0
        for it in M.como_lista(s.get("itens")):
            if isinstance(it, dict):
                it = f"**{it.get('termo', '').rstrip(':')}:** {it.get('texto', '')}"
            p = par(it, pt, "texto", ls=pt * 1.4)
            h = self.h_pars([p], w)
            self.caixa(sl, M.ME, y, w, h, [p])
            y += h + 0.12
        y -= 0.12
        if lateral:
            y = max(y, self.pilha(sl, lateral, 8.028, y0, M.MD - 8.028, r))
        return M.Y_LIMITE - y

    def t_cartoes(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        itens = M.como_lista(s.get("itens"))
        ncol = int(s.get("colunas") or (3 if len(itens) in (3, 6) else 2))
        wc = (M.LC - 0.194 * (ncol - 1)) / ncol
        wt = wc - 0.805 - 0.15
        pt_t, pt_x = self.pt_r(14, r, 12), self.pt_r(12, r, 11)
        for i in range(0, len(itens), ncol):
            linha = itens[i:i + ncol]
            hs = []
            for it in linha:
                pars = [par(it.get("titulo"), pt_t, "texto", ls=pt_t * 1.2, neg=True)]
                if it.get("texto"):
                    pars.append(par(it["texto"], pt_x, "texto", ls=pt_x * 1.3, antes=1))
                hs.append(self.h_pars(pars, wt) + 0.222 + 0.23)
            hc = max(0.936, max(hs))
            for j, it in enumerate(linha):
                x = M.ME + j * (wc + 0.194)
                dest = bool(it.get("destaque"))
                self.caixa(sl, x, y, wc, hc, fill="marinho" if dest else "cartao", forma="cartao")
                self.caixa(sl, x + 0.25, y + 0.193, 0.5, 0.45,
                           [par(str(it.get("numero", i + j + 1)), 28, "ciano_claro" if dest else "petroleo", ls=32.2, neg=True)])
                pars = [par(it.get("titulo"), pt_t, "branco" if dest else "texto", ls=pt_t * 1.2, neg=True)]
                if it.get("texto"):
                    pars.append(par(it["texto"], pt_x, "lavanda" if dest else "texto", ls=pt_x * 1.3, antes=1))
                self.caixa(sl, x + 0.805, y + 0.222, wt, hc - 0.3, pars)
            y += hc + 0.194
        y -= 0.194
        if s.get("faixa"):
            y += 0.194
            pt = self.pt_r(14, r, 12)
            y += self.cartao(sl, M.ME, y, M.LC, [par(s["faixa"], pt, "fundo", ls=pt * 1.4)], fill="marinho")
        return M.Y_LIMITE - y

    # ---- figura
    def _dim_figura(self, info, wmax, hmax):
        pw, ph = info["largura_px"], info["altura_px"]
        w = min(wmax, pw / M.PPP_MINIMO)
        h = w * ph / pw
        if h > hmax:
            h = hmax
            w = h * pw / ph
        return w, h

    def _destaques(self, sl, s, ix, iy, iw, ih):
        cores = {"alerta": "alerta", "ciano": "ciano", "marinho": "marinho", "petroleo": "petroleo"}
        for d in M.como_lista(s.get("destaques")):
            try:
                coords = [d.get(k) for k in ("x", "y") if d.get(k) is not None]
                if d.get("w") is not None:
                    coords += [float(d["x"]) + float(d["w"]), float(d["y"]) + float(d.get("h", 0))]
                for k in ("de", "para"):
                    coords += list(d.get(k) or [])
                if any(not -0.02 <= float(c) <= 1.02 for c in coords):
                    self.aviso(f"destaque {d.get('texto') or d.get('tipo')!r} sai da figura: as coordenadas são "
                               "relativas à imagem e vão de 0 a 1.", "erro")
                cor = cores.get(d.get("cor", "alerta"), "alerta")
                tipo = d.get("tipo", "retangulo")
                if tipo in ("retangulo", "elipse"):
                    x, y = ix + float(d["x"]) * iw, iy + float(d["y"]) * ih
                    w, h = float(d["w"]) * iw, float(d["h"]) * ih
                    self.caixa(sl, x, y, w, h, borda=cor, esp_borda=2.25,
                               forma="elipse" if tipo == "elipse" else "cartao", nome="Destaque")
                    if d.get("texto"):
                        pos = d.get("rotulo_pos", "sup-esq")
                        ex = x + w if pos.endswith("dir") else x
                        ey = y + h if pos.startswith("inf") else y
                        self._etiqueta(sl, ex, ey, str(d["texto"]), cor, centro=True)
                elif tipo == "seta":
                    (x1, y1), (x2, y2) = d["de"], d["para"]
                    self.linha(sl, ix + float(x1) * iw, iy + float(y1) * ih, ix + float(x2) * iw, iy + float(y2) * ih,
                               cor=cor, esp=2.25, seta=True)
                    if d.get("texto"):
                        self._etiqueta(sl, ix + float(x1) * iw, iy + float(y1) * ih, str(d["texto"]), cor, centro=True)
                elif tipo == "rotulo":
                    self._etiqueta(sl, ix + float(d["x"]) * iw, iy + float(d["y"]) * ih, str(d.get("texto", "")), cor, centro=True)
                else:
                    self.aviso(f"destaque de tipo desconhecido: {tipo!r} (use retangulo, elipse, seta ou rotulo).")
            except (KeyError, TypeError, ValueError) as e:
                self.aviso(f"destaque mal formado ({d}): {e}", "erro")

    def _etiqueta(self, sl, x, y, texto, cor, centro=False):
        w = max(0.3, self.med.largura(texto, 12, True) + 0.2)
        h = 0.3
        if centro:
            x, y = x - w / 2, y - h / 2
        else:
            x, y = x - 0.12, y - h / 2
        x = min(max(x, 0.05), M.LARGURA - w - 0.05)
        self.caixa(sl, x, y, w, h, [par(texto, 12, "branco", ls=14.4, neg=True, alin="c")], fill=cor,
                   forma="pilula", ancora="m", nome="Rotulo")

    def _plano_figura(self, s, info, y0, p_leg, pontos, pt, total):
        """Calcula tamanho da figura e alturas de legenda e pontos para um dos layouts."""
        pad = 0.12
        pl = {"total": total, "pad": pad, "h_pts": 0.0, "wcol": 0.0}
        if total:
            n = max(1, len(pontos))
            pl["wcol"] = (M.LC - 0.5 - 0.3 * (n - 1)) / n
            if pontos:
                pl["h_pts"] = max(self.h_pars([par(t, pt, "texto", ls=pt * 1.35)], pl["wcol"] - 0.42) for t in pontos) + 0.28
            wmax = M.LC - 2 * pad
            h_leg = (self.h_pars([p_leg], M.LC) + 0.08) if p_leg else 0.0
            hmax = M.Y_LIMITE - y0 - 2 * pad - h_leg - (pl["h_pts"] + 0.14 if pontos else 0)
            iw, ih = self._dim_figura(info, wmax, max(hmax, 1.0)) if info["existe"] else (wmax, max(1.0, min(hmax, 3.0)))
            pl["wl"] = M.LC
            pl["leg_dir"] = False
            if p_leg and info["existe"] and M.LC - (iw + 2 * pad) - 0.3 >= 2.4:
                # figura limitada pela altura: a legenda vai para a direita e a figura cresce
                hmax2 = M.Y_LIMITE - y0 - 2 * pad - (pl["h_pts"] + 0.14 if pontos else 0)
                iw2, ih2 = self._dim_figura(info, wmax, max(hmax2, 1.0))
                sobra = M.LC - (iw2 + 2 * pad) - 0.3
                if sobra >= 2.4:
                    iw, ih, hmax, h_leg = iw2, ih2, hmax2, 0.0
                    pl["leg_dir"], pl["wl"] = True, sobra
        else:
            wmax = float(s.get("largura_figura") or 7.0) - 2 * pad
            h_leg = 0.0
            for _ in range(4):   # a legenda acompanha a largura da moldura, entao itera
                hmax = M.Y_LIMITE - y0 - 2 * pad - h_leg
                iw, ih = self._dim_figura(info, wmax, max(hmax, 1.0)) if info["existe"] else (wmax, max(1.0, min(hmax, 3.2)))
                pl["wl"] = max(iw + 2 * pad, 5.0)
                novo_h = (self.h_pars([p_leg], pl["wl"]) + 0.08) if p_leg else 0.0
                if abs(novo_h - h_leg) < 0.01:
                    break
                h_leg = novo_h
        pl.update(iw=iw, ih=ih, wmax=wmax, hmax=hmax, h_leg=h_leg)
        return pl

    def t_figura(self, sl, s, r):
        y0 = self.cabecalho(sl, s, r=r)
        info = M.resolver_figura(s, self.catalogo, self.pasta_cat, self.base)
        pontos = M.como_lista(s.get("o_que_olhar"))
        lateral = M.como_lista(s.get("lateral"))
        leg = info.get("legenda")
        p_leg = par(leg, 12, "texto2", ls=15.6) if leg else None
        layout = (s.get("layout") or "auto").lower()
        pt = self.pt_r(14, r, 12)
        pt_tot = self.pt_r(13, r, 11.5)
        if layout == "total":
            pl = self._plano_figura(s, info, y0, p_leg, pontos, pt_tot, True)
        elif layout == "meia" or lateral or not info["existe"]:
            pl = self._plano_figura(s, info, y0, p_leg, pontos, pt, False)
        else:   # auto: fica com o layout em que a figura aparece maior
            a = self._plano_figura(s, info, y0, p_leg, pontos, pt, False)
            b = self._plano_figura(s, info, y0, p_leg, pontos, pt_tot, True)
            pl = b if b["iw"] * b["ih"] > 1.15 * a["iw"] * a["ih"] else a
        total, pad, iw, ih = pl["total"], pl["pad"], pl["iw"], pl["ih"]
        if total:
            pt = pt_tot
        if info["existe"]:
            if not self.seco:
                ppp = info["largura_px"] / iw
                if iw < pl["wmax"] * 0.72 and ih < pl["hmax"] * 0.72:
                    self.aviso(f"figura pequena no slide ({M.num(iw)} × {M.num(ih)} pol): o recorte tem só "
                               f"{info['largura_px']} × {info['altura_px']} px. Recorte de novo em 300 dpi ou mais.")
                if iw < 2.5 or ih < 1.8:
                    self.aviso(f"figura com proporção extrema ocupa só {M.num(iw)} × {M.num(ih)} pol no slide e fica "
                               "ilegível: recorte só o painel que a aula usa.")
                if ppp < M.PPP_MINIMO - 1:
                    self.aviso(f"figura ampliada além da resolução útil ({ppp:.0f} px/pol).", "erro")
        else:
            self.aviso(f"figura não encontrada: {info.get('caminho') or info.get('id')}", "erro")
        fw, fh = iw + 2 * pad, ih + 2 * pad
        leg_dir = bool(pl.get("leg_dir"))
        xf = M.ME + (M.LC - fw) / 2 if (total and not leg_dir) else M.ME
        self.caixa(sl, xf, y0, fw, fh, fill="branco", borda="borda", forma="cartao", nome="Moldura da figura")
        if info["existe"]:
            pic = self.imagem(sl, info["caminho"], xf + pad, y0 + pad, iw, ih)
            if pic is not None:
                pic.name = "Figura do artigo"
            self._destaques(sl, s, xf + pad, y0 + pad, iw, ih)
        else:
            self.caixa(sl, xf + pad, y0 + pad, iw, ih,
                       [par(f"FIGURA NÃO ENCONTRADA\n{info.get('caminho') or info.get('id')}", 14, "alerta", neg=True, alin="c")],
                       ancora="m")
        y = y0 + fh
        if p_leg and leg_dir:
            hl = self.h_pars([p_leg], pl["wl"])
            self.caixa(sl, xf + fw + 0.3, y0 + 0.02, pl["wl"], hl, [p_leg], nome="Legenda")
            y = max(y, y0 + 0.02 + hl)
        elif p_leg:
            hl = self.h_pars([p_leg], pl["wl"])
            self.caixa(sl, M.ME, y + 0.08, pl["wl"], hl, [p_leg], nome="Legenda")
            y += 0.08 + hl
        if total:
            if pontos:
                y += 0.14
                h_pts, wcol = pl["h_pts"], pl["wcol"]
                self.caixa(sl, M.ME, y, M.LC, h_pts, fill="cartao", forma="cartao")
                for i, t in enumerate(pontos):
                    x = M.ME + 0.25 + i * (wcol + 0.3)
                    self.caixa(sl, x, y + 0.11, 0.36, 0.3, [par(str(i + 1), 18, "petroleo", ls=19.8, neg=True)])
                    self.caixa(sl, x + 0.42, y + 0.14, wcol - 0.42, h_pts - 0.24, [par(t, pt, "texto", ls=pt * 1.35)])
                y += h_pts
        else:
            xc = M.ME + fw + 0.3
            wc = M.MD - xc
            yc = y0
            if wc < 3.2:
                self.aviso("coluna 'o que olhar' ficou estreita: reduza largura_figura ou use layout total.")
            if pontos:
                olho = s.get("rotulo_pontos") or "O que olhar"
                wt = wc - 0.25 - 0.42 - 0.2
                hs = [self.h_pars([par(t, pt, "texto", ls=pt * 1.35)], wt) for t in pontos]
                hc = 0.2 + 0.228 + 0.1 + sum(max(h, 0.3) for h in hs) + 0.14 * (len(pontos) - 1) + 0.2
                self.caixa(sl, xc, yc, wc, hc, fill="cartao", forma="cartao")
                self.caixa(sl, xc + 0.25, yc + 0.2, wc - 0.4, 0.228, [olho_par(olho)])
                yy = yc + 0.2 + 0.228 + 0.1
                for i, t in enumerate(pontos):
                    self.caixa(sl, xc + 0.25, yy - 0.01, 0.36, 0.3, [par(str(i + 1), 18, "petroleo", ls=19.8, neg=True)])
                    self.caixa(sl, xc + 0.25 + 0.42, yy + 0.01, wt, hs[i], [par(t, pt, "texto", ls=pt * 1.35)])
                    yy += max(hs[i], 0.3) + 0.14
                yc += hc + 0.14
            if lateral:
                yc = self.pilha(sl, lateral, xc, yc, wc, r) + 0.14
            y = max(y, yc - 0.14)
        self._fonte_figura = info.get("citacao")
        return M.Y_LIMITE - y

    # ---- tabela
    def _tabela(self, sl, s, x, y, w, r):
        cols = M.como_lista(s.get("colunas"))
        linhas = [M.como_lista(l) for l in M.como_lista(s.get("linhas"))]
        nc = max([len(cols)] + [len(l) for l in linhas]) if (cols or linhas) else 0
        if nc == 0:
            return 0.0
        larg = M.como_lista(s.get("larguras")) or [1.0] * nc
        larg = (larg + [1.0] * nc)[:nc]
        tot = float(sum(larg))
        ws = [w * float(v) / tot for v in larg]
        pt = (12, 11.5, 11, 10)[min(r, 3)]
        ls = pt * 1.4
        mx, my = 0.153, 0.083
        dados = ([cols] if cols else []) + linhas
        alturas = []
        for li, lin in enumerate(dados):
            hmax = 0.0
            for ci in range(nc):
                t = lin[ci] if ci < len(lin) else ""
                neg = bool(cols) and li == 0
                hmax = max(hmax, self.h_pars([par(t, pt, "texto", ls=ls, neg=neg)], ws[ci] - 2 * mx))
            alturas.append(hmax + 2 * my)
        total = sum(alturas)
        if self.seco or sl is None:
            return total
        gf = sl.shapes.add_table(len(dados), nc, Inches(x), Inches(y), Inches(w), Inches(total))
        gf.name = "Tabela"
        tb = gf.table
        tblPr = tb._tbl.tblPr
        for at in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
            if at in tblPr.attrib:
                del tblPr.attrib[at]
        for ch in list(tblPr):
            tblPr.remove(ch)
        for ci in range(nc):
            tb.columns[ci].width = Inches(ws[ci])
        dest = set(int(i) for i in M.como_lista(s.get("destaque_linhas")))
        for li, lin in enumerate(dados):
            tb.rows[li].height = Inches(alturas[li])
            cab = bool(cols) and li == 0
            idx_dado = li - (1 if cols else 0)
            for ci in range(nc):
                cel = tb.cell(li, ci)
                t = lin[ci] if ci < len(lin) else ""
                cel.margin_left = cel.margin_right = Inches(mx)
                cel.margin_top = cel.margin_bottom = Inches(my)
                cel.vertical_anchor = MSO_ANCHOR.TOP
                destaque = (not cab) and idx_dado in dest
                cel.fill.solid()
                cel.fill.fore_color.rgb = rgb("marinho" if cab else ("cartao" if destaque else "branco"))
                cor = "branco" if cab else ("marinho" if ci == 0 else "texto")
                tf = cel.text_frame
                tf.word_wrap = True
                pg = tf.paragraphs[0]
                pg.line_spacing = Pt(ls)
                for texto, neg in M.partes(str(t), cab or destaque and ci == 0):
                    rn = pg.add_run()
                    rn.text = texto
                    rn.font.size = Pt(pt)
                    rn.font.bold = bool(neg)
                    rn.font.name = M.FONTE
                    rn.font.color.rgb = rgb(cor)
                    rn._r.get_or_add_rPr().set("lang", "pt-BR")
                self._bordas_celula(cel, "marinho_escuro" if cab else "borda_tabela")
        return total

    @staticmethod
    def _bordas_celula(cel, cor):
        tcPr = cel._tc.get_or_add_tcPr()
        for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
            antigo = tcPr.find(qn(tag))
            if antigo is not None:
                tcPr.remove(antigo)
        novos = []
        for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
            ln = etree.Element(qn(tag))
            ln.set("w", "12700")
            ln.set("cap", "flat")
            ln.set("cmpd", "sng")
            ln.set("algn", "ctr")
            sf = etree.SubElement(ln, qn("a:solidFill"))
            c = etree.SubElement(sf, qn("a:srgbClr"))
            c.set("val", C[cor])
            etree.SubElement(ln, qn("a:prstDash")).set("val", "solid")
            novos.append(ln)
        for i, ln in enumerate(novos):
            tcPr.insert(i, ln)

    def t_tabela(self, sl, s, r):
        y0 = self.cabecalho(sl, s, r=r)
        lateral = M.como_lista(s.get("lateral"))
        w = 6.24 if lateral else M.LC - 0.02
        h = self._tabela(sl, s, M.ME + 0.01, y0 + 0.01, w, r)
        y = y0 + 0.01 + h
        if s.get("nota"):
            p = par(s["nota"], 12, "texto2", ls=15.6)
            hn = self.h_pars([p], w)
            self.caixa(sl, M.ME, y + 0.1, w, hn, [p])
            y += 0.1 + hn
        if lateral:
            y = max(y, self.pilha(sl, lateral, M.ME + w + 0.35, y0, M.MD - (M.ME + w + 0.35), r))
        return M.Y_LIMITE - y

    def t_numeros(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        itens = M.como_lista(s.get("itens"))
        n = max(1, len(itens))
        wc = (M.LC - 0.194 * (n - 1)) / n
        wt = wc - 0.25 - 0.15
        pt_n = 48
        for it in itens:
            while pt_n > 28 and self.med.largura(str(it.get("numero", "")), pt_n, True) > wt:
                pt_n -= 2
        longos = [str(it.get("numero", "")) for it in itens if self.med.largura(str(it.get("numero", "")), pt_n, True) > wt]
        if longos:
            self.aviso(f"número grande demais para o cartão ({'; '.join(longos)}): deixe só o número no campo "
                       "'numero' e passe o intervalo ou a unidade longa para o 'rotulo'.", "erro")
        pt_l = self.pt_r(14, r, 12)
        h_rot = max([self.h_pars([par(it.get("rotulo"), pt_l, "texto", ls=pt_l * 1.4)], wt) for it in itens] or [0.3])
        hc = 0.17 + pt_n * 1.15 / 72 + 0.03 + h_rot + 0.22
        for i, it in enumerate(itens):
            x = M.ME + i * (wc + 0.194)
            dest = bool(it.get("destaque"))
            self.caixa(sl, x, y, wc, hc, fill="marinho" if dest else "cartao", forma="cartao")
            self.caixa(sl, x + 0.25, y + 0.17, wt, pt_n * 1.15 / 72,
                       [par(str(it.get("numero", "")), pt_n, "branco" if dest else "petroleo", ls=pt_n * 1.15, neg=True)])
            self.caixa(sl, x + 0.25, y + 0.17 + pt_n * 1.15 / 72 + 0.03, wt, h_rot,
                       [par(it.get("rotulo"), pt_l, "branco" if dest else "texto", ls=pt_l * 1.4)])
        y += hc
        for ln in M.como_lista(s.get("linhas")):
            y += 0.17
            y += self.cartao(sl, M.ME, y, M.LC, [par(ln, pt_l, "texto", ls=pt_l * 1.4)], fill="branco", borda="borda")
        return M.Y_LIMITE - y

    # ---- graficos nativos
    def _legenda_manual(self, sl, series, x, y, largura=None):
        """Legenda desenhada como no deck de referencia: quadradinho + nome. Quebra a linha quando
        passa da largura do grafico. Devolve a altura ocupada."""
        x0, linhas = x, 1
        largura = largura or M.LC
        for i, se in enumerate(series):
            cor = se.get("cor") or M.CORES_SERIES[i % len(M.CORES_SERIES)]
            nome = str(se.get("nome", ""))
            w = self.med.largura(nome, 12) + 0.1
            if x > x0 and x + 0.25 + w > x0 + largura:
                x, y, linhas = x0, y + 0.3, linhas + 1
            self.caixa(sl, x, y + 0.035, 0.167, 0.167, fill=cor, forma="cartao", raio=0.028)
            self.caixa(sl, x + 0.25, y, w, 0.24, [par(nome, 12, "texto", ls=15.6)])
            x += 0.25 + w + 0.25
        return 0.24 + 0.3 * (linhas - 1)

    def _grafico(self, sl, s, x, y, w, h, tipo):
        if self.seco or sl is None:
            return
        cats = [str(c) for c in M.como_lista(s.get("categorias"))]
        series = M.como_lista(s.get("series"))
        fmt = s.get("formato") or "General"
        cd = CategoryChartData(number_format=fmt)
        cd.categories = cats
        for se in series:
            cd.add_series(str(se.get("nome", "")), [None if v is None else float(v) for v in M.como_lista(se.get("valores"))])
        horizontal = (s.get("orientacao") or "vertical") == "horizontal"
        if tipo == "linha":
            xl = XL_CHART_TYPE.LINE_MARKERS
        else:
            xl = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
        gf = sl.shapes.add_chart(xl, Inches(x), Inches(y), Inches(w), Inches(h), cd)
        gf.name = "Grafico nativo (editavel)"
        ch = gf.chart
        # O modelo de colunas/barras do python-pptx grava ids de eixo negativos; o esquema OOXML pede
        # inteiro sem sinal. Usa o valor absoluto (fica abaixo de 2^31: o LibreOffice lê como inteiro
        # com sinal e perde o eixo de categorias se o id passar disso).
        for el in ch._chartSpace.iter(qn("c:axId"), qn("c:crossAx")):
            v = int(el.get("val"))
            if v < 0:
                el.set("val", str(abs(v)))
        ch.has_title = False
        ch.has_legend = False
        ch.font.name = M.FONTE
        ch.font.size = Pt(12)
        ch.font.color.rgb = rgb("texto")
        plot = ch.plots[0]
        ca, va = ch.category_axis, ch.value_axis
        ca.has_major_gridlines = False
        ca.major_tick_mark = XL_TICK_MARK.NONE
        ca.format.line.color.rgb = rgb("eixo")
        ca.format.line.width = Pt(1)
        ca.tick_labels.font.size = Pt(12)
        ca.tick_labels.font.name = M.FONTE
        ca.tick_labels.font.color.rgb = rgb("texto")
        if s.get("minimo") is not None:
            va.minimum_scale = float(s["minimo"])
        elif tipo != "linha":
            va.minimum_scale = 0
        if s.get("maximo") is not None:
            va.maximum_scale = float(s["maximo"])
        rotulos = s.get("rotulos", True)
        if tipo == "linha":
            va.visible = True
            va.has_major_gridlines = True
            va.major_gridlines.format.line.color.rgb = rgb("borda")
            va.major_gridlines.format.line.width = Pt(0.75)
            va.format.line.fill.background()
            va.major_tick_mark = XL_TICK_MARK.NONE
            va.tick_labels.font.size = Pt(12)
            va.tick_labels.font.color.rgb = rgb("texto2")
            va.tick_labels.number_format = fmt
            va.tick_labels.number_format_is_linked = False
        else:
            va.visible = False
            va.has_major_gridlines = False
            plot.gap_width = int(s.get("vao") or (55 if len(series) > 1 else 45))
            plot.overlap = -8 if len(series) > 1 else 0
            if horizontal:
                ca.reverse_order = True
        if rotulos:
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.font.size = Pt(14 if (len(cats) * max(1, len(series)) <= 8 and tipo != "linha") else 12)
            dl.font.bold = True
            dl.font.name = M.FONTE
            dl.font.color.rgb = rgb("texto")
            dl.number_format = fmt
            dl.number_format_is_linked = False
            dl.position = XL_LABEL_POSITION.ABOVE if tipo == "linha" else XL_LABEL_POSITION.OUTSIDE_END
        dest = set(int(i) for i in M.como_lista(s.get("destaque_categorias")))
        for i, se in enumerate(plot.series):
            cor = series[i].get("cor") or M.CORES_SERIES[i % len(M.CORES_SERIES)]
            if tipo == "linha":
                se.smooth = False
                se.format.line.color.rgb = rgb(cor)
                se.format.line.width = Pt(2.5)
                se.marker.style = XL_MARKER_STYLE.CIRCLE
                se.marker.size = 8
                se.marker.format.fill.solid()
                se.marker.format.fill.fore_color.rgb = rgb(cor)
                se.marker.format.line.color.rgb = rgb(cor)
                for j in dest:
                    if j < len(cats):
                        pto = se.points[j]
                        pto.marker.style = XL_MARKER_STYLE.CIRCLE
                        pto.marker.size = 11
                        pto.marker.format.fill.solid()
                        pto.marker.format.fill.fore_color.rgb = rgb("alerta")
                        pto.marker.format.line.color.rgb = rgb("alerta")
                        # O PowerPoint pinta o marcador pelo spPr do marcador (acima). O render do
                        # LibreOffice ignora essa cor e mostra o ponto maior, na cor da serie; pintar
                        # o spPr do ponto deixaria vermelho no LibreOffice, mas tambem o trecho de
                        # linha no PowerPoint. Fica o que e certo no PowerPoint.
            else:
                se.format.fill.solid()
                se.format.fill.fore_color.rgb = rgb(cor)
                se.format.line.fill.background()
                se.invert_if_negative = False
                if len(series) == 1:
                    for j in dest:
                        if j < len(cats):
                            pto = se.points[j]
                            pto.format.fill.solid()
                            pto.format.fill.fore_color.rgb = rgb("alerta")

    def _t_grafico(self, sl, s, r, tipo):
        y0 = self.cabecalho(sl, s, r=r)
        lateral = M.como_lista(s.get("lateral"))
        series = M.como_lista(s.get("series"))
        w = 6.9 if lateral else M.LC
        y = y0
        if s.get("rotulo"):
            p_rot = olho_par(s["rotulo"], "texto2")
            n_rot = self.n_linhas(p_rot, w)
            if n_rot > 1:
                self.aviso("o rótulo do gráfico ocupa mais de uma linha: encurte (é um olho, não uma frase).")
            h_rot = n_rot * p_rot["ls"] / 72.0
            self.caixa(sl, M.ME, y, w, h_rot, [p_rot])
            y += h_rot + 0.1
        mostra_leg = len(series) > 1 or s.get("legenda_destaque")
        if mostra_leg:
            leg = list(series) if len(series) > 1 else []
            if s.get("legenda_destaque"):
                leg.append({"nome": s["legenda_destaque"], "cor": "alerta"})
            y += self._legenda_manual(sl, leg, M.ME, y, w) + 0.1
        cats = [str(c) for c in M.como_lista(s.get("categorias"))]
        if cats and tipo == "barras" and (s.get("orientacao") or "vertical") != "horizontal":
            vaga = w / len(cats) - 0.1
            if max(self.med.largura(c, 12) for c in cats) > 2 * vaga:
                self.aviso("nomes de categoria longos para colunas: o PowerPoint vai girar os rótulos. "
                           "Encurte os nomes ou use \"orientacao\": \"horizontal\".")
        p_nota = par(s["nota"], 12, "texto2", ls=15.6) if s.get("nota") else None
        h_nota = (self.h_pars([p_nota], w) + 0.1) if p_nota else 0
        y_lat = self.pilha(sl, lateral, M.ME + w + 0.35, y0, M.MD - (M.ME + w + 0.35), r) if lateral else y0
        h = float(s.get("altura") or min(3.6, M.Y_LIMITE - y - h_nota))
        h = max(h, 1.8)
        self._grafico(sl, s, M.ME - 0.05, y, w + 0.05, h, tipo)
        y += h
        if p_nota:
            self.caixa(sl, M.ME, y + 0.1, w, h_nota - 0.1, [p_nota])
            y += h_nota
        y = max(y, y_lat)
        return M.Y_LIMITE - y

    def t_barras(self, sl, s, r):
        return self._t_grafico(sl, s, r, "barras")

    def t_linha(self, sl, s, r):
        return self._t_grafico(sl, s, r, "linha")

    def t_etapas(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        passos = M.como_lista(s.get("passos"))
        n = max(1, len(passos))
        vao = 0.385
        wc = (M.LC - vao * (n - 1)) / n
        pt_t, pt_x = self.pt_r(14, r, 12), self.pt_r(12, r, 11)
        ins = (0.167, 0.167, 0.12, 0.17)
        blocos = []
        for i, p in enumerate(passos):
            dest = bool(p.get("destaque"))
            tit = p.get("titulo", "")
            if s.get("numerar"):
                tit = f"{i + 1}. {tit}"
            pars = [par(tit, pt_t, "branco" if dest else "marinho", ls=pt_t * 1.2, neg=True)]
            if p.get("texto"):
                pars.append(par(p["texto"], pt_x, "lavanda" if dest else "texto", ls=pt_x * 1.3, antes=2))
            blocos.append((pars, dest))
        hc = max([self.h_cartao(wc, b[0], ins) for b in blocos] or [1.0])
        for i, (pars, dest) in enumerate(blocos):
            x = M.ME + i * (wc + vao)
            self.cartao(sl, x, y, wc, pars, fill="marinho" if dest else "cartao", ins=ins, h=hc)
            if i < n - 1:
                self.linha(sl, x + wc + 0.07, y + hc / 2, x + wc + vao - 0.07, y + hc / 2, cor="marinho", esp=1.5, seta=True)
        y += hc
        baixo = M.como_lista(s.get("cartoes_baixo"))
        if baixo:
            y += 0.19
            nb = len(baixo)
            wb = (M.LC - 0.194 * (nb - 1)) / nb
            pt = self.pt_r(14, r, 12)
            pars_b = []
            for c in baixo:
                if isinstance(c, str):
                    c = {"texto": c}
                esc = c.get("estilo") == "escuro"
                pars_b.append(([par(c.get("texto"), pt, "branco" if esc else "texto", ls=pt * 1.4)], esc))
            hb = max(self.h_cartao(wb, p, (0.2, 0.15, 0.12, 0.15)) for p, _ in pars_b)
            for i, (p, esc) in enumerate(pars_b):
                self.cartao(sl, M.ME + i * (wb + 0.194), y, wb, p, fill="marinho" if esc else "branco",
                            borda=None if esc else "borda", ins=(0.2, 0.15, 0.12, 0.15), h=hb)
            y += hb
        return M.Y_LIMITE - y

    def t_comparacao(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        faixas = M.como_lista(s.get("faixas"))
        for fi, fx in enumerate(faixas):
            itens = M.como_lista(fx.get("itens"))
            n = max(1, len(itens))
            if fx.get("rotulo"):
                self.caixa(sl, M.ME, y, M.LC, 0.228, [olho_par(fx["rotulo"], "texto2" if fi == 0 else "petroleo")])
                y += 0.228 + 0.085
            vao = 0.083
            wc = (M.LC - vao * (n - 1)) / n
            grande = n <= 4
            pt_t = self.pt_r(14 if grande else 12, r, 11)
            pt_x = self.pt_r(13 if grande else 12, r, 10.5)
            ins = (0.17, 0.14, 0.1, 0.13) if grande else (0.11, 0.11, 0.06, 0.1)
            blocos = []
            for it in itens:
                dest = bool(it.get("destaque"))
                pars = [par(it.get("titulo"), pt_t, "branco" if dest else "texto", ls=pt_t * 1.3, neg=True)]
                if it.get("texto"):
                    pars.append(par(it["texto"], pt_x, "branco" if dest else "texto", ls=pt_x * 1.3, antes=1.5))
                if it.get("etiqueta"):
                    pars.append(par(it["etiqueta"], 12, "ciano_claro" if dest else "texto2", ls=15.6, neg=True, antes=4))
                blocos.append((pars, dest))
            hc = max([self.h_cartao(wc, b[0], ins) for b in blocos] or [0.8])
            for i, (pars, dest) in enumerate(blocos):
                self.cartao(sl, M.ME + i * (wc + vao), y, wc, pars, fill="marinho" if dest else "cartao", ins=ins, h=hc)
            y += hc + 0.11
        y -= 0.11
        if s.get("nota"):
            y += 0.17
            pt = self.pt_r(14, r, 12)
            y += self.cartao(sl, M.ME, y, M.LC, [par(s["nota"], pt, "texto", ls=pt * 1.4)], fill="branco", borda="borda")
        return M.Y_LIMITE - y

    def t_citacao(self, sl, s, r):
        escuro = s.get("fundo") == "escuro"
        y0 = self.cabecalho(sl, s, escuro=escuro, r=r)
        cart = s.get("cartao") or {}
        wl = 7.1 if cart else 9.2
        y = y0
        if s.get("contexto"):
            pt = self.pt_r(16, r, 13)
            p = par(s["contexto"], pt, "fundo" if escuro else "texto", ls=pt * 1.35)
            h = self.h_pars([p], wl)
            self.caixa(sl, M.ME, y, wl, h, [p])
            y += h + 0.17
        pt_f = self.pt_r(18, r, 14)
        pars = []
        if s.get("rotulo"):
            pars.append(olho_par(s["rotulo"], "ciano_claro" if escuro else "petroleo"))
        pars.append(par(s.get("fala"), pt_f, "branco" if escuro else "texto", ls=pt_f * 1.3, antes=4))
        if s.get("quem"):
            pars.append(par(s["quem"], 12, "lavanda" if escuro else "texto2", ls=15.6, antes=6))
        y += self.cartao(sl, M.ME, y, wl, pars, fill="petroleo" if escuro else "branco",
                         borda=None if escuro else "borda", ins=(0.26, 0.22, 0.2, 0.2))
        if s.get("fala2"):
            y += 0.18
            pt2 = self.pt_r(16, r, 13)
            y += self.cartao(sl, M.ME, y, wl, [par(s["fala2"], pt2, "texto", ls=pt2 * 1.3)], fill="cartao",
                             ins=(0.23, 0.2, 0.15, 0.17))
        if cart:
            x = M.ME + wl + 0.29
            w = M.MD - x
            c = dict(cart)
            c.setdefault("estilo", "claro" if escuro else "escuro")
            if c["estilo"] == "escuro":
                pt = self.pt_r(14, r, 12)
                pars = [olho_par(c["olho"], "ciano_claro")] if c.get("olho") else []
                for it in M.como_lista(c.get("itens")):
                    pars.append(par(it, pt, "branco", ls=pt * 1.35, antes=8))
                if c.get("texto"):
                    pars.append(par(c["texto"], pt, "branco", ls=pt * 1.35, antes=8))
                hc = self.cartao(sl, x, y0, w, pars, fill="marinho", ins=(0.28, 0.28, 0.17, 0.28))
                y = max(y, y0 + hc)
            else:
                y = max(y, self.pilha(sl, [c], x, y0, w, r))
        return M.Y_LIMITE - y

    def t_sintese(self, sl, s, r):
        y = self.cabecalho(sl, s, r=r)
        pontos = M.como_lista(s.get("pontos"))
        pt_t, pt_x = self.pt_r(16, r, 13), self.pt_r(14, r, 12)
        wt = M.LC - 0.95 - 0.25
        for i, p in enumerate(pontos, 1):
            if isinstance(p, str):
                p = {"titulo": p}
            pars = [par(p.get("titulo"), pt_t, "texto", ls=pt_t * 1.3, neg=True)]
            if p.get("texto"):
                pars.append(par(p["texto"], pt_x, "texto2", ls=pt_x * 1.4, antes=2))
            hc = max(0.8, self.h_pars(pars, wt) + 0.36)
            self.caixa(sl, M.ME, y, M.LC, hc, fill="cartao", forma="cartao")
            self.caixa(sl, M.ME + 0.28, y + (hc - 0.45) / 2, 0.5, 0.45, [par(str(i), 28, "petroleo", ls=32.2, neg=True)])
            ht = self.h_pars(pars, wt)
            self.caixa(sl, M.ME + 0.95, y + (hc - ht) / 2, wt, ht, pars)
            y += hc + 0.14
        y -= 0.14
        if s.get("faixa"):
            y += 0.19
            pt = self.pt_r(14, r, 12)
            y += self.cartao(sl, M.ME, y, M.LC, [par(s["faixa"], pt, "fundo", ls=pt * 1.4)], fill="marinho")
        return M.Y_LIMITE - y

    # ---- referencias (pagina sozinho)
    def linhas_referencias(self) -> list[str]:
        """Uma referencia por linha, como no deck de referencia ("Autor et al. Revista Ano. PMID n").
        Se alguma forma completa quebra a linha, todas perdem volume e paginas, para o slide ficar
        homogeneo; a forma completa continua no resumo do aluno e no rodape das figuras."""
        itens = []
        for ref in sorted(self.refs.values(), key=lambda x: M.sem_marcacao(str(x.get("texto") or x.get("curta") or x.get("id"))).lower()):
            t = str(ref.get("texto") or ref.get("curta") or ref.get("id")).strip().rstrip(".")
            sufixo = ""
            if ref.get("pmid"):
                sufixo += f". PMID {ref['pmid']}"
            if ref.get("doi") and (not ref.get("pmid") or self.meta.get("referencias_com_doi")):
                sufixo += f". DOI {ref['doi']}"
            itens.append((t, sufixo))
        curto = self.meta.get("referencias_formato") == "curto" or (
            self.meta.get("referencias_formato") != "completo"
            and any(self.med.n_linhas(t + suf, 12, 5.722) > 1 for t, suf in itens))
        if curto:
            itens = [(re.sub(r"(\b(19|20)\d{2}[a-z]?)\s*;[^;]*$", r"\1", t), suf) for t, suf in itens]
        return [t + suf for t, suf in itens]

    def nota_referencias(self, s) -> str:
        if (s.get("notas") or "").strip():
            return s["notas"].strip()
        grupos = {"texto completo": [], "resumo": [], "nao conferido": []}
        for ref in self.refs.values():
            c = str(ref.get("conferido") or "nao conferido").lower()
            chave = "texto completo" if "complet" in c else ("resumo" if "resumo" in c else "nao conferido")
            grupos[chave].append(ref.get("curta") or ref.get("id"))
        partes_ = []
        if grupos["texto completo"]:
            partes_.append("Conferidos no texto completo: " + "; ".join(sorted(grupos["texto completo"])) + ".")
        if grupos["resumo"]:
            partes_.append("Conferidos só no resumo: " + "; ".join(sorted(grupos["resumo"])) + ".")
        if grupos["nao conferido"]:
            partes_.append("Não conferidos na fonte: " + "; ".join(sorted(grupos["nao conferido"])) + ".")
        props = M.como_lista(self.meta.get("propostas_clinicas"))
        if props:
            partes_.append("Propostas clínicas, sem ensaio que as teste: " + "; ".join(str(p).rstrip(".") for p in props) + ".")
        if self.meta.get("caso_ficticio"):
            partes_.append("O paciente do caso e seus dados são fictícios.")
        return " ".join(partes_)

    def montar_referencias(self, s):
        linhas = self.linhas_referencias()
        for extra in M.como_lista(s.get("outras")):
            linhas.append(f"Também: {extra}")
        wcol = 5.722               # medido no deck de referencia: duas colunas de 5,722 pol em x=0,889 e 6,889
        xs = [M.ME, 6.889]
        pt, ls = 12, 15.6
        blocos = [(t, self.h_pars([par(t, pt, "texto", ls=ls)], wcol)) for t in linhas]
        y_fim = 6.45
        pag, i = 0, 0
        s_nota = dict(s)
        s_nota["notas"] = self.nota_referencias(s)
        s_nota["apoio"] = True
        if not blocos:
            blocos = [("(sem referências no deck.json)", 0.22)]
        while i < len(blocos):
            pag += 1
            sl = self.novo_slide()
            sp = dict(s)
            sp.pop("interacao", None)
            sp["olho"] = s.get("olho") or "Fontes"
            sp["titulo"] = (s.get("titulo") or "**Referências**") + (f" ({pag})" if pag > 1 else "")
            y0 = self.cabecalho(sl, sp)
            # quantas cabem nesta pagina (duas colunas cheias) e quantas vao para a esquerda:
            # como no deck de referencia, as duas colunas ficam com alturas parecidas
            cap, j = [], i
            for _x in xs:
                y, c = y0, 0
                while j < len(blocos) and y + blocos[j][1] <= y_fim:
                    y += blocos[j][1] + 0.042
                    j += 1
                    c += 1
                cap.append(c)
            n_pag = sum(cap)
            # poucas referencias (ate 8 linhas) ficam numa coluna so, como uma lista curta
            limite_esq = i + (cap[0] if n_pag <= 8 else min(cap[0], (n_pag + 1) // 2))
            for k, x in enumerate(xs):
                y = y0
                while i < len(blocos) and y + blocos[i][1] <= y_fim and (k > 0 or i < limite_esq):
                    t, h = blocos[i]
                    self.caixa(sl, x, y, wcol, h, [par(t, pt, "texto", ls=ls)])
                    y += h + 0.042         # passo de 0,286 pol entre referencias de uma linha, como no deck de referencia
                    i += 1
                if i >= len(blocos):
                    break
            self.rodape(sl, {}, False, fonte="")
            self.notas(sl, s_nota)
        if pag > 1:
            self.aviso(f"referências ocuparam {pag} slides.", "info")

    # ------------------------------------------------------------------ laco principal
    def montar(self) -> None:
        slides = M.como_lista(self.deck.get("slides"))
        for n, s in enumerate(slides, 1):
            self.n_atual = n
            if not isinstance(s, dict):
                self.aviso("slide não é um objeto JSON; ignorado.", "erro")
                continue
            tipo = s.get("tipo")
            if tipo not in M.TIPOS:
                self.aviso(f"tipo de slide desconhecido: {tipo!r}. Tipos válidos: {', '.join(M.TIPOS)}.", "erro")
                continue
            t = int(s.get("tempo_s") or 0)
            if not s.get("apoio"):
                self.acumulado += t
            try:
                if tipo == "referencias":
                    self.montar_referencias(s)
                    continue
                fn = getattr(self, "t_" + tipo)
                escuro = tipo in ("capa", "pergunta") or (tipo == "citacao" and s.get("fundo") == "escuro")
                self.seco = True
                r_ok, folga = 0, -1.0
                for r in range(0, 4):
                    folga = fn(None, s, r)
                    r_ok = r
                    if folga >= -0.005:
                        break
                self.seco = False
                self._fonte_figura = None
                sl = self.novo_slide(escuro)
                fn(sl, s, r_ok)
                if r_ok > 0 and folga >= -0.005:
                    self.aviso(f"texto reduzido em {r_ok} pt para caber. Se puder, corte palavras.")
                if folga < -0.005:
                    passa = f"{abs(folga):.2f}".replace(".", ",")
                    self.aviso(f"o conteúdo não cabe no slide nem com a fonte reduzida (passa {passa} pol do limite). "
                               "Corte texto ou divida em dois slides.", "erro")
                fonte = None
                if tipo == "figura":
                    cit = self._fonte_figura
                    extra = self.texto_fonte(s)
                    fonte = "; ".join(x for x in (cit, extra) if x) or ""
                    if not cit:
                        self.aviso("figura sem citação completa: preencha 'citacao' no catálogo ou em figura.citacao.", "erro")
                if tipo != "capa":
                    self.rodape(sl, s, escuro, fonte)
                self.notas(sl, s)
            except Exception as e:  # um slide com problema nao derruba o deck
                self.seco = False
                self.aviso(f"falha ao montar este slide ({type(e).__name__}: {e}).", "erro")

    def salvar(self, saida: Path) -> None:
        cp = self.prs.core_properties
        cp.title = M.sem_marcacao(self.meta.get("titulo") or "Aula Boost Education")
        cp.author = self.meta.get("autor") or "Boost Education"
        cp.language = "pt-BR"
        cp.keywords = "Boost Education"
        saida.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(saida))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Monta o .pptx da aula Boost a partir do deck.json.")
    ap.add_argument("deck", help="caminho do deck.json")
    ap.add_argument("-o", "--saida", help="arquivo .pptx de saída (padrão: <slug>.pptx ao lado do deck.json)")
    ap.add_argument("--estrito", action="store_true", help="não gera o .pptx se a validação tiver erros")
    ap.add_argument("--sem-validar", action="store_true", help="pula a validação pedagógica (só para rascunho)")
    ap.add_argument("--sem-linha-do-tempo", action="store_true", help="não imprime a linha do tempo")
    a = ap.parse_args(argv)

    caminho = Path(a.deck).expanduser().resolve()
    deck = M.carregar_json(caminho)
    if not isinstance(deck, dict) or not isinstance(deck.get("slides"), list):
        M.sair("o deck.json precisa ser um objeto com a lista 'slides'. Veja references/deck-json.md.")
    base = caminho.parent
    meta = deck.get("meta") or {}
    saida = Path(a.saida).expanduser().resolve() if a.saida else base / f"{meta.get('slug') or caminho.stem}.pptx"

    erros_val: list[str] = []
    if not a.sem_validar:
        import validar_aula
        rel = validar_aula.validar(deck, base)
        validar_aula.imprimir(rel, linha_do_tempo=not a.sem_linha_do_tempo)
        erros_val = rel["erros"]
        if erros_val and a.estrito:
            print("\nModo estrito: o .pptx não foi gerado. Corrija os erros acima.")
            return 1

    c = Construtor(copy.deepcopy(deck), base)
    c.montar()
    c.salvar(saida)

    print("\n== Montagem ==")
    print(f"Fonte usada para medir o texto: {c.med.familia}" + ("" if c.med.familia == "Lato" else
          " (Lato não está instalada aqui; as medidas ficam do lado seguro e o arquivo continua pedindo Lato)"))
    erros_lay = [x for x in c.avisos if x[1] == "erro"]
    for n, nivel, msg in c.avisos:
        print(f"  [{nivel.upper()}] slide {n}: {msg}")
    if not c.avisos:
        print("  Nenhum texto reduzido ou fora da caixa.")
    print(f"\nArquivo: {saida}")
    print(f"Slides: {c.n_slides_pptx} | tempo previsto: {M.relogio(c.acumulado)} min")
    print("Próximo passo: python renderizar.py <arquivo.pptx> e olhar cada PNG antes de entregar.")
    if erros_val or erros_lay:
        print(f"\nATENÇÃO: {len(erros_val)} erro(s) de validação e {len(erros_lay)} erro(s) de layout. "
              "O arquivo foi gerado para você ver, mas não está pronto para entrega.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
