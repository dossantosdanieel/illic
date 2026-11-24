#!/usr/bin/env python3
"""Recorte manual preciso de uma figura ou tabela, e aprovação no catálogo.

A caixa é dada pela página e por quatro números: esquerda, topo, direita, base.
  --frac  em fração da página (0 a 1), lida direto na régua das miniaturas *_grade.png
  --bbox  em pontos PDF, origem no canto superior esquerdo (os mesmos de catalogo.json)

Uso:
  # recorte novo, olhando paginas/Breda2021/p006_grade.png
  python3 recortar.py AULA --chave Breda2021 --id fig4 --pagina 6 --frac 0.52,0.60,0.93,0.90 \\
      --rotulo "Figure 4" --tipo grafico
  # só ver a caixa desenhada na página, sem recortar
  python3 recortar.py AULA --chave Breda2021 --pagina 6 --frac 0.52,0.60,0.93,0.90 --previa
  # ajustar um candidato automático: abre 10 pt à esquerda e 14 pt na base
  python3 recortar.py AULA --id Breda2021_fig4 --ajustar -10,0,0,14
  # apagar um trecho (legenda colada, cabeçalho da revista) e aparar o branco
  python3 recortar.py AULA --id Breda2021_fig4 --apagar 0.52,0.86,0.93,0.90 --aparar
  # juntar painéis (da mesma página ou de outra) lado a lado
  python3 recortar.py AULA --chave Vlist2021 --id fig4e5 --pagina 5 --frac 0.08,0.06,0.48,0.30 \\
      --painel 5:0.52,0.06,0.93,0.30 --juntar horizontal
  # tabela em paisagem
  python3 recortar.py AULA --chave Centner2019 --id tab1 --pagina 4 --frac 0.1,0.05,0.9,0.95 --girar 90
  # aprovar (ou rejeitar) e preencher os campos didáticos, sem recortar de novo
  python3 recortar.py AULA --id Breda2021_fig4 --aprovar --tipo grafico \\
      --legenda-pt "Evolução do VISA-P em 24 semanas" --ensina "A carga progressiva supera o excêntrico em 24 semanas"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402
import _pdf as P  # noqa: E402

TIPOS = ["forest plot", "grafico", "fluxograma", "tabela", "imagem", "esquema", "algoritmo"]


def log(msg: str) -> None:
    print(msg, flush=True)


def numeros(texto: str, n: int = 4) -> list[float]:
    try:
        vals = [float(v) for v in re.split(r"[,; ]+", texto.strip().replace("−", "-")) if v]
    except ValueError:
        C.sair(f"não entendi os números: {texto!r} (use {n} valores separados por vírgula, com ponto decimal)")
    if len(vals) != n:
        C.sair(f"esperava {n} números (esquerda,topo,direita,base) e recebi {len(vals)}: {texto!r}")
    return vals


def caixa_em_pontos(vals: list[float], larg: float, alt: float, forcar: str | None = None) -> tuple:
    """Aceita fração (todos os valores até 1,5) ou pontos; devolve pontos ordenados e dentro da página."""
    em_fracao = forcar == "frac" or (forcar is None and all(abs(v) <= 1.5 for v in vals))
    x0, y0, x1, y1 = vals
    if em_fracao:
        x0, x1, y0, y1 = x0 * larg, x1 * larg, y0 * alt, y1 * alt
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    return (max(x0, 0.0), max(y0, 0.0), min(x1, larg), min(y1, alt))


def caixa_com_pagina(texto: str, pagina_padrao: int | None) -> tuple[int | None, list[float]]:
    if ":" in texto:
        pg, resto = texto.split(":", 1)
        return int(pg), numeros(resto)
    return pagina_padrao, numeros(texto)


def texto_logo_fora(bbox, palavras: list[dict], alcance: float = 14.0) -> list[tuple[str, str, float]]:
    """A linha de texto mais próxima fora de cada borda (até 'alcance' pt), na faixa da caixa.
    Mostra o que ficou de fora: uma linha de tabela, um rótulo de eixo, um título de painel.
    Os lados são os da página (antes de --girar)."""
    x0, y0, x1, y1 = bbox
    saida = []
    lados = {
        "acima": lambda w: (y0 - w["bottom"]) if w["bottom"] <= y0 + 0.5 and w["x1"] > x0 and w["x0"] < x1 else None,
        "abaixo": lambda w: (w["top"] - y1) if w["top"] >= y1 - 0.5 and w["x1"] > x0 and w["x0"] < x1 else None,
        "à esquerda": lambda w: (x0 - w["x1"]) if w["x1"] <= x0 + 0.5 and w["bottom"] > y0 and w["top"] < y1 else None,
        "à direita": lambda w: (w["x0"] - x1) if w["x0"] >= x1 - 0.5 and w["bottom"] > y0 and w["top"] < y1 else None,
    }
    for lado, dist in lados.items():
        perto = [(d, w) for w in palavras if (d := dist(w)) is not None and d <= alcance]
        if not perto:
            continue
        dmin = min(d for d, _ in perto)
        linha = sorted((w for d, w in perto if d <= dmin + 3), key=lambda w: (round(w["top"]), w["x0"]))
        txt = " ".join(w["text"] for w in linha)[:70]
        saida.append((lado, txt, max(dmin, 0.0)))
    return saida


def nome_de(rotulo: str) -> str:
    m = re.match(r"\s*(\D+?)\.?\s*(S?\d+[A-Za-z]?|[IVXLC]+)\s*$", rotulo or "")
    if not m:
        return re.sub(r"[^A-Za-z0-9]", "", C.sem_acento(rotulo)).lower() or "fig"
    prefixo = "tab" if C.normalizar_texto(m.group(1)).startswith(("tab", "quadro")) else "fig"
    return f"{prefixo}{m.group(2)}"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Recorta uma região de uma página do PDF em alta resolução e registra no catálogo (origem manual).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--chave", help="chave do artigo (ex.: Breda2021); dispensável se --id já traz Chave_nome")
    ap.add_argument("--id", dest="ident", help="nome do recorte (fig2, tab1, fig2a) ou id completo (Breda2021_fig2)")
    ap.add_argument("--pagina", type=int, help="página do PDF (1 = primeira)")
    ap.add_argument("--frac", help="caixa em fração da página: esquerda,topo,direita,base (0 a 1)")
    ap.add_argument("--bbox", help="caixa em pontos PDF: x0,y0,x1,y1 (origem no canto superior esquerdo)")
    ap.add_argument("--dentro", metavar="ID",
                    help="--frac passa a ser fração do recorte ID que você já abriu (ex.: só o painel A de "
                         "Owen2020_fig3: --dentro Owen2020_fig3 --frac 0,0,0.5,0.5); a página vem dele, e --apagar "
                         "sem página também vira fração desse recorte")
    ap.add_argument("--ajustar", help="desloca as bordas da caixa atual, em pontos: d_esq,d_topo,d_dir,d_base "
                                      "(negativo = para a esquerda/para cima)")
    ap.add_argument("--painel", action="append", default=[], metavar="[PAG:]x0,y0,x1,y1",
                    help="painel extra a juntar (fração ou pontos; pode repetir)")
    ap.add_argument("--juntar", choices=["horizontal", "vertical"], default="horizontal",
                    help="como dispor os painéis (padrão: horizontal)")
    ap.add_argument("--apagar", action="append", default=[], metavar="[PAG:]x0,y0,x1,y1",
                    help="região da página a cobrir de branco antes do recorte (fração ou pontos; pode repetir)")
    ap.add_argument("--exato", action="store_true",
                    help="usa a caixa exatamente como dada (por padrão ela se ajusta para não cortar palavras ao meio)")
    ap.add_argument("--aparar", action="store_true", help="apara as bordas brancas depois de recortar")
    ap.add_argument("--margem-aparo", type=int, default=18, help="margem em px deixada pelo --aparar (padrão 18)")
    ap.add_argument("--girar", type=int, choices=[0, 90, 180, 270], default=0,
                    help="gira o recorte no sentido horário (tabelas em paisagem)")
    ap.add_argument("--dpi", type=int, help="resolução do recorte (padrão: a do catálogo, ou 300)")
    ap.add_argument("--rotulo", help='rótulo original, ex.: "Figure 2" ou "Table 1"')
    ap.add_argument("--tipo", choices=TIPOS, help="tipo da figura")
    ap.add_argument("--legenda", help="legenda original (se omitida, procuro no PDF pelo rótulo)")
    ap.add_argument("--legenda-pt", help="legenda em português para o slide")
    ap.add_argument("--ensina", help="o que a figura ensina, em uma frase")
    ap.add_argument("--aprovar", action="store_true", help="marca como aprovada (só depois de OLHAR o PNG)")
    ap.add_argument("--rejeitar", action="store_true", help="marca como não aprovada")
    ap.add_argument("--remover", action="store_true", help="tira a entrada do catálogo e apaga os PNGs")
    ap.add_argument("--previa", action="store_true", help="só desenha a caixa na página (pNNN_previa.png), sem recortar")
    args = ap.parse_args()

    aula = C.Aula(args.aula)
    aula.exigir()
    aula.criar_pastas()
    catalogo = C.carregar_catalogo(aula)
    chave, nome = args.chave, args.ident
    if nome and "_" in nome and not chave:
        chave, nome = nome.split("_", 1)
    elif nome and chave and nome.startswith(chave + "_"):
        nome = nome[len(chave) + 1:]
    if not nome and args.rotulo:
        nome = nome_de(args.rotulo)
    if not chave:
        C.sair("informe --chave (ou --id no formato Chave_nome).")
    ident = f"{chave}_{nome}" if nome else None
    atual = next((e for e in catalogo if e["id"] == ident), None) if ident else None

    if args.remover:
        if not atual:
            C.sair(f"{ident} não está no catálogo.")
        for campo in ("arquivo", "arquivo_com_legenda"):
            if atual.get(campo):
                (aula.figuras / atual[campo]).unlink(missing_ok=True)
        catalogo.remove(atual)
        C.salvar_catalogo(aula, catalogo)
        log(f"Removido do catálogo: {ident}")
        return 0

    pdf = aula.pdf / f"{chave}.pdf"
    recortar = bool(args.frac or args.bbox or args.ajustar or args.painel or args.apagar or args.aparar
                    or args.girar or args.previa or (args.dpi and atual))
    if recortar and not pdf.exists():
        C.sair(f"PDF não encontrado: {pdf}")

    img = None
    if recortar:
        pdfium = P.abrir_pdfium(pdf)
        n_pag = len(pdfium)
        base_dentro = None
        if args.dentro:
            base_dentro = next((e for e in catalogo if e["id"] == args.dentro), None)
            if not base_dentro or not base_dentro.get("bbox_pt"):
                C.sair(f"--dentro: {args.dentro} não está no catálogo (ou não tem bbox_pt).")
            if base_dentro.get("girado") or len(base_dentro.get("paineis") or []) > 1:
                C.sair("--dentro não serve para recorte girado ou de vários painéis; use --frac da página.")
            if not args.frac:
                C.sair("--dentro precisa de --frac (frações do recorte de origem).")
            if base_dentro.get("chave") != chave:
                C.sair(f"--dentro: {args.dentro} é de outro artigo ({base_dentro.get('chave')}).")
        pagina = (base_dentro or {}).get("pagina") or args.pagina or (atual or {}).get("pagina")
        if not pagina:
            C.sair("informe --pagina.")
        if not 1 <= pagina <= n_pag:
            C.sair(f"página {pagina} não existe (o PDF tem {n_pag}).")
        larg, alt = P.tamanho_pagina(pdfium, pagina - 1)
        if base_dentro:
            bx0, by0, bx1, by1 = base_dentro["bbox_pt"]
            f = numeros(args.frac)
            bbox = caixa_em_pontos([bx0 + f[0] * (bx1 - bx0), by0 + f[1] * (by1 - by0),
                                    bx0 + f[2] * (bx1 - bx0), by0 + f[3] * (by1 - by0)], larg, alt, "pt")
        elif args.frac:
            bbox = caixa_em_pontos(numeros(args.frac), larg, alt, "frac")
        elif args.bbox:
            bbox = caixa_em_pontos(numeros(args.bbox), larg, alt, "pt")
        elif atual and atual.get("bbox_pt"):
            bbox = tuple(atual["bbox_pt"])
        else:
            C.sair("informe a caixa com --frac ou --bbox (não há caixa anterior deste id no catálogo).")
        if args.ajustar:
            d = numeros(args.ajustar)
            bbox = (max(bbox[0] + d[0], 0.0), max(bbox[1] + d[1], 0.0), min(bbox[2] + d[2], larg), min(bbox[3] + d[3], alt))
        if bbox[2] - bbox[0] < 5 or bbox[3] - bbox[1] < 5:
            C.sair(f"caixa vazia ou invertida: {[round(v, 1) for v in bbox]}")
        paineis = [(pagina, bbox)]
        for txt in args.painel:
            pg, vals = caixa_com_pagina(txt, pagina)
            if not 1 <= pg <= n_pag:
                C.sair(f"página {pg} não existe (painel {txt}).")
            lw, lh = P.tamanho_pagina(pdfium, pg - 1)
            paineis.append((pg, caixa_em_pontos(vals, lw, lh)))
        apagar: dict[int, list[tuple]] = {}
        for txt in args.apagar:
            pg, vals = caixa_com_pagina(txt, pagina)
            lw, lh = P.tamanho_pagina(pdfium, pg - 1)
            if base_dentro and ":" not in txt:   # com --dentro, --apagar também é fração do recorte de origem
                bx0, by0, bx1, by1 = base_dentro["bbox_pt"]
                vals = [bx0 + vals[0] * (bx1 - bx0), by0 + vals[1] * (by1 - by0),
                        bx0 + vals[2] * (bx1 - bx0), by0 + vals[3] * (by1 - by0)]
                apagar.setdefault(pg, []).append(caixa_em_pontos(vals, lw, lh, "pt"))
                continue
            apagar.setdefault(pg, []).append(caixa_em_pontos(vals, lw, lh))
        if not args.exato:   # nenhuma palavra fica cortada ao meio pela borda
            ajustados = []
            for pg, bb in paineis:
                lw, lh = P.tamanho_pagina(pdfium, pg - 1)
                nova, mudou = P.encaixar_em_palavras(bb, P.palavras_da_pagina(pdf, pg), lw, lh, apagar.get(pg))
                if mudou:
                    log(f"Caixa da p.{pg} ajustada para não cortar palavras: {[round(v, 1) for v in bb]} -> "
                        f"{[round(v, 1) for v in nova]}  (use --exato para desligar)")
                ajustados.append((pg, nova))
            paineis = ajustados
            bbox = paineis[0][1]

        if args.previa:
            esc = 100 / 72.0
            saidas = []
            for pg in sorted({p for p, _ in paineis}):
                mini = P.render_pagina(pdfium, pg - 1, 100)
                caixas = [(b, nome or "caixa", (0, 140, 80)) for p, b in paineis if p == pg]
                caixas += [(b, "apagar", (178, 58, 58)) for b in apagar.get(pg, [])]
                destino = aula.paginas / chave / f"p{pg:03d}_previa.png"
                destino.parent.mkdir(parents=True, exist_ok=True)
                P.desenhar_grade(mini, caixas, esc).save(destino)
                saidas.append(destino)
            pdfium.close()
            for b in paineis:
                log(f"Caixa na p.{b[0]}: pontos {[round(v, 1) for v in b[1]]}")
            log("Prévia (nada foi recortado). Olhe: " + "  ".join(str(s) for s in saidas))
            return 0

        from PIL import Image, ImageDraw

        dpi = args.dpi or (atual or {}).get("dpi") or 300
        e_ = dpi / 72.0
        cache: dict[int, object] = {}
        partes = []
        for pg, bb in paineis:
            if pg not in cache:
                pagina_img = P.render_pagina(pdfium, pg - 1, dpi).convert("RGB")
                d = ImageDraw.Draw(pagina_img)
                for r in apagar.get(pg, []):
                    d.rectangle([r[0] * e_, r[1] * e_, r[2] * e_, r[3] * e_], fill=(255, 255, 255))
                cache[pg] = pagina_img
            pi = cache[pg]
            partes.append(pi.crop((int(bb[0] * e_), int(bb[1] * e_),
                                   min(int(round(bb[2] * e_)), pi.width), min(int(round(bb[3] * e_)), pi.height))))
        pdfium.close()
        if args.girar:
            partes = [p.rotate(-args.girar, expand=True) for p in partes]
        corte = (0, 0, 0, 0)
        if args.aparar:
            aparadas = [P.aparar_branco(p, args.margem_aparo) for p in partes]
            partes = [a[0] for a in aparadas]
            corte = aparadas[0][1]
        if len(partes) == 1:
            img = partes[0]
        else:
            vao = int(0.12 * dpi)
            if args.juntar == "horizontal":
                img = Image.new("RGB", (sum(p.width for p in partes) + vao * (len(partes) - 1), max(p.height for p in partes)),
                                (255, 255, 255))
                x = 0
                for p in partes:
                    img.paste(p, (x, (img.height - p.height) // 2))
                    x += p.width + vao
            else:
                img = Image.new("RGB", (max(p.width for p in partes), sum(p.height for p in partes) + vao * (len(partes) - 1)),
                                (255, 255, 255))
                y = 0
                for p in partes:
                    img.paste(p, ((img.width - p.width) // 2, y))
                    y += p.height + vao
        if args.aparar and not args.girar and len(paineis) == 1:   # a caixa registrada acompanha o aparo
            bbox = (bbox[0] + corte[0] / e_, bbox[1] + corte[1] / e_, bbox[2] - corte[2] / e_, bbox[3] - corte[3] / e_)
            paineis[0] = (pagina, bbox)
        if not nome:
            C.sair("informe --id (ex.: fig2) ou --rotulo para dar nome ao recorte.")

    if not recortar and not atual:
        C.sair(f"{ident or 'recorte'} não está no catálogo; para criar, informe --pagina e --frac/--bbox.")

    reg, manifest = {"chave": chave}, {}
    try:
        registros, _ = C.carregar_registros(aula)
        reg = next((r for r in registros if r["chave"] == chave), reg)
    except SystemExit:
        pass
    manifest = C.carregar_manifest(aula).get(chave, {})

    ent = dict(atual) if atual else {"id": ident, "chave": chave, "legenda_pt": "", "o_que_ensina": "", "aprovada": False}
    if img is not None:
        arq = f"{chave}/{nome}.png"
        (aula.figuras / chave).mkdir(parents=True, exist_ok=True)
        img.save(aula.figuras / arq)
        ent.update(arquivo=arq, pagina=paineis[0][0], bbox_pt=[round(v, 1) for v in paineis[0][1]], dpi=dpi,
                   largura_px=img.width, altura_px=img.height, origem="manual")
        if len(paineis) > 1:
            ent["paineis"] = [{"pagina": p, "bbox_pt": [round(v, 1) for v in b]} for p, b in paineis]
            ent["juntar"] = args.juntar
        else:
            ent.pop("paineis", None)
        if args.apagar:
            ent["apagado_pt"] = [{"pagina": p, "bbox_pt": [round(v, 1) for v in b]} for p, bs in apagar.items() for b in bs]
        else:
            ent.pop("apagado_pt", None)
        if args.girar:
            ent["girado"] = args.girar
        for k in ("confianca", "avisos", "numero_folha", "qc"):
            ent.pop(k, None)
        if not args.aprovar and atual and atual.get("aprovada"):
            ent["aprovada"] = False   # recorte mudou: precisa ser olhado de novo
    if args.rotulo:
        ent["rotulo"] = args.rotulo
    ent.setdefault("rotulo", "")
    if args.legenda is not None:
        ent["legenda_original"] = args.legenda
    elif not ent.get("legenda_original") and ent.get("rotulo") and pdf.exists() and img is not None:
        try:   # procura a legenda pelo rótulo
            alvo = (("tabela" if nome_de(ent["rotulo"]).startswith("tab") else "figura"),
                    re.sub(r"^\D+", "", ent["rotulo"]).strip().lower())
            for leg in P.DocLayout(pdf).legendas:
                if (leg.tipo, leg.numero.lower()) == alvo:
                    ent["legenda_original"] = leg.texto
                    break
        except Exception:
            pass
    ent.setdefault("legenda_original", "")
    if args.legenda_pt is not None:
        ent["legenda_pt"] = args.legenda_pt
    if args.ensina is not None:
        ent["o_que_ensina"] = args.ensina
    if args.tipo:
        ent["tipo"] = args.tipo
    ent.setdefault("tipo", "tabela" if (nome or "").startswith("tab") else "grafico")
    ent["licenca"] = ent.get("licenca") or manifest.get("licenca") or C.normalizar_licenca(reg.get("licenca")) \
        or C.LICENCA_DESCONHECIDA
    if not ent.get("citacao") or args.rotulo:
        ent["citacao"] = C.citacao_curta(reg, manifest, ent.get("rotulo") or None)
    ent.setdefault("origem", "manual")
    if args.aprovar:
        ent["aprovada"] = True
    if args.rejeitar:
        ent["aprovada"] = False
        ent["rejeitada"] = True
    elif args.aprovar:
        ent.pop("rejeitada", None)

    if atual in catalogo:
        catalogo[catalogo.index(atual)] = ent
    else:
        catalogo.append(ent)
    C.salvar_catalogo(aula, catalogo)

    if img is not None:
        palavras = P.palavras_da_pagina(pdf, ent["pagina"]) if len(paineis) == 1 else None
        nativo = P.dpi_nativo_pdf(pdf, ent["pagina"], tuple(ent["bbox_pt"])) if len(paineis) == 1 else None
        if nativo:
            ent["dpi_nativo"] = int(nativo)
        else:
            ent.pop("dpi_nativo", None)
        C.salvar_catalogo(aula, catalogo)
        apagadas = [tuple(a["bbox_pt"]) for a in ent.get("apagado_pt", [])]
        continua = None
        if len(paineis) == 1:
            try:
                continua = P.continua_fora(pdf, ent["pagina"], tuple(ent["bbox_pt"]), apagadas)
            except Exception:
                continua = None
        qc = P.avaliar_recorte(img, tuple(ent["bbox_pt"]) if palavras else None, palavras, ent["dpi"], nativo,
                               apagadas, continua)
        log(f"Recorte gravado: {aula.figuras / ent['arquivo']}")
        log(f"  {ent['id']} · p.{ent['pagina']} · {img.width}×{img.height} px a {ent['dpi']} dpi · cabe em: {qc['cabe']}"
            f" · caixa (pt) {ent['bbox_pt']}")
        for e in qc["erros"]:
            log(f"  PROBLEMA: {e}")
        for a in qc["avisos"]:
            log(f"  aviso: {a}")
        if palavras:
            for lado, txt, dist in texto_logo_fora(tuple(ent["bbox_pt"]), palavras):
                log(f"  logo fora da caixa, {lado} (a {dist:.0f} pt): \"{txt}\" — é da figura? então abra a caixa")
        if ent.get("aprovada"):
            log("  Marcado como aprovado. Se ainda não olhou o PNG, olhe agora.")
        else:
            log("  Ainda NÃO aprovado. Olhe o PNG; se estiver bom, rode de novo só com --id e --aprovar "
                "(e --ensina, --legenda-pt, --tipo).")
    else:
        estado = "aprovada" if ent.get("aprovada") else ("rejeitada" if ent.get("rejeitada") else "não aprovada")
        log(f"Catálogo atualizado: {ent['id']} ({estado}; tipo {ent['tipo']}; licença {ent['licenca']})")
        faltam = [n for n, k in (("--ensina", "o_que_ensina"), ("--legenda-pt", "legenda_pt")) if not ent.get(k)]
        if ent.get("aprovada") and faltam:
            log("  Falta preencher: " + ", ".join(faltam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
