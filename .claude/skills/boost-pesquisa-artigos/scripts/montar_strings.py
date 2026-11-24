#!/usr/bin/env python3
"""Gera as strings de busca (PubMed, Scopus, Crossref/JOSPT) a partir de conceitos.json.

Uma única fonte (os blocos de conceito) produz todas as strings, para que a busca seja
a mesma em todas as bases e possa ser refeita. Grava estrategia.md (pronto para colar)
e strings.json (para os outros scripts).

Uso:
  python3 montar_strings.py aulas/2026-11-ombro/01_busca/conceitos.json
  python3 montar_strings.py conceitos.json --verificar-mesh        # confere cada MeSH no NLM
  python3 montar_strings.py conceitos.json --saida outra/pasta --hoje 2026-11-24
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import re
from datetime import date
from urllib.parse import quote_plus

from _comum import (Cliente, ErroRede, carregar_conceitos, gravar_json, issns_alvo, ler_json, limpar_termo)

# --------------------------------------------------------------------------- filtros metodológicos
# Cada filtro traz a origem. O que foi adaptado está dito em 'nota'; nada aqui é apresentado
# como validado se não for.

FILTROS = {
    "rs": {
        "rotulo": "Revisões sistemáticas e meta-análises",
        "pubmed": '(systematic[sb] OR "meta-analysis"[pt] OR "systematic review"[ti] OR meta-analy*[ti] '
                  'OR "umbrella review"[ti])',
        "scopus": 'TITLE-ABS-KEY("systematic review" OR "meta analy*" OR metaanaly* OR "umbrella review")',
        "origem": "PubMed: subconjunto systematic[sb] (filtro de revisões sistemáticas da NLM) somado ao tipo de "
                  "publicação Meta-Analysis e a palavras de título. Scopus: tradução aproximada, sem validação.",
        "nota": "systematic[sb] é sensível e pouco preciso: traz revisões narrativas que dizem 'systematic'. "
                "A triagem resolve.",
    },
    "ecr": {
        "rotulo": "Ensaios clínicos randomizados",
        "pubmed": '(("randomized controlled trial"[pt] OR "controlled clinical trial"[pt] OR randomized[tiab] '
                  'OR randomised[tiab] OR placebo[tiab] OR "clinical trials as topic"[mesh:noexp] OR randomly[tiab] '
                  'OR trial[ti]) NOT (animals[mh] NOT humans[mh]))',
        "scopus": '(TITLE-ABS-KEY(randomized OR randomised OR randomly OR placebo OR "controlled trial" '
                  'OR "clinical trial") OR TITLE(trial))',
        "origem": "PubMed: Cochrane Highly Sensitive Search Strategy, versão que maximiza sensibilidade e precisão "
                  "(revisão de 2008; Cochrane Handbook, suplemento técnico do cap. 4). "
                  "Scopus: tradução aproximada, sem validação.",
        "nota": "Acréscimo nosso ao filtro Cochrane: randomised[tiab] (grafia britânica), que só aumenta a "
                "sensibilidade.",
    },
    "ecr_sensivel": {
        "rotulo": "Ensaios clínicos randomizados (versão de máxima sensibilidade)",
        "pubmed": '(("randomized controlled trial"[pt] OR "controlled clinical trial"[pt] OR randomized[tiab] '
                  'OR randomised[tiab] OR placebo[tiab] OR "drug therapy"[sh] OR randomly[tiab] OR trial[tiab] '
                  'OR groups[tiab]) NOT (animals[mh] NOT humans[mh]))',
        "scopus": 'TITLE-ABS-KEY(random* OR placebo OR trial OR groups)',
        "origem": "PubMed: Cochrane Highly Sensitive Search Strategy, versão que maximiza sensibilidade "
                  "(revisão de 2008). Scopus: tradução aproximada, sem validação.",
        "nota": "Use quando o filtro padrão perder um ensaio-sentinela; o volume de ruído sobe bastante.",
    },
    "diretriz": {
        "rotulo": "Diretrizes e consensos",
        "pubmed": '("practice guideline"[pt] OR "guideline"[pt] OR "consensus statement"[pt] '
                  'OR guideline*[ti] OR "practice guideline*"[tiab] OR consensus[ti] OR "position statement*"[ti] '
                  'OR "position stand"[ti] OR recommendation*[ti])',
        "scopus": '(TITLE(guideline* OR consensus OR "position statement*" OR "position stand" OR recommendation*) '
                  'OR TITLE-ABS-KEY("practice guideline*"))',
        "origem": "Filtro pragmático: tipos de publicação do PubMed (Practice Guideline, Guideline, Consensus "
                  "Statement, nome atual do antigo Consensus Development Conference) e palavras de título, na linha do filtro de diretrizes do CADTH. "
                  "Não é um filtro validado.",
        "nota": "Diretrizes de sociedades também ficam fora das bases (sites de APTA, NICE, AAOS). "
                "Complete com busca manual.",
    },
}

ORDEM_VARIANTES = ["base", "rs", "ecr", "diretriz", "revistas", "ecr_sensivel"]
ROTULO_VARIANTE = {"base": "Base (só os blocos e os limites)", "revistas": "Somente revistas-alvo"}

IDIOMAS_SCOPUS = {"english": "english", "portuguese": "portuguese", "spanish": "spanish", "french": "french",
                  "german": "german", "italian": "italian"}
IDIOMAS_PUBMED = {"english": "english", "portuguese": "portuguese", "spanish": "spanish", "french": "french",
                  "german": "german", "italian": "italian"}


# --------------------------------------------------------------------------- PubMed

def _tag_campo(campo: str) -> str:
    return {"tiab": "tiab", "ti": "ti", "tw": "tw"}[campo]


def termo_pubmed(termo: str, campo: str = "tiab") -> str:
    termo = limpar_termo(termo)
    if re.search(r"[\s\-/]", termo):
        return f'"{termo}"[{_tag_campo(campo)}]'
    return f"{termo}[{_tag_campo(campo)}]"


def mesh_pubmed(m: dict) -> list[str]:
    if m["principal"]:
        tag = "Majr" if m["explodir"] else "Majr:NoExp"
    else:
        tag = "Mesh" if m["explodir"] else "Mesh:NoExp"
    if m["subtitulos"]:
        return [f'"{m["termo"]}/{s}"[{tag}]' for s in m["subtitulos"]]
    return [f'"{m["termo"]}"[{tag}]']


def proximidade_pubmed(p: dict, campo: str, avisos: list[str], bloco_id: str) -> list[str]:
    campo_prox = "ti" if campo == "ti" else "tiab"
    partes = []
    if p["ordenado"]:
        avisos.append(f"Bloco '{bloco_id}': o PubMed não tem proximidade ordenada; "
                      f"'{' | '.join(p['a'])}' PRE/{p['n']} '{' | '.join(p['b'])}' vira proximidade sem ordem.")
    for a in p["a"]:
        for b in p["b"]:
            if "*" in a or "*" in b:
                partes.append(f"({termo_pubmed(a, campo_prox)} AND {termo_pubmed(b, campo_prox)})")
                avisos.append(f"Bloco '{bloco_id}': o PubMed ignora a proximidade quando há truncagem; "
                              f"'{a}' perto de '{b}' virou AND no mesmo campo (mais sensível, menos preciso).")
            else:
                partes.append(f'"{a} {b}"[{campo_prox}:~{p["n"]}]')
    return partes


def bloco_pubmed(bloco: dict, avisos: list[str]) -> str:
    partes: list[str] = []
    for m in bloco["mesh"]:
        partes.extend(mesh_pubmed(m))
    for t in bloco["livres"]:
        raiz = re.split(r"[\s\-]", t)[-1]
        if raiz.endswith("*") and len(raiz.rstrip("*")) < 4:
            avisos.append(f"Bloco '{bloco['id']}': '{t}' tem menos de 4 letras antes do *; o PubMed recusa ou "
                          f"devolve ruído.")
        if "?" in t:
            avisos.append(f"Bloco '{bloco['id']}': '{t}' usa '?', que o PubMed não entende (só o Scopus). "
                          f"Escreva as grafias por extenso.")
        if re.search(r"[^\x00-\x7f]", t):
            avisos.append(f"Bloco '{bloco['id']}': '{t}' tem acento ou letra fora do inglês. Se não for nome próprio, "
                          f"troque pelo termo em inglês: PubMed e Scopus indexam título e resumo em inglês (idioma "
                          f"se limita em 'limites.idiomas').")
        partes.append(termo_pubmed(t, bloco["campo"]))
    for p in bloco["proximidade"]:
        partes.extend(proximidade_pubmed(p, bloco["campo"], avisos, bloco["id"]))
    partes = list(dict.fromkeys(partes))
    return "(" + " OR ".join(partes) + ")"


def limites_pubmed(conceitos: dict) -> list[str]:
    lim = conceitos["limites"]
    partes = []
    if lim["ano_inicio"] or lim["ano_fim"]:
        inicio = lim["ano_inicio"] or 1800
        fim = lim["ano_fim"] or 3000
        partes.append(f"{inicio}:{fim}[dp]")
    if lim["idiomas"]:
        idiomas = [f"{IDIOMAS_PUBMED.get(i, i)}[la]" for i in lim["idiomas"]]
        partes.append("(" + " OR ".join(idiomas) + ")")
    return partes


def exclusao_pubmed(conceitos: dict) -> str | None:
    exc = conceitos.get("excluir")
    if not exc:
        return None
    partes = []
    for m in exc["mesh"]:
        partes.extend(mesh_pubmed(m))
    partes += [termo_pubmed(t, exc["campo"]) for t in exc["livres"]]
    return "(" + " OR ".join(partes) + ")" if partes else None


def jornal_pubmed(conceitos: dict) -> str | None:
    issns = issns_alvo(conceitos)
    if not issns:
        return None
    return "(" + " OR ".join(f'"{i}"[jour]' for i in issns) + ")"


def montar_pubmed(conceitos: dict, variante: str = "base", avisos: list[str] | None = None) -> str:
    """String PubMed completa para a variante pedida (base, rs, ecr, ecr_sensivel, diretriz, revistas)."""
    avisos = avisos if avisos is not None else []
    partes = [bloco_pubmed(b, avisos) for b in conceitos["blocos"]]
    if variante in FILTROS:
        partes.append(FILTROS[variante]["pubmed"])
    elif variante == "revistas":
        jornal = jornal_pubmed(conceitos)
        if not jornal:
            raise ValueError("variante 'revistas' pede 'revistas_alvo' em conceitos.json")
        partes.append(jornal)
    elif variante != "base":
        raise ValueError(f"variante desconhecida: {variante}")
    partes += limites_pubmed(conceitos)
    consulta = " AND ".join(partes)
    exc = exclusao_pubmed(conceitos)
    if exc:
        consulta = f"({consulta}) NOT {exc}"
    if conceitos["limites"]["somente_humanos"] and variante not in ("ecr", "ecr_sensivel"):
        consulta = f"({consulta}) NOT (animals[mh] NOT humans[mh])"
    return consulta


# --------------------------------------------------------------------------- Scopus

def termo_scopus(termo: str) -> str:
    termo = limpar_termo(termo)
    if re.search(r"[\s\-/,]", termo):
        return f'"{termo}"'
    return termo


def _lista_scopus(termos: list[str]) -> str:
    vistos, saida = set(), []
    for t in termos:
        chave = limpar_termo(t).lower()
        if chave and chave not in vistos:
            vistos.add(chave)
            saida.append(termo_scopus(t))
    return " OR ".join(saida)


def bloco_scopus(bloco: dict, avisos: list[str], campo_padrao: str = "TITLE-ABS-KEY") -> str:
    campo = "TITLE" if bloco["campo"] == "ti" else campo_padrao
    termos = list(bloco["livres"]) + list(bloco["scopus_extra"])
    if campo != "TITLE":
        # o nome do descritor MeSH entra como frase: o campo KEY do Scopus inclui os termos de indexação
        termos += [m["termo"] for m in bloco["mesh"]]
        if any(m["explodir"] for m in bloco["mesh"]):
            avisos.append(f"Bloco '{bloco['id']}': o Scopus não explode MeSH. Os descritores mais específicos "
                          f"só entram se estiverem em 'livres' ou 'scopus_extra'.")
    clausulas = []
    if termos:
        clausulas.append(f"{campo}({_lista_scopus(termos)})")
    for p in bloco["proximidade"]:
        operador = f"PRE/{p['n']}" if p["ordenado"] else f"W/{p['n']}"
        campo_prox = "TITLE" if bloco["campo"] == "ti" else "TITLE-ABS"
        clausulas.append(f"{campo_prox}(({_lista_scopus(p['a'])}) {operador} ({_lista_scopus(p['b'])}))")
    if len(clausulas) == 1:
        return clausulas[0]
    return "(" + " OR ".join(clausulas) + ")"


def limites_scopus(conceitos: dict) -> list[str]:
    lim = conceitos["limites"]
    partes = []
    if lim["ano_inicio"]:
        partes.append(f"PUBYEAR > {lim['ano_inicio'] - 1}")
    if lim["ano_fim"]:
        partes.append(f"PUBYEAR < {lim['ano_fim'] + 1}")
    if lim["tipos_scopus"]:
        partes.append("(" + " OR ".join(f"DOCTYPE({t})" for t in lim["tipos_scopus"]) + ")")
    if lim["idiomas"]:
        partes.append("(" + " OR ".join(f"LANGUAGE({IDIOMAS_SCOPUS.get(i, i)})" for i in lim["idiomas"]) + ")")
    return partes


def montar_scopus(conceitos: dict, variante: str = "base", avisos: list[str] | None = None,
                  campo_padrao: str = "TITLE-ABS-KEY") -> str:
    avisos = avisos if avisos is not None else []
    partes = [bloco_scopus(b, avisos, campo_padrao) for b in conceitos["blocos"]]
    if variante in FILTROS:
        partes.append(FILTROS[variante]["scopus"])
    elif variante == "revistas":
        issns = issns_alvo(conceitos)
        if not issns:
            raise ValueError("variante 'revistas' pede 'revistas_alvo' em conceitos.json")
        partes.append("(" + " OR ".join(f"ISSN({i})" for i in issns) + ")")
    elif variante != "base":
        raise ValueError(f"variante desconhecida: {variante}")
    partes += limites_scopus(conceitos)
    consulta = " AND ".join(partes)
    exc = conceitos.get("excluir")
    if exc and (exc["livres"] or exc["mesh"]):
        campo = "TITLE" if exc["campo"] == "ti" else "TITLE-ABS-KEY"
        termos = exc["livres"] + [m["termo"] for m in exc["mesh"]]
        consulta += f" AND NOT {campo}({_lista_scopus(termos)})"
    if conceitos["limites"]["somente_humanos"]:
        avisos.append("Scopus não tem filtro 'humanos' equivalente ao do PubMed; o limite foi deixado de fora "
                      "na string Scopus. Exclua estudos em animais na triagem.")
    return consulta


# --------------------------------------------------------------------------- Crossref / site do JOSPT

def termos_simples(bloco: dict, manter_truncagem: bool, maximo: int = 4) -> list[str]:
    """Palavras-chave sem sintaxe, para buscadores que não aceitam booleanos completos."""
    if bloco["simples"]:
        return bloco["simples"][:maximo]
    saida = []
    for t in bloco["livres"]:
        if "*" in t and not manter_truncagem:
            continue
        saida.append(t)
    if not saida:
        saida = [m["termo"] for m in bloco["mesh"] if "," not in m["termo"]]
    if not saida and not manter_truncagem:
        saida = [t.replace("*", "") for t in bloco["livres"][:2]]
    return saida[:maximo]


def montar_crossref(conceitos: dict) -> str:
    """Consulta de relevância (query.bibliographic): só palavras, sem operadores."""
    palavras: list[str] = []
    for b in conceitos["blocos"]:
        for t in termos_simples(b, manter_truncagem=False, maximo=3):
            for p in t.split():
                if p.lower() not in (x.lower() for x in palavras):
                    palavras.append(p)
    return " ".join(palavras)


def montar_jospt_url(conceitos: dict) -> tuple[str, str]:
    """Consulta booleana simples e URL de busca do site do JOSPT (plataforma Atypon)."""
    grupos = []
    for b in conceitos["blocos"]:
        termos = termos_simples(b, manter_truncagem=True, maximo=5)
        itens = [f'"{t}"' if " " in t and "*" not in t else t for t in termos]
        if itens:
            grupos.append("(" + " OR ".join(itens) + ")" if len(itens) > 1 else itens[0])
    consulta = " AND ".join(grupos)
    url = f"https://www.jospt.org/action/doSearch?AllField={quote_plus(consulta)}"
    lim = conceitos["limites"]
    if lim["ano_inicio"]:
        url += f"&AfterYear={lim['ano_inicio']}"
    if lim["ano_fim"]:
        url += f"&BeforeYear={lim['ano_fim']}"
    return consulta, url


# --------------------------------------------------------------------------- recorte

def aplicar_recorte(conceitos: dict, hoje: date) -> list[str]:
    """Ajusta os limites conforme o recorte. Devolve notas sobre o que mudou."""
    notas = []
    lim = conceitos["limites"]
    if conceitos["recorte"] == "fronteira":
        inicio_fronteira = hoje.year - 2
        if not lim["ano_inicio"] or lim["ano_inicio"] < inicio_fronteira:
            notas.append(f"Recorte 'fronteira': ano inicial ajustado de {lim['ano_inicio'] or 'sem limite'} para "
                         f"{inicio_fronteira} (últimos 3 anos-calendário).")
            lim["ano_inicio"] = inicio_fronteira
    return notas


def variantes_do_recorte(conceitos: dict) -> list[str]:
    recorte = conceitos["recorte"]
    if recorte == "so_topo":
        base = ["rs", "diretriz", "ecr"]
    elif recorte == "fronteira":
        base = ["base"]
    else:
        base = ["rs", "diretriz", "ecr", "base"]
    if conceitos["revistas_alvo"]:
        base.append("revistas")
    return base


# --------------------------------------------------------------------------- verificacao de MeSH

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def verificar_mesh(conceitos: dict, email: str | None = None) -> list[dict]:
    """Confere no banco MeSH do NLM se cada termo é mesmo um descritor (e não um termo de entrada ou invenção)."""
    cliente = Cliente(email)
    base = {"tool": "boost_education", "email": cliente.email}
    termos = []
    for b in conceitos["blocos"]:
        termos += [(b["id"], m["termo"]) for m in b["mesh"]]
    if conceitos.get("excluir"):
        termos += [("excluir", m["termo"]) for m in conceitos["excluir"]["mesh"]]
    saida = []
    for bloco_id, termo in termos:
        item = {"bloco": bloco_id, "termo": termo, "ok": False, "sugestao": None, "ano": None, "detalhe": ""}
        try:
            r = cliente.get(EUTILS + "esearch.fcgi", {**base, "db": "mesh", "retmode": "json",
                                                      "term": f'"{termo}"[MeSH Terms]'}).json()
            ids = r.get("esearchresult", {}).get("idlist", [])
            if not ids:
                item["detalhe"] = "não existe no MeSH com esse nome"
            else:
                s = cliente.get(EUTILS + "esummary.fcgi", {**base, "db": "mesh", "retmode": "json",
                                                           "id": ",".join(ids[:5])}).json().get("result", {})
                candidatos = [s[u] for u in s.get("uids", []) if u in s]
                for d in candidatos:
                    nomes = d.get("ds_meshterms") or []
                    if nomes and nomes[0].lower() == termo.lower() and d.get("ds_recordtype") == "descriptor":
                        item.update(ok=True, ano=d.get("ds_yearintroduced"), detalhe="descritor confirmado")
                        if nomes[0] != termo:
                            item["detalhe"] = f"descritor confirmado (grafia oficial: {nomes[0]})"
                        break
                else:
                    for d in candidatos:
                        nomes = d.get("ds_meshterms") or []
                        if termo.lower() in [n.lower() for n in nomes[1:]]:
                            item["sugestao"] = nomes[0]
                            item["detalhe"] = f"é termo de entrada; o descritor é '{nomes[0]}'"
                            break
                    else:
                        item["detalhe"] = "não é descritor (pode ser qualificador ou conceito suplementar)"
        except ErroRede as exc:
            item["detalhe"] = f"não foi possível conferir: {exc}"
            item["ok"] = None
        saida.append(item)
    return saida


def _ano_mesh(ano: str | None) -> str:
    """O NLM grava '2026 (1966)' para descritor revisado em 2026 e criado em 1966: mostra os dois por extenso."""
    if not ano:
        return ""
    anos = re.findall(r"\d{4}", str(ano))
    if len(anos) > 1:
        return f" (existe desde {min(anos)}; revisado ou renomeado em {max(anos)})"
    return f" (ano no MeSH: {anos[0]})" if anos else ""


# --------------------------------------------------------------------------- estrategia.md

MARCA_MANUAL = "<!-- MANUAL: tudo abaixo desta linha é seu e será preservado quando o arquivo for gerado de novo -->"


def _bloco_codigo(texto: str) -> str:
    return "```\n" + texto + "\n```"


def _tabela_blocos(conceitos: dict) -> str:
    linhas = ["| Bloco | Papel | MeSH | Termos livres | Proximidade |", "|---|---|---|---|---|"]
    for b in conceitos["blocos"]:
        mesh = "; ".join(
            m["termo"] + ("" if m["explodir"] else " (sem explosão)") + (" (principal)" if m["principal"] else "")
            + (f" /{', '.join(m['subtitulos'])}" if m["subtitulos"] else "") for m in b["mesh"]) or "-"
        livres = "; ".join(b["livres"]) or "-"
        prox = "; ".join(f"[{' / '.join(p['a'])}] {'PRE' if p['ordenado'] else 'W'}/{p['n']} [{' / '.join(p['b'])}]"
                         for p in b["proximidade"]) or "-"
        linhas.append(f"| {b['rotulo']} (`{b['id']}`) | {b['papel'] or '-'} | {mesh} | {livres} | {prox} |")
    return "\n".join(linhas)


def _secao_execucoes(pasta: Path) -> str:
    """Resume as execuções já registradas em brutos/, para a estratégia documentar contagens reais."""
    linhas = []
    pubmed = ler_json(pasta / "brutos" / "pubmed.json")
    if pubmed and pubmed.get("execucoes"):
        linhas += ["### PubMed", "", "| Data | Variante | Total na base | Baixados | Avisos |", "|---|---|---|---|---|"]
        for e in pubmed["execucoes"]:
            avisos = "; ".join(e.get("avisos") or []) or "-"
            baixados = "só contagem" if e.get("so_contagem") else e.get("baixados")
            linhas.append(f"| {e.get('data', '')[:10]} | {e.get('variante') or '-'} | {e.get('total')} | "
                          f"{baixados} | {avisos} |")
        linhas.append("")
        linhas.append(f"Registros únicos do PubMed: **{len(pubmed.get('registros', []))}**.")
        linhas.append("")
        com_traducao = [e for e in pubmed["execucoes"] if e.get("traducao")]
        escolhida = next((e for e in reversed(com_traducao) if e.get("variante") == "base"),
                         com_traducao[-1] if com_traducao else None)
        if escolhida:
            linhas += [f"Tradução que o PubMed fez da variante `{escolhida.get('variante') or '-'}` "
                       f"({escolhida.get('data', '')[:10]}). Confira se cada termo virou o campo esperado; as "
                       f"traduções das outras variantes estão em `brutos/pubmed.json`.", "",
                       _bloco_codigo(escolhida["traducao"]), ""]
    crossref = ler_json(pasta / "brutos" / "crossref.json")
    if crossref and crossref.get("execucoes"):
        linhas += ["### Crossref", "", "| Data | Consulta | ISSNs | Total na base | Lidos | Mantidos |",
                   "|---|---|---|---|---|---|"]
        for e in crossref["execucoes"]:
            linhas.append(f"| {e.get('data', '')[:10]} | {e.get('consulta')} | {', '.join(e.get('issn') or []) or 'todos'} | "
                          f"{e.get('total')} | {e.get('lidos')} | {e.get('mantidos')} |")
        linhas.append("")
    scopus = ler_json(pasta / "brutos" / "scopus.json")
    if scopus and scopus.get("execucoes"):
        linhas += ["### Scopus (exportação manual importada)", "", "| Data | Arquivo | Formato | Registros |",
                   "|---|---|---|---|"]
        for e in scopus["execucoes"]:
            linhas.append(f"| {e.get('data', '')[:10]} | {e.get('arquivo')} | {e.get('formato')} | {e.get('registros')} |")
        linhas.append("")
    openalex = ler_json(pasta / "brutos" / "openalex.json")
    if openalex and openalex.get("execucoes"):
        linhas += ["### OpenAlex", "", "| Data | Operação | Detalhe | Registros |", "|---|---|---|---|"]
        for e in openalex["execucoes"]:
            linhas.append(f"| {e.get('data', '')[:10]} | {e.get('operacao')} | {e.get('detalhe', '')} | {e.get('registros')} |")
        linhas.append("")
    sent = ler_json(pasta / "sentinelas.json")
    if sent and sent.get("resultados"):
        linhas += ["### Teste de sentinela", "",
                   f"Variante testada: `{sent.get('variante')}`. Recuperados: **{sent.get('recuperados')} de "
                   f"{sent.get('total')}** ({sent.get('data', '')[:10]}).", "",
                   "| Sentinela | Título | Resultado | Blocos que falharam |", "|---|---|---|---|"]
        for r in sent["resultados"]:
            ident = f"PMID {r['pmid']}" if r.get("pmid") else f"DOI {r.get('doi')}"
            linhas.append(f"| {ident} | {(r.get('titulo') or '')[:90]} | {r.get('situacao')} | "
                          f"{', '.join(r.get('blocos_falhos') or []) or '-'} |")
        linhas.append("")
    cons = ler_json(pasta / "fluxo.json")
    if cons:
        linhas += ["### Consolidação", "",
                   f"Identificados: {cons.get('identificados')} | duplicatas removidas: {cons.get('duplicatas')} | "
                   f"registros únicos: {cons.get('unicos')} ({cons.get('data', '')[:10]}).", ""]
    if not linhas:
        return ("_Nenhuma busca registrada ainda. Rode pubmed_busca.py, crossref_busca.py e teste_sentinela.py; "
                "depois rode montar_strings.py de novo para preencher esta seção._\n")
    return "\n".join(linhas)


def gerar_estrategia_md(conceitos: dict, strings: dict, pasta: Path, avisos: list[str], notas_recorte: list[str],
                        verificacao: list[dict] | None, hoje: date, manual_anterior: str | None) -> str:
    c = conceitos
    lim = c["limites"]
    L: list[str] = []
    L.append(f"# Estratégia de busca - {c['tema'] or 'tema não informado'}")
    L.append("")
    L.append(f"Gerado em {hoje.isoformat()} por `montar_strings.py` a partir de `conceitos.json`. "
             f"Para mudar uma string, edite `conceitos.json` e rode o script de novo: assim PubMed, Scopus e "
             f"Crossref continuam dizendo a mesma coisa.")
    L.append("")
    L.append("## Pergunta e recorte")
    L.append("")
    p = c["pergunta"]
    if p:
        for chave, rotulo in (("P", "População/problema"), ("I", "Intervenção/exposição"), ("C", "Comparador"),
                              ("O", "Desfechos"), ("nota", "Nota")):
            if p.get(chave):
                L.append(f"- **{rotulo}:** {p[chave]}")
    nomes_recorte = {"topo_mecanismos": "topo da pirâmide + mecanismos (padrão)", "so_topo": "só o topo da pirâmide",
                     "fronteira": "fronteira (últimos 3 anos)"}
    L.append(f"- **Recorte:** {nomes_recorte[c['recorte']]}")
    for n in notas_recorte:
        L.append(f"- {n}")
    L.append("")
    L.append("## Blocos de conceito")
    L.append("")
    L.append("Dentro do bloco os termos se somam (OR); os blocos se cruzam (AND).")
    L.append("")
    L.append(_tabela_blocos(c))
    L.append("")
    L.append("## Limites")
    L.append("")
    L.append(f"- Anos: {lim['ano_inicio'] or 'sem limite inferior'} a {lim['ano_fim'] or 'hoje'}")
    L.append(f"- Idiomas: {', '.join(lim['idiomas']) or 'sem limite'}")
    L.append(f"- Somente humanos (PubMed): {'sim' if lim['somente_humanos'] else 'nao'}")
    L.append(f"- Tipos de documento no Scopus: {', '.join(lim['tipos_scopus']) or 'sem limite'}")
    if c["revistas_alvo"]:
        L.append("- Revistas-alvo: " + "; ".join(f"{r['nome']} ({', '.join(r['issn'])})" for r in c["revistas_alvo"]))
    L.append("")

    L.append("## PubMed")
    L.append("")
    L.append("Cole em https://pubmed.ncbi.nlm.nih.gov/advanced/ ou rode `pubmed_busca.py --conceitos conceitos.json "
             "--variante <nome>`.")
    L.append("")
    for v in strings["variantes"]:
        rotulo = FILTROS[v]["rotulo"] if v in FILTROS else ROTULO_VARIANTE[v]
        L.append(f"### {rotulo} (`{v}`)")
        L.append("")
        L.append(_bloco_codigo(strings["pubmed"][v]))
        L.append("")
    L.append("## Scopus")
    L.append("")
    L.append("Cole em Scopus > Advanced document search (https://www.scopus.com/search/form.uri?display=advanced). "
             "Uma string por vez. Depois exporte o resultado (passo a passo no SKILL.md) e salve em "
             "`brutos/scopus.csv`.")
    L.append("")
    for v in strings["variantes"]:
        rotulo = FILTROS[v]["rotulo"] if v in FILTROS else ROTULO_VARIANTE[v]
        L.append(f"### {rotulo} (`{v}`)")
        L.append("")
        L.append(_bloco_codigo(strings["scopus"][v]))
        L.append("")
    L.append("## Crossref e site do JOSPT")
    L.append("")
    L.append("A Crossref não aceita booleanos: recebe palavras e ordena por relevância. O script filtra depois, "
             "localmente, pelos blocos de conceito.")
    L.append("")
    L.append(_bloco_codigo(strings["crossref"]["consulta"]))
    L.append("")
    L.append(f"ISSNs consultados por padrão: {', '.join(strings['crossref']['issn'])}.")
    L.append("")
    L.append("Busca no site do JOSPT (abra no navegador; o site bloqueia acesso automatizado):")
    L.append("")
    L.append(_bloco_codigo(strings["jospt"]["consulta"]))
    L.append("")
    L.append(f"<{strings['jospt']['url']}>")
    L.append("")
    L.append("## Filtros metodológicos usados")
    L.append("")
    for v in strings["variantes"]:
        if v in FILTROS:
            f = FILTROS[v]
            L.append(f"- **{f['rotulo']}** (`{v}`): {f['origem']} {f['nota']}")
    L.append("")
    L.append("Todo filtro de desenho troca sensibilidade por precisão. Se um artigo-sentinela sumir quando o filtro "
             "entra, a perda é do filtro, não dos blocos: confira com `teste_sentinela.py --variante <nome>`.")
    L.append("")
    if avisos or verificacao:
        L.append("## Avisos de tradução entre bases")
        L.append("")
        for a in dict.fromkeys(avisos):
            L.append(f"- {a}")
        if verificacao:
            L.append("")
            L.append("Conferência dos descritores MeSH no NLM:")
            L.append("")
            L.append("| Bloco | Termo | Situação | Desde |")
            L.append("|---|---|---|---|")
            for v in verificacao:
                estado = "ok" if v["ok"] else ("NÃO CONFERIDO" if v["ok"] is None else "PROBLEMA")
                L.append(f"| {v['bloco']} | {v['termo']} | {estado}: {v['detalhe']} | {v['ano'] or '-'} |")
        L.append("")
    L.append("## Execuções e contagens")
    L.append("")
    L.append(_secao_execucoes(pasta))
    L.append("")
    L.append("## Artigos-sentinela")
    L.append("")
    if c["sentinelas"]:
        for s in c["sentinelas"]:
            ident = " / ".join(x for x in (f"PMID {s['pmid']}" if s["pmid"] else "", f"DOI {s['doi']}" if s["doi"] else "") if x)
            L.append(f"- {ident}{' - ' + s['nota'] if s['nota'] else ''}")
    else:
        L.append("_Nenhum sentinela definido. Sem sentinela não há como medir a sensibilidade da busca._")
    L.append("")
    L.append("## Decisões e histórico")
    L.append("")
    L.append(MARCA_MANUAL)
    if manual_anterior is not None:
        L.append(manual_anterior.rstrip("\n"))
    else:
        L.append("")
        L.append("- (anote aqui cada mudança nos blocos: o que mudou, por que, e o efeito na contagem e nos sentinelas)")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- principal

def montar_tudo(conceitos: dict, incluir_sensivel: bool = False, campo_scopus: str = "TITLE-ABS-KEY"):
    avisos: list[str] = []
    variantes = ["base", "rs", "ecr", "diretriz"]
    if conceitos["revistas_alvo"]:
        variantes.append("revistas")
    if incluir_sensivel:
        variantes.append("ecr_sensivel")
    consulta_jospt, url_jospt = montar_jospt_url(conceitos)
    strings = {
        "tema": conceitos["tema"],
        "recorte": conceitos["recorte"],
        "variantes": variantes,
        "variantes_do_recorte": variantes_do_recorte(conceitos),
        "pubmed": {v: montar_pubmed(conceitos, v, avisos) for v in variantes},
        "scopus": {v: montar_scopus(conceitos, v, avisos, campo_scopus) for v in variantes},
        "crossref": {"consulta": montar_crossref(conceitos),
                     "issn": issns_alvo(conceitos) or ["0190-6011", "1938-1344"]},
        "jospt": {"consulta": consulta_jospt, "url": url_jospt},
    }
    return strings, list(dict.fromkeys(avisos))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Gera as strings de busca de PubMed, Scopus e Crossref/JOSPT a partir de conceitos.json "
                    "e grava estrategia.md e strings.json.",
        epilog="O esquema de conceitos.json está em references/esquema-conceitos.md.")
    ap.add_argument("conceitos", help="caminho de conceitos.json (normalmente aulas/<aula>/01_busca/conceitos.json)")
    ap.add_argument("--saida", help="pasta de saída (padrão: a pasta de conceitos.json)")
    ap.add_argument("--hoje", help="data de referência AAAA-MM-DD (padrão: hoje); define o recorte 'fronteira'")
    ap.add_argument("--verificar-mesh", action="store_true",
                    help="confere cada descritor MeSH no banco do NLM (precisa de rede)")
    ap.add_argument("--ecr-sensivel", action="store_true",
                    help="inclui também a versão de máxima sensibilidade do filtro de ECR")
    ap.add_argument("--scopus-campo", default="TITLE-ABS-KEY", choices=["TITLE-ABS-KEY", "TITLE-ABS"],
                    help="campo padrão no Scopus; TITLE-ABS é mais preciso, TITLE-ABS-KEY mais sensível (padrão)")
    ap.add_argument("--email", help="e-mail de contato enviado ao NCBI (ou variável BOOST_EMAIL)")
    ap.add_argument("--so-imprimir", action="store_true", help="mostra as strings sem gravar arquivos")
    args = ap.parse_args(argv)

    conceitos = carregar_conceitos(args.conceitos)
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()
    notas_recorte = aplicar_recorte(conceitos, hoje)
    strings, avisos = montar_tudo(conceitos, args.ecr_sensivel, args.scopus_campo)
    strings["gerado_em"] = hoje.isoformat()
    strings["limites"] = conceitos["limites"]

    verificacao = None
    if args.verificar_mesh:
        print("Conferindo descritores MeSH no NLM...")
        verificacao = verificar_mesh(conceitos, args.email)
        problemas = [v for v in verificacao if v["ok"] is False]
        for v in verificacao:
            marca = "ok " if v["ok"] else ("?? " if v["ok"] is None else "ERRO")
            print(f"  {marca} [{v['bloco']}] {v['termo']}: {v['detalhe']}" + _ano_mesh(v["ano"]))
        strings["mesh_verificado"] = verificacao
        if problemas:
            print(f"\nATENÇÃO: {len(problemas)} termo(s) MeSH com problema. No PubMed, um MeSH inexistente devolve "
                  f"zero sem avisar e enfraquece o bloco. Corrija conceitos.json.")
        nao_conferidos = [v for v in verificacao if v["ok"] is None]
        if nao_conferidos:
            print(f"\nATENÇÃO: {len(nao_conferidos)} descritor(es) NÃO CONFERIDO(S) (falha de rede). As strings foram "
                  f"geradas, mas diga ao usuário que os MeSH não foram verificados, ou use só descritores de "
                  f"references/vocabulario-fisioterapia.md.")

    pasta = Path(args.saida) if args.saida else Path(args.conceitos).resolve().parent
    print(f"\nTema: {conceitos['tema']}")
    print(f"Recorte: {conceitos['recorte']} | blocos: {len(conceitos['blocos'])} | "
          f"variantes: {', '.join(strings['variantes'])}")
    print("\n--- PubMed (base) ---\n" + strings["pubmed"]["base"])
    print("\n--- Scopus (base) ---\n" + strings["scopus"]["base"])
    print("\n--- Crossref ---\n" + strings["crossref"]["consulta"])
    print("\n--- Site do JOSPT ---\n" + strings["jospt"]["url"])
    if avisos:
        print("\nAvisos:")
        for a in avisos:
            print(f"  - {a}")
    if args.so_imprimir:
        return 0

    pasta.mkdir(parents=True, exist_ok=True)
    destino_md = pasta / "estrategia.md"
    manual = None
    if destino_md.exists():
        antigo = destino_md.read_text(encoding="utf-8")
        if MARCA_MANUAL in antigo:
            manual = antigo.split(MARCA_MANUAL, 1)[1]
    md = gerar_estrategia_md(conceitos, strings, pasta, avisos, notas_recorte, verificacao, hoje, manual)
    destino_md.write_text(md, encoding="utf-8")
    gravar_json(pasta / "strings.json", strings)
    print(f"\nGravado: {destino_md}")
    print(f"Gravado: {pasta / 'strings.json'}")
    print(f"Variantes recomendadas para o recorte '{conceitos['recorte']}': "
          f"{', '.join(strings['variantes_do_recorte'])}")
    if verificacao and any(v["ok"] is not True for v in verificacao):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
