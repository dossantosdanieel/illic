#!/usr/bin/env python3
"""Controle de qualidade dos recortes aprovados e folha de contato final.

Para cada recorte aprovado no catálogo confere: arquivo existe e bate com o catálogo;
resolução suficiente para meio slide ou slide inteiro (16:9, 13,33 × 7,5 pol);
fração em branco; texto cortado na borda; proporção extrema; campos didáticos
preenchidos (tipo, legenda em português, o que ensina, citação); licença.
Grava o resultado em cada entrada ("qc") e monta 03_figuras/folha_contato.png
com rótulo e citação.

Uso:
  python3 conferir_recortes.py AULA
  python3 conferir_recortes.py AULA --todos            # inclui candidatos não aprovados
  python3 conferir_recortes.py AULA --apenas Breda2021
  python3 conferir_recortes.py AULA --estrito          # sai com código 1 se houver problema
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402
import _pdf as P  # noqa: E402

TIPOS = {"forest plot", "grafico", "fluxograma", "tabela", "imagem", "esquema", "algoritmo"}


def log(msg: str) -> None:
    print(msg, flush=True)


def nota_licenca(lic: str | None) -> str | None:
    lic = lic or C.LICENCA_DESCONHECIDA
    if lic in ("cc-by", "cc0", "dominio publico", "cc-by-sa"):
        return None
    if lic.startswith("cc-") and "nc" in lic and "nd" in lic:
        return f"licença {lic}: reprodução só sem fins comerciais e sem alterar a figura; em curso vendido, pedir permissão ou redesenhar os dados"
    if lic.startswith("cc-") and "nc" in lic:
        return f"licença {lic}: uso não comercial; em curso vendido ou gravado para venda, pedir permissão ao editor ou redesenhar os dados"
    if lic.startswith("cc-") and "nd" in lic:
        return f"licença {lic}: reproduzir inteira e sem alterações (recortar um painel ou traduzir dentro da figura conta como alteração)"
    if lic == C.LICENCA_RESERVADA:
        return "todos os direitos reservados: uso em curso vendido ou gravado pode exigir permissão do editor; alternativa: redesenhar os dados com 'Adaptado de'"
    return "licença desconhecida: confirmar na página do artigo antes de usar em material vendido ou gravado"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Confere os recortes aprovados (resolução, branco, texto cortado, proporção, metadados) e gera a folha de contato final.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--todos", action="store_true", help="confere também os candidatos não aprovados")
    ap.add_argument("--apenas", nargs="+", metavar="CHAVE", help="confere só estes artigos")
    ap.add_argument("--estrito", action="store_true", help="código de saída 1 se algum recorte aprovado tiver problema")
    args = ap.parse_args()

    from PIL import Image

    aula = C.Aula(args.aula)
    aula.exigir()
    catalogo = C.carregar_catalogo(aula)
    if not catalogo:
        log(f"Catálogo vazio ({aula.catalogo}). Rode detectar_figuras.py e aprove recortes com recortar.py.")
        return 0
    alvo = [e for e in catalogo if (args.todos or e.get("aprovada")) and not e.get("rejeitada")
            and (not args.apenas or e.get("chave") in set(args.apenas))]
    if not alvo:
        log("Nenhum recorte aprovado ainda. Aprove com recortar.py --id ... --aprovar (ou use --todos para conferir os candidatos).")
        return 0

    palavras_cache: dict[tuple[str, int], list] = {}
    itens_folha = []
    n_prob = n_aviso = 0
    por_chave: dict[str, int] = {}
    for n, e in enumerate(sorted(alvo, key=lambda e: (e.get("chave", ""), e.get("pagina", 0), e["id"])), 1):
        erros: list[str] = []
        avisos: list[str] = []
        arq = aula.figuras / str(e.get("arquivo") or "")
        qc = {"cabe": None}
        if not e.get("arquivo") or not arq.exists():
            erros.append(f"arquivo não encontrado: {e.get('arquivo')}")
        else:
            try:
                with Image.open(arq) as im:
                    im.load()
                    img = im.convert("RGB")
            except Exception as ex:
                img = None
                erros.append(f"imagem não abre ({type(ex).__name__})")
            if img is not None:
                if (e.get("largura_px"), e.get("altura_px")) != (img.width, img.height):
                    avisos.append(f"tamanho no catálogo ({e.get('largura_px')}×{e.get('altura_px')}) difere do arquivo "
                                  f"({img.width}×{img.height}); catálogo corrigido")
                    e["largura_px"], e["altura_px"] = img.width, img.height
                palavras = None
                pdf = aula.pdf / f"{e.get('chave')}.pdf"
                simples = not e.get("paineis") and e.get("bbox_pt") and e.get("pagina")
                if simples and pdf.exists():
                    k = (e["chave"], int(e["pagina"]))
                    if k not in palavras_cache:
                        palavras_cache[k] = P.palavras_da_pagina(pdf, int(e["pagina"]))
                    palavras = palavras_cache[k]
                apagadas = [tuple(a["bbox_pt"]) for a in e.get("apagado_pt", [])]
                continua = None
                if simples and pdf.exists():
                    try:
                        continua = P.continua_fora(pdf, int(e["pagina"]), tuple(e["bbox_pt"]), apagadas)
                    except Exception:
                        continua = None
                qc = P.avaliar_recorte(img, tuple(e["bbox_pt"]) if simples else None, palavras,
                                       float(e.get("dpi") or 300), e.get("dpi_nativo"), apagadas, continua)
                erros += qc.pop("erros")
                avisos += qc.pop("avisos")
        if e.get("aprovada"):
            if e.get("tipo") not in TIPOS:
                avisos.append(f"tipo fora da lista ({e.get('tipo')!r}); use um de: {', '.join(sorted(TIPOS))}")
            faltam = [rot for rot, k in (("o que ensina", "o_que_ensina"), ("legenda em português", "legenda_pt"),
                                         ("citação", "citacao"), ("rótulo", "rotulo")) if not str(e.get(k) or "").strip()]
            if faltam:
                avisos.append("falta preencher: " + ", ".join(faltam))
        nota = nota_licenca(e.get("licenca"))
        e["qc"] = {**{k: v for k, v in qc.items()}, "ok": not erros, "erros": erros, "avisos": avisos,
                   "nota_licenca": nota, "conferido_em": C.agora()}
        n_prob += bool(erros)
        n_aviso += bool(avisos)
        por_chave[e.get("chave", "?")] = por_chave.get(e.get("chave", "?"), 0) + 1
        estado = "PROBLEMA" if erros else ("atenção " if avisos else "ok      ")
        marca = "" if e.get("aprovada") else "  [não aprovado]"
        log(f"{n:>2}. {estado} {e['id']:<28} {e.get('largura_px')}×{e.get('altura_px')} px · {qc.get('cabe') or '-'}"
            f" · {e.get('licenca')}{marca}")
        for x in erros:
            log(f"      PROBLEMA: {x}")
        for x in avisos:
            log(f"      aviso: {x}")
        if nota:
            log(f"      nota: {nota}")
        cor = (178, 58, 58) if erros else ((200, 130, 0) if avisos else (0, 122, 153))
        itens_folha.append({"img": arq, "numero": n, "cor": cor,
                            "linhas": [f"{e['id']} · {e.get('rotulo') or ''} · {e.get('tipo') or ''}",
                                       str(e.get("citacao") or "(sem citação)"),
                                       (f"{qc.get('cabe') or '-'} · {e.get('licenca')}"
                                        + (" · PROBLEMA" if erros else ""))]})
    C.salvar_catalogo(aula, catalogo)
    titulo = "Figuras aprovadas" if not args.todos else "Figuras (aprovadas e candidatas)"
    folhas = P.folha_contato(itens_folha, aula.figuras / "folha_contato.png", titulo=f"{titulo} — {aula.raiz.name}")

    log("")
    log(f"Resumo: {len(alvo)} recorte(s) conferido(s); {n_prob} com problema, {n_aviso} com aviso.")
    log("  Por artigo: " + ", ".join(f"{k} {v}" for k, v in sorted(por_chave.items())))
    restritas = sorted({e["id"] for e in alvo if nota_licenca(e.get("licenca"))})
    if restritas:
        log(f"  {len(restritas)} figura(s) com restrição de licença (ver notas acima): avisar o usuário antes de "
            "usar em curso vendido ou gravado.")
    if folhas:
        log("  Folha de contato para OLHAR: " + "  ".join(str(f) for f in folhas))
    log(f"  Catálogo atualizado: {aula.catalogo}")
    return 1 if (args.estrito and n_prob) else 0


if __name__ == "__main__":
    sys.exit(main())
