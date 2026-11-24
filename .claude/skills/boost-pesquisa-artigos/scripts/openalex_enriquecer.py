#!/usr/bin/env python3
"""Enriquece os registros com dados do OpenAlex e faz perseguição de citações.

Por DOI/PMID traz: contagem de citações, status de acesso aberto, licença e URL de PDF aberto.
Com --perseguir, parte de um artigo-sentinela e lista quem o cita e o que ele cita: é a forma
de achar artigos que usam vocabulário diferente do da sua string.

Uso:
  python3 openalex_enriquecer.py --pasta aulas/x/01_busca                       # enriquece tudo que está em brutos/
  python3 openalex_enriquecer.py --pasta aulas/x/01_busca --perseguir sentinelas --direcao ambos
  python3 openalex_enriquecer.py --pasta aulas/x/01_busca --perseguir 32571081 --direcao citam --de-ano 2021
  python3 openalex_enriquecer.py --doi 10.2519/jospt.2025.13182 --saida /tmp/x/openalex.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import os
import re

from _comum import (Cliente, ErroRede, agora_iso, autor_curto, carregar_conceitos, gravar_json, ler_json,
                    limpar_texto, lista_issn, normalizar_doi, normalizar_pmid, passa_filtro_local, sair)

API = "https://api.openalex.org/works"
CAMPOS_ENRIQ = ("id,doi,ids,title,publication_year,cited_by_count,open_access,best_oa_location,primary_location,"
                "type,is_retracted")
CAMPOS_REG = CAMPOS_ENRIQ + ",authorships,abstract_inverted_index,biblio"


def _params(cliente: Cliente, **extra) -> dict:
    p = {"mailto": cliente.email, **extra}
    if os.environ.get("OPENALEX_API_KEY"):
        p["api_key"] = os.environ["OPENALEX_API_KEY"]
    return p


def licenca_openalex(valor) -> str | None:
    if not valor:
        return None
    valor = str(valor).lower().replace("https://openalex.org/licenses/", "")
    return valor or None


def resumo_de_indice(indice: dict | None) -> str:
    """O OpenAlex guarda o resumo como índice invertido (palavra -> posições); aqui ele volta a ser texto."""
    if not indice:
        return ""
    posicoes = []
    for palavra, lugares in indice.items():
        for lugar in lugares:
            posicoes.append((lugar, palavra))
    return limpar_texto(" ".join(p for _, p in sorted(posicoes)))


def _nome_curto(nome: str) -> tuple[str, str]:
    """'Ann M. Cools' -> ('Cools AM', 'Cools'). Partículas (van, de, da...) ficam no sobrenome."""
    partes = (nome or "").split()
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], partes[0]
    corte = len(partes) - 1
    while corte > 1 and partes[corte - 1].lower() in ("van", "von", "de", "da", "do", "dos", "das", "der", "den",
                                                       "del", "della", "di", "la", "le", "ter", "ten"):
        corte -= 1
    sobrenome = " ".join(partes[corte:])
    return autor_curto(sobrenome, " ".join(partes[:corte])), sobrenome


def enriquecimento_de(obra: dict) -> dict:
    ids = obra.get("ids") or {}
    oa = obra.get("open_access") or {}
    melhor = obra.get("best_oa_location") or {}
    return {
        "doi": normalizar_doi(obra.get("doi")),
        "pmid": normalizar_pmid((ids.get("pmid") or "").rsplit("/", 1)[-1]) if ids.get("pmid") else None,
        "pmcid": ((ids.get("pmcid") or "").rstrip("/").rsplit("/", 1)[-1] or None) if ids.get("pmcid") else None,
        "openalex_id": (obra.get("id") or "").rsplit("/", 1)[-1],
        "citacoes": obra.get("cited_by_count"),
        "acesso_aberto": bool(oa.get("is_oa")),
        "status_oa": oa.get("oa_status"),
        "licenca": licenca_openalex(melhor.get("license")),
        "url_pdf_aberto": melhor.get("pdf_url") or None,
        "url_oa": oa.get("oa_url") or melhor.get("landing_page_url") or None,
        "versao_oa": melhor.get("version"),
        "ano": obra.get("publication_year"),
        "tipo_openalex": obra.get("type"),
        "retratado": bool(obra.get("is_retracted")),
    }


def registro_de(obra: dict) -> dict:
    """Converte uma obra do OpenAlex em registro bibliográfico (para a perseguição de citações)."""
    base = enriquecimento_de(obra)
    autores, primeiro = [], ""
    for i, a in enumerate(obra.get("authorships") or []):
        curto, sobrenome = _nome_curto((a.get("author") or {}).get("display_name") or a.get("raw_author_name") or "")
        if curto:
            autores.append(curto)
            if i == 0:
                primeiro = sobrenome
    fonte = ((obra.get("primary_location") or {}).get("source") or {})
    biblio = obra.get("biblio") or {}
    paginas = "-".join(x for x in (biblio.get("first_page"), biblio.get("last_page")) if x)
    return {
        "fonte": "openalex",
        "doi": base["doi"], "pmid": base["pmid"], "pmcid": base["pmcid"], "openalex_id": base["openalex_id"],
        "titulo": limpar_texto(obra.get("title")),
        "autores": autores, "primeiro_autor": primeiro,
        "ano": base["ano"],
        "revista": limpar_texto(fonte.get("display_name")),
        "issn": lista_issn(fonte.get("issn")),
        "volume": biblio.get("volume") or "", "fasciculo": biblio.get("issue") or "", "paginas": paginas,
        "resumo": resumo_de_indice(obra.get("abstract_inverted_index")),
        "tipo_openalex": base["tipo_openalex"],
        "citacoes": base["citacoes"], "acesso_aberto": base["acesso_aberto"], "status_oa": base["status_oa"],
        "licenca": base["licenca"], "url_pdf_aberto": base["url_pdf_aberto"], "url_oa": base["url_oa"],
        "retratado": base["retratado"],
    }


# --------------------------------------------------------------------------- chamadas

def buscar_por_ids(cliente: Cliente, campo: str, valores: list[str], campos: str, lote: int = 50):
    """Consulta em lotes (filtro com OR por '|'). Devolve (obras, erros)."""
    obras, erros = [], []
    for inicio in range(0, len(valores), lote):
        grupo = valores[inicio:inicio + lote]
        try:
            r = cliente.get(API, _params(cliente, filter=f"{campo}:{'|'.join(grupo)}", select=campos,
                                         **{"per-page": str(lote)})).json()
            obras += r.get("results") or []
        except ErroRede as exc:
            erros.append(f"lote de {len(grupo)} {campo}(s) a partir de '{grupo[0]}': {exc}")
        except ValueError:
            erros.append(f"lote de {campo}: resposta que não é JSON")
        print(f"  {campo}: {min(inicio + lote, len(valores))}/{len(valores)}", file=sys.stderr)
    return obras, erros


def listar_paginado(cliente: Cliente, filtro: str, maximo: int, ordem: str = "cited_by_count:desc"):
    """Lista obras de um filtro. Sem chave de API o OpenAlex só aceita paginação por número de página
    (até 10.000 resultados), que basta aqui; com OPENALEX_API_KEY usa cursor, sem esse teto."""
    obras, erros, total = [], [], None
    com_chave = bool(os.environ.get("OPENALEX_API_KEY"))
    cursor, pagina_n = "*", 1
    por_pagina = max(1, min(100, maximo))
    while len(obras) < maximo:
        extra = {"cursor": cursor} if com_chave else {"page": str(pagina_n)}
        try:
            r = cliente.get(API, _params(cliente, filter=filtro, select=CAMPOS_REG, sort=ordem,
                                         **{"per-page": str(por_pagina)}, **extra)).json()
        except ErroRede as exc:
            erros.append(str(exc))
            break
        except ValueError:
            erros.append("resposta que não é JSON")
            break
        meta = r.get("meta") or {}
        if total is None:
            total = meta.get("count", 0)
        pagina = r.get("results") or []
        obras += pagina
        if not pagina or len(obras) >= total:
            break
        if com_chave:
            cursor = meta.get("next_cursor")
            if not cursor:
                break
        else:
            pagina_n += 1
            if pagina_n * por_pagina > 10000:
                erros.append("limite de 10.000 resultados sem chave de API; defina OPENALEX_API_KEY para ir além")
                break
    return obras[:maximo], total or 0, erros


def resolver_obra(cliente: Cliente, identificador: str) -> dict | None:
    doi = normalizar_doi(identificador)
    campo, valor = ("doi", doi) if doi else ("pmid", normalizar_pmid(identificador))
    if not valor:
        return None
    obras, _ = buscar_por_ids(cliente, campo, [valor], CAMPOS_REG + ",referenced_works")
    return obras[0] if obras else None


# --------------------------------------------------------------------------- coleta de identificadores

def coletar_ids(pasta: Path) -> tuple[list[str], list[str]]:
    """Lê brutos/*.json e registros.json e devolve (DOIs, PMIDs sem DOI)."""
    dois: dict[str, None] = {}
    pmids: dict[str, None] = {}
    arquivos = [pasta / "brutos" / n for n in ("pubmed.json", "crossref.json", "scopus.json", "openalex.json")]
    arquivos.append(pasta / "registros.json")
    for arq in arquivos:
        dados = ler_json(arq)
        if not dados:
            continue
        registros = dados if isinstance(dados, list) else dados.get("registros", [])
        for r in registros:
            doi = normalizar_doi(r.get("doi"))
            if doi:
                dois[doi] = None
            elif normalizar_pmid(r.get("pmid")):
                pmids[normalizar_pmid(r.get("pmid"))] = None
    return list(dois), list(pmids)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OpenAlex: citações, acesso aberto, licença e PDF aberto por DOI/PMID; perseguição de citações "
                    "a partir de artigos-sentinela. Grava brutos/openalex.json.")
    ap.add_argument("--pasta", help="pasta 01_busca da aula (lê brutos/*.json e conceitos.json)")
    ap.add_argument("--doi", help="DOIs separados por vírgula (além dos encontrados em --pasta)")
    ap.add_argument("--pmid", help="PMIDs separados por vírgula")
    ap.add_argument("--perseguir", help="'sentinelas' (os de conceitos.json) ou PMIDs/DOIs separados por vírgula")
    ap.add_argument("--direcao", default="ambos", choices=["citam", "citados", "ambos"],
                    help="citam = quem cita o sentinela; citados = o que o sentinela cita (padrão ambos)")
    ap.add_argument("--max-citam", type=int, default=200, help="máximo de artigos que citam, por sentinela (padrão 200, "
                                                              "os mais citados primeiro)")
    ap.add_argument("--de-ano", type=int, help="na perseguição para a frente (quem cita o sentinela), só artigos "
                                                "publicados a partir deste ano. Para trás (o que o sentinela cita) "
                                                "vale o ano inicial de conceitos.json, para não perder os clássicos")
    ap.add_argument("--filtro-local", default="ancora", choices=["ancora", "auto", "um", "todos", "nenhum"],
                    help="filtro dos artigos perseguidos pelos blocos de conceito: 'ancora' exige o bloco da "
                         "condição (papel P) no titulo/resumo (padrão)")
    ap.add_argument("--so-perseguir", action="store_true", help="não refaz o enriquecimento")
    ap.add_argument("--saida", help="arquivo de saída (padrão: <pasta>/brutos/openalex.json)")
    ap.add_argument("--email", help="e-mail de contato (mailto) enviado ao OpenAlex (ou variável BOOST_EMAIL)")
    args = ap.parse_args(argv)

    pasta = Path(args.pasta).resolve() if args.pasta else None
    if not pasta and not args.saida:
        sair("informe --pasta ou --saida")
    destino = Path(args.saida) if args.saida else pasta / "brutos" / "openalex.json"
    conceitos = None
    if pasta and (pasta / "conceitos.json").exists():
        conceitos = carregar_conceitos(pasta / "conceitos.json")

    try:
        cliente = Cliente(args.email)
    except ErroRede as exc:
        sair(str(exc))

    saida = ler_json(destino)
    if not saida or not isinstance(saida, dict):
        saida = {"fonte": "openalex", "execucoes": [], "enriquecimento": [], "registros": []}
    saida.setdefault("execucoes", [])
    saida.setdefault("enriquecimento", [])
    saida.setdefault("registros", [])
    falhou = False

    # ------------------------------------------------------------------ enriquecimento
    if not args.so_perseguir:
        dois, pmids = coletar_ids(pasta) if pasta else ([], [])
        for d in re.split(r"[,\s;]+", args.doi or ""):
            if normalizar_doi(d) and normalizar_doi(d) not in dois:
                dois.append(normalizar_doi(d))
        for p in re.split(r"[,\s;]+", args.pmid or ""):
            if normalizar_pmid(p) and normalizar_pmid(p) not in pmids:
                pmids.append(normalizar_pmid(p))
        if dois or pmids:
            print(f"=== OpenAlex | enriquecimento de {len(dois)} DOI(s) e {len(pmids)} PMID(s) sem DOI ===")
            obras, erros = buscar_por_ids(cliente, "doi", dois, CAMPOS_ENRIQ)
            obras_p, erros_p = buscar_por_ids(cliente, "pmid", pmids, CAMPOS_ENRIQ) if pmids else ([], [])
            erros += erros_p
            indice = {}
            for e in saida["enriquecimento"]:
                indice[e.get("doi") or f"pmid:{e.get('pmid')}"] = e
            achados = 0
            for obra in obras + obras_p:
                try:
                    e = enriquecimento_de(obra)
                except Exception as exc:  # noqa: BLE001
                    erros.append(f"obra {obra.get('id')}: {type(exc).__name__}: {exc}")
                    continue
                indice[e.get("doi") or f"pmid:{e.get('pmid')}"] = e
                achados += 1
            saida["enriquecimento"] = list(indice.values())
            abertos = sum(1 for e in saida["enriquecimento"] if e["acesso_aberto"])
            com_pdf = sum(1 for e in saida["enriquecimento"] if e["url_pdf_aberto"])
            pedidos = len(dois) + len(pmids)
            saida["execucoes"].append({"data": agora_iso(), "operacao": "enriquecimento",
                                       "detalhe": f"{pedidos} identificadores pedidos, {achados} encontrados",
                                       "registros": achados, "avisos": erros})
            print(f"Encontrados no OpenAlex: {achados} de {pedidos}")
            print(f"Acesso aberto: {abertos} | com URL de PDF aberto: {com_pdf} (total acumulado: "
                  f"{len(saida['enriquecimento'])})")
            for e in erros:
                print(f"  aviso: {e}")
            falhou = falhou or (bool(erros) and not achados)
        elif not args.perseguir:
            sair("nada para enriquecer: nenhum DOI/PMID em --pasta, --doi ou --pmid")

    # ------------------------------------------------------------------ perseguição de citações
    if args.perseguir:
        if args.perseguir.strip().lower() == "sentinelas":
            if not conceitos or not conceitos["sentinelas"]:
                sair("--perseguir sentinelas precisa de conceitos.json com 'sentinelas' em --pasta")
            alvos = [s["doi"] or s["pmid"] for s in conceitos["sentinelas"]]
        else:
            alvos = [x for x in re.split(r"[,\s;]+", args.perseguir) if x]
        por_chave = {(r.get("doi") or r.get("openalex_id")): r for r in saida["registros"]}
        for alvo in alvos:
            print(f"\n=== OpenAlex | perseguição de citações a partir de {alvo} ===")
            try:
                obra = resolver_obra(cliente, alvo)
            except ErroRede as exc:
                print(f"  FALHA: {exc}")
                falhou = True
                continue
            if not obra:
                print("  não encontrado no OpenAlex; pulei.")
                continue
            wid = obra["id"].rsplit("/", 1)[-1]
            print(f"  {limpar_texto(obra.get('title'))[:110]} ({obra.get('publication_year')}) - "
                  f"{obra.get('cited_by_count')} citações, {len(obra.get('referenced_works') or [])} referências")
            lotes = []
            if args.direcao in ("citam", "ambos"):
                filtro = f"cites:{wid}" + (f",from_publication_date:{args.de_ano}-01-01" if args.de_ano else "")
                obras, total, erros = listar_paginado(cliente, filtro, args.max_citam)
                lotes.append(("cita o sentinela", obras, total, erros))
            if args.direcao in ("citados", "ambos"):
                # Para trás, --de-ano cortaria justamente os artigos fundadores que o sentinela cita (um consenso
                # de 2016 citado pela diretriz de 2023 sumia com --de-ano 2018). Vale o limite da busca.
                ano_tras = ((conceitos or {}).get("limites") or {}).get("ano_inicio")
                filtro = f"cited_by:{wid}" + (f",from_publication_date:{ano_tras}-01-01" if ano_tras else "")
                obras, total, erros = listar_paginado(cliente, filtro, 500)
                lotes.append(("citado pelo sentinela", obras, total, erros))
            for relacao, obras, total, erros in lotes:
                mantidos = novos = 0
                for o in obras:
                    try:
                        reg = registro_de(o)
                    except Exception as exc:  # noqa: BLE001
                        erros.append(f"obra {o.get('id')}: {type(exc).__name__}: {exc}")
                        continue
                    if not reg["titulo"] or not passa_filtro_local(reg, conceitos, args.filtro_local):
                        continue
                    mantidos += 1
                    chave = reg["doi"] or reg["openalex_id"]
                    marca = {"sentinela": alvo, "relacao": relacao}
                    if chave in por_chave:
                        origem = por_chave[chave].setdefault("origem_citacao", [])
                        if marca not in origem:
                            origem.append(marca)
                    else:
                        reg["origem_citacao"] = [marca]
                        por_chave[chave] = reg
                        saida["registros"].append(reg)
                        novos += 1
                saida["execucoes"].append({"data": agora_iso(), "operacao": f"perseguição ({relacao})",
                                           "detalhe": f"sentinela {alvo}: {total} na base, {len(obras)} lidos, "
                                                      f"{mantidos} após o filtro '{args.filtro_local}'",
                                           "registros": novos, "avisos": erros})
                print(f"  {relacao}: {total} na base | lidos {len(obras)} | mantidos {mantidos} | novos {novos}")
                for e in erros:
                    print(f"    aviso: {e}")
                    falhou = True

    gravar_json(destino, saida)
    print(f"\nGravado: {destino} ({len(saida['enriquecimento'])} enriquecidos, "
          f"{len(saida['registros'])} registros de perseguição de citações)")
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main())
