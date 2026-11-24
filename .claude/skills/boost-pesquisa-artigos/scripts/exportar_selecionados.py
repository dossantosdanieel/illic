#!/usr/bin/env python3
"""Lê as decisões de triagem.xlsx e grava selecionados.json (os artigos incluídos, com o papel na aula).

É o arquivo que as próximas etapas consomem (download dos PDFs, leitura, slides). Cada item e o
registro completo de registros.json acrescido de 'papel', 'decisao' e 'observacoes'.

Uso:
  python3 exportar_selecionados.py --pasta aulas/x/01_busca
  python3 exportar_selecionados.py --pasta aulas/x/01_busca --incluir-talvez
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
from collections import Counter

from _comum import agora_iso, gravar_json, ler_json, sair
from consolidar import CAMPOS_DECISAO, ler_planilha_anterior


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Gera selecionados.json a partir das decisões preenchidas em triagem.xlsx.")
    ap.add_argument("--pasta", required=True, help="pasta 01_busca da aula (com registros.json e triagem.xlsx)")
    ap.add_argument("--incluir-talvez", action="store_true",
                    help="leva também os marcados como 'talvez' (para decidir depois de ler o texto completo)")
    ap.add_argument("--saida", help="arquivo de saída (padrão: <pasta>/selecionados.json)")
    args = ap.parse_args(argv)

    pasta = Path(args.pasta).resolve()
    registros = ler_json(pasta / "registros.json")
    if not registros:
        sair(f"não achei {pasta / 'registros.json'}. Rode consolidar.py antes.")
    planilha = pasta / "triagem.xlsx"
    if not planilha.exists():
        sair(f"não achei {planilha}. Rode consolidar.py antes.")
    try:
        decisoes, _, fora = ler_planilha_anterior(planilha)
    except Exception as exc:  # noqa: BLE001
        sair(f"não consegui ler {planilha} ({type(exc).__name__}: {exc}). Feche o arquivo e tente de novo.", 1)

    por_chave = {r["chave"]: r for r in registros}
    aceitas = {"incluir", "talvez"} if args.incluir_talvez else {"incluir"}
    contagem = Counter((d.get("decisao") or "sem decisão") for d in decisoes.values())
    motivos = Counter(d.get("motivo") or "(sem motivo)" for d in decisoes.values() if d.get("decisao") == "excluir")
    selecionados, sem_papel, orfas = [], [], []
    for chave, d in decisoes.items():
        if d.get("decisao") not in aceitas:
            continue
        reg = por_chave.get(chave)
        if not reg:
            orfas.append(chave)
            continue
        item = dict(reg)
        item["decisao"] = d["decisao"]
        item["papel"] = d.get("papel") or ""
        item["observacoes"] = d.get("observacoes") or ""
        if not item["papel"]:
            sem_papel.append(chave)
        selecionados.append(item)
    selecionados.sort(key=lambda r: (-r.get("pontuacao", 0), r["chave"]))

    destino = Path(args.saida) if args.saida else pasta / "selecionados.json"
    gravar_json(destino, selecionados)

    fluxo = ler_json(pasta / "fluxo.json") or {}
    fluxo["triagem"] = {"data": agora_iso(), "incluidos": contagem.get("incluir", 0),
                        "excluidos": contagem.get("excluir", 0), "talvez": contagem.get("talvez", 0),
                        "sem_decisao": len(registros) - sum(contagem.get(k, 0) for k in ("incluir", "excluir", "talvez")),
                        "excluidos_por_motivo": dict(motivos)}
    gravar_json(pasta / "fluxo.json", fluxo)

    print("=== Selecionados para a aula ===")
    print(f"Registros únicos: {len(registros)} | incluir: {contagem.get('incluir', 0)} | "
          f"excluir: {contagem.get('excluir', 0)} | talvez: {contagem.get('talvez', 0)} | "
          f"sem decisão: {fluxo['triagem']['sem_decisao']}")
    if motivos:
        print("Excluídos por motivo: " + "; ".join(f"{m}: {n}" for m, n in motivos.most_common()))
    print(f"Por desenho: " + "; ".join(f"{d}: {n}" for d, n in Counter(r["desenho"] for r in selecionados).most_common()))
    for r in selecionados:
        oa = {True: "aberto", False: "pago"}.get(r.get("acesso_aberto"), "acesso ?")
        print(f"  {r['chave'].ljust(20)} {r['desenho'][:24].ljust(24)} {oa.ljust(8)} papel: {r['papel'] or '(vazio)'}")
    if sem_papel:
        print(f"\nATENÇÃO: {len(sem_papel)} incluído(s) sem 'Papel na aula': {', '.join(sem_papel)}. "
              f"Preencha: é o papel que orienta a leitura e os slides.")
    if orfas:
        print(f"ATENÇÃO: {len(orfas)} chave(s) da planilha não existem em registros.json: {', '.join(orfas)}")
    if fluxo["triagem"]["sem_decisao"]:
        print(f"Aviso: {fluxo['triagem']['sem_decisao']} registro(s) ainda sem decisão na planilha.")
    if not selecionados:
        print("Nenhum artigo marcado como 'incluir'. Preencha a coluna Decisão de triagem.xlsx.")
    print(f"\nGravado: {destino} ({len(selecionados)} artigos)")
    return 0 if selecionados else 1


if __name__ == "__main__":
    raise SystemExit(main())
