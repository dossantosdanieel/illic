#!/usr/bin/env python3
"""Gera miniaturas de todas as páginas e propõe recortes de figuras e tabelas.

Para cada PDF de 02_artigos/pdf/:
  1. grava 03_figuras/paginas/<chave>/pNNN.png (miniatura limpa), pNNN_grade.png (a mesma
     página com régua de frações e as caixas propostas) e _visao_geral.png (todas as páginas);
  2. localiza as legendas ("Figure 2", "Fig. 2", "FIGURE 2 |", "Table 1", "Tabela 1"...),
     estima a região da figura (o que há entre a legenda e o texto corrido, respeitando a
     coluna) ou da tabela (entre os fios horizontais) e recorta a 300 dpi, sem e com a legenda;
  3. registra cada candidato em 03_figuras/catalogo.json com origem "auto" e aprovada false,
     e monta a folha de contato numerada 03_figuras/<chave>/_candidatos.png.

O resultado é uma PROPOSTA. Olhe a folha de contato e as miniaturas antes de aprovar
qualquer recorte; ajuste com recortar.py.

Uso:
  python3 detectar_figuras.py AULA
  python3 detectar_figuras.py AULA --apenas Breda2021 --dpi 300
  python3 detectar_figuras.py AULA --so-miniaturas
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402
import _pdf as P  # noqa: E402

ESCALA_ANALISE = 2.0   # px por ponto na análise (144 dpi)
LIMIAR_TINTA = 235


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------
# Máscaras de tinta
# --------------------------------------------------------------------------


def _px(v: float, s: float) -> int:
    return int(round(v * s))


def apagar(mask, bbox, s: float, folga: float = 1.0) -> None:
    x0, y0, x1, y1 = bbox
    h, w = mask.shape
    a, b = max(_px(y0 - folga, s), 0), min(_px(y1 + folga, s), h)
    c, d = max(_px(x0 - folga, s), 0), min(_px(x1 + folga, s), w)
    if b > a and d > c:
        mask[a:b, c:d] = False


def caixa_tinta(mask, regiao, s: float):
    """Menor caixa (em pontos) que contém a tinta dentro da região; None se vazia."""
    import numpy as np

    x0, y0, x1, y1 = regiao
    h, w = mask.shape
    a, b = max(_px(y0, s), 0), min(_px(y1, s), h)
    c, d = max(_px(x0, s), 0), min(_px(x1, s), w)
    if b - a < 2 or d - c < 2:
        return None, 0.0
    sub = mask[a:b, c:d]
    lin = np.where(sub.sum(axis=1) >= 1)[0]
    col = np.where(sub.sum(axis=0) >= 1)[0]
    if len(lin) == 0 or len(col) == 0:
        return None, 0.0
    caixa = ((c + col[0]) / s, (a + lin[0]) / s, (c + col[-1] + 1) / s, (a + lin[-1] + 1) / s)
    return caixa, float(sub.mean())


def achar_fios(tinta, s: float, comp_min: float = 70.0) -> list[tuple[float, float, float, float]]:
    """Fios horizontais longos (réguas de tabela): lista de (x0, y0, x1, y1) em pontos."""
    import numpy as np

    h, w = tinta.shape
    L = int(comp_min * s)
    if w <= L + 2:
        return []
    c = np.cumsum(tinta, axis=1, dtype=np.int32)
    c = np.concatenate([np.zeros((h, 1), np.int32), c], axis=1)
    cheio = (c[:, L:] - c[:, :-L]) >= int(0.985 * L)
    linhas = np.where(cheio.any(axis=1))[0]
    trechos = []  # (y, x0, x1) em px
    for y in linhas:
        xs = np.where(cheio[y])[0]
        cortes = np.where(np.diff(xs) > int(10 * s))[0]
        ini = 0
        for k in list(cortes) + [len(xs) - 1]:
            trechos.append((int(y), int(xs[ini]), int(xs[k]) + L))
            ini = k + 1
    fios: list[list[float]] = []  # x0, y0, x1, y1 px
    for y, x0, x1 in trechos:
        for f in reversed(fios[-8:]):
            if y - f[3] <= 1 and min(x1, f[2]) - max(x0, f[0]) >= 0.7 * min(x1 - x0, f[2] - f[0]):
                f[0], f[2], f[3] = min(f[0], x0), max(f[2], x1), y
                break
        else:
            fios.append([x0, y, x1, y])
    return [(f[0] / s, f[1] / s, f[2] / s, (f[3] + 1) / s) for f in fios]


# --------------------------------------------------------------------------
# Regiões
# --------------------------------------------------------------------------


def _faixa(pag: P.PaginaLayout, lado: str) -> tuple[float, float]:
    x_min, x_max = 6.0, pag.largura - 6.0
    for fx0, _, fx1, _ in pag.faixas_laterais:
        if fx0 > pag.largura / 2:
            x_max = min(x_max, fx0 - 2)
        else:
            x_min = max(x_min, fx1 + 2)
    if pag.calha is None or lado in ("L", "U"):
        return x_min, x_max
    return (x_min, pag.calha) if lado == "E" else (pag.calha, x_max)


def _bloqueios(pag: P.PaginaLayout, leg: P.Legenda) -> list[tuple[float, float, float, float, str]]:
    saida = []
    for b in pag.blocos:
        if b.tipo not in ("corpo", "legenda"):
            continue
        x0, t, x1, bt = b.bbox
        lx0, lt, lx1, lb = leg.bbox
        if b.tipo == "legenda" and t >= lt - 1 and bt <= lb + 1 and x0 >= lx0 - 1 and x1 <= lx1 + 1:
            continue  # é a própria legenda
        saida.append((x0, t, x1, bt, b.tipo))
    return saida


def _sobrepoe_x(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def regiao_vizinha(pag: P.PaginaLayout, leg: P.Legenda, residual, s: float, direcao: str):
    """Região com tinta entre a legenda e o texto corrido, acima ('cima') ou abaixo ('baixo')."""
    lx0, lt, lx1, lb = leg.bbox
    topo_pag = pag.y_cab + 1 if pag.y_cab else 8.0
    base_pag = pag.y_rod - 1 if pag.y_rod else pag.altura - 8.0
    bloqueios = _bloqueios(pag, leg)

    def calcular(lado: str):
        fx0, fx1 = _faixa(pag, lado)
        if direcao == "cima":
            limite = topo_pag
            for x0, t, x1, bt, _ in bloqueios:
                if bt <= lt + 2 and _sobrepoe_x(x0, x1, fx0, fx1) > min(20.0, 0.3 * (x1 - x0)):
                    limite = max(limite, bt)
            regiao = (fx0, limite + 0.5, fx1, lt - 0.5)
        else:
            limite = base_pag
            for x0, t, x1, bt, _ in bloqueios:
                if t >= lb - 2 and _sobrepoe_x(x0, x1, fx0, fx1) > min(20.0, 0.3 * (x1 - x0)):
                    limite = min(limite, t)
            regiao = (fx0, lb + 0.5, fx1, limite - 0.5)
        caixa, dens = caixa_tinta(residual, regiao, s)
        return caixa, dens, regiao

    lado = leg.lado
    caixa, dens, regiao = calcular(lado)
    alargou = False
    if lado in ("E", "D") and pag.calha is not None:
        outro = "D" if lado == "E" else "E"
        if caixa is not None:
            # a tinta atravessa a calha? então a figura ocupa as duas colunas
            faixa_calha = (pag.calha - 2.5, caixa[1], pag.calha + 2.5, caixa[3])
            cruz, _ = caixa_tinta(residual, faixa_calha, s)
            atravessa = cruz is not None and (cruz[3] - cruz[1]) >= max(4.0, 0.04 * (caixa[3] - caixa[1]))
            if not atravessa:
                # painel solto na outra coluna, na mesma altura, sem texto corrido nem legenda própria
                ox0, ox1 = _faixa(pag, outro)
                viz, _ = caixa_tinta(residual, (ox0, caixa[1], ox1, caixa[3]), s)
                if viz is not None and (viz[3] - viz[1]) >= 0.5 * (caixa[3] - caixa[1]):
                    ocupado = any(_sobrepoe_x(x0, x1, ox0, ox1) > 20 and min(bt, caixa[3]) - max(t, caixa[1]) > 12
                                  for x0, t, x1, bt, tp in bloqueios if tp == "corpo")
                    dona = any(l is not leg and l.lado == outro and caixa[1] - 5 <= l.bbox[1] <= lb + 80
                               for l in pag.legendas)
                    atravessa = not ocupado and not dona
            if atravessa:
                c2, d2, r2 = calcular("L")
                if c2 is not None and (c2[2] - c2[0]) > (caixa[2] - caixa[0]) + 20:
                    caixa, dens, regiao, alargou = c2, d2, r2, True
        elif direcao == "cima":
            # nada na coluna da legenda: a figura pode estar inteira na largura da página
            c2, d2, r2 = calcular("L")
            if c2 is not None:
                caixa, dens, regiao, alargou = c2, d2, r2, True
    return caixa, dens, regiao, alargou


def _valida(caixa, min_alt: float = 28.0, min_larg: float = 45.0) -> bool:
    return caixa is not None and (caixa[3] - caixa[1]) >= min_alt and (caixa[2] - caixa[0]) >= min_larg


def soltar_texto_da_borda(pag: P.PaginaLayout, residual, caixa, regiao, s: float):
    """Se o limite da região cortou uma linha de texto (a caixa encosta no limite e uma linha
    atravessa essa borda), recua a borda para fora dessa linha. Evita meia linha de texto
    corrido no topo ou na base do recorte (visto em BMJ e Springer)."""
    for _ in range(3):
        x0, y0, x1, y1 = caixa
        novo = None
        for sg in pag.segs:
            if sg.margem or _sobrepoe_x(sg.x0, sg.x1, x0, x1) < 3:
                continue
            # a linha pode terminar logo antes da borda e só as descendentes passarem dela
            if abs(y0 - regiao[1]) <= 1.5 and sg.top < y0 - 0.8 and sg.bottom > y0 - 2.5:
                novo = (x0, max(sg.bottom, y0) + 2.0, x1, y1)
                break
            if abs(y1 - regiao[3]) <= 1.5 and sg.top < y1 + 1.5 and sg.bottom > y1 + 0.8:
                novo = (x0, y0, x1, sg.top - 0.6)
                break
        if novo is None:
            return caixa, regiao
        c2, _ = caixa_tinta(residual, novo, s)
        if not _valida(c2):
            return caixa, regiao
        regiao = (regiao[0], max(regiao[1], novo[1]), regiao[2], min(regiao[3], novo[3]))
        caixa = c2
    return caixa, regiao


def regiao_figura(pag, leg, residual, s):
    caixa, dens, regiao, alargou = regiao_vizinha(pag, leg, residual, s, "cima")
    avisos = []
    if not _valida(caixa):
        c2, d2, r2, a2 = regiao_vizinha(pag, leg, residual, s, "baixo")
        if _valida(c2):
            caixa, dens, regiao, alargou = c2, d2, r2, a2
            lx0, lt, lx1, lb = leg.bbox
            # legenda ao lado, alinhada pelo topo (Springer): a figura começa na altura do topo
            # da legenda, à direita dela. Sem isto o topo da figura sai cortado.
            lado_cx, _ = caixa_tinta(residual, (max(lx1 + 2, regiao[0]), lt - 1, regiao[2], lb + 0.5), s)
            if (lado_cx is not None and (lx1 - lx0) < 0.4 * pag.largura
                    and lado_cx[3] >= lb - 1 and lado_cx[0] >= lx1 - 1):
                caixa = (min(caixa[0], lado_cx[0]), lado_cx[1], max(caixa[2], lado_cx[2]), caixa[3])
                regiao = (regiao[0], lt - 1, regiao[2], regiao[3])
                avisos.append("legenda ao lado da figura: conferir topo e laterais")
            else:
                avisos.append("figura abaixo da legenda (incomum): conferir")
        else:
            return None, ["não achei conteúdo gráfico junto à legenda"]
    caixa, regiao = soltar_texto_da_borda(pag, residual, caixa, regiao, s)
    return (caixa, regiao), avisos


def regiao_tabela(doc: P.DocLayout, pag, leg, tinta, residual, fios, s, exigir_fios: bool = False):
    lx0, lt, lx1, lb = leg.bbox
    base_pag = pag.y_rod - 1 if pag.y_rod else pag.altura - 8.0
    avisos: list[str] = []
    # fios abaixo da legenda
    abaixo = sorted([f for f in fios if f[1] >= lt + 6], key=lambda f: f[1])
    primeiro = None
    for f in abaixo:
        if f[1] > lb + 48:
            break
        perto = abs(f[0] - lx0) <= 45 or _sobrepoe_x(f[0], f[2], lx0, lx1) >= 0.3 * min(f[2] - f[0], lx1 - lx0)
        if perto:
            primeiro = f
            break
    if primeiro is not None:
        tx0, tx1 = primeiro[0], primeiro[2]
        # o fio mais largo logo em seguida define a largura (o primeiro pode ser parcial)
        for f in abaixo:
            if primeiro[1] <= f[1] <= primeiro[1] + 60 and _sobrepoe_x(f[0], f[2], tx0, tx1) > 0.5 * (tx1 - tx0):
                tx0, tx1 = min(tx0, f[0]), max(tx1, f[2])
        cheios = [f for f in abaixo if f[1] >= primeiro[1] and
                  _sobrepoe_x(f[0], f[2], tx0, tx1) >= 0.6 * (tx1 - tx0)]
        outras = [l for l in pag.legendas if l is not leg]
        ultimo = cheios[0] if cheios else primeiro
        for f in cheios[1:]:
            zona = (tx0, ultimo[3], tx1, f[1])
            if any(l.bbox[1] >= zona[1] - 1 and l.bbox[3] <= zona[3] + 1 and
                   _sobrepoe_x(l.bbox[0], l.bbox[2], tx0, tx1) > 10 for l in outras):
                break
            corrido = 0
            for b in pag.blocos:
                if b.tipo != "corpo" or len(b.segs) < 3:
                    continue
                if b.top >= zona[1] - 1 and b.bottom <= zona[3] + 1 and b.x0 <= tx0 + 30 \
                        and _sobrepoe_x(b.x0, b.x1, tx0, tx1) > 0.5 * (b.x1 - b.x0) \
                        and (b.x1 - b.x0) >= 0.72 * min(doc.larg_corpo or 200.0, tx1 - tx0):
                    corrido += len(b.segs)
            if corrido >= 3:
                break
            ultimo = f
        topo = lb + 0.5
        # tabela sem fio de fechamento: se abaixo do último fio ainda há linhas com várias células, ela continua
        limite = base_pag
        for l in outras:
            if l.bbox[1] > ultimo[3] and _sobrepoe_x(l.bbox[0], l.bbox[2], tx0, tx1) > 10:
                limite = min(limite, l.bbox[1] - 1)
        for b in pag.blocos:
            if b.tipo == "corpo" and b.top > ultimo[3] and len(b.segs) >= 2 and b.x0 <= tx0 + 30 \
                    and _sobrepoe_x(b.x0, b.x1, tx0, tx1) > 0.5 * (b.x1 - b.x0):
                limite = min(limite, b.top - 1)
        aberta = None
        linhas_multi: dict[int, list] = {}
        for x in pag.segs:
            if not x.margem and ultimo[3] - 1 <= x.top < limite and _sobrepoe_x(x.x0, x.x1, tx0, tx1) > 0.5 * (x.x1 - x.x0):
                linhas_multi.setdefault(x.linha, []).append(x)
        multi = sorted((v for v in linhas_multi.values() if len(v) >= 2), key=lambda v: v[0].top)
        if len(multi) >= 2 and multi[0][0].top - ultimo[3] <= 16:
            fim = max(x.bottom for v in multi for x in v)
            # inclui as linhas de continuação (células que quebram) até a última linha com várias células
            fim = max([fim] + [x.bottom for v in linhas_multi.values() for x in v if x.top <= fim + 12])
            aberta = min(fim + 1.0, limite)
        if aberta is not None or ultimo is not (cheios[0] if cheios else primeiro) or (ultimo[3] - primeiro[1]) > 14:
            base = max(ultimo[3] + 0.5, aberta or 0.0)
            # notas de rodapé da tabela: linhas logo abaixo do último fio, em fonte diferente do corpo
            notas_base = base
            segs = sorted([x for x in pag.segs if not x.margem and x.top >= base - 1 and x.top <= base + 150
                           and _sobrepoe_x(x.x0, x.x1, tx0, tx1) > 0.5 * (x.x1 - x.x0)], key=lambda x: x.top)
            ant = base
            for x in segs:
                if x.top - ant > max(11.0, 1.1 * x.tam):
                    break
                mesmo = abs(x.tam - doc.tam_corpo) <= 0.3 and P._familia(x.fonte) == P._familia(doc.fonte_corpo)
                if mesmo or any(abs(l.bbox[1] - x.top) < 2 for l in outras):
                    break
                notas_base = max(notas_base, x.bottom)
                ant = x.bottom
            caixa = (tx0 - 1, topo, tx1 + 1, base)
            return (caixa, (tx0 - 1, lt, tx1 + 1, notas_base + 0.5)), avisos
        avisos.append("tabela com um fio só: limite inferior estimado pelo texto")
    if exigir_fios:
        return None, ["tabela sem fios horizontais"]
    # sem fios (ou só o de cima): usa o que há entre o título e o próximo texto corrido
    caixa, dens, regiao, alargou = regiao_vizinha(pag, leg, residual, s, "baixo")
    if not _valida(caixa, 18.0, 60.0):
        # título abaixo da tabela (Nature/Scientific Reports): tenta acima
        c2, d2, r2, a2 = regiao_vizinha(pag, leg, residual, s, "cima")
        if not _valida(c2, 18.0, 60.0):
            return None, ["não achei a grade da tabela abaixo nem acima do título"]
        c2, r2 = soltar_texto_da_borda(pag, residual, c2, r2, s)
        avisos.append("título abaixo da tabela: conferir os limites")
        return (c2, (min(c2[0], lx0), c2[1], max(c2[2], lx1), lb)), avisos
    if primeiro is None:
        avisos.append("tabela sem fios horizontais: conferir os limites")
    return (caixa, (min(caixa[0], lx0), lt, max(caixa[2], lx1), caixa[3])), avisos


# --------------------------------------------------------------------------
# Tipo provável (palpite pelo texto da legenda)
# --------------------------------------------------------------------------


def tipo_provavel(leg: P.Legenda, eh_raster: bool) -> str:
    if leg.tipo == "tabela":
        return "tabela"
    t = leg.texto.lower()
    if re.search(r"forest|funnel|meta-?an[aá]l", t):
        return "forest plot"
    if re.search(r"flow\s?(chart|diagram)|consort|prisma|fluxograma|study selection|flow of participants", t):
        return "fluxograma"
    if re.search(r"algorithm|decision tree|algoritmo|pathway", t):
        return "algoritmo"
    if re.search(r"mri|ultrasound|radiograph|photograph|x-ray|image[s]? of|histolog|picture|position", t):
        return "imagem"
    if re.search(r"model|framework|schematic|overview|concept|esquema|illustration|summary of", t):
        return "esquema"
    return "imagem" if eh_raster and not re.search(r"mean|score|change|plot|curve|graph|%|time course", t) else "grafico"


# --------------------------------------------------------------------------
# Processamento de um artigo
# --------------------------------------------------------------------------


def nome_arquivo(leg: P.Legenda, usados: set[str]) -> str:
    prefixo = "tab" if leg.tipo == "tabela" else "fig"
    base = f"{prefixo}{re.sub(r'[^A-Za-z0-9]', '', leg.numero)}"
    if leg.continuacao:
        base += "_cont"
    nome, n = base, 1
    while nome in usados:
        n += 1
        nome = f"{base}_p{leg.pagina}" if n == 2 else f"{base}_p{leg.pagina}_{n}"
    usados.add(nome)
    return nome


def aparar_fios_soltos(residual, caixa, s: float, altura_pag: float = 1e9):
    """Tira da caixa um fio fino e longo isolado no topo ou na base (régua de página, filete
    decorativo da revista). Um fio que faz parte da figura vem colado a mais tinta e fica."""
    import numpy as np

    for _ in range(2):
        mudou = False
        x0, y0, x1, y1 = caixa
        a, b = _px(y0, s), _px(y1, s)
        c, d = _px(x0, s), _px(x1, s)
        sub = residual[a:b, c:d]
        if sub.shape[0] < 8 or sub.shape[1] < 8:
            return caixa
        conta = sub.sum(axis=1)
        com = conta > 0
        for lado in ("topo", "base"):
            ordem = range(len(com)) if lado == "topo" else range(len(com) - 1, -1, -1)
            grupo = []
            vazio = 0
            for i in ordem:
                if com[i]:
                    if vazio:
                        break
                    grupo.append(i)
                elif grupo:
                    vazio += 1
                    if vazio >= int(4 * s):
                        break
            else:
                continue
            if not grupo or len(grupo) > int(6 * s) or vazio < int(4 * s):
                continue
            fio = conta[grupo].max() >= 0.5 * sub.shape[1]
            y_grupo = (a + (max(grupo) if lado == "topo" else min(grupo))) / s
            na_margem = y_grupo < 0.12 * altura_pag if lado == "topo" else y_grupo > 0.9 * altura_pag
            cisco = len(grupo) <= int(3 * s) and na_margem   # resto de cabeçalho/rodapé colado à régua
            if not (fio or cisco):
                continue
            if lado == "topo":
                novo, _ = caixa_tinta(residual, (x0, (a + max(grupo) + 2) / s, x1, y1), s)
            else:
                novo, _ = caixa_tinta(residual, (x0, y0, x1, (a + min(grupo) - 1) / s), s)
            if novo is not None and (novo[3] - novo[1]) >= 20:
                caixa, mudou = novo, True
                break
        if not mudou:
            break
    return caixa


def margem_segura(caixa, limites, m: float, pag: P.PaginaLayout):
    """Expande a caixa em m pontos sem cortar palavra ao meio nem invadir o texto vizinho."""
    x0, y0, x1, y1 = (max(caixa[0] - m, limites[0], 0.0), max(caixa[1] - m, limites[1], 0.0),
                      min(caixa[2] + m, limites[2], pag.largura), min(caixa[3] + m, limites[3], pag.altura))
    for sg in pag.segs:
        if sg.x1 <= x0 or sg.x0 >= x1 or sg.bottom <= y0 or sg.top >= y1:
            continue
        if sg.x0 >= caixa[0] - 0.5 and sg.x1 <= caixa[2] + 0.5 and sg.top >= caixa[1] - 0.5 and sg.bottom <= caixa[3] + 0.5:
            continue  # dentro do miolo: é conteúdo
        if sg.top >= caixa[3] - 1.0:
            y1 = min(y1, sg.top - 0.4)
        elif sg.bottom <= caixa[1] + 1.0:
            y0 = max(y0, sg.bottom + 0.4)
        elif sg.x0 >= caixa[2] - 1.0:
            x1 = min(x1, sg.x0 - 0.4)
        elif sg.x1 <= caixa[0] + 1.0:
            x0 = max(x0, sg.x1 + 0.4)
    return (x0, min(y0, caixa[1]), x1, max(y1, caixa[3]))


FAIXA_MARGEM = 0.11   # fração da altura da página no topo e na base onde mora o cabeçalho/rodapé


def _faixas_margem(tinta):
    import numpy as np

    h = tinta.shape[0]
    k = int(h * FAIXA_MARGEM)
    m = np.zeros_like(tinta)
    m[:k] = tinta[:k]
    m[h - k:] = tinta[h - k:]
    return m


def tinta_repetida(faixas: dict) -> dict:
    """Pixels com tinta, nas faixas de topo e base, na mesma posição em pelo menos 80% das
    páginas do mesmo formato (ou 85% das pares/ímpares): logotipo, filete e cabeçalho gráfico
    da revista, que não são texto e escapam da detecção de cabeçalho (visto no PeerJ)."""
    import numpy as np

    saida = {}
    for _, itens in faixas.items():
        if len(itens) < 3:
            continue
        soma = np.zeros(itens[0][1].shape, np.int32)
        par = {0: np.zeros_like(soma), 1: np.zeros_like(soma)}
        npar = {0: 0, 1: 0}
        for i, m in itens:
            soma += m
            par[i % 2] += m
            npar[i % 2] += 1
        # limiar alto: texto corrido e figuras no alto da página coincidem em parte entre páginas,
        # e apagar isso cortaria figura de verdade; logotipo e filete estão em quase todas
        rep = soma >= max(3, 0.8 * len(itens))
        for k in (0, 1):
            if npar[k] >= 3:
                rep |= par[k] >= max(3, 0.85 * npar[k])
        if not rep.any():
            continue
        # engorda 2 px para levar a borda antisserrilhada junto
        g = rep.copy()
        g[1:] |= rep[:-1]; g[:-1] |= rep[1:]; g[:, 1:] |= rep[:, :-1]; g[:, :-1] |= rep[:, 1:]
        for i, _ in itens:
            saida[i] = g
    return saida


def mobilia(fios_por_pagina: list[list[tuple]], n_pag: int) -> set[tuple]:
    """Fios que se repetem na mesma posição em muitas páginas (réguas de cabeçalho e rodapé)."""
    from collections import Counter

    cont = Counter()
    for fios in fios_por_pagina:
        for k in {(round(f[1] / 3), round(f[0] / 6), round(f[2] / 6)) for f in fios}:
            cont[k] += 1
    minimo = max(3, round(0.3 * n_pag))
    return {k for k, v in cont.items() if v >= minimo}


def _e_mobilia(f, chaves: set[tuple]) -> bool:
    ky, kx0, kx1 = round(f[1] / 3), round(f[0] / 6), round(f[2] / 6)
    return any((ky + dy, kx0 + da, kx1 + db) in chaves for dy in (-1, 0, 1) for da in (-1, 0, 1) for db in (-1, 0, 1))


def processar(aula: C.Aula, pdf: Path, reg: dict, ent: dict, catalogo: list[dict], args) -> dict:
    import numpy as np

    chave = pdf.stem
    pasta_pag = aula.paginas / chave
    pasta_fig = aula.figuras / chave
    pasta_pag.mkdir(parents=True, exist_ok=True)
    pasta_fig.mkdir(parents=True, exist_ok=True)
    doc = P.DocLayout(pdf)
    pdfium = P.abrir_pdfium(pdf)
    n_pag = len(doc.paginas)
    esc_min = args.dpi_miniatura / 72.0
    S = ESCALA_ANALISE

    preservados = {e["id"] for e in catalogo if e.get("chave") == chave
                   and (e.get("origem") == "manual" or e.get("aprovada") or e.get("rejeitada"))}
    for e in [e for e in catalogo if e.get("chave") == chave and e["id"] not in preservados]:
        for campo in ("arquivo", "arquivo_com_legenda"):
            if e.get(campo):
                (aula.figuras / e[campo]).unlink(missing_ok=True)
        catalogo.remove(e)

    usados: set[str] = set()   # nomes desta rodada (um id já aprovado mantém o nome e não é refeito)
    novos: list[dict] = []
    avisos_art: list[str] = list(doc.avisos)
    if sum(pg.n_palavras for pg in doc.paginas) < 30 * max(n_pag, 1):
        avisos_art.append("PDF quase sem camada de texto (digitalizado?): legendas não podem ser achadas. "
                          "Olhe _visao_geral.png e recorte à mão com recortar.py --pagina N --frac ...")
    miniaturas: list[Path] = []
    licenca = ent.get("licenca") or C.normalizar_licenca(reg.get("licenca")) or C.LICENCA_DESCONHECIDA

    # passada 1: fios de todas as páginas (para reconhecer as réguas que se repetem)
    fios_pag: list[list[tuple]] = []
    tintas: dict[int, object] = {}
    mascara_mobilia = {}
    if not args.so_miniaturas:
        faixas: dict[tuple, list] = {}   # formato da página -> [(i, máscara das faixas de topo e base)]
        for i, pag in enumerate(doc.paginas):
            cinza = np.asarray(P.render_pagina(pdfium, i, 72.0 * S, cinza=True))
            tinta = cinza < LIMIAR_TINTA
            fios_pag.append(achar_fios(tinta, S))
            if pag.legendas:
                tintas[i] = tinta
            faixas.setdefault(tinta.shape, []).append((i, _faixas_margem(tinta)))
        repetidos = mobilia(fios_pag, n_pag)
        mascara_mobilia = tinta_repetida(faixas)
    else:
        repetidos = set()

    for i, pag in enumerate(doc.paginas):
        mini = P.render_pagina(pdfium, i, args.dpi_miniatura)
        destino_mini = pasta_pag / f"p{pag.numero:03d}.png"
        mini.save(destino_mini)
        miniaturas.append(destino_mini)
        caixas_grade = []
        if args.depurar:
            for b in pag.blocos:
                cor = {"corpo": (150, 150, 150), "legenda": (230, 140, 0)}.get(b.tipo, (120, 190, 235))
                caixas_grade.append((b.bbox, "", cor))
        if pag.frac_girado > 0.5 and pag.n_palavras > 40:
            avisos_art.append(f"p.{pag.numero}: conteúdo girado (tabela em paisagem?). Sem recorte automático; "
                              f"use recortar.py --pagina {pag.numero} --girar 90 (ou 270).")
        if i in tintas:
            tinta = tintas.pop(i)
            fios = []
            for f in fios_pag[i]:
                if _e_mobilia(f, repetidos) or (pag.y_cab and f[3] <= pag.y_cab + 6) or (pag.y_rod and f[1] >= pag.y_rod - 6):
                    apagar(tinta, f, S, 1.0)
                else:
                    fios.append(f)
            if i in mascara_mobilia:   # logotipo/filete da revista repetido no topo ou na base
                tinta = tinta & ~mascara_mobilia[i]
            residual = tinta.copy()
            for b in pag.blocos:
                if b.tipo in ("corpo", "legenda"):
                    apagar(residual, b.bbox, S)
            for sg in pag.segs:
                if sg.margem:
                    apagar(residual, (sg.x0, sg.top, sg.x1, sg.bottom), S)
            if pag.y_cab:
                apagar(residual, (0, 0, pag.largura, pag.y_cab), S)
            if pag.y_rod:
                apagar(residual, (0, pag.y_rod, pag.largura, pag.altura), S)
            for fx in pag.faixas_laterais:
                apagar(residual, fx, S, 0)
            pagina_alta = None
            m = args.margem
            achados: list[tuple] = []   # (leg, bbox, bbox_leg, avisos)
            falhas: list[tuple] = []

            def tentar_tabela(leg, exigir_fios: bool):
                res, avisos = regiao_tabela(doc, pag, leg, tinta, residual, fios, S, exigir_fios)
                if res is None:
                    return None, avisos
                caixa, com_leg = res
                bbox = margem_segura(caixa, (0, caixa[1], pag.largura, pag.altura), m, pag)
                bbox_leg = (max(min(com_leg[0], leg.bbox[0]) - m, 0), max(com_leg[1] - m, 0),
                            min(max(com_leg[2], leg.bbox[2]) + m, pag.largura), min(com_leg[3] + m, pag.altura))
                apagar(residual, (caixa[0], leg.bbox[1], caixa[2], com_leg[3]), S)
                return (leg, bbox, bbox_leg, avisos), avisos

            tabelas = [l for l in pag.legendas if l.tipo == "tabela"]
            pendentes_tab = []
            for leg in tabelas:           # 1) tabelas delimitadas por fios: são as mais confiáveis
                item, avisos = tentar_tabela(leg, True)
                if item:
                    achados.append(item)
                else:
                    pendentes_tab.append(leg)
            for leg in [l for l in pag.legendas if l.tipo == "figura"]:   # 2) figuras
                res, avisos = regiao_figura(pag, leg, residual, S)
                if res is None:
                    falhas.append((leg, avisos))
                    continue
                caixa, regiao = res
                caixa = aparar_fios_soltos(residual, caixa, S, pag.altura)
                bbox = margem_segura(caixa, regiao, m, pag)
                lx0, lt, lx1, lb = leg.bbox
                bbox_leg = (max(min(bbox[0], lx0 - m), 0), max(min(bbox[1], lt - m), 0),
                            min(max(bbox[2], lx1 + m), pag.largura), min(max(bbox[3], lb + m), pag.altura))
                apagar(residual, caixa, S)
                achados.append((leg, bbox, bbox_leg, avisos))
            for leg in pendentes_tab:     # 3) tabelas sem fios: o que sobrou abaixo do título
                item, avisos = tentar_tabela(leg, False)
                if item:
                    achados.append(item)
                else:
                    falhas.append((leg, avisos))
            for leg, avisos in falhas:
                avisos_art.append(f"p.{pag.numero}: {leg.rotulo} — {avisos[0]} (recortar à mão)")
                caixas_grade.append((leg.bbox, leg.rotulo + " ?", (178, 58, 58)))

            for leg, bbox, bbox_leg, avisos in sorted(achados, key=lambda t: (t[1][1], t[1][0])):
                nome = nome_arquivo(leg, usados)
                ident = f"{chave}_{nome}"
                if ident in preservados:
                    caixas_grade.append((bbox, f"{nome} (já decidido)", (90, 95, 99)))
                    continue
                if pagina_alta is None:
                    pagina_alta = P.render_pagina(pdfium, i, args.dpi)
                e_ = args.dpi / 72.0

                def cortar(bb):
                    return pagina_alta.crop((max(int(bb[0] * e_), 0), max(int(bb[1] * e_), 0),
                                             min(int(round(bb[2] * e_)), pagina_alta.width),
                                             min(int(round(bb[3] * e_)), pagina_alta.height)))

                img = cortar(bbox)
                arq = f"{chave}/{nome}.png"
                arq_leg = f"{chave}/{nome}_legenda.png"
                img.save(aula.figuras / arq)
                cortar(bbox_leg).save(aula.figuras / arq_leg)
                nativo = P.dpi_nativo(pag, bbox)
                avisos = list(avisos)
                branco = float((np.asarray(img.convert("L")) >= 245).mean())
                conf = 0.55 + (0.2 if leg.forte else 0.0) + (0.15 if not avisos else 0.0) + (0.1 if 0.3 < branco < 0.97 else -0.2)
                if nativo and nativo < 120:
                    avisos.append(f"imagem embutida de baixa resolução (~{int(nativo)} dpi): pode ficar borrada no slide")
                entrada = {
                    "id": ident, "chave": chave, "arquivo": arq, "arquivo_com_legenda": arq_leg,
                    "pagina": pag.numero, "bbox_pt": [round(v, 1) for v in bbox],
                    "bbox_legenda_pt": [round(v, 1) for v in bbox_leg],
                    "dpi": args.dpi, "largura_px": img.width, "altura_px": img.height,
                    "rotulo": leg.rotulo, "legenda_original": leg.texto, "legenda_pt": "",
                    "tipo": tipo_provavel(leg, bool(nativo)), "o_que_ensina": "",
                    "licenca": licenca, "origem": "auto", "aprovada": False,
                    "citacao": C.citacao_curta(reg, ent, leg.rotulo),
                    "confianca": round(max(0.05, min(conf, 0.99)), 2), "avisos": avisos,
                }
                if nativo:
                    entrada["dpi_nativo"] = int(nativo)
                novos.append(entrada)
                cor = (0, 140, 80) if leg.tipo == "figura" else (130, 60, 170)
                caixas_grade.append((bbox, nome, cor))
        grade = P.desenhar_grade(mini, caixas_grade, esc_min, fino=args.depurar)
        grade.save(pasta_pag / f"p{pag.numero:03d}_grade.png")

    pdfium.close()
    catalogo.extend(novos)
    P.folha_contato([{"img": mm, "numero": f"p.{k + 1}", "linhas": []} for k, mm in enumerate(miniaturas)],
                    pasta_pag / "_visao_geral.png", titulo=f"{chave} — {n_pag} páginas", colunas=6,
                    celula=(300, 400), por_folha=24)
    itens = []
    for k, e in enumerate(sorted(novos, key=lambda e: (e["pagina"], e["bbox_pt"][1])), 1):
        e["numero_folha"] = k
        aviso = ("! " + e["avisos"][0]) if e["avisos"] else (e["legenda_original"][:70])
        itens.append({"img": aula.figuras / e["arquivo"], "numero": k,
                      "linhas": [f"{e['id']}  ·  p.{e['pagina']}  ·  {e['largura_px']}×{e['altura_px']} px",
                                 f"{e['rotulo']} · {e['tipo']} · confiança {e['confianca']:.2f}", aviso],
                      "cor": (178, 58, 58) if e["avisos"] else (0, 122, 153)})
    folhas = P.folha_contato(itens, pasta_fig / "_candidatos.png",
                             titulo=f"{chave} — candidatos automáticos (não aprovados)")
    return {"chave": chave, "paginas": n_pag, "candidatos": novos, "avisos": avisos_art, "folhas": folhas,
            "legendas": len(doc.legendas)}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Miniaturas de todas as páginas + candidatos de recorte de figuras e tabelas (origem auto, não aprovados).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--apenas", nargs="+", metavar="CHAVE", help="processa só estas chaves")
    ap.add_argument("--dpi", type=int, default=300, help="resolução dos recortes (padrão 300)")
    ap.add_argument("--dpi-miniatura", type=int, default=100, help="resolução das miniaturas de página (padrão 100)")
    ap.add_argument("--margem", type=float, default=6.0, help="margem em pontos ao redor do recorte (padrão 6)")
    ap.add_argument("--so-miniaturas", action="store_true", help="gera só as miniaturas, sem propor recortes")
    ap.add_argument("--depurar", action="store_true",
                    help="desenha na grade os blocos de texto (cinza = corpo, laranja = legenda, azul = solto)")
    args = ap.parse_args()

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
        log(f"Nenhum PDF em {aula.pdf}.")
        return 0
    catalogo = C.carregar_catalogo(aula)
    total = 0
    for pdf in pdfs:
        chave = pdf.stem
        ok, motivo, _ = C.validar_pdf(pdf, 1000)
        if not ok:
            log(f"{chave}: pulado ({motivo})")
            continue
        try:
            r = processar(aula, pdf, por_chave.get(chave, {"chave": chave}), manifest.get(chave, {}), catalogo, args)
        except Exception as e:
            log(f"{chave}: falhou ({type(e).__name__}: {e})")
            if args.depurar:
                raise
            continue
        C.salvar_catalogo(aula, catalogo)
        if chave in manifest:
            manifest[chave]["figuras_detectadas"] = len(r["candidatos"])
            C.salvar_manifest(aula, manifest)
        total += len(r["candidatos"])
        log(f"{chave}: {r['paginas']} páginas, {r['legendas']} legendas, {len(r['candidatos'])} candidato(s)")
        for e in sorted(r["candidatos"], key=lambda e: e.get("numero_folha", 0)):
            marca = "  !" if e["avisos"] else "   "
            log(f"{marca} {e.get('numero_folha', 0):>2}. {e['id']:<28} p.{e['pagina']:<3} {e['largura_px']}×{e['altura_px']} px  "
                f"{e['tipo']}" + (f"  — {e['avisos'][0]}" if e["avisos"] else ""))
        for a in r["avisos"]:
            log(f"    aviso: {a}")
        if r["folhas"]:
            log(f"    olhar: {r['folhas'][0]}" + (f" (+{len(r['folhas']) - 1} folha(s))" if len(r["folhas"]) > 1 else ""))
        log(f"    páginas: {aula.paginas / chave / '_visao_geral.png'}")
    log("")
    log(f"Resumo: {total} candidato(s) em {len(pdfs)} artigo(s). Catálogo: {aula.catalogo}")
    log("Nada está aprovado. Olhe as folhas _candidatos.png e as páginas *_grade.png, escolha o que ensina "
        "e ajuste com recortar.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
