#!/usr/bin/env python3
"""Busca na Crossref por revista (ISSN) e grava brutos/crossref.json.

É por aqui que o JOSPT entra sem depender do site da revista (que bloqueia robôs): a Crossref
tem todos os DOIs 10.2519. O padrão já consulta o JOSPT; --issn ou as 'revistas_alvo' de
conceitos.json trocam o alvo. A Crossref não entende booleanos: recebe palavras, ordena por
relevância e o script filtra localmente pelos blocos de conceito.

Uso:
  python3 crossref_busca.py --conceitos aulas/x/01_busca/conceitos.json            # JOSPT + revistas-alvo
  python3 crossref_busca.py --conceitos conceitos.json --varrer --de-ano 2023      # lê a revista inteira e filtra
  python3 crossref_busca.py --consulta "rotator cuff exercise" --issn 0306-3674,1473-0480 --saida brutos/crossref.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import re
from datetime import date

from _comum import (JOSPT, Cliente, ErroRede, json_com, agora_iso, autor_curto, carregar_conceitos, gravar_json,
                    issns_alvo, ler_json, limpar_texto, lista_issn, normalizar_doi, passa_filtro_local, sair)
import montar_strings as ms

API = "https://api.crossref.org/works"
CAMPOS = ("DOI,title,subtitle,author,issued,published,container-title,short-container-title,ISSN,type,abstract,"
          "is-referenced-by-count,license,URL,volume,issue,page,score")


def licenca_curta(licencas) -> str | None:
    """Reduz a URL da licença a um rótulo ('cc-by', 'cc-by-nc-nd'...). Licenças de editora viram None."""
    for lic in licencas or []:
        url = (lic.get("URL") or "").lower()
        achado = re.search(r"creativecommons\.org/licenses/([a-z\-]+)", url)
        if achado:
            return "cc-" + achado.group(1)
        if "creativecommons.org/publicdomain" in url:
            return "cc0"
    return None


def converter(item: dict) -> dict:
    titulo = limpar_texto(" ".join(item.get("title") or []))
    subtitulo = limpar_texto(" ".join(item.get("subtitle") or []))
    if subtitulo and subtitulo.lower() not in titulo.lower():
        titulo = f"{titulo}: {subtitulo}"
    autores = []
    for a in item.get("author") or []:
        if a.get("family"):
            autores.append(autor_curto(a["family"], a.get("given", "")))
        elif a.get("name"):
            autores.append(a["name"])
    primeiro = ""
    if item.get("author"):
        primeiro = item["author"][0].get("family") or item["author"][0].get("name") or ""
    ano = None
    for chave in ("issued", "published"):
        partes = (item.get(chave) or {}).get("date-parts") or [[None]]
        if partes and partes[0] and partes[0][0]:
            ano = int(partes[0][0])
            break
    curta = item.get("short-container-title") or []
    longa = item.get("container-title") or []
    return {
        "fonte": "crossref",
        "doi": normalizar_doi(item.get("DOI")),
        "titulo": titulo,
        "autores": autores,
        "primeiro_autor": primeiro,
        "ano": ano,
        "revista": limpar_texto((curta or longa or [""])[0]),
        "revista_completa": limpar_texto((longa or [""])[0]),
        "issn": lista_issn(item.get("ISSN")),
        "volume": item.get("volume") or "",
        "fasciculo": item.get("issue") or "",
        "paginas": item.get("page") or "",
        "tipo_crossref": item.get("type") or "",
        "resumo": limpar_texto(item.get("abstract")),
        "citacoes_crossref": item.get("is-referenced-by-count"),
        "licenca": licenca_curta(item.get("license")),
        "url": item.get("URL") or "",
        "relevancia_crossref": item.get("score"),
    }


def buscar(cliente: Cliente, consulta: str | None, issns: list[str], de_ano: int | None, ate_ano: int | None,
           tipo: str | None, maximo: int, linhas: int = 100):
    """Devolve (itens, total_na_base, erros, modo).

    A Crossref só ordena por relevância na paginação por offset; com cursor a ordem é a do índice.
    Por isso: se o conjunto inteiro cabe em 'maximo', lê tudo por cursor (cobertura completa, a ordem
    não importa porque o filtro local decide); se não cabe, lê os 'maximo' mais relevantes por offset.
    """
    filtros = [f"issn:{i}" for i in issns]
    if de_ano:
        filtros.append(f"from-pub-date:{de_ano}-01-01")
    if ate_ano:
        filtros.append(f"until-pub-date:{ate_ano}-12-31")
    if tipo:
        filtros.append(f"type:{tipo}")
    base = {"mailto": cliente.email, "select": CAMPOS}
    if filtros:
        base["filter"] = ",".join(filtros)
    if consulta:
        base["query.bibliographic"] = consulta
    erros: list[str] = []
    try:
        total = json_com(cliente.get(API, {**base, "rows": "0"}), "message", "a Crossref")["message"].get(
            "total-results", 0)
    except (ErroRede, ValueError) as exc:
        return [], 0, [f"contagem inicial falhou: {exc}"], "falha"
    if total == 0:
        return [], 0, erros, "vazio"
    modo = "cursor" if total <= maximo else "relevancia"
    if modo == "relevancia" and not consulta:
        modo = "cursor"  # varredura sem consulta: não há relevância; lê os primeiros do índice e avisa
    itens: list[dict] = []
    params = {**base, "rows": str(min(linhas, maximo))}
    if modo == "cursor":
        params["cursor"] = "*"
    else:
        params["offset"] = "0"
    while len(itens) < min(maximo, total):
        try:
            msg = json_com(cliente.get(API, params), "message", "a Crossref")["message"]
        except ErroRede as exc:
            erros.append(str(exc))
            break
        except ValueError:
            erros.append("a Crossref devolveu uma resposta que não é JSON")
            break
        pagina = msg.get("items") or []
        if not pagina:
            break
        itens += pagina
        print(f"  lidos {min(len(itens), maximo)}/{min(total, maximo)}", file=sys.stderr)
        if modo == "cursor":
            if not msg.get("next-cursor"):
                break
            params["cursor"] = msg["next-cursor"]
        else:
            params["offset"] = str(len(itens))
            if len(itens) >= 10000:
                break
    return itens[:maximo], total, erros, modo


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Busca na Crossref por ISSN (padrão: JOSPT) com consulta bibliográfica e paginação por cursor; "
                    "grava brutos/crossref.json.")
    ap.add_argument("--conceitos", help="conceitos.json: fornece a consulta, as revistas-alvo, os anos e o filtro local")
    ap.add_argument("--consulta", help="palavras da consulta (sem operadores). Padrão: derivada de conceitos.json")
    ap.add_argument("--issn", help="ISSNs separados por vírgula. Padrão: JOSPT (0190-6011, 1938-1344) mais as "
                                   "revistas-alvo de conceitos.json")
    ap.add_argument("--todas-as-revistas", action="store_true", help="não restringe por ISSN (busca na Crossref inteira)")
    ap.add_argument("--varrer", action="store_true",
                    help="ignora a consulta: lê todos os artigos das revistas no período e filtra localmente pelos "
                         "blocos (mais sensível; use com --de-ano)")
    ap.add_argument("--de-ano", type=int, help="ano inicial (padrão: limites de conceitos.json)")
    ap.add_argument("--ate-ano", type=int, help="ano final")
    ap.add_argument("--tipo", default="journal-article", help="tipo Crossref (padrão journal-article; vazio = todos)")
    ap.add_argument("--max", type=int, default=2000,
                    help="máximo de registros lidos da Crossref (padrão 2000). Se o total couber, lê tudo por cursor; "
                         "se não couber, lê os mais relevantes")
    ap.add_argument("--filtro-local", default="auto", choices=["auto", "ancora", "todos", "um", "nenhum"],
                    help="filtro pelos blocos de conceito após baixar. auto (padrão): com resumo exige todos os "
                         "blocos; sem resumo, o bloco da condição no título; diretrizes passam só com a condição. "
                         "ancora: só o bloco da condição. todos / um / nenhum: literal")
    ap.add_argument("--saida", help="arquivo de saída (padrão: <pasta de conceitos>/brutos/crossref.json)")
    ap.add_argument("--substituir", action="store_true", help="começa o arquivo do zero (padrão: acumula)")
    ap.add_argument("--hoje", help="data de referência AAAA-MM-DD para o recorte 'fronteira'")
    ap.add_argument("--email", help="e-mail de contato (mailto) enviado a Crossref (ou variável BOOST_EMAIL)")
    args = ap.parse_args(argv)

    conceitos = None
    pasta = None
    if args.conceitos:
        conceitos = carregar_conceitos(args.conceitos)
        ms.aplicar_recorte(conceitos, date.fromisoformat(args.hoje) if args.hoje else date.today())
        pasta = Path(args.conceitos).resolve().parent
    consulta = None if args.varrer else (args.consulta or (ms.montar_crossref(conceitos) if conceitos else None))
    if not consulta and not args.varrer:
        sair("informe --consulta, --conceitos ou --varrer")
    if args.varrer and not conceitos and args.filtro_local != "nenhum":
        sair("--varrer sem --conceitos traria a revista inteira; passe --conceitos ou --filtro-local nenhum")

    if args.todas_as_revistas:
        issns: list[str] = []
    elif args.issn:
        issns = lista_issn(args.issn)
        if not issns:
            sair(f"nenhum ISSN válido em --issn '{args.issn}'")
    else:
        issns = list(JOSPT["issn"])
        for i in issns_alvo(conceitos):
            if i not in issns:
                issns.append(i)
    de_ano = args.de_ano or (conceitos["limites"]["ano_inicio"] if conceitos else None)
    ate_ano = args.ate_ano or (conceitos["limites"]["ano_fim"] if conceitos else None)

    if args.saida:
        destino = Path(args.saida)
    elif pasta:
        destino = pasta / "brutos" / "crossref.json"
    else:
        sair("informe --saida (sem --conceitos não há pasta padrão)")

    try:
        cliente = Cliente(args.email)
    except ErroRede as exc:
        sair(str(exc))

    print("=== Crossref ===")
    print(f"Consulta: {consulta or '(varredura da revista inteira)'}")
    print(f"ISSNs: {', '.join(issns) or 'todos'} | anos: {de_ano or '-'} a {ate_ano or '-'} | máximo: {args.max}")
    itens, total, erros, modo = buscar(cliente, consulta, issns, de_ano, ate_ano, args.tipo or None, args.max)
    registros, descartados, sem_doi = [], 0, 0
    for item in itens:
        try:
            reg = converter(item)
        except Exception as exc:  # noqa: BLE001 - um item ruim não para o lote
            erros.append(f"item {item.get('DOI')}: {type(exc).__name__}: {exc}")
            continue
        if not reg["doi"] or not reg["titulo"]:
            sem_doi += 1
            continue
        if passa_filtro_local(reg, conceitos, args.filtro_local):
            reg["sem_resumo"] = not bool(reg["resumo"])
            registros.append(reg)
        else:
            descartados += 1

    substituir = args.substituir
    if substituir and not itens and erros and ler_json(destino):
        # sem rede (ou Crossref fora do ar) não se apaga o que já foi baixado
        print("AVISO: nada foi lido da Crossref; --substituir ignorado para não apagar o arquivo existente.")
        substituir = False
    saida = None if substituir else ler_json(destino)
    if not saida or not isinstance(saida, dict):
        saida = {"fonte": "crossref", "execucoes": [], "registros": []}
    por_doi = {r["doi"]: r for r in saida.get("registros", [])}
    novos = 0
    for r in registros:
        if r["doi"] not in por_doi:
            novos += 1
        por_doi[r["doi"]] = r
    saida["registros"] = list(por_doi.values())
    saida.setdefault("execucoes", []).append({
        "data": agora_iso(), "consulta": consulta or "(varredura)", "issn": issns, "de_ano": de_ano,
        "ate_ano": ate_ano, "total": total, "modo": modo, "lidos": len(itens), "mantidos": len(registros), "novos": novos,
        "filtro_local": args.filtro_local if conceitos else "nenhum", "avisos": erros})
    gravar_json(destino, saida)

    com_resumo = sum(1 for r in registros if r["resumo"])
    print(f"Total na Crossref para esses filtros: {total}")
    print(f"Lidos: {len(itens)} | mantidos após o filtro local: {len(registros)} | descartados: {descartados}"
          + (f" | sem DOI/titulo: {sem_doi}" if sem_doi else ""))
    print(f"Com resumo depositado: {com_resumo} de {len(registros)} (a Crossref só tem resumo quando a editora deposita)")
    if modo == "cursor" and total <= len(itens):
        print("Cobertura: todos os resultados da Crossref para esses filtros foram lidos (paginação por cursor).")
    elif total > len(itens):
        if consulta:
            print(f"AVISO: há {total} resultados e só os {len(itens)} mais relevantes foram lidos. Aumente --max, "
                  f"restrinja os anos, ou use --varrer com --de-ano para cobrir a revista inteira.")
        else:
            print(f"AVISO: a varredura parou em {len(itens)} de {total}. Aumente --max ou restrinja com --de-ano.")
    for e in erros:
        print(f"  aviso: {e}")
    print(f"Gravado: {destino} ({len(saida['registros'])} registros, {novos} novos)")
    return 1 if erros and not registros else 0


if __name__ == "__main__":
    raise SystemExit(main())
