"""Análise de layout de PDF científico para a skill boost-leitura-figuras.

Transforma as palavras de cada página em linhas, segmentos e blocos; detecta duas
colunas, cabeçalhos/rodapés repetidos, texto corrido ("corpo") e legendas de figuras
e tabelas. Também reúne os utilitários de imagem (render, grade, folha de contato).

Coordenadas: pontos PDF (1/72 pol) com origem no canto superior esquerdo da página
como ela é vista (x para a direita, y para baixo) — o mesmo sistema das miniaturas.
"""
from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------


@dataclass
class Seg:
    """Trecho contínuo de uma linha visual (uma célula de tabela ou uma linha de coluna)."""
    x0: float
    x1: float
    top: float
    bottom: float
    texto: str
    tam: float
    fonte: str
    negrito: bool          # a primeira palavra está em negrito
    n_pal: int
    linha: int = -1        # índice da linha visual
    lado: str = "U"        # E, D (colunas), L (atravessa a calha) ou U (coluna única)
    sozinho: bool = True   # único segmento da sua linha visual no seu lado
    de_corpo: bool = False
    margem: bool = False   # cabeçalho/rodapé repetido
    bloco: int = -1

    @property
    def largura(self) -> float:
        return self.x1 - self.x0


@dataclass
class Bloco:
    segs: list[Seg]
    tipo: str = "solto"    # corpo | solto | legenda

    @property
    def x0(self): return min(s.x0 for s in self.segs)
    @property
    def x1(self): return max(s.x1 for s in self.segs)
    @property
    def top(self): return min(s.top for s in self.segs)
    @property
    def bottom(self): return max(s.bottom for s in self.segs)
    @property
    def bbox(self): return (self.x0, self.top, self.x1, self.bottom)


@dataclass
class Legenda:
    tipo: str              # figura | tabela
    rotulo: str            # "Figure 2", "Table 1"
    numero: str
    pagina: int            # 1 = primeira
    bbox: tuple[float, float, float, float]
    texto: str
    forte: bool            # negrito/fonte diferente do corpo (legenda quase certa)
    continuacao: bool = False
    lado: str = "U"


@dataclass
class PaginaLayout:
    numero: int
    largura: float
    altura: float
    segs: list[Seg] = field(default_factory=list)
    blocos: list[Bloco] = field(default_factory=list)
    legendas: list[Legenda] = field(default_factory=list)
    calha: float | None = None           # x do centro da calha, se duas colunas
    y_cab: float = 0.0                   # tudo acima é cabeçalho repetido
    y_rod: float = 0.0                   # tudo abaixo é rodapé repetido (0 = não há)
    faixas_laterais: list[tuple[float, float, float, float]] = field(default_factory=list)
    caixas: list[tuple[float, float, float, float]] = field(default_factory=list)
    imagens: list[dict] = field(default_factory=list)
    frac_girado: float = 0.0             # fração das palavras que estão giradas
    n_palavras: int = 0


# --------------------------------------------------------------------------
# Padrões
# --------------------------------------------------------------------------

RE_LEGENDA = re.compile(
    r"^\s*(?:(?:Supplementary|Supplemental|Suppl\.?|Online|Appendix|Extended\s+Data)\s+)?"
    r"(?P<nome>Figure|Figura|Fig|Table|Tabela|Tab|Quadro|Scheme|Chart|Graph|Gr[aá]fico|Plate)"
    r"(?P<ponto>\.?)(?:\s+|(?=\d))(?P<num>[A-Z]?\d{1,3}[A-Za-z]?|[IVXL]{1,6})(?![\w])"
    r"(?P<sep>\s*[.:|—–-]?)\s*(?P<resto>.*)$",
    re.I | re.S)

RE_LEGENDA_SEM_NUM = re.compile(
    r"^\s*(?P<nome>Figure|Figura|Table|Tabela)(?P<ponto>)(?P<num>)(?P<sep>\s*[.:|])\s+(?P<resto>[A-Z].*)$", re.S)
RE_ESPACADO = re.compile(r"^\s*((?:[A-Z] ){3,}[A-Z])(?=\s|$)")


def casar_legenda(texto: str):
    """Reconhece o rótulo de legenda no começo de uma linha, inclusive com letras espaçadas
    ("F I G U R E 1", estilo Wiley) e figura única sem número ("Figure. Flow diagram...")."""
    t = texto or ""
    m = RE_ESPACADO.match(t)
    if m:
        t = t[:m.start(1)] + m.group(1).replace(" ", "") + t[m.end(1):]
    return RE_LEGENDA.match(t) or RE_LEGENDA_SEM_NUM.match(t)


RE_MENCAO = re.compile(
    r"^(shows?|showed|presents?|illustrates?|depicts?|demonstrates?|summari[sz]es?|displays?|provides?|"
    r"lists?|compares?|and|or|are|is|was|were|in|for|to|of|also|which|that|below|above|"
    r"mostra|apresenta|ilustra|resume|e|ou)\b|^[),;\]]", re.I)

RE_NEGRITO = re.compile(r"(bold|black|heavy|semibold|demi|medium|[-.,_]b(d|old)?$|[-.,_]bi$|\.b$)", re.I)

TIPOS_TABELA = ("tab", "quadro")
ZONA_CAB, ZONA_ROD = 0.11, 0.90   # frações da altura onde moram cabeçalho e rodapé


def normalizar(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def _e_negrito(fonte: str) -> bool:
    return bool(RE_NEGRITO.search(fonte or ""))


def _familia(fonte: str) -> str:
    f = (fonte or "").split("+")[-1]
    return re.split(r"[-,.]", f)[0].lower()


def reparar_hifens(t: str) -> str:
    """Conserta dois defeitos comuns do texto de PDFs de editoras: 'self-a dministered' e 'VISA- P'."""
    t = re.sub(r"(?<=[A-Za-z])-([a-z]) (?=[a-z])", r"-\1", t)
    t = re.sub(r"(?<=[A-Za-z])- (?=[A-Z0-9]\b)", "-", t)
    t = re.sub(r"(?<=[a-z])- (?!(?:and|or|e|ou)\b)(?=[a-z])", "-", t)   # "tendon- loading"; preserva "pre- and post-"
    return t


def juntar_linhas(linhas: list[str]) -> str:
    """Junta linhas de um parágrafo desfazendo a hifenização de fim de linha."""
    manter = {"meta", "non", "self", "cross", "well", "follow", "long", "short", "high", "low", "double",
              "single", "evidence", "patient", "pre", "post", "co", "anti", "intra", "inter", "mid", "sub",
              "between", "within", "dose", "time", "load", "pain", "sport", "exercise", "placebo", "sham",
              "intention", "per", "one", "two", "three", "four", "six", "first", "second", "third"}
    saida = ""
    for ln in linhas:
        ln = ln.strip()
        if not ln:
            continue
        if not saida:
            saida = ln
            continue
        m = re.search(r"([A-Za-zÀ-ÿ]+)-$", saida)
        if m and ln[:1].islower():
            if m.group(1).lower() in manter or re.match(r"(based|up|related|reported|term|blind|blinded|"
                                                        r"specific|week|month|year|day|point|to|treat)\b", ln):
                saida += ln
            else:
                saida = saida[:-1] + ln
        elif m and ln[:1].isupper():
            saida += ln
        else:
            saida += " " + ln
    return reparar_hifens(saida)


# --------------------------------------------------------------------------
# Leitura da página (pdfplumber)
# --------------------------------------------------------------------------


def tem_espacos(pdf, amostra: int = 5) -> bool:
    """O PDF grava o espaço entre palavras como caractere? (decidido pelo documento, não pela página)"""
    total = espacos = 0
    for page in pdf.pages[:amostra]:
        chars = page.chars
        total += len(chars)
        espacos += sum(1 for c in chars if c.get("text") == " ")
    return total > 0 and espacos / total > 0.05


def extrair_palavras(page, extras: list[str], com_espacos: bool) -> list[dict]:
    """Palavras da página. PDFs que gravam o espaço como caractere usam a tolerância padrão;
    os que só afastam as letras (PLOS, MDPI, Frontiers, Elsevier...) precisam de uma tolerância
    proporcional ao corpo da letra, senão as palavras saem grudadas."""
    if com_espacos:
        return page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False,
                                  use_text_flow=False, extra_attrs=extras)
    return page.extract_words(x_tolerance_ratio=0.13, y_tolerance=3, keep_blank_chars=False,
                              use_text_flow=False, extra_attrs=extras)


def _linhas_visuais(palavras: list[dict]) -> list[list[dict]]:
    linhas: list[dict] = []   # {top, bottom, itens}
    for w in sorted(palavras, key=lambda w: (w["top"], w["x0"])):
        h = max(w["bottom"] - w["top"], 0.5)
        melhor, melhor_sob = None, 0.0
        for ln in reversed(linhas[-12:]):
            sob = min(ln["bottom"], w["bottom"]) - max(ln["top"], w["top"])
            hl = max(ln["bottom"] - ln["top"], 0.5)
            if sob >= 0.5 * min(h, hl) and sob > melhor_sob:
                melhor, melhor_sob = ln, sob
        if melhor is None:
            linhas.append({"top": w["top"], "bottom": w["bottom"], "itens": [w]})
        else:
            melhor["itens"].append(w)
            # a faixa da linha é a das palavras de tamanho normal (expoentes não deslocam)
            if h >= 0.8 * (melhor["bottom"] - melhor["top"]):
                melhor["top"] = min(melhor["top"], w["top"])
                melhor["bottom"] = max(melhor["bottom"], w["bottom"])
    saida = [sorted(ln["itens"], key=lambda w: w["x0"]) for ln in linhas]
    saida.sort(key=lambda it: (min(w["top"] for w in it)))
    return saida


def _achar_calha(linhas: list[list[dict]], largura: float) -> tuple[float | None, int]:
    """Procura uma faixa vertical vazia perto do centro com texto dos dois lados."""
    if len(linhas) < 12:
        return None, 0
    votos = Counter()
    for it in linhas:
        for a, b in zip(it, it[1:]):
            g0, g1 = a["x1"], b["x0"]
            if g1 - g0 < 6:
                continue
            esq = a["x1"] - it[0]["x0"]
            dire = it[-1]["x1"] - b["x0"]
            if esq < 60 or dire < 60:
                continue
            lo, hi = max(g0 + 2, 0.36 * largura), min(g1 - 2, 0.64 * largura)
            x = lo
            while x <= hi:
                votos[round(x)] += 1
                x += 1.0
    if not votos:
        return None, 0
    melhor_n = max(votos.values())
    xs = [x for x, n in votos.items() if n >= 0.9 * melhor_n]
    return (min(xs) + max(xs)) / 2.0, melhor_n


def _segmentar(linhas: list[list[dict]], calha: float | None) -> list[Seg]:
    segs: list[Seg] = []
    for i, it in enumerate(linhas):
        grupos, atual = [], [it[0]]
        for a, b in zip(it, it[1:]):
            gap = b["x0"] - a["x1"]
            tam = max(a.get("size") or 8.0, b.get("size") or 8.0)
            cortar = gap > max(1.5 * tam, 10.0)
            if not cortar and calha is not None and gap >= 6.0 and a["x1"] <= calha + 1 and b["x0"] >= calha - 1:
                cortar = True
            if cortar:
                grupos.append(atual)
                atual = [b]
            else:
                atual.append(b)
        grupos.append(atual)
        for g in grupos:
            tamanhos = [w.get("size") or 0 for w in g if (w.get("size") or 0) > 0]
            fontes = Counter(w.get("fontname") or "" for w in g)
            alturas = sorted(w["bottom"] - w["top"] for w in g)
            h_ref = alturas[len(alturas) // 2]
            normais = [w for w in g if (w["bottom"] - w["top"]) >= 0.75 * h_ref] or g
            x0, x1 = g[0]["x0"], max(w["x1"] for w in g)
            if calha is None:
                lado = "U"
            elif x1 <= calha + 2:
                lado = "E"
            elif x0 >= calha - 2:
                lado = "D"
            else:
                lado = "L"
            segs.append(Seg(x0=x0, x1=x1, top=min(w["top"] for w in normais),
                            bottom=max(w["bottom"] for w in normais),
                            texto=" ".join(w["text"] for w in g),
                            tam=statistics.median(tamanhos) if tamanhos else 8.0,
                            fonte=fontes.most_common(1)[0][0],
                            negrito=_e_negrito(g[0].get("fontname") or ""),
                            n_pal=len(g), linha=i, lado=lado))
    por_linha: dict[tuple[int, str], int] = Counter()
    for s in segs:
        por_linha[(s.linha, "E" if s.lado == "E" else "D" if s.lado == "D" else "X")] += 1
    conta_linha = Counter(s.linha for s in segs)
    for s in segs:
        if s.lado in ("E", "D"):
            s.sozinho = por_linha[(s.linha, s.lado)] == 1 and por_linha.get((s.linha, "X"), 0) == 0
        else:
            s.sozinho = conta_linha[s.linha] == 1
    return segs


class DocLayout:
    """Layout de um PDF inteiro. Use: doc = DocLayout(caminho); doc.paginas[i]."""

    def __init__(self, caminho: str | Path, max_paginas: int | None = None):
        import pdfplumber

        self.caminho = Path(caminho)
        self.paginas: list[PaginaLayout] = []
        self.avisos: list[str] = []
        self._brutas: list[list[list[dict]]] = []
        self._giradas: list[list[dict]] = []
        try:
            visor = abrir_pdfium(self.caminho)   # para descartar texto invisível (camadas ocultas)
        except Exception:
            visor = None
        with pdfplumber.open(str(self.caminho)) as pdf:
            self._com_espacos = tem_espacos(pdf)
            for i, page in enumerate(pdf.pages):
                if max_paginas and i >= max_paginas:
                    break
                self._ler_pagina(i, page, visor)
                try:
                    page.close()
                except Exception:
                    pass
        if visor is not None:
            visor.close()
        self._estatisticas()
        self._margens_repetidas()
        for pag in self.paginas:
            self._blocos(pag)
            self._legendas(pag)
        self._deduplicar_legendas()

    # -- leitura ------------------------------------------------------------

    def _ler_pagina(self, i: int, page, visor=None) -> None:
        try:
            # pdfium desenha a CropBox; as coordenadas do pdfplumber partem da mesma origem da bbox da página
            dx, dy = float(page.cropbox[0]), float(page.cropbox[1])
            largura = float(page.cropbox[2]) - dx
            altura = float(page.cropbox[3]) - dy
        except Exception:
            largura, altura, dx, dy = float(page.width), float(page.height), 0.0, 0.0
        pag = PaginaLayout(numero=i + 1, largura=largura, altura=altura)
        try:
            palavras = extrair_palavras(page, ["fontname", "size", "upright"], self._com_espacos)
        except Exception as e:
            self.avisos.append(f"p.{i + 1}: não consegui ler o texto ({type(e).__name__})")
            palavras = []
        cinza = None
        if visor is not None and palavras:
            try:
                import numpy as np

                cinza = np.asarray(render_pagina(visor, i, 108.0, cinza=True))
                if abs(cinza.shape[1] - largura * 1.5) > 3 or abs(cinza.shape[0] - altura * 1.5) > 3:
                    cinza = None   # geometria diferente (página girada): não arrisca
            except Exception:
                cinza = None
        retas, giradas = [], []
        ocultas = 0
        for w in palavras:
            w["x0"] -= dx; w["x1"] -= dx; w["top"] -= dy; w["bottom"] -= dy
            if not (w.get("text") or "").strip():
                continue
            if w["x1"] < 0 or w["x0"] > largura or w["bottom"] < 0 or w["top"] > altura:
                continue
            if cinza is not None:
                a, b = max(int(w["top"] * 1.5), 0), min(int(w["bottom"] * 1.5) + 1, cinza.shape[0])
                c, d = max(int(w["x0"] * 1.5), 0), min(int(w["x1"] * 1.5) + 1, cinza.shape[1])
                if b > a and d > c and int(cinza[a:b, c:d].min()) >= 215:
                    ocultas += 1
                    continue   # nenhuma tinta sob a palavra: texto oculto (camada de rascunho, OCR, marca d'água)
            (retas if w.get("upright", True) else giradas).append(w)
        pag.n_palavras = len(retas) + len(giradas)
        pag.frac_girado = len(giradas) / pag.n_palavras if pag.n_palavras else 0.0
        try:
            for r in page.rects:
                w_, h_ = r["x1"] - r["x0"], r["bottom"] - r["top"]
                if r.get("stroke") and 30 < w_ < 0.92 * largura and 14 < h_ < 0.7 * altura:
                    pag.caixas.append((r["x0"] - dx, r["top"] - dy, r["x1"] - dx, r["bottom"] - dy))
            for im in page.images:
                src = im.get("srcsize") or (0, 0)
                pag.imagens.append({"bbox": (im["x0"] - dx, im["top"] - dy, im["x1"] - dx, im["bottom"] - dy),
                                    "px": (int(src[0] or 0), int(src[1] or 0))})
        except Exception:
            pass
        self.paginas.append(pag)
        self._brutas.append(_linhas_visuais(retas))
        self._giradas.append(giradas)

    # -- estatísticas do documento -----------------------------------------

    def _estatisticas(self) -> None:
        calhas = []
        for pag, linhas in zip(self.paginas, self._brutas):
            x, n = _achar_calha(linhas, pag.largura)
            if x is not None and n >= max(8, 0.3 * len(linhas)):
                pag.calha = x
                calhas.append(x)
        com_texto = [p for p, l in zip(self.paginas, self._brutas) if len(l) >= 15]
        self.duas_colunas = bool(com_texto) and len(calhas) >= max(2, 0.35 * len(com_texto))
        if self.duas_colunas:
            for paridade in (0, 1):
                xs = [p.calha for p in self.paginas if p.calha is not None and p.numero % 2 == paridade]
                ref = statistics.median(xs) if xs else statistics.median(calhas)
                for p in self.paginas:
                    if p.numero % 2 == paridade and p.calha is None:
                        p.calha = ref
        else:
            for p in self.paginas:
                p.calha = None
        tam_fonte, larguras = Counter(), Counter()
        for pag, linhas in zip(self.paginas, self._brutas):
            pag.segs = _segmentar(linhas, pag.calha) if linhas else []
            for s in pag.segs:
                tam_fonte[(s.fonte, round(s.tam, 1))] += len(s.texto)
                if s.n_pal >= 6:
                    larguras[round(s.largura / 4.0) * 4] += 1
        self.fonte_corpo, self.tam_corpo = (tam_fonte.most_common(1)[0][0] if tam_fonte else ("", 9.0))
        if larguras:
            # largura de coluna = a largura mais frequente entre as linhas longas (pico e vizinhos)
            pico = max(larguras, key=lambda k: larguras[k] + larguras.get(k - 4, 0) + larguras.get(k + 4, 0))
            self.larg_corpo = float(pico)
        else:
            self.larg_corpo = 0.0

    def _margens_repetidas(self) -> None:
        n = len(self.paginas)
        if n < 3:
            return

        def norm(t: str) -> str:
            return re.sub(r"\s+", " ", re.sub(r"\d+", "#", t.lower())).strip()

        cont_cab, cont_rod = Counter(), Counter()
        for pag in self.paginas:
            vistos = set()
            for s in pag.segs:
                chave = norm(s.texto)
                if len(chave) < 1:
                    continue
                if casar_legenda(s.texto):
                    continue
                if s.bottom < ZONA_CAB * pag.altura and ("c", chave) not in vistos:
                    cont_cab[chave] += 1; vistos.add(("c", chave))
                elif s.top > ZONA_ROD * pag.altura and ("r", chave) not in vistos:
                    cont_rod[chave] += 1; vistos.add(("r", chave))
        minimo = max(2 if n < 6 else 3, round(0.25 * n))
        rep_cab = {k for k, v in cont_cab.items() if v >= minimo}
        rep_rod = {k for k, v in cont_rod.items() if v >= minimo}
        for pag in self.paginas:
            y_cab, y_rod = 0.0, 0.0
            for s in pag.segs:
                chave = norm(s.texto)
                eh_num = bool(re.fullmatch(r"(page |p\. ?|página )?#+( of #+| de #+)?", chave))
                if casar_legenda(s.texto):
                    continue
                if s.bottom < ZONA_CAB * pag.altura and (chave in rep_cab or eh_num):
                    s.margem = True
                    y_cab = max(y_cab, s.bottom)
                elif s.top > ZONA_ROD * pag.altura and (chave in rep_rod or eh_num):
                    s.margem = True
                    y_rod = min(y_rod, s.top) if y_rod else s.top
            # tudo que está acima do cabeçalho repetido, ou abaixo do rodapé, também é margem
            for s in pag.segs:
                if casar_legenda(s.texto):
                    continue
                if (y_cab and s.bottom <= y_cab + 1) or (y_rod and s.top >= y_rod - 1):
                    s.margem = True
            pag.y_cab, pag.y_rod = y_cab, y_rod
        # faixas laterais giradas que se repetem (ex.: "Downloaded from ... Protected by copyright")
        cont = Counter()
        for pag, gir in zip(self.paginas, self._giradas):
            for t in {norm(w["text"]) for w in gir if w["x0"] > 0.9 * pag.largura or w["x1"] < 0.1 * pag.largura}:
                cont[t] += 1
        rep = {k for k, v in cont.items() if v >= max(3, round(0.3 * n))}
        for pag, gir in zip(self.paginas, self._giradas):
            for lado in ("dir", "esq"):
                ws = [w for w in gir if norm(w["text"]) in rep and
                      ((w["x0"] > 0.9 * pag.largura) if lado == "dir" else (w["x1"] < 0.1 * pag.largura))]
                if ws:
                    pag.faixas_laterais.append((min(w["x0"] for w in ws) - 2, 0.0,
                                                max(w["x1"] for w in ws) + 2, pag.altura))

    # -- blocos e corpo ------------------------------------------------------

    def _bordas_esquerdas(self, pag: PaginaLayout) -> dict[str, float]:
        bordas = {}
        for lado in ("E", "D", "U", "L"):
            xs = Counter(round(s.x0) for s in pag.segs
                         if s.lado == lado and not s.margem and s.largura >= 0.6 * self.larg_corpo and s.n_pal >= 5)
            if xs and xs.most_common(1)[0][1] >= 3:
                bordas[lado] = float(xs.most_common(1)[0][0])
        return bordas

    def _blocos(self, pag: PaginaLayout) -> None:
        bordas = self._bordas_esquerdas(pag)
        larg = self.larg_corpo or 200.0
        for s in pag.segs:
            if s.margem:
                continue
            largo = s.largura >= 0.72 * larg
            borda = bordas.get(s.lado)
            na_borda = borda is None or (borda - 3 <= s.x0 <= borda + 26)
            s.de_corpo = bool(largo and s.sozinho and s.n_pal >= 5 and na_borda)
        abertos: list[Bloco] = []
        blocos: list[Bloco] = []
        for s in sorted((s for s in pag.segs if not s.margem), key=lambda s: (s.top, s.x0)):
            melhor, melhor_sob = None, 0.0
            for b in abertos:
                u = b.segs[-1]
                if u.linha == s.linha or u.sozinho != s.sozinho:
                    continue
                if u.lado != s.lado and not ("L" in (u.lado, s.lado) and abs(b.x0 - s.x0) <= 3.0):
                    continue  # lados diferentes só se juntam na última linha curta de um parágrafo largo
                gap = s.top - u.bottom
                if gap < -2.5 or gap > 0.62 * max(s.tam, u.tam, 6.0):
                    continue
                if abs(s.tam - u.tam) > 0.9:
                    continue
                sob = min(b.x1, s.x1) - max(b.x0, s.x0)
                if sob < 0.5 * min(s.largura, b.x1 - b.x0):
                    continue
                if sob > melhor_sob:
                    melhor, melhor_sob = b, sob
            if melhor is None:
                melhor = Bloco(segs=[s])
                blocos.append(melhor)
                abertos.append(melhor)
            else:
                melhor.segs.append(s)
            abertos = [b for b in abertos if s.top - b.segs[-1].bottom < 40]
        for b in blocos:
            n = len(b.segs)
            corpo = [s.de_corpo for s in b.segs]
            if n >= 2:
                # a última linha de um parágrafo costuma ser curta: não conta contra
                base = corpo[:-1] if (not corpo[-1] and corpo[-2]) else corpo
                eh_corpo = sum(base) / len(base) >= 0.6 and (sum(corpo) >= 2 or (n == 2 and b.segs[1].sozinho))
            else:
                s = b.segs[0]
                eh_corpo = s.de_corpo and abs(s.tam - self.tam_corpo) <= 0.4 and _familia(s.fonte) == _familia(self.fonte_corpo)
            if not eh_corpo:
                # resto de parágrafo que veio da página anterior, título de seção: fonte do corpo na borda da coluna
                borda = bordas.get(b.segs[0].lado)
                if borda is not None and sum(x.n_pal for x in b.segs) >= 2 and all(
                        x.sozinho and abs(x.tam - self.tam_corpo) <= 0.3
                        and _familia(x.fonte) == _familia(self.fonte_corpo)
                        and borda - 3 <= x.x0 <= borda + 26 for x in b.segs):
                    eh_corpo = True
            if eh_corpo and self._dentro_de_caixa(pag, b):
                eh_corpo = False
            b.tipo = "corpo" if eh_corpo else "solto"
        blocos.sort(key=lambda b: (b.top, b.x0))
        for i, b in enumerate(blocos):
            for s in b.segs:
                s.bloco = i
        pag.blocos = blocos

    @staticmethod
    def _dentro_de_caixa(pag: PaginaLayout, b: Bloco) -> bool:
        x0, t, x1, bt = b.bbox
        for cx0, ct, cx1, cb in pag.caixas:
            if cx0 - 2 <= x0 and x1 <= cx1 + 2 and ct - 2 <= t and bt <= cb + 2:
                return True
        return False

    # -- legendas ------------------------------------------------------------

    def _legendas(self, pag: PaginaLayout) -> None:
        novos: list[Bloco] = []
        for b in list(pag.blocos):
            inicio = None
            for k, s in enumerate(b.segs):
                m = casar_legenda(s.texto)
                if not m:
                    continue
                if not self._parece_legenda(s, m, b, k):
                    continue
                inicio = k
                break
            if inicio is None:
                continue
            if inicio > 0:  # separa o que vinha antes (texto corrido colado à legenda)
                antes = Bloco(segs=b.segs[:inicio], tipo=b.tipo)
                novos.append(antes)
                b.segs = b.segs[inicio:]
            # uma segunda legenda dentro do mesmo bloco encerra a primeira
            for k in range(1, len(b.segs)):
                m2 = casar_legenda(b.segs[k].texto)
                if m2 and self._parece_legenda(b.segs[k], m2, b, k) and b.segs[k].negrito:
                    resto = Bloco(segs=b.segs[k:], tipo="solto")
                    b.segs = b.segs[:k]
                    pag.blocos.append(resto)
                    break
            b.tipo = "legenda"
        pag.blocos.extend(novos)
        pag.blocos.sort(key=lambda b: (b.top, b.x0))
        # legendas recém-criadas por divisão de bloco
        for b in pag.blocos:
            if b.tipo != "legenda":
                m = casar_legenda(b.segs[0].texto)
                if m and b.segs[0].negrito and self._parece_legenda(b.segs[0], m, b, 0):
                    b.tipo = "legenda"
        for b in pag.blocos:
            if b.tipo != "legenda":
                continue
            s0 = b.segs[0]
            m = casar_legenda(s0.texto)
            # continua em blocos logo abaixo com a mesma fonte (quando não é a fonte do corpo)
            partes = [b]
            atual = b
            while True:
                ult = atual.segs[-1]
                prox = None
                for c in pag.blocos:
                    if c is atual or c.tipo == "legenda" or c in partes:
                        continue
                    p = c.segs[0]
                    gap = p.top - ult.bottom
                    if not (-1 <= gap <= 1.0 * max(ult.tam, 6)):
                        continue
                    mesmo_lado = p.lado == ult.lado or ("L" in (p.lado, ult.lado) and abs(c.x0 - atual.x0) <= 3.0)
                    if not mesmo_lado or abs(p.tam - ult.tam) > 0.3 or _familia(p.fonte) != _familia(ult.fonte):
                        continue
                    if abs(p.tam - self.tam_corpo) <= 0.3 and _familia(p.fonte) == _familia(self.fonte_corpo):
                        continue
                    sob = min(c.x1, atual.x1) - max(c.x0, atual.x0)
                    if sob < 0.5 * min(c.x1 - c.x0, atual.x1 - atual.x0):
                        continue
                    if casar_legenda(p.texto) and p.negrito:
                        continue
                    if not all(x.sozinho for x in c.segs):
                        continue  # células de tabela logo abaixo do título não são legenda
                    prox = c
                    break
                if prox is None or (max(x.bottom for x in partes) - b.top) > 0.3 * pag.altura:
                    break
                prox.tipo = "legenda_cont"
                partes.append(prox)
                atual = prox
            segs = [s for p in partes for s in p.segs]
            segs.sort(key=lambda s: (s.top, s.x0))
            texto = juntar_linhas([s.texto for s in segs])
            me = RE_ESPACADO.match(texto)
            if me:
                texto = texto[:me.start(1)] + me.group(1).replace(" ", "") + texto[me.end(1):]
            nome = m.group("nome").lower()
            tipo = "tabela" if nome.startswith(TIPOS_TABELA) else "figura"
            nome_pad = {"fig": "Figure", "figure": "Figure", "figura": "Figura", "table": "Table", "tab": "Table",
                        "tabela": "Tabela", "quadro": "Quadro"}.get(nome, m.group("nome").capitalize())
            sup = "S" if re.match(r"\s*(supp|online|appendix|extended)", s0.texto, re.I) and not m.group("num").upper().startswith("S") else ""
            numero = sup + m.group("num")
            cont = bool(re.search(r"\b(continued|cont\.|continua[çc][ãa]o|continuação)\b", texto[:80], re.I))
            forte = s0.negrito or abs(s0.tam - self.tam_corpo) > 0.4 or _familia(s0.fonte) != _familia(self.fonte_corpo)
            x0 = min(s.x0 for s in segs); x1 = max(s.x1 for s in segs)
            top = min(s.top for s in segs); bottom = max(s.bottom for s in segs)
            if pag.calha is not None and x1 <= pag.calha + 2:
                # legenda curta composta em duas colunas: o resto começa na mesma altura, do outro lado
                for c in pag.blocos:
                    p0 = c.segs[0]
                    if c.tipo in ("legenda", "legenda_cont") or p0.lado != "D" or abs(c.top - top) > 3:
                        continue
                    if abs(p0.tam - s0.tam) > 0.3 or (abs(p0.tam - self.tam_corpo) <= 0.3
                                                      and _familia(p0.fonte) == _familia(self.fonte_corpo)):
                        continue
                    if c.bottom > bottom + 1.6 * s0.tam or casar_legenda(p0.texto):
                        continue
                    c.tipo = "legenda_cont"
                    texto = juntar_linhas([texto] + [x.texto for x in sorted(c.segs, key=lambda x: x.top)])
                    x1 = max(x1, c.x1); bottom = max(bottom, c.bottom)
                    break
            if any(l.rotulo == f"{nome_pad} {numero}".strip() and abs(l.bbox[1] - top) < 40
                   and normalizar(l.texto)[:60] == normalizar(texto)[:60] for l in pag.legendas):
                continue  # mesma legenda desenhada duas vezes (camada de texto duplicada)
            if pag.calha is None:
                lado = "U"
            elif x1 <= pag.calha + 2:
                lado = "E"
            elif x0 >= pag.calha - 2:
                lado = "D"
            else:
                lado = "L"
            pag.legendas.append(Legenda(tipo=tipo, rotulo=f"{nome_pad} {numero}".strip(), numero=numero, pagina=pag.numero,
                                        bbox=(x0, top, x1, bottom), texto=texto, forte=forte,
                                        continuacao=cont, lado=lado))
        for b in pag.blocos:
            if b.tipo == "legenda_cont":
                b.tipo = "legenda"
        pag.legendas.sort(key=lambda l: (l.bbox[1], l.bbox[0]))

    def _parece_legenda(self, s: Seg, m: re.Match, b: Bloco, k: int) -> bool:
        resto = (m.group("resto") or "").strip()
        sep = (m.group("sep") or "").strip()
        if RE_MENCAO.match(resto) and not sep:
            return False
        if resto[:1] and resto[:1] in "),;]":
            return False
        difere = abs(s.tam - self.tam_corpo) > 0.4 or _familia(s.fonte) != _familia(self.fonte_corpo)
        if not m.group("num"):   # figura única sem número: só com destaque tipográfico e no início do bloco
            return k == 0 and (s.negrito or difere)
        if m.group("nome").isupper() and k == 0 and not resto[:1].islower():
            return True          # "TABLE 1", "FIGURE 2": caixa alta só aparece em legenda
        if s.negrito:
            return k == 0 or not b.segs[k - 1].negrito
        if k > 0:
            return False  # no meio de um parágrafo, sem negrito: é menção no texto
        if difere:
            return not (resto[:1].islower() and not sep)
        # mesma fonte do corpo: exige pontuação depois do número, ou rótulo sozinho na linha
        return (not resto) or (bool(sep) and resto[:1].isupper())

    def _deduplicar_legendas(self) -> None:
        """Se o mesmo rótulo aparece duas vezes, fica a legenda mais forte (a outra é menção)."""
        vistos: dict[tuple[str, str], list[Legenda]] = {}
        for pag in self.paginas:
            for leg in pag.legendas:
                vistos.setdefault((leg.tipo, leg.numero.lower()), []).append(leg)
        descartar = set()
        for legs in vistos.values():
            fortes = [l for l in legs if l.forte]
            if fortes and len(fortes) < len(legs):
                for l in legs:
                    if not l.forte and not l.continuacao:
                        descartar.add(id(l))
        if descartar:
            for pag in self.paginas:
                removidas = [l for l in pag.legendas if id(l) in descartar]
                pag.legendas = [l for l in pag.legendas if id(l) not in descartar]
                for l in removidas:
                    for b in pag.blocos:
                        if b.tipo == "legenda" and abs(b.top - l.bbox[1]) < 1 and abs(b.x0 - l.bbox[0]) < 1:
                            b.tipo = "corpo"

    @property
    def legendas(self) -> list[Legenda]:
        return [l for p in self.paginas for l in p.legendas]


# --------------------------------------------------------------------------
# Texto em ordem de leitura
# --------------------------------------------------------------------------

SECOES = [
    ("RESUMO", r"abstract|resumo|summary"),
    ("INTRODUÇÃO", r"introduction|background|introdu[cç][aã]o"),
    ("MÉTODOS", r"methods?|materials?\s+and\s+methods?|methods?\s+and\s+materials?|patients\s+and\s+methods|"
                r"participants\s+and\s+methods|subjects\s+and\s+methods|methodology|m[eé]todos?|"
                r"materiais?\s+e\s+m[eé]todos?"),
    ("RESULTADOS", r"results?|findings|resultados?"),
    ("DISCUSSÃO", r"discussion|discuss[aã]o|results\s+and\s+discussion|comment"),
    ("CONCLUSÃO", r"conclusions?|conclus[aã]o|conclus[oõ]es|concluding\s+remarks"),
    ("REFERÊNCIAS", r"references?|refer[eê]ncias|bibliography|literature\s+cited"),
]
RE_SECAO = [(nome, re.compile(rf"^\s*(?:\d{{1,2}}(?:\.\d{{1,2}})*\.?\s+|[IVX]{{1,4}}\.\s+)?(?:{pad})\s*[:.]?\s*$", re.I))
            for nome, pad in SECOES]


def secao_de(texto: str) -> str | None:
    t = texto.strip()
    if len(t) > 40:
        return None
    for nome, rx in RE_SECAO:
        if rx.match(t):
            return nome
    return None


def _separar_lateral(faixa: list[Seg]) -> list[list[Seg]]:
    """Separa uma coluna lateral independente (afiliações ao lado do resumo, notas de margem).

    Linhas de tabela também têm vários trechos por linha, mas na mesma letra; aqui os dois lados
    têm corpos de letra diferentes, sinal de que são textos independentes e devem ser lidos um
    depois do outro, não intercalados.
    """
    por_linha: dict[int, list[Seg]] = {}
    for s_ in faixa:
        por_linha.setdefault(s_.linha, []).append(s_)
    multi = [sorted(v, key=lambda x: x.x0) for v in por_linha.values() if len(v) == 2]
    if len(multi) < 6:
        return [faixa]
    votos = Counter()
    for a_, b_ in multi:
        for x in range(int(a_.x1) + 1, int(b_.x0)):
            votos[x] += 1
    if not votos:
        return [faixa]
    x_corte, n = votos.most_common(1)[0]
    if n < 0.8 * len(multi):
        return [faixa]
    esq = [s_ for s_ in faixa if s_.x1 <= x_corte + 1]
    dire = [s_ for s_ in faixa if s_.x0 >= x_corte - 1]
    if len(esq) + len(dire) < 0.95 * len(faixa) or len(esq) < 5 or len(dire) < 5:
        return [faixa]
    if abs(statistics.median(s_.tam for s_ in esq) - statistics.median(s_.tam for s_ in dire)) <= 0.8:
        return [faixa]
    resto = [s_ for s_ in faixa if s_ not in esq and s_ not in dire]
    chave = lambda s_: (s_.top, s_.x0)   # noqa: E731
    lateral, principal = (esq, dire) if statistics.median(s_.tam for s_ in esq) < statistics.median(s_.tam for s_ in dire) else (dire, esq)
    return [p_ for p_ in (sorted(resto, key=chave), sorted(principal, key=chave), sorted(lateral, key=chave)) if p_]


def texto_ordenado(doc: DocLayout, pag: PaginaLayout) -> list[dict]:
    """Devolve a página como lista de parágrafos em ordem de leitura.

    Cada item: {"tipo": "p" | "secao" | "legenda" | "linha", "texto": ..., "secao": nome}.
    Em duas colunas: tudo o que atravessa a calha separa faixas; em cada faixa, lê a coluna
    esquerda inteira e depois a direita.
    """
    segs = [s for s in pag.segs if not s.margem]
    if not segs:
        return []
    faixas: list[list[Seg]] = []
    if pag.calha is None:
        faixas = [sorted(segs, key=lambda s: (s.linha, s.x0))]
    else:
        largos = sorted([s for s in segs if s.lado == "L"], key=lambda s: s.top)
        cortes = [0.0]
        for s in largos:
            cortes.append(s.top - 0.1)
        cortes.append(pag.altura + 1)
        for a, b in zip(cortes, cortes[1:]):
            dentro = [s for s in segs if a <= s.top < b]
            if not dentro:
                continue
            l_ = sorted([s for s in dentro if s.lado == "L"], key=lambda s: (s.linha, s.x0))
            e_ = sorted([s for s in dentro if s.lado == "E"], key=lambda s: (s.top, s.x0))
            d_ = sorted([s for s in dentro if s.lado == "D"], key=lambda s: (s.top, s.x0))
            # linhas largas consecutivas ficam juntas na frente da faixa
            if l_:
                faixas.append(l_)
            if e_:
                faixas.append(e_)
            if d_:
                faixas.append(d_)
    faixas = [parte for f in faixas for parte in _separar_lateral(f)]
    itens: list[dict] = []
    mapa_tipo = {}
    for b in pag.blocos:
        for s in b.segs:
            mapa_tipo[id(s)] = b.tipo
    for faixa in faixas:
        # agrupa por linha visual (células de tabela na mesma linha ficam juntas)
        linhas: list[list[Seg]] = []
        for s in faixa:
            if linhas and linhas[-1][-1].linha == s.linha:
                linhas[-1].append(s)
            else:
                linhas.append([s])
        par: list[str] = []
        par_tipo = "p"
        ult: Seg | None = None

        def fechar():
            nonlocal par, par_tipo
            if par:
                itens.append({"tipo": par_tipo, "texto": juntar_linhas(par)})
            par, par_tipo = [], "p"

        for ln in linhas:
            s0 = ln[0]
            if len(ln) > 1:  # linha de tabela ou rótulos soltos
                fechar()
                itens.append({"tipo": "linha", "texto": "  |  ".join(s.texto for s in ln)})
                ult = None
                continue
            sec = secao_de(s0.texto)
            if sec and s0.n_pal <= 5:
                isolado = not (0 <= s0.bloco < len(pag.blocos)) or len(pag.blocos[s0.bloco].segs) == 1
                destaque = (s0.negrito or s0.texto.isupper() or s0.tam > doc.tam_corpo + 0.3
                            or _familia(s0.fonte) != _familia(doc.fonte_corpo) or isolado)
            else:
                destaque = False
            if sec and destaque:
                fechar()
                itens.append({"tipo": "secao", "texto": s0.texto.strip(), "secao": sec})
                ult = None
                continue
            tipo = "legenda" if mapa_tipo.get(id(s0)) == "legenda" else "p"
            folga = 1.3 if tipo == "legenda" else 0.62   # legendas costumam ter entrelinha mais aberta
            novo = ult is None or tipo != par_tipo or (s0.top - ult.bottom) > folga * max(s0.tam, ult.tam, 6.0) \
                or abs(s0.tam - ult.tam) > 0.9 or s0.top < ult.top - 2
            if tipo == "legenda" and casar_legenda(s0.texto) and (s0.negrito or s0.texto[:5].isupper()):
                novo = True
            if novo:
                fechar()
                par_tipo = tipo
            par.append(s0.texto)
            ult = s0
        fechar()
    return itens


# --------------------------------------------------------------------------
# Imagem: render, grade, folha de contato
# --------------------------------------------------------------------------


def abrir_pdfium(caminho: str | Path):
    import pypdfium2 as pdfium

    return pdfium.PdfDocument(str(caminho))


def render_pagina(doc_pdfium, indice: int, dpi: float = 100.0, cinza: bool = False):
    """Renderiza a página (índice a partir de 0) e devolve uma imagem PIL."""
    page = doc_pdfium[indice]
    try:
        bitmap = page.render(scale=dpi / 72.0, grayscale=cinza)
        img = bitmap.to_pil()
    finally:
        page.close()
    if img.mode not in ("RGB", "L"):
        img = img.convert("L" if cinza else "RGB")
    return img


def tamanho_pagina(doc_pdfium, indice: int) -> tuple[float, float]:
    page = doc_pdfium[indice]
    try:
        return page.get_size()
    finally:
        page.close()


_FONTES_CACHE: dict = {}


def fonte(tamanho: int, negrito: bool = False):
    from PIL import ImageFont

    chave = (tamanho, negrito)
    if chave in _FONTES_CACHE:
        return _FONTES_CACHE[chave]
    nomes = (["Inter-Bold.otf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf"]
             if negrito else
             ["Inter-Regular.otf", "DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "LiberationSans-Regular.ttf"])
    f = None
    for nome in nomes:
        try:
            f = ImageFont.truetype(nome, tamanho)
            break
        except Exception:
            continue
    if f is None:
        try:
            f = ImageFont.load_default(size=tamanho)
        except TypeError:
            f = ImageFont.load_default()
    _FONTES_CACHE[chave] = f
    return f


def desenhar_grade(img, caixas: list[tuple[tuple[float, float, float, float], str, tuple[int, int, int]]] | None = None,
                   escala: float = 1.0, fino: bool = False):
    """Cópia da miniatura com régua de frações (0,1 a 0,9) e, se houver, caixas rotuladas.

    'caixas' em pontos PDF; 'escala' = pixels por ponto da miniatura.
    """
    from PIL import ImageDraw

    borda = 34
    w, h = img.size
    tela = img.convert("RGB").copy()
    from PIL import Image

    base = Image.new("RGB", (w + borda, h + borda), (255, 255, 255))
    base.paste(tela, (borda, borda))
    d = ImageDraw.Draw(base, "RGBA")
    f = fonte(15, True)
    for i in range(1, 20):
        fr = i / 20.0
        x, y = borda + round(fr * w), borda + round(fr * h)
        forte = i % 2 == 0
        cor = (0, 122, 153, 90 if forte else 38)
        d.line([(x, borda), (x, borda + h)], fill=cor, width=1)
        d.line([(borda, y), (borda + w, y)], fill=cor, width=1)
        if forte:
            rot = f"{fr:.1f}".replace(".", ",")
            d.text((x - 10, 8), rot, fill=(0, 90, 120, 255), font=f)
            d.text((3, y - 9), rot, fill=(0, 90, 120, 255), font=f)
    d.rectangle([borda, borda, borda + w - 1, borda + h - 1], outline=(0, 122, 153, 160), width=1)
    for (x0, y0, x1, y1), rotulo, cor in (caixas or []):
        r = [borda + x0 * escala, borda + y0 * escala, borda + x1 * escala, borda + y1 * escala]
        d.rectangle(r, outline=cor + (255,), width=3 if (rotulo or not fino) else 1)
        if rotulo:
            tw = d.textlength(rotulo, font=f)
            d.rectangle([r[0], r[1] - 20, r[0] + tw + 8, r[1]], fill=cor + (255,))
            d.text((r[0] + 4, r[1] - 19), rotulo, fill=(255, 255, 255, 255), font=f)
    return base


def folha_contato(itens: list[dict], destino: Path, titulo: str = "", colunas: int = 4,
                  celula: tuple[int, int] = (430, 330), por_folha: int = 24) -> list[Path]:
    """Monta folha(s) de contato. Cada item: {"img": caminho, "numero": n, "linhas": [texto, ...],
    "cor": (r,g,b) opcional para a etiqueta}. Devolve os caminhos gravados."""
    from PIL import Image, ImageDraw

    saidas: list[Path] = []
    if not itens:
        return saidas
    cw, ch = celula
    texto_h = 62
    margem = 14
    paginas = [itens[i:i + por_folha] for i in range(0, len(itens), por_folha)]
    for n_folha, grupo in enumerate(paginas, 1):
        linhas = (len(grupo) + colunas - 1) // colunas
        topo = 46 if titulo else margem
        W = margem + colunas * (cw + margem)
        H = topo + linhas * (ch + texto_h + margem)
        folha = Image.new("RGB", (W, H), (247, 249, 250))
        d = ImageDraw.Draw(folha)
        if titulo:
            sufixo = f"  ({n_folha}/{len(paginas)})" if len(paginas) > 1 else ""
            d.text((margem, 12), titulo + sufixo, fill=(32, 32, 129), font=fonte(22, True))
        for k, it in enumerate(grupo):
            col, lin = k % colunas, k // colunas
            x = margem + col * (cw + margem)
            y = topo + lin * (ch + texto_h + margem)
            d.rectangle([x, y, x + cw, y + ch], fill=(255, 255, 255), outline=(213, 221, 226))
            try:
                with Image.open(it["img"]) as im:
                    im = im.convert("RGB")
                    im.thumbnail((cw - 12, ch - 12), Image.LANCZOS)
                    folha.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2))
            except Exception:
                d.text((x + 10, y + 10), "(imagem não encontrada)", fill=(178, 58, 58), font=fonte(15))
            cor = tuple(it.get("cor") or (0, 122, 153))
            etiqueta = str(it.get("numero", k + 1))
            tw = d.textlength(etiqueta, font=fonte(20, True))
            d.rectangle([x, y, x + tw + 16, y + 30], fill=cor)
            d.text((x + 8, y + 3), etiqueta, fill=(255, 255, 255), font=fonte(20, True))
            for j, ln in enumerate((it.get("linhas") or [])[:3]):
                f = fonte(15, j == 0)
                while d.textlength(ln, font=f) > cw and len(ln) > 8:
                    ln = ln[:-5].rstrip() + "…"
                d.text((x + 2, y + ch + 4 + j * 19), ln, fill=(20, 26, 26) if j == 0 else (75, 83, 88), font=f)
        caminho = destino if len(paginas) == 1 or n_folha == 1 else destino.with_name(
            f"{destino.stem}_{n_folha}{destino.suffix}")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        folha.save(caminho)
        saidas.append(caminho)
    return saidas


def aparar_branco(img, margem_px: int = 16, limiar: int = 245):
    """Remove as bordas brancas. Devolve (imagem, (esq, topo, dir, base) cortados em px)."""
    import numpy as np

    a = np.asarray(img.convert("L"))
    tinta = a < limiar
    if not tinta.any():
        return img, (0, 0, 0, 0)
    ys = np.where(tinta.any(axis=1))[0]
    xs = np.where(tinta.any(axis=0))[0]
    x0 = max(int(xs[0]) - margem_px, 0)
    y0 = max(int(ys[0]) - margem_px, 0)
    x1 = min(int(xs[-1]) + 1 + margem_px, img.width)
    y1 = min(int(ys[-1]) + 1 + margem_px, img.height)
    return img.crop((x0, y0, x1, y1)), (x0, y0, img.width - x1, img.height - y1)


def dpi_nativo(pag: PaginaLayout, bbox: tuple[float, float, float, float]) -> float | None:
    """Resolução real da imagem embutida que domina a região (None se a figura é vetorial)."""
    x0, y0, x1, y1 = bbox
    area = max((x1 - x0) * (y1 - y0), 1.0)
    melhor = None
    for im in pag.imagens:
        ix0, iy0, ix1, iy1 = im["bbox"]
        sob = max(0.0, min(x1, ix1) - max(x0, ix0)) * max(0.0, min(y1, iy1) - max(y0, iy0))
        if sob / area >= 0.35 and im["px"][0] > 0 and (ix1 - ix0) > 1:
            d = im["px"][0] / ((ix1 - ix0) / 72.0)
            melhor = d if melhor is None else max(melhor, d)
    return round(melhor, 0) if melhor else None


# --------------------------------------------------------------------------
# Controle de qualidade de um recorte
# --------------------------------------------------------------------------

CAIXA_INTEIRO = (11.5, 5.0)   # área útil de um slide 16:9 (pol), abaixo do título
CAIXA_MEIO = (5.6, 4.6)       # metade do slide, ao lado de texto
DPI_BOM, DPI_MINIMO = 150, 110


def palavras_da_pagina(caminho: str | Path, pagina: int) -> list[dict]:
    """Palavras de uma página (1 = primeira), em pontos com origem no canto superior esquerdo."""
    import pdfplumber

    try:
        with pdfplumber.open(str(caminho)) as pdf:
            page = pdf.pages[pagina - 1]
            dx, dy = float(page.cropbox[0]), float(page.cropbox[1])
            ws = extrair_palavras(page, ["upright"], tem_espacos(pdf))
            return [{"x0": w["x0"] - dx, "x1": w["x1"] - dx, "top": w["top"] - dy, "bottom": w["bottom"] - dy,
                     "text": w["text"] if w.get("upright", True) else w["text"][::-1]}
                    for w in ws if (w.get("text") or "").strip()]
    except Exception:
        return []


def avaliar_recorte(img, bbox_pt=None, palavras: list[dict] | None = None, dpi: float = 300.0,
                    nativo: float | None = None, apagadas: list | None = None) -> dict:
    """Mede um recorte: resolução útil no slide, branco, conteúdo na borda, proporção.

    Devolve {"cabe", "dpi_slide_inteiro", "dpi_meio_slide", "branco", "erros": [...], "avisos": [...]}.
    """
    import numpy as np

    w, h = img.size
    a = np.asarray(img.convert("L"))
    erros: list[str] = []
    avisos: list[str] = []
    fator = min(1.0, (nativo / dpi)) if nativo and dpi else 1.0   # imagem embutida mais pobre que o recorte
    we, he = w * fator, h * fator
    dpi_int = max(we / CAIXA_INTEIRO[0], he / CAIXA_INTEIRO[1])
    dpi_meio = max(we / CAIXA_MEIO[0], he / CAIXA_MEIO[1])
    if dpi_int >= DPI_MINIMO:
        cabe = "slide inteiro"
    elif dpi_meio >= DPI_MINIMO:
        cabe = "meio slide"
    else:
        cabe = "pequena"
        if fator < 1.0:
            erros.append(f"imagem pequena no próprio PDF (~{int(we)}×{int(he)} px reais, {int(nativo)} dpi): fica borrada "
                         f"mesmo em meio slide (~{int(dpi_meio)} dpi úteis; mínimo {DPI_MINIMO}). Usar pequena, como detalhe, "
                         "ou buscar a figura original na página do artigo")
        else:
            erros.append(f"resolução baixa até para meio slide (~{int(dpi_meio)} dpi úteis; mínimo {DPI_MINIMO}): "
                         "recortar de novo com --dpi maior (600)")
    if cabe != "pequena" and fator < 1.0 and nativo:
        avisos.append(f"a imagem embutida no PDF tem ~{int(nativo)} dpi: aumentar o --dpi do recorte não melhora a nitidez")
    branco = float((a >= 245).mean())
    if branco > 0.97:
        erros.append("recorte quase todo em branco: a caixa não pegou a figura")
    else:
        tinta = a < 245
        ys = np.where(tinta.any(axis=1))[0]
        xs = np.where(tinta.any(axis=0))[0]
        sobras = {"esquerda": xs[0] / w, "direita": (w - 1 - xs[-1]) / w, "topo": ys[0] / h, "base": (h - 1 - ys[-1]) / h}
        grandes = [k for k, v in sobras.items() if v > 0.12]
        if grandes:
            avisos.append("sobra de branco (" + ", ".join(grandes) + "): refazer com --aparar")
    t = max(2, int(round(dpi / 150)))
    faixas = {"topo": a[:t, :], "base": a[-t:, :], "esquerda": a[:, :t], "direita": a[:, -t:]}
    encostado = [k for k, f in faixas.items() if float((f < 190).mean()) > 0.012]
    cortadas: list[str] = []
    if bbox_pt and palavras:
        x0, y0, x1, y1 = bbox_pt
        for p in palavras:
            ix = min(p["x1"], x1) - max(p["x0"], x0)
            iy = min(p["bottom"], y1) - max(p["top"], y0)
            if ix <= 0.8 or iy <= 0.8:
                continue
            fora_x = max(x0 - p["x0"], p["x1"] - x1)
            fora_y = max(y0 - p["top"], p["bottom"] - y1)
            if fora_x > 1.2 or fora_y > 1.5:
                cx, cy = (max(p["x0"], x0) + min(p["x1"], x1)) / 2, (max(p["top"], y0) + min(p["bottom"], y1)) / 2
                if any(r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for r in (apagadas or [])):
                    continue
                cortadas.append(p["text"])
    if cortadas:
        amostra = ", ".join(repr(c) for c in cortadas[:4])
        erros.append(f"texto cortado pela borda do recorte ({amostra}{'…' if len(cortadas) > 4 else ''}): "
                     "abrir a caixa ou apagar esse trecho com --apagar")
    elif encostado:
        avisos.append("conteúdo encostado na borda (" + ", ".join(encostado) + "): conferir se nada foi cortado")
    prop = w / max(h, 1)
    if prop > 3.2:
        avisos.append(f"muito larga e baixa (proporção {prop:.1f}:1): no slide 16:9 fica uma faixa fina; "
                      "considere dividir em painéis")
    elif prop < 0.45:
        avisos.append(f"muito alta e estreita (proporção 1:{1 / prop:.1f}): no slide 16:9 as letras ficam miúdas; "
                      "considere recortar só a parte que ensina")
    return {"cabe": cabe, "dpi_slide_inteiro": int(dpi_int), "dpi_meio_slide": int(dpi_meio),
            "branco": round(branco, 3), "erros": erros, "avisos": avisos}


def dpi_nativo_pdf(caminho: str | Path, pagina: int, bbox: tuple[float, float, float, float]) -> float | None:
    """Como dpi_nativo, lendo direto do PDF (para recortes manuais)."""
    import pdfplumber

    try:
        with pdfplumber.open(str(caminho)) as pdf:
            page = pdf.pages[pagina - 1]
            dx, dy = float(page.cropbox[0]), float(page.cropbox[1])
            falso = PaginaLayout(numero=pagina, largura=float(page.width), altura=float(page.height))
            for im in page.images:
                src = im.get("srcsize") or (0, 0)
                falso.imagens.append({"bbox": (im["x0"] - dx, im["top"] - dy, im["x1"] - dx, im["bottom"] - dy),
                                      "px": (int(src[0] or 0), int(src[1] or 0))})
            return dpi_nativo(falso, bbox)
    except Exception:
        return None


def encaixar_em_palavras(bbox, palavras: list[dict], larg: float, alt: float, ignorar: list | None = None):
    """Ajusta a caixa para não cortar palavra ao meio: a palavra que está mais dentro do que fora
    entra inteira; a que está mais fora sai inteira (se isso não cortar outra que entrou).
    A decisão de cada palavra é tomada uma vez, sobre a caixa original. Devolve (caixa, houve_ajuste)."""
    ox0, oy0, ox1, oy1 = bbox
    entram, saem = [], []
    for p in palavras:
        ix = min(p["x1"], ox1) - max(p["x0"], ox0)
        iy = min(p["bottom"], oy1) - max(p["top"], oy0)
        if ix <= 0.3 or iy <= 0.3:
            continue
        if p["x0"] >= ox0 - 0.3 and p["x1"] <= ox1 + 0.3 and p["top"] >= oy0 - 0.3 and p["bottom"] <= oy1 + 0.3:
            continue
        cx, cy = (p["x0"] + p["x1"]) / 2, (p["top"] + p["bottom"]) / 2
        if any(r[0] <= cx <= r[2] and r[1] <= cy <= r[3] for r in (ignorar or [])):
            continue
        area = max((p["x1"] - p["x0"]) * (p["bottom"] - p["top"]), 0.01)
        (entram if ix * iy / area >= 0.5 else saem).append(p)
    x0, y0, x1, y1 = ox0, oy0, ox1, oy1
    for p in entram:
        x0, y0 = min(x0, p["x0"] - 1.0), min(y0, p["top"] - 1.0)
        x1, y1 = max(x1, p["x1"] + 1.0), max(y1, p["bottom"] + 1.0)
    dentro = [p for p in palavras if p["x0"] >= x0 - 0.3 and p["x1"] <= x1 + 0.3
              and p["top"] >= y0 - 0.3 and p["bottom"] <= y1 + 0.3]
    for p in saem:
        if min(p["x1"], x1) - max(p["x0"], x0) <= 0.3 or min(p["bottom"], y1) - max(p["top"], y0) <= 0.3:
            continue
        opcoes = []
        if p["x0"] < x0: opcoes.append((p["x1"] - x0, "x0", p["x1"] + 0.6))
        if p["x1"] > x1: opcoes.append((x1 - p["x0"], "x1", p["x0"] - 0.6))
        if p["top"] < y0: opcoes.append((p["bottom"] - y0, "y0", p["bottom"] + 0.6))
        if p["bottom"] > y1: opcoes.append((y1 - p["top"], "y1", p["top"] - 0.6))
        for _, lado, valor in sorted(opcoes):
            nx0, ny0, nx1, ny1 = (valor if lado == "x0" else x0, valor if lado == "y0" else y0,
                                  valor if lado == "x1" else x1, valor if lado == "y1" else y1)
            corta = any(min(q["x1"], nx1) - max(q["x0"], nx0) < (q["x1"] - q["x0"]) - 0.4
                        or min(q["bottom"], ny1) - max(q["top"], ny0) < (q["bottom"] - q["top"]) - 0.4
                        for q in dentro if q is not p)
            if not corta:
                x0, y0, x1, y1 = nx0, ny0, nx1, ny1
                break
    caixa = (max(x0, 0.0), max(y0, 0.0), min(x1, larg), min(y1, alt))
    if caixa[2] - caixa[0] < 5 or caixa[3] - caixa[1] < 5:
        return tuple(bbox), False
    mudou = any(abs(a_ - b_) > 0.05 for a_, b_ in zip(caixa, bbox))
    return caixa, mudou
