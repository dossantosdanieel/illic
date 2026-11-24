#!/usr/bin/env python3
"""Teste de sensibilidade: a estratégia recupera os artigos que ela TEM de recuperar?

Para cada artigo-sentinela (PMID/DOI que você já sabe ser relevante), pergunta ao PubMed se a
string o encontra. Para os perdidos, testa bloco por bloco, os limites e o filtro de desenho, e
mostra os descritores MeSH e as palavras do título/palavras-chave do artigo que não estão nos
blocos: e daí que saem os termos que faltam.

Uso:
  python3 teste_sentinela.py --conceitos aulas/x/01_busca/conceitos.json
  python3 teste_sentinela.py --conceitos conceitos.json --variante base,rs,ecr
  python3 teste_sentinela.py --conceitos conceitos.json --pmids 32571081,22349588 --dois 10.2519/jospt.2025.13182

Código de saída: 0 se a variante 'base' recuperou todos; 1 se perdeu algum; 2 em erro de uso.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import re
from datetime import date

from _comum import (Cliente, ErroRede, agora_iso, bloco_casa_texto, carregar_conceitos, gravar_json, ler_json,
                    normalizar_doi, normalizar_pmid, sair, sem_acento, termo_para_regex)
import montar_strings as ms
import pubmed_busca as pb

VAZIAS = set("""a an the of and or in on for to with without by from at as is are was were be been versus vs
after before during between among into than that this these those their its it we our study trial randomized
randomised controlled clinical systematic review meta analysis effect effects effectiveness efficacy patients
patient adults adult using use compared comparison among results outcomes outcome protocol pilot does do can
not no more less better new one two three months weeks years year month week care treatment therapy
management based evidence primary secondary double blind single group groups""".split())


# "check tags" e descritores de método: aparecem em quase todo registro e não ajudam a montar bloco
MESH_GENERICOS = {"Humans", "Male", "Female", "Adult", "Middle Aged", "Aged", "Aged, 80 and over", "Young Adult",
                  "Adolescent", "Child", "Animals", "Treatment Outcome", "Follow-Up Studies", "Prospective Studies",
                  "Retrospective Studies", "Double-Blind Method", "Single-Blind Method", "Time Factors",
                  "Surveys and Questionnaires", "Reproducibility of Results", "Cross-Sectional Studies"}


def filtrar_ids(cliente: Cliente, consulta: str, pmids: list[str]) -> set[str]:
    """Quais destes PMIDs a consulta recupera? Uma chamada só."""
    if not pmids:
        return set()
    ids = " OR ".join(f"{p}[uid]" for p in pmids)
    res = pb.esearch(cliente, f"({consulta}) AND ({ids})", historico=False, retmax=len(pmids) + 5)
    return set(res["ids"])


def resolver_doi(cliente: Cliente, doi: str) -> str | None:
    res = pb.esearch(cliente, f'"{doi}"[aid]', historico=False, retmax=3)
    return res["ids"][0] if len(res["ids"]) == 1 else None


def presenca_em_brutos(pasta: Path) -> dict:
    """Índice (pmid/doi -> fontes) do que já foi baixado, para dizer onde cada sentinela apareceu."""
    indice: dict[str, set] = {}
    for nome in ("pubmed", "crossref", "scopus", "openalex"):
        dados = ler_json(pasta / "brutos" / f"{nome}.json")
        for r in (dados or {}).get("registros", []):
            for chave in (normalizar_pmid(r.get("pmid")), normalizar_doi(r.get("doi"))):
                if chave:
                    indice.setdefault(chave, set()).add(nome)
    return indice


def palavras_fora_do_bloco(texto: str, bloco: dict) -> list[str]:
    """Palavras do texto que nenhum termo livre do bloco cobre (candidatas a entrar no bloco)."""
    padroes = [termo_para_regex(t) for t in bloco["livres"]]
    saida = []
    for palavra in re.findall(r"[a-z][a-z\-]{2,}", sem_acento(texto).lower()):
        if palavra in VAZIAS or palavra in saida:
            continue
        if any(p.search(palavra) for p in padroes):
            continue
        saida.append(palavra)
    return saida


def diagnosticar(cliente: Cliente, conceitos: dict, variante: str, perdidos: list[str], registros: dict) -> dict:
    """Para os perdidos, descobre que parte da string os eliminou."""
    componentes: list[tuple[str, str, str]] = []  # (tipo, id, consulta)
    for b in conceitos["blocos"]:
        componentes.append(("bloco", b["id"], ms.bloco_pubmed(b, [])))
    limites = ms.limites_pubmed(conceitos)
    for lim in limites:
        componentes.append(("limite", lim, lim))
    if conceitos["limites"]["somente_humanos"]:
        componentes.append(("limite", "somente humanos", "all[sb] NOT (animals[mh] NOT humans[mh])"))
    if variante in ms.FILTROS:
        componentes.append(("filtro", variante, ms.FILTROS[variante]["pubmed"]))
    elif variante == "revistas":
        componentes.append(("filtro", "revistas-alvo", ms.jornal_pubmed(conceitos)))
    exc = ms.exclusao_pubmed(conceitos)
    falhas: dict[str, list[tuple[str, str]]] = {p: [] for p in perdidos}
    for tipo, ident, consulta in componentes:
        try:
            passam = filtrar_ids(cliente, consulta, perdidos)
        except ErroRede as exc_rede:
            print(f"  (não consegui testar {tipo} '{ident}': {exc_rede})")
            continue
        for p in perdidos:
            if p not in passam:
                falhas[p].append((tipo, ident))
    if exc:
        try:
            pegos = filtrar_ids(cliente, exc, perdidos)
            for p in pegos:
                falhas[p].append(("exclusao", "bloco NOT"))
        except ErroRede:
            pass
    saida = {}
    for p in perdidos:
        reg = registros.get(p, {})
        info = {"falhas": falhas[p], "blocos_falhos": [i for t, i in falhas[p] if t == "bloco"], "sugestoes": {}}
        for b in conceitos["blocos"]:
            if b["id"] not in info["blocos_falhos"]:
                continue
            tem = {m["termo"].lower() for m in b["mesh"]}
            texto_titulo = reg.get("titulo", "")
            info["sugestoes"][b["id"]] = {
                "mesh_do_artigo_fora_do_bloco": [
                    m + ("*" if m in reg.get("mesh_principal", []) else "")
                    for m in reg.get("mesh", []) if m.lower() not in tem and m not in MESH_GENERICOS],
                "palavras_do_titulo_fora_do_bloco": palavras_fora_do_bloco(texto_titulo, b),
                "palavras_chave_do_autor": reg.get("palavras_chave", []),
                "casa_no_texto_local": bloco_casa_texto(b, f"{texto_titulo} . {reg.get('resumo', '')}"),
            }
        saida[p] = info
    return saida


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Teste de sentinela: confere se a estratégia recupera os artigos que deveria e explica as perdas.")
    ap.add_argument("--conceitos", required=True, help="conceitos.json (traz os blocos e a lista 'sentinelas')")
    ap.add_argument("--pmids", help="PMIDs extras, separados por vírgula")
    ap.add_argument("--dois", help="DOIs extras, separados por vírgula")
    ap.add_argument("--variante", default="base",
                    help="variante(s) a testar, separadas por vírgula (padrão base). O código de saída considera "
                         "a primeira")
    ap.add_argument("--saida", help="arquivo JSON do relatório (padrão: <pasta de conceitos>/sentinelas.json)")
    ap.add_argument("--hoje", help="data de referência AAAA-MM-DD para o recorte 'fronteira'")
    ap.add_argument("--email", help="e-mail de contato enviado ao NCBI (ou variável BOOST_EMAIL)")
    args = ap.parse_args(argv)

    conceitos = carregar_conceitos(args.conceitos)
    ms.aplicar_recorte(conceitos, date.fromisoformat(args.hoje) if args.hoje else date.today())
    pasta = Path(args.conceitos).resolve().parent
    destino = Path(args.saida) if args.saida else pasta / "sentinelas.json"

    sentinelas = [dict(s) for s in conceitos["sentinelas"]]
    for p in re.split(r"[,\s;]+", args.pmids or ""):
        if normalizar_pmid(p):
            sentinelas.append({"pmid": normalizar_pmid(p), "doi": None, "nota": ""})
    for d in re.split(r"[,\s;]+", args.dois or ""):
        if normalizar_doi(d):
            sentinelas.append({"pmid": None, "doi": normalizar_doi(d), "nota": ""})
    if not sentinelas:
        sair("nenhum sentinela: preencha 'sentinelas' em conceitos.json ou use --pmids/--dois")

    try:
        cliente = Cliente(args.email)
    except ErroRede as exc:
        sair(str(exc))

    # resolve DOIs sem PMID
    for s in sentinelas:
        if not s["pmid"] and s["doi"]:
            try:
                s["pmid"] = resolver_doi(cliente, s["doi"])
            except ErroRede as exc:
                print(f"  aviso: não consegui resolver o DOI {s['doi']}: {exc}")
    vistos, unicos = set(), []
    for s in sentinelas:
        chave = s["pmid"] or s["doi"]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(s)
    sentinelas = unicos
    pmids = [s["pmid"] for s in sentinelas if s["pmid"]]

    registros: dict[str, dict] = {}
    if pmids:
        try:
            lista, erros = pb.efetch_ids(cliente, pmids)
            registros = {r["pmid"]: r for r in lista}
            for e in erros:
                print(f"  aviso: {e}")
        except ErroRede as exc:
            sair(f"não consegui baixar os sentinelas do PubMed: {exc}", 1)

    variantes = [v.strip() for v in args.variante.split(",") if v.strip()]
    brutos = presenca_em_brutos(pasta)
    relatorio = {"data": agora_iso(), "variante": variantes[0], "variantes": {}, "total": len(sentinelas),
                 "recuperados": 0, "resultados": []}
    codigo = 0

    matriz: dict[str, set[str]] = {}
    falha_tecnica = False
    for n_var, variante in enumerate(variantes):
        try:
            consulta = ms.montar_pubmed(conceitos, variante)
            recuperados = filtrar_ids(cliente, consulta, pmids)
        except (ErroRede, ValueError) as exc:
            print(f"FALHA ao testar a variante '{variante}': {exc}")
            codigo = 1
            falha_tecnica = True
            continue
        matriz[variante] = recuperados
        testaveis = len(pmids)
        relatorio["variantes"][variante] = {"recuperados": sorted(recuperados), "testaveis": testaveis}
        if n_var > 0:
            continue  # o detalhe é só para a primeira variante; as demais entram na matriz
        perdidos = [p for p in pmids if p not in recuperados and p in registros]
        diag = diagnosticar(cliente, conceitos, variante, perdidos, registros) if perdidos else {}
        print(f"\n=== Teste de sentinela | variante '{variante}' ===")
        print(f"Recuperados: {len(recuperados)} de {testaveis} sentinelas com PMID"
              + (f" ({len(sentinelas) - testaveis} fora do PubMed)" if testaveis < len(sentinelas) else ""))
        for s in sentinelas:
            reg = registros.get(s["pmid"] or "", {})
            onde = sorted(brutos.get(s["pmid"] or "", set()) | brutos.get(s["doi"] or reg.get("doi") or "", set()))
            titulo = reg.get("titulo", "")
            ident = f"PMID {s['pmid']}" if s["pmid"] else f"DOI {s['doi']}"
            if not s["pmid"]:
                situacao = "fora do PubMed"
            elif s["pmid"] not in registros:
                situacao = "PMID inexistente"
            elif s["pmid"] in recuperados:
                situacao = "recuperado"
            else:
                situacao = "PERDIDO"
            linha = {"pmid": s["pmid"], "doi": s["doi"] or reg.get("doi"), "titulo": titulo, "nota": s.get("nota", ""),
                     "primeiro_autor": reg.get("primeiro_autor", ""), "ano": reg.get("ano"),
                     "situacao": situacao, "indexacao": reg.get("situacao_indexacao", ""),
                     "presente_em_brutos": onde, "blocos_falhos": [], "falhas": [], "sugestoes": {}}
            marca = {"recuperado": "ok     ", "PERDIDO": "PERDIDO"}.get(situacao, "?      ")
            print(f"\n  [{marca}] {ident} | {reg.get('primeiro_autor', '')} {reg.get('ano', '')} | {titulo[:95]}")
            if s.get("nota"):
                print(f"            nota: {s['nota']}")
            if situacao == "fora do PubMed":
                print(f"            sem PMID: o PubMed não tem como recupera-lo. Presente em: "
                      f"{', '.join(onde) or 'nenhuma fonte baixada'}")
            if situacao == "recuperado" and "pubmed" not in onde and brutos:
                print("            atenção: a string recupera, mas o registro não está em brutos/pubmed.json "
                      "(provável corte por --max; aumente --max ou rode a variante certa).")
                linha["falhas"].append(["download", "fora de brutos/pubmed.json"])
            if situacao == "PERDIDO":
                d = diag.get(s["pmid"], {})
                linha["falhas"] = [list(f) for f in d.get("falhas", [])]
                linha["blocos_falhos"] = d.get("blocos_falhos", [])
                linha["sugestoes"] = d.get("sugestoes", {})
                if reg.get("situacao_indexacao") != "MEDLINE":
                    print(f"            indexação: {reg.get('situacao_indexacao')} - registro SEM MeSH; só texto "
                          f"livre o alcança.")
                for tipo, quem in d.get("falhas", []):
                    print(f"            eliminado por {tipo}: {quem}")
                if not d.get("falhas"):
                    print("            nenhum componente isolado o elimina: confira a combinação de limites.")
                for bloco_id, sug in d.get("sugestoes", {}).items():
                    print(f"            bloco '{bloco_id}' não casa. O artigo tem:")
                    print(f"              MeSH fora do bloco (* = principal): "
                          f"{'; '.join(sug['mesh_do_artigo_fora_do_bloco']) or '(sem MeSH)'}")
                    print(f"              palavras do título fora do bloco: "
                          f"{', '.join(sug['palavras_do_titulo_fora_do_bloco']) or '-'}")
                    if sug["palavras_chave_do_autor"]:
                        print(f"              palavras-chave do autor: {'; '.join(sug['palavras_chave_do_autor'])}")
            relatorio["resultados"].append(linha)
        relatorio["recuperados"] = len(recuperados)
        if perdidos:
            codigo = 1
        if testaveis:
            print(f"\nSensibilidade na variante '{variante}': {100 * len(recuperados) / testaveis:.0f}% "
                  f"({len(recuperados)}/{testaveis}).")

    if len(matriz) > 1:
        print("\n=== Matriz sentinela x variante ===")
        print("  " + "sentinela".ljust(34) + "".join(v.ljust(13) for v in matriz))
        for s in sentinelas:
            if not s["pmid"] or s["pmid"] not in registros:
                continue
            reg = registros[s["pmid"]]
            nome = f"{s['pmid']} {reg.get('primeiro_autor', '')[:14]} {reg.get('ano', '')}"
            print("  " + nome.ljust(34) + "".join(("ok" if s["pmid"] in matriz[v] else "-").ljust(13) for v in matriz))
        de_desenho = [v for v in matriz if v in ms.FILTROS]
        if de_desenho:
            fora = [s["pmid"] for s in sentinelas if s["pmid"] in registros
                    and not any(s["pmid"] in matriz[v] for v in de_desenho)]
            relatorio["fora_de_todos_os_filtros"] = fora
            print(f"\n  Um filtro de desenho só deve recuperar os sentinelas daquele desenho; o que importa é nenhum "
                  f"ficar fora de todos.")
            if fora:
                print(f"  FORA DE TODOS os filtros de desenho testados ({', '.join(de_desenho)}): {', '.join(fora)}. "
                      f"Se a busca usar só esses filtros (recorte 'so_topo'), esses artigos se perdem.")
            else:
                print(f"  Todo sentinela é alcançado por pelo menos um filtro de desenho ({', '.join(de_desenho)}).")

    gravar_json(destino, relatorio)
    print(f"\nGravado: {destino}")
    if falha_tecnica:
        print("O teste não foi concluído por falha de rede ou de consulta; o resultado acima não vale como teste.")
    elif codigo:
        print("Há sentinela perdido na primeira variante: ajuste os blocos em conceitos.json, rode montar_strings.py "
              "e repita o teste. Anote a mudança em 'Decisões e histórico' de estrategia.md.")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
