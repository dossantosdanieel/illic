#!/usr/bin/env python3
"""Roda a busca no PubMed (esearch + efetch em XML) e grava brutos/pubmed.json.

Registra, para cada execução, o total de resultados e a TRADUÇÃO que o PubMed fez da
consulta (querytranslation): é por ela que se confere se cada termo foi entendido como
o esperado. Usa o history server e baixa em lotes, respeitando 3 requisições por segundo.

Uso:
  python3 pubmed_busca.py --conceitos aulas/x/01_busca/conceitos.json --variante recorte
  python3 pubmed_busca.py --conceitos conceitos.json --variante base --so-contar
  python3 pubmed_busca.py --conceitos conceitos.json --diagnostico        # contagem por bloco e por termo
  python3 pubmed_busca.py --consulta '"Rotator Cuff Injuries"[Mesh] AND exercise[tiab]' --saida brutos/pubmed.json
  python3 pubmed_busca.py --consulta 'Naunton[au] AND rotator cuff AND exercise' --listar 5   # achar sentinela
  python3 pubmed_busca.py --pmids 12345,67890 --saida brutos/pubmed.json   # acrescenta artigos pontuais
  python3 pubmed_busca.py --importar pubmed-export.nbib --saida brutos/pubmed.json   # sem rede: arquivo do site
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import os
import re
import xml.etree.ElementTree as ET
from datetime import date

from _comum import (FERRAMENTA, Cliente, ErroRede, agora_iso, carregar_conceitos, gravar_json, ler_json,
                    limpar_texto, normalizar_doi, normalizar_issn, sair)
import montar_strings as ms

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def parametros_base(cliente: Cliente) -> dict:
    p = {"tool": FERRAMENTA, "email": cliente.email}
    if os.environ.get("NCBI_API_KEY"):
        p["api_key"] = os.environ["NCBI_API_KEY"]
    return p


# --------------------------------------------------------------------------- esearch

def esearch(cliente: Cliente, consulta: str, ordem: str = "relevance", historico: bool = True,
            retmax: int = 0) -> dict:
    """Devolve total, tradução, avisos e as chaves do history server."""
    dados = {**parametros_base(cliente), "db": "pubmed", "term": consulta, "retmode": "json",
             "retmax": str(retmax), "sort": ordem}
    if historico:
        dados["usehistory"] = "y"
    try:
        r = cliente.post(EUTILS + "esearch.fcgi", dados).json()
    except ValueError:
        raise ErroRede("O PubMed devolveu uma resposta que não é JSON (provável erro de sintaxe na consulta).")
    res = r.get("esearchresult", {})
    if "ERROR" in res:
        raise ErroRede(f"O PubMed recusou a consulta: {res['ERROR']}")
    avisos = []
    for origem in ("warninglist", "errorlist"):
        for chave, itens in (res.get(origem) or {}).items():
            if chave == "outputmessages":
                continue
            nomes = {"quotedphrasesnotfound": "frase entre aspas não encontrada (zero resultados para o termo)",
                     "phrasesnotfound": "termo não encontrado", "phrasesignored": "termo ignorado",
                     "fieldsnotfound": "campo inexistente"}
            for item in itens or []:
                avisos.append(f"{nomes.get(chave, chave)}: {item}")
    traducao = res.get("querytranslation", "")
    if re.search(r"\[All Fields\]", traducao) and not re.search(r"\[(all fields|all)\]", consulta, re.I):
        avisos.append("há termo sem etiqueta de campo: o PubMed aplicou o mapeamento automático "
                      "([All Fields] na tradução). Confira se era a intenção.")
    return {"total": int(res.get("count", 0) or 0), "traducao": traducao, "avisos": avisos,
            "webenv": res.get("webenv"), "query_key": res.get("querykey"), "ids": res.get("idlist", [])}


# --------------------------------------------------------------------------- efetch + XML

def _texto(no) -> str:
    return limpar_texto("".join(no.itertext())) if no is not None else ""


def _ano(artigo: ET.Element) -> int | None:
    for caminho in ("MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
                    "MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate",
                    "MedlineCitation/Article/ArticleDate/Year",
                    "PubmedData/History/PubMedPubDate[@PubStatus='pubmed']/Year"):
        no = artigo.find(caminho)
        if no is not None and no.text:
            achado = re.search(r"(19|20)\d{2}", no.text)
            if achado:
                return int(achado.group(0))
    return None


def analisar_artigo(artigo: ET.Element) -> dict:
    mc = artigo.find("MedlineCitation")
    art = mc.find("Article")
    reg: dict = {"fonte": "pubmed"}
    reg["pmid"] = (mc.findtext("PMID") or "").strip()
    reg["situacao_indexacao"] = mc.get("Status", "")
    reg["titulo"] = _texto(art.find("ArticleTitle")).rstrip(".") if art is not None else ""
    if not reg["titulo"] and art is not None:
        reg["titulo"] = _texto(art.find("VernacularTitle")).rstrip(".")
    # resumo estruturado: uma seção por AbstractText, com o rótulo quando houver
    secoes = []
    if art is not None:
        for no in art.findall("Abstract/AbstractText"):
            texto = _texto(no)
            if texto:
                secoes.append({"rotulo": (no.get("Label") or "").strip(), "texto": texto})
    reg["resumo_secoes"] = secoes
    reg["resumo"] = "\n".join((f"{s['rotulo']}: " if s["rotulo"] else "") + s["texto"] for s in secoes)
    autores = []
    if art is not None:
        for a in art.findall("AuthorList/Author"):
            sobrenome = (a.findtext("LastName") or "").strip()
            iniciais = (a.findtext("Initials") or "").strip()
            coletivo = (a.findtext("CollectiveName") or "").strip()
            if sobrenome:
                autores.append(f"{sobrenome} {iniciais}".strip())
            elif coletivo:
                autores.append(coletivo)
    reg["autores"] = autores
    primeiro = art.find("AuthorList/Author") if art is not None else None
    reg["primeiro_autor"] = ((primeiro.findtext("LastName") or primeiro.findtext("CollectiveName") or "").strip()
                             if primeiro is not None else "")
    jornal = art.find("Journal") if art is not None else None
    reg["revista"] = ((jornal.findtext("ISOAbbreviation") if jornal is not None else "")
                      or mc.findtext("MedlineJournalInfo/MedlineTA") or "").strip()
    reg["revista_completa"] = (jornal.findtext("Title") or "").strip() if jornal is not None else ""
    issns = []
    for no in ([jornal.find("ISSN")] if jornal is not None else []) + [mc.find("MedlineJournalInfo/ISSNLinking")]:
        if no is not None and no.text:
            issn = normalizar_issn(no.text)
            if issn and issn not in issns:
                issns.append(issn)
    reg["issn"] = issns
    reg["ano"] = _ano(artigo)
    reg["volume"] = (jornal.findtext("JournalIssue/Volume") or "").strip() if jornal is not None else ""
    reg["fasciculo"] = (jornal.findtext("JournalIssue/Issue") or "").strip() if jornal is not None else ""
    reg["paginas"] = (art.findtext("Pagination/MedlinePgn") or "").strip() if art is not None else ""
    reg["idiomas"] = [x.text for x in art.findall("Language") if x.text] if art is not None else []
    reg["tipos_publicacao"] = [x.text for x in art.findall("PublicationTypeList/PublicationType") if x.text] \
        if art is not None else []
    mesh, principais = [], []
    for mh in mc.findall("MeshHeadingList/MeshHeading"):
        d = mh.find("DescriptorName")
        if d is None or not d.text:
            continue
        mesh.append(d.text)
        if d.get("MajorTopicYN") == "Y" or any(q.get("MajorTopicYN") == "Y" for q in mh.findall("QualifierName")):
            principais.append(d.text)
    reg["mesh"] = mesh
    reg["mesh_principal"] = principais
    reg["palavras_chave"] = [limpar_texto(k.text) for k in mc.findall("KeywordList/Keyword") if k.text]
    doi = pmcid = None
    for aid in artigo.findall("PubmedData/ArticleIdList/ArticleId"):
        tipo = aid.get("IdType")
        if tipo == "doi" and not doi:
            doi = normalizar_doi(aid.text)
        elif tipo == "pmc" and not pmcid:
            pmcid = (aid.text or "").strip() or None
    if not doi and art is not None:
        for el in art.findall("ELocationID"):
            if el.get("EIdType") == "doi":
                doi = normalizar_doi(el.text)
    reg["doi"] = doi
    reg["pmcid"] = pmcid
    reg["retratado"] = ("Retracted Publication" in reg["tipos_publicacao"]
                        or any(c.get("RefType") == "RetractionIn"
                               for c in mc.findall("CommentsCorrectionsList/CommentsCorrections")))
    return reg


def analisar_xml(xml_bytes: bytes) -> tuple[list[dict], list[str]]:
    """Devolve (registros, erros). Um artigo com problema não derruba o lote."""
    registros, erros = [], []
    try:
        raiz = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        return [], [f"XML ilegível: {exc}"]
    for artigo in raiz.findall("PubmedArticle"):
        try:
            registros.append(analisar_artigo(artigo))
        except Exception as exc:  # noqa: BLE001 - um registro ruim não pode parar o lote
            pmid = artigo.findtext("MedlineCitation/PMID") or "?"
            erros.append(f"PMID {pmid}: {type(exc).__name__}: {exc}")
    livros = len(raiz.findall("PubmedBookArticle"))
    if livros:
        erros.append(f"{livros} registro(s) de livro ignorado(s)")
    return registros, erros


def efetch_historico(cliente: Cliente, webenv: str, query_key: str, total: int, maximo: int, lote: int):
    registros, erros = [], []
    alvo = min(total, maximo)
    for inicio in range(0, alvo, lote):
        tamanho = min(lote, alvo - inicio)
        dados = {**parametros_base(cliente), "db": "pubmed", "WebEnv": webenv, "query_key": query_key,
                 "retstart": str(inicio), "retmax": str(tamanho), "retmode": "xml"}
        try:
            xml = cliente.post(EUTILS + "efetch.fcgi", dados).content
        except ErroRede as exc:
            erros.append(f"lote {inicio + 1}-{inicio + tamanho}: {exc}")
            continue
        novos, erros_lote = analisar_xml(xml)
        registros += novos
        erros += erros_lote
        print(f"  baixados {min(inicio + tamanho, alvo)}/{alvo}", file=sys.stderr)
    return registros, erros


def efetch_ids(cliente: Cliente, pmids: list[str], lote: int = 200):
    registros, erros = [], []
    for inicio in range(0, len(pmids), lote):
        grupo = pmids[inicio:inicio + lote]
        dados = {**parametros_base(cliente), "db": "pubmed", "id": ",".join(grupo), "retmode": "xml"}
        try:
            xml = cliente.post(EUTILS + "efetch.fcgi", dados).content
        except ErroRede as exc:
            erros.append(f"PMIDs {grupo[0]}...: {exc}")
            continue
        novos, erros_lote = analisar_xml(xml)
        registros += novos
        erros += erros_lote
    return registros, erros


# --------------------------------------------------------------------------- importação de arquivo do site

def analisar_medline(texto: str) -> tuple[list[dict], list[str]]:
    """Lê o formato 'PubMed' (MEDLINE com etiquetas, arquivos .nbib ou .txt) que o site do PubMed grava em
    Save > Format: PubMed ou Send to > Citation manager. É o caminho para quem não tem acesso à API."""
    blocos, atual, etiqueta = [], None, None
    for linha in texto.splitlines():
        achado = re.match(r"^([A-Z]{2,4})\s*- (.*)$", linha)
        if achado:
            etiqueta, valor = achado.group(1), achado.group(2).strip()
            if etiqueta == "PMID":
                atual = {}
                blocos.append(atual)
            if atual is not None:
                atual.setdefault(etiqueta, []).append(valor)
        elif linha.startswith("      ") and atual is not None and etiqueta:
            atual[etiqueta][-1] += " " + linha.strip()
    registros, erros = [], []
    for b in blocos:
        try:
            um = lambda t: (b.get(t) or [""])[0]  # noqa: E731
            doi = None
            for campo in b.get("LID", []) + b.get("AID", []):
                if "[doi]" in campo and not doi:
                    doi = normalizar_doi(campo.replace("[doi]", ""))
            mesh, principais = [], []
            for m in b.get("MH", []):
                nome = m.split("/")[0].lstrip("*")
                if nome not in mesh:
                    mesh.append(nome)
                if "*" in m and nome not in principais:
                    principais.append(nome)
            autores = b.get("AU", []) or b.get("CN", [])
            primeiro = (b.get("FAU") or [""])[0].split(",")[0] or (autores[0].rsplit(" ", 1)[0] if autores else "")
            ano = re.search(r"(19|20)\d{2}", um("DP") or um("DEP"))
            issns = [i for i in (normalizar_issn(x) for x in b.get("IS", [])) if i]
            resumo = um("AB")
            registros.append({
                "fonte": "pubmed", "pmid": um("PMID"), "situacao_indexacao": um("STAT"),
                "titulo": um("TI").rstrip("."), "resumo": resumo,
                "resumo_secoes": [{"rotulo": "", "texto": resumo}] if resumo else [],
                "autores": autores, "primeiro_autor": primeiro,
                "revista": um("TA"), "revista_completa": um("JT"), "issn": list(dict.fromkeys(issns)),
                "ano": int(ano.group(0)) if ano else None, "volume": um("VI"), "fasciculo": um("IP"),
                "paginas": um("PG"), "idiomas": b.get("LA", []), "tipos_publicacao": b.get("PT", []),
                "mesh": mesh, "mesh_principal": principais, "palavras_chave": b.get("OT", []),
                "doi": doi, "pmcid": um("PMC") or None,
                "retratado": "Retracted Publication" in b.get("PT", []) or bool(b.get("RIN")),
            })
        except Exception as exc:  # noqa: BLE001 - um registro ruim não para o arquivo
            erros.append(f"PMID {(b.get('PMID') or ['?'])[0]}: {type(exc).__name__}: {exc}")
    return registros, erros


# --------------------------------------------------------------------------- arquivo de saída

def carregar_saida(caminho: Path, substituir: bool) -> dict:
    atual = None if substituir else ler_json(caminho)
    if not atual or not isinstance(atual, dict):
        atual = {"fonte": "pubmed", "execucoes": [], "registros": []}
    atual.setdefault("execucoes", [])
    atual.setdefault("registros", [])
    return atual


def fundir(saida: dict, novos: list[dict], variante: str) -> int:
    """Acrescenta registros novos e marca, em cada um, as variantes que o recuperaram."""
    por_pmid = {r["pmid"]: r for r in saida["registros"]}
    acrescentados = 0
    for r in novos:
        if not r.get("pmid"):
            continue
        antigo = por_pmid.get(r["pmid"])
        if antigo:
            variantes = antigo.get("variantes", [])
            r["variantes"] = variantes + ([variante] if variante not in variantes else [])
            antigo.clear()
            antigo.update(r)
        else:
            r["variantes"] = [variante]
            saida["registros"].append(r)
            por_pmid[r["pmid"]] = r
            acrescentados += 1
    return acrescentados


# --------------------------------------------------------------------------- diagnóstico

def diagnostico(cliente: Cliente, conceitos: dict) -> list[dict]:
    """Conta resultados por termo e por bloco. Termo com zero costuma ser erro de grafia ou MeSH inexistente;
    termo que sozinho responde por quase todo o bloco costuma ser a fonte do ruído."""
    linhas = []
    avisos: list[str] = []
    limites = ms.limites_pubmed(conceitos)
    for b in conceitos["blocos"]:
        partes: list[tuple[str, str]] = []
        for m in b["mesh"]:
            for s in ms.mesh_pubmed(m):
                partes.append(("MeSH", s))
        for t in b["livres"]:
            partes.append(("livre", ms.termo_pubmed(t, b["campo"])))
        for p in b["proximidade"]:
            for s in ms.proximidade_pubmed(p, b["campo"], avisos, b["id"]):
                partes.append(("proximidade", s))
        total_bloco = esearch(cliente, " AND ".join([ms.bloco_pubmed(b, [])] + limites), historico=False)["total"]
        linhas.append({"bloco": b["id"], "tipo": "BLOCO", "termo": b["rotulo"], "n": total_bloco})
        print(f"\nBloco '{b['id']}' ({b['rotulo']}): {total_bloco} com os limites")
        for tipo, termo in partes:
            try:
                res = esearch(cliente, " AND ".join([termo] + limites), historico=False)
                n = res["total"]
                marca = "  <-- ZERO: confira grafia/descritor" if n == 0 else ""
            except ErroRede as exc:
                n, marca = None, f"  (falhou: {exc})"
            linhas.append({"bloco": b["id"], "tipo": tipo, "termo": termo, "n": n})
            print(f"  {str(n).rjust(8)}  {termo}{marca}")
    return linhas


# --------------------------------------------------------------------------- principal

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Busca no PubMed com esearch + efetch e grava brutos/pubmed.json com total, tradução da "
                    "consulta e registros completos.")
    origem = ap.add_argument_group("origem da consulta (escolha uma)")
    origem.add_argument("--conceitos", help="conceitos.json; a string é montada na hora, igual à de estrategia.md")
    origem.add_argument("--consulta", help="string PubMed pronta")
    origem.add_argument("--arquivo-consulta", help="arquivo de texto com a string PubMed")
    origem.add_argument("--pmids", help="PMIDs separados por vírgula, para acrescentar artigos pontuais")
    origem.add_argument("--importar", nargs="+", metavar="ARQUIVO",
                        help="sem rede: arquivo(s) .nbib ou .txt salvos no site do PubMed (Save > Format: PubMed)")
    ap.add_argument("--variante", default="recorte",
                    help="com --conceitos: base, rs, ecr, ecr_sensivel, diretriz, revistas, várias separadas por "
                         "vírgula, ou 'recorte' (as recomendadas para o recorte; padrão)")
    ap.add_argument("--saida", help="arquivo de saída (padrão: <pasta de conceitos>/brutos/pubmed.json)")
    ap.add_argument("--max", type=int, default=1000, help="máximo de registros baixados por variante (padrão 1000)")
    ap.add_argument("--lote", type=int, default=200, help="registros por chamada de efetch (padrão 200)")
    ap.add_argument("--ordem", default="relevance", choices=["relevance", "pub_date"],
                    help="ordem dos resultados; importa quando o total passa de --max (padrão relevance)")
    ap.add_argument("--so-contar", action="store_true", help="mostra total e tradução, sem baixar registros")
    ap.add_argument("--listar", type=int, default=0, metavar="N",
                    help="mostra os N primeiros resultados (PMID, autor, ano, revista, desenho, título) sem gravar "
                         "nada; serve para achar e conferir artigos-sentinela")
    ap.add_argument("--diagnostico", action="store_true",
                    help="com --conceitos: conta resultados por bloco e por termo e grava brutos/diagnostico_pubmed.json")
    ap.add_argument("--substituir", action="store_true",
                    help="começa o arquivo de saída do zero (padrão: acumula variantes no mesmo arquivo)")
    ap.add_argument("--hoje", help="data de referência AAAA-MM-DD para o recorte 'fronteira' (padrão: hoje)")
    ap.add_argument("--email", help="e-mail de contato enviado ao NCBI (ou variável BOOST_EMAIL)")
    args = ap.parse_args(argv)

    if args.importar:
        if not args.saida:
            sair("com --importar informe --saida (normalmente <aula>/01_busca/brutos/pubmed.json)")
        saida = carregar_saida(Path(args.saida), args.substituir)
        for nome in args.importar:
            caminho = Path(nome)
            if not caminho.exists():
                print(f"{nome}: arquivo não encontrado; pulei.")
                continue
            registros, erros = analisar_medline(caminho.read_text(encoding="utf-8-sig", errors="replace"))
            novos = fundir(saida, registros, "importado")
            saida["execucoes"].append({"data": agora_iso(), "variante": "importado",
                                       "consulta": f"arquivo exportado do site: {caminho.name}",
                                       "total": len(registros), "baixados": len(registros), "novos": novos,
                                       "traducao": "", "avisos": erros})
            print(f"{caminho.name}: {len(registros)} registros lidos | novos no arquivo: {novos}")
            if not registros:
                print("  nenhum registro reconhecido: o arquivo precisa estar no formato 'PubMed' (linhas 'PMID- ...').")
            for e in erros:
                print(f"  aviso: {e}")
        gravar_json(Path(args.saida), saida)
        print(f"Gravado: {args.saida} ({len(saida['registros'])} registros únicos)")
        return 0 if saida["registros"] else 1

    fontes = [x for x in (args.conceitos, args.consulta, args.arquivo_consulta, args.pmids) if x]
    if len(fontes) != 1:
        sair("informe exatamente uma origem: --conceitos, --consulta, --arquivo-consulta, --pmids ou --importar")

    conceitos = None
    consultas: list[tuple[str, str]] = []
    pasta = None
    if args.conceitos:
        conceitos = carregar_conceitos(args.conceitos)
        hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
        ms.aplicar_recorte(conceitos, hoje)
        pasta = Path(args.conceitos).resolve().parent
        variantes = ms.variantes_do_recorte(conceitos) if args.variante == "recorte" \
            else [v.strip() for v in args.variante.split(",") if v.strip()]
        for v in variantes:
            try:
                consultas.append((v, ms.montar_pubmed(conceitos, v)))
            except ValueError as exc:
                sair(str(exc))
        gravadas = ler_json(pasta / "strings.json")
        if gravadas and any(gravadas.get("pubmed", {}).get(v) not in (None, c) for v, c in consultas):
            print("AVISO: conceitos.json mudou desde a última geração de estrategia.md. "
                  "Rode montar_strings.py para atualizar a documentação.", file=sys.stderr)
    elif args.consulta:
        consultas.append(("manual", args.consulta.strip()))
    elif args.arquivo_consulta:
        consultas.append(("manual", Path(args.arquivo_consulta).read_text(encoding="utf-8").strip()))

    if args.saida:
        destino = Path(args.saida)
    elif pasta:
        destino = pasta / "brutos" / "pubmed.json"
    elif args.listar:
        destino = None
    else:
        sair("informe --saida (sem --conceitos não há pasta padrão)")

    try:
        cliente = Cliente(args.email)
    except ErroRede as exc:
        sair(str(exc))

    if args.listar:
        if args.pmids:
            sair("--listar funciona com --consulta, --arquivo-consulta ou --conceitos")
        for variante, consulta in consultas:
            try:
                res = esearch(cliente, consulta, ordem=args.ordem, historico=False, retmax=args.listar)
                registros, erros = efetch_ids(cliente, res["ids"]) if res["ids"] else ([], [])
            except ErroRede as exc:
                sair(f"busca falhou: {exc}", 1)
            print(f"\n=== PubMed | '{variante}' | {res['total']} resultados; mostrando {len(registros)} ===")
            print(f"Tradução: {res['traducao']}")
            for a in res["avisos"] + erros:
                print(f"  AVISO: {a}")
            ordem_ids = {p: i for i, p in enumerate(res["ids"])}
            for r in sorted(registros, key=lambda r: ordem_ids.get(r["pmid"], 0)):
                tipos = [t for t in r["tipos_publicacao"] if t not in ("Journal Article",) and "Research Support" not in t]
                print(f"  PMID {r['pmid']} | {r['primeiro_autor']} {r['ano']} | {r['revista']} | "
                      f"{', '.join(tipos) or 'Journal Article'} | {r['titulo'][:110]}"
                      + (f" | DOI {r['doi']}" if r["doi"] else ""))
        return 0

    if args.diagnostico:
        if not conceitos:
            sair("--diagnostico precisa de --conceitos")
        try:
            linhas = diagnostico(cliente, conceitos)
        except ErroRede as exc:
            sair(f"diagnóstico interrompido: {exc}", 1)
        gravar_json(destino.parent / "diagnostico_pubmed.json", {"data": agora_iso(), "linhas": linhas})
        print(f"\nGravado: {destino.parent / 'diagnostico_pubmed.json'}")
        return 0

    saida = carregar_saida(destino, args.substituir)
    falhas = 0
    falharam: list[str] = []

    if args.pmids:
        pmids = [p for p in re.split(r"[,\s;]+", args.pmids) if p.isdigit()]
        registros, erros = efetch_ids(cliente, pmids)
        novos = fundir(saida, registros, "manual")
        saida["execucoes"].append({"data": agora_iso(), "variante": "manual", "consulta": f"PMIDs: {','.join(pmids)}",
                                   "total": len(pmids), "baixados": len(registros), "novos": novos,
                                   "traducao": "", "avisos": erros})
        gravar_json(destino, saida)
        print(f"PMIDs pedidos: {len(pmids)} | recuperados: {len(registros)} | novos no arquivo: {novos}")
        for e in erros:
            print(f"  aviso: {e}")
        print(f"Gravado: {destino}")
        return 0

    for variante, consulta in consultas:
        print(f"\n=== PubMed | variante '{variante}' ===")
        print(consulta)
        try:
            res = esearch(cliente, consulta, ordem=args.ordem, historico=not args.so_contar)
        except ErroRede as exc:
            print(f"FALHA na busca: {exc}")
            falhas += 1
            falharam.append(variante)
            continue
        print(f"\nTotal no PubMed: {res['total']}")
        print("Tradução feita pelo PubMed (confira se cada termo virou o que você queria):")
        print(res["traducao"])
        for a in res["avisos"]:
            print(f"  AVISO: {a}")
        execucao = {"data": agora_iso(), "variante": variante, "consulta": consulta, "total": res["total"],
                    "traducao": res["traducao"], "avisos": list(res["avisos"]), "baixados": 0, "novos": 0,
                    "ordem": args.ordem, "max": args.max}
        if args.so_contar:
            execucao["so_contagem"] = True
            saida["execucoes"].append(execucao)
            continue
        if res["total"] == 0:
            saida["execucoes"].append(execucao)
            continue
        if res["total"] > args.max:
            aviso = (f"total ({res['total']}) maior que --max ({args.max}): baixados só os {args.max} primeiros "
                     f"por '{args.ordem}'. Estreite a busca ou aumente --max.")
            print(f"  AVISO: {aviso}")
            execucao["avisos"].append(aviso)
        registros, erros = efetch_historico(cliente, res["webenv"], res["query_key"], res["total"], args.max,
                                            args.lote)
        execucao["baixados"] = len(registros)
        execucao["novos"] = fundir(saida, registros, variante)
        execucao["avisos"] += erros
        saida["execucoes"].append(execucao)
        print(f"Baixados: {len(registros)} | novos no arquivo: {execucao['novos']} | "
              f"total acumulado: {len(saida['registros'])}")
        for e in erros:
            print(f"  aviso: {e}")
        if len(registros) < min(res["total"], args.max):
            falhas += 1
            falharam.append(variante)

    if not saida["execucoes"] and not saida["registros"]:
        print("\nNenhuma busca foi concluída; nada foi gravado.")
        return 1
    gravar_json(destino, saida)
    print(f"\nGravado: {destino} ({len(saida['registros'])} registros únicos, {len(saida['execucoes'])} execuções)")
    if falharam:
        print(f"ATENÇÃO: variante(s) incompleta(s) por falha de rede: {', '.join(falharam)}. O arquivo está parcial. "
              f"Rode de novo só o que faltou: --variante {','.join(falharam)} (o resultado se soma ao que já existe).")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
