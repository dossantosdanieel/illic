#!/usr/bin/env python3
"""Une as fontes, remove duplicatas, classifica o desenho, pontua e gera a planilha de triagem.

Lê brutos/pubmed.json, crossref.json, scopus.json e openalex.json; grava registros.json
(registro unificado do contrato), duplicatas.json (auditoria), fluxo.json (números tipo PRISMA)
e triagem.xlsx. Pode ser rodado quantas vezes for preciso: as chaves SobrenomeAno já atribuídas
e as decisões já preenchidas na planilha são preservadas.

Uso:
  python3 consolidar.py --pasta aulas/x/01_busca
  python3 consolidar.py --pasta aulas/x/01_busca --decisoes aulas/x/01_busca/decisoes.json
  python3 consolidar.py --pasta aulas/x/01_busca --recorte fronteira --hoje 2026-11-24
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import math
import re
import shutil
from collections import Counter
from datetime import date
from difflib import SequenceMatcher

from _comum import (DESENHOS, JOSPT, RECORTES, agora_iso, bloco_casa_texto, carregar_conceitos, gravar_json,
                    issns_alvo, ler_json, lista_issn, normalizar_doi, normalizar_pmid, normalizar_titulo, sair,
                    sem_acento, sobrenome_de)

PRIORIDADE_FONTE = ["pubmed", "scopus", "crossref", "openalex"]

# --------------------------------------------------------------------------- pesos por recorte
# 'desenho' = fração do teto de pontos de desenho. Explicado em references/recortes-de-evidencia.md.
PESOS = {
    "topo_mecanismos": {
        "tetos": {"desenho": 35, "atualidade": 20, "citacoes": 15, "revista": 10, "sentinela": 10, "aderencia": 10},
        "desenho": {"Diretriz": 1.0, "Revisao sistematica/meta-analise": 1.0, "ECR": 0.85, "Consenso/Delphi": 0.7,
                    "Laboratorio/mecanistico": 0.7, "Coorte": 0.6, "Estudo de acuracia diagnostica": 0.6,
                    "Caso-controle": 0.45, "Transversal": 0.4, "Revisao narrativa": 0.4,
                    "Relato/serie de casos": 0.15, "Editorial/comentario": 0.1, "Outro": 0.15},
        "idade_cheia": 2, "idade_zero": 15,
    },
    "so_topo": {
        "tetos": {"desenho": 45, "atualidade": 20, "citacoes": 10, "revista": 10, "sentinela": 10, "aderencia": 5},
        "desenho": {"Diretriz": 1.0, "Revisao sistematica/meta-analise": 1.0, "ECR": 0.8, "Consenso/Delphi": 0.55,
                    "Laboratorio/mecanistico": 0.1, "Coorte": 0.3, "Estudo de acuracia diagnostica": 0.3,
                    "Caso-controle": 0.2, "Transversal": 0.15, "Revisao narrativa": 0.15,
                    "Relato/serie de casos": 0.05, "Editorial/comentario": 0.05, "Outro": 0.05},
        "idade_cheia": 3, "idade_zero": 15,
    },
    "fronteira": {
        "tetos": {"desenho": 25, "atualidade": 35, "citacoes": 10, "revista": 10, "sentinela": 10, "aderencia": 10},
        "desenho": {"Diretriz": 1.0, "Revisao sistematica/meta-analise": 1.0, "ECR": 0.95, "Consenso/Delphi": 0.75,
                    "Laboratorio/mecanistico": 0.7, "Coorte": 0.7, "Estudo de acuracia diagnostica": 0.7,
                    "Caso-controle": 0.5, "Transversal": 0.5, "Revisao narrativa": 0.45,
                    "Relato/serie de casos": 0.2, "Editorial/comentario": 0.25, "Outro": 0.25},
        "idade_cheia": 1, "idade_zero": 4,
    },
}

# --------------------------------------------------------------------------- planilha
DECISOES = ["incluir", "excluir", "talvez"]
MOTIVOS = ["fora do tema", "população diferente", "intervenção diferente", "desenho inadequado",
           "sem resultados (protocolo)", "duplicata ou republicação", "superado por evidência mais nova",
           "qualidade insuficiente", "idioma", "sem acesso ao texto", "outro"]
PAPEIS = ["âncora da aula", "evidência principal", "mecanismo", "contraponto", "aplicação clínica",
          "contexto", "leitura complementar"]
COLUNAS = [  # (campo interno, título, largura)
    ("chave", "Chave", 18), ("decisao", "Decisão", 11), ("motivo", "Motivo da exclusão", 24),
    ("papel", "Papel na aula", 22), ("observacoes", "Observações", 30), ("pontuacao", "Pontuação", 10),
    ("desenho", "Desenho", 26), ("ano", "Ano", 7), ("primeiro_autor", "1º autor", 16), ("titulo", "Título", 70),
    ("revista", "Revista", 26), ("citacoes", "Citações", 9), ("cit_ano", "Cit./ano", 9),
    ("acesso_aberto", "Acesso aberto", 12), ("fontes", "Fontes", 20), ("sentinela", "Sentinela", 10),
    ("doi", "DOI", 30), ("pmid", "PMID", 11), ("motivos", "Por que esta pontuação", 70), ("resumo", "Resumo", 90),
]
CAMPOS_DECISAO = ("decisao", "motivo", "papel", "observacoes")


# --------------------------------------------------------------------------- leitura das fontes

def carregar_fontes(pasta: Path) -> tuple[list[dict], dict, list[dict]]:
    """Devolve (registros brutos com 'fonte', contagem por fonte, enriquecimento do OpenAlex)."""
    todos, contagem, enriquecimento = [], {}, []
    for fonte in PRIORIDADE_FONTE:
        dados = ler_json(pasta / "brutos" / f"{fonte}.json")
        if not dados:
            continue
        registros = dados.get("registros", []) if isinstance(dados, dict) else dados
        validos = 0
        for r in registros:
            if not isinstance(r, dict) or not (r.get("titulo") or "").strip():
                continue
            r = dict(r)
            r["fonte"] = fonte
            r["doi"] = normalizar_doi(r.get("doi"))
            r["pmid"] = normalizar_pmid(r.get("pmid"))
            r["_titulo_norm"] = normalizar_titulo(r["titulo"])
            r["_sobrenome"] = sem_acento(r.get("primeiro_autor") or sobrenome_de((r.get("autores") or [""])[0])).lower()
            todos.append(r)
            validos += 1
        contagem[fonte] = validos
        if fonte == "openalex" and isinstance(dados, dict):
            enriquecimento = dados.get("enriquecimento", [])
    return todos, contagem, enriquecimento


# --------------------------------------------------------------------------- deduplicação

class Conjuntos:
    """Union-find que guarda, por grupo, os DOIs e PMIDs já reunidos."""

    def __init__(self, registros: list[dict]):
        self.pai = list(range(len(registros)))
        self.dois = [{r["doi"]} if r["doi"] else set() for r in registros]
        self.pmids = [{r["pmid"]} if r["pmid"] else set() for r in registros]
        self.criterios = [set() for _ in registros]

    def raiz(self, i: int) -> int:
        while self.pai[i] != i:
            self.pai[i] = self.pai[self.pai[i]]
            i = self.pai[i]
        return i

    def conflito(self, a: int, b: int) -> bool:
        """Verdadeiro se juntar criaria um grupo com dois DOIs ou dois PMIDs diferentes."""
        ra, rb = self.raiz(a), self.raiz(b)
        return len(self.dois[ra] | self.dois[rb]) > 1 or len(self.pmids[ra] | self.pmids[rb]) > 1

    def unir(self, a: int, b: int, criterio: str) -> None:
        ra, rb = self.raiz(a), self.raiz(b)
        if ra == rb:
            self.criterios[ra].add(criterio)
            return
        self.pai[rb] = ra
        self.dois[ra] |= self.dois[rb]
        self.pmids[ra] |= self.pmids[rb]
        self.criterios[ra] |= self.criterios[rb] | {criterio}


def _anos_compativeis(a: dict, b: dict, tolerancia: int) -> bool:
    if not a.get("ano") or not b.get("ano"):
        return True
    return abs(int(a["ano"]) - int(b["ano"])) <= tolerancia


def deduplicar(registros: list[dict], tolerancia_ano: int = 1) -> tuple[list[list[dict]], list[set]]:
    """Agrupa registros do mesmo artigo. Ordem dos critérios: DOI, PMID, EID, título normalizado + ano
    (com tolerância) e, por fim, título quase igual do mesmo primeiro autor."""
    uf = Conjuntos(registros)
    for campo in ("doi", "pmid", "scopus_eid"):
        visto: dict[str, int] = {}
        for i, r in enumerate(registros):
            valor = r.get(campo)
            if not valor:
                continue
            if valor in visto:
                uf.unir(visto[valor], i, campo.replace("scopus_eid", "eid"))
            else:
                visto[valor] = i
    por_titulo: dict[str, list[int]] = {}
    for i, r in enumerate(registros):
        if r["_titulo_norm"]:
            por_titulo.setdefault(r["_titulo_norm"], []).append(i)
    for titulo, indices in por_titulo.items():
        curto = len(titulo.split()) < 5
        for x in range(len(indices)):
            for y in range(x + 1, len(indices)):
                a, b = indices[x], indices[y]
                if uf.raiz(a) == uf.raiz(b):
                    continue
                ra, rb = registros[a], registros[b]
                if not _anos_compativeis(ra, rb, tolerancia_ano):
                    continue
                if curto and ra["_sobrenome"] and rb["_sobrenome"] and ra["_sobrenome"] != rb["_sobrenome"]:
                    continue  # títulos genéricos ('Shoulder pain') só se juntam com o mesmo primeiro autor
                if uf.conflito(a, b):
                    continue
                uf.unir(a, b, "titulo+ano")
    # títulos quase iguais (subtítulo a mais, pontuação), restrito ao mesmo primeiro autor
    por_autor: dict[str, list[int]] = {}
    for i, r in enumerate(registros):
        if r["_sobrenome"] and len(r["_titulo_norm"]) >= 25:
            por_autor.setdefault(r["_sobrenome"], []).append(i)
    for indices in por_autor.values():
        if len(indices) > 400:
            continue
        for x in range(len(indices)):
            for y in range(x + 1, len(indices)):
                a, b = indices[x], indices[y]
                if uf.raiz(a) == uf.raiz(b):
                    continue
                ra, rb = registros[a], registros[b]
                if not _anos_compativeis(ra, rb, tolerancia_ano) or uf.conflito(a, b):
                    continue
                ta, tb = ra["_titulo_norm"], rb["_titulo_norm"]
                if abs(len(ta) - len(tb)) > 0.25 * max(len(ta), len(tb)) and not (ta.startswith(tb) or tb.startswith(ta)):
                    continue
                if (ta.startswith(tb) or tb.startswith(ta)) and min(len(ta), len(tb)) >= 40:
                    uf.unir(a, b, "título aproximado")
                elif SequenceMatcher(None, ta, tb).ratio() >= 0.94:
                    uf.unir(a, b, "título aproximado")
    grupos: dict[int, list[dict]] = {}
    for i, r in enumerate(registros):
        grupos.setdefault(uf.raiz(i), []).append(r)
    raizes = list(grupos)
    return [grupos[r] for r in raizes], [uf.criterios[r] for r in raizes]


# --------------------------------------------------------------------------- fusão

def _primeiro(grupo: list[dict], campo: str, vazio=None):
    for fonte in PRIORIDADE_FONTE:
        for r in grupo:
            if r["fonte"] == fonte and r.get(campo) not in (None, "", [], {}):
                return r[campo]
    return vazio


def fundir(grupo: list[dict], criterios: set) -> dict:
    resumos = [r.get("resumo") or "" for r in grupo]
    resumo = next((r.get("resumo") for r in grupo if r["fonte"] == "pubmed" and r.get("resumo")), "") \
        or max(resumos, key=len)
    autores = _primeiro(grupo, "autores", [])
    mais_longa = max((r.get("autores") or [] for r in grupo), key=len)
    if len(mais_longa) > len(autores) and not any(r["fonte"] == "pubmed" and r.get("autores") for r in grupo):
        autores = mais_longa
    issn: list[str] = []
    for r in grupo:
        for i in lista_issn(r.get("issn")):
            if i not in issn:
                issn.append(i)
    primeiro_autor = _primeiro(grupo, "primeiro_autor", "") or (sobrenome_de(autores[0]) if autores else "")
    origem = []
    for r in grupo:
        for o in r.get("origem_citacao") or []:
            if o not in origem:
                origem.append(o)
    variantes = []
    for r in grupo:
        for v in r.get("variantes") or []:
            if v not in variantes:
                variantes.append(v)
    reg = {
        "chave": None,
        "titulo": _primeiro(grupo, "titulo", ""),
        "autores": autores,
        "primeiro_autor": primeiro_autor,
        "ano": _primeiro(grupo, "ano"),
        "revista": _primeiro(grupo, "revista", ""),
        "issn": issn,
        "doi": _primeiro(grupo, "doi"),
        "pmid": _primeiro(grupo, "pmid"),
        "pmcid": _primeiro(grupo, "pmcid"),
        "scopus_eid": _primeiro(grupo, "scopus_eid"),
        "resumo": resumo,
        "tipos_publicacao": _primeiro(grupo, "tipos_publicacao", []),
        "mesh": _primeiro(grupo, "mesh", []),
        "desenho": "Outro",
        "citacoes": None, "acesso_aberto": None, "licenca": None, "url_pdf_aberto": None,
        "fontes": [f for f in PRIORIDADE_FONTE if any(r["fonte"] == f for r in grupo)],
        "pontuacao": 0.0, "motivos_pontuacao": [],
        # campos extras (fora do contrato mínimo, úteis para as outras skills)
        "revista_completa": _primeiro(grupo, "revista_completa", ""),
        "volume": _primeiro(grupo, "volume", ""), "fasciculo": _primeiro(grupo, "fasciculo", ""),
        "paginas": _primeiro(grupo, "paginas", ""),
        "palavras_chave": _primeiro(grupo, "palavras_chave", []),
        "tipo_scopus": _primeiro(grupo, "tipo_scopus", ""),
        "tipo_openalex": _primeiro(grupo, "tipo_openalex", ""),
        "situacao_indexacao": _primeiro(grupo, "situacao_indexacao", ""),
        "variantes_pubmed": variantes,
        "origem_citacao": origem,
        "retratado": any(r.get("retratado") for r in grupo),
        "sentinela": False,
        "registros_fundidos": len(grupo),
        "criterios_dedup": sorted(criterios),
        "_citacoes_scopus": _primeiro(grupo, "citacoes_scopus"),
        "_citacoes_crossref": _primeiro(grupo, "citacoes_crossref"),
        "_citacoes_openalex": next((r.get("citacoes") for r in grupo if r["fonte"] == "openalex"
                                    and r.get("citacoes") is not None), None),
        "_oa": next(({k: r.get(k) for k in ("acesso_aberto", "licenca", "url_pdf_aberto", "status_oa", "url_oa")}
                     for r in grupo if r["fonte"] == "openalex"), None),
        "_licenca_crossref": _primeiro(grupo, "licenca"),
    }
    return reg


def enriquecer(reg: dict, por_doi: dict, por_pmid: dict) -> None:
    e = (por_doi.get(reg["doi"]) if reg["doi"] else None) or (por_pmid.get(reg["pmid"]) if reg["pmid"] else None) \
        or reg.pop("_oa", None) or {}
    reg.pop("_oa", None)
    citacoes = e.get("citacoes")
    origem = "OpenAlex"
    if citacoes is None and reg["_citacoes_openalex"] is not None:
        citacoes = reg["_citacoes_openalex"]
    if citacoes is None and reg["_citacoes_scopus"] is not None:
        citacoes, origem = reg["_citacoes_scopus"], "Scopus"
    if citacoes is None and reg["_citacoes_crossref"] is not None:
        citacoes, origem = reg["_citacoes_crossref"], "Crossref"
    reg["citacoes"] = citacoes
    reg["citacoes_fonte"] = origem if citacoes is not None else None
    if e:
        reg["acesso_aberto"] = bool(e.get("acesso_aberto"))
        reg["licenca"] = e.get("licenca")
        reg["url_pdf_aberto"] = e.get("url_pdf_aberto")
        reg["status_oa"] = e.get("status_oa")
        reg["url_oa"] = e.get("url_oa")
        if not reg["pmcid"] and e.get("pmcid"):
            reg["pmcid"] = e["pmcid"]
        if not reg["pmid"] and e.get("pmid"):
            reg["pmid"] = e["pmid"]
        if e.get("retratado"):
            reg["retratado"] = True
    if reg["acesso_aberto"] is None and reg["pmcid"]:
        reg["acesso_aberto"] = True  # texto completo no PMC
    if not reg["licenca"] and reg["_licenca_crossref"]:
        reg["licenca"] = reg["_licenca_crossref"]
    for k in ("_citacoes_scopus", "_citacoes_crossref", "_citacoes_openalex", "_licenca_crossref"):
        reg.pop(k, None)


# --------------------------------------------------------------------------- desenho do estudo

_R = lambda padrao: re.compile(padrao, re.I)  # noqa: E731
RE_ERRATA = _R(r"^(correction|corrigendum|erratum|retraction|expression of concern|notice of retraction)\b")
RE_PROTOCOLO = _R(r"\b(study protocol|trial protocol|protocol (for|of) (a|an|the)\b|: (a |study )?protocol\b|"
                  r"protocol for\b|rationale and design)")
RE_DIRETRIZ = _R(r"\b(clinical practice guidelines?|practice guidelines?|guidelines?|best practice recommendations?)\b")
RE_DIRETRIZ_NAO = _R(r"\b(adher|complian|implement|survey|knowledge|awareness|concordan|consisten|according to|"
                     r"quality of|appraisal|uptake|follow)")
RE_COMENTARIO = _R(r"^(re:|response\b|reply\b|letter to|letter:|comments? on|commentary\b|authors?['’]? ?(response|reply)|"
                   r"in reply|editorial\b|correspondence|invited commentary|corr insights|editor['’]s spotlight|"
                   r"critically appraised paper|expert commentary)|perspectives for patients|"
                   r"\bletter to the editor\b|: (a )?(commentary|response|reply)\b")
RE_CONSENSO = _R(r"\b(consensus statement|expert consensus|international consensus|consensus (recommendations?|"
                 r"document|exercise|study|meeting|conference|opinion|expert|definition|for|on)|"
                 r"consensus$|delphi|position statement|position stand)\b")
RE_CONSENSO_NAO = _R(r"consensus on exercise reporting|\bCERT\b|consensus[- ]based (standards|checklist)")
RE_LAB_FORTE = _R(r"\b(cadaver\w*|in vitro|finite element|animal model|rat model|murine|mice|rats?|rabbits?|"
                  r"biomechanical (analysis|study|evaluation|comparison|testing|assessment))\b")
RE_RS = _R(r"systematic(ally)? review|systematic literature review|meta-?analy|metaanaly|umbrella review|"
           r"scoping review|overview of (systematic )?reviews|network meta|cochrane review|rapid review|"
           r"review of systematic reviews|evidence synthesis|meta-regression|best[- ]evidence synthesis")
RE_RS_RESUMO = _R(r"systematic(ally)? (review|search)|meta-analys|were searched|prisma\b|risk of bias")
RE_ECR_TITULO = _R(r"randomi[sz]ed|\brct\b|randomly (assigned|allocated)|controlled (clinical )?trial")
RE_ECR_RESUMO = _R(r"randomly (assigned|allocated|divided|distributed)|were randomi[sz]ed|was randomi[sz]ed|"
                   r"randomi[sz]ed (to|into)\b|participants? (were|was) (randomly|randomi[sz]ed)|"
                   r"(design|methods?):?\s*(a |this |the )?(\w+[- ]){0,4}randomi[sz]ed (controlled|clinical)")
RE_SECUNDARIA = _R(r"secondary analysis|post[- ]hoc|ancillary|follow-up of a randomi|exploratory analysis|"
                   r"prespecified|pre-specified|mediation analysis")
RE_ACURACIA = _R(r"diagnostic accuracy|sensitivity and specificity|likelihood ratio|diagnostic (value|validity|"
                 r"performance|utility)|accuracy of\b.*\b(tests?|examination|ultraso|mri|imaging|assessment)|"
                 r"clinical tests? for")
RE_LAB = _R(r"\b(electromyograph\w*|emg|biomechanic\w*|kinematic\w*|kinetics?|cadaver\w*|in vitro|in vivo|"
            r"finite element|animal model|rat model|murine|mice|rats?|rabbits?|histolog\w*|gene expression|"
            r"muscle activ\w+|mechanobiolog\w*|tendon (stiffness|thickness|properties|structure)|shear[- ]wave|"
            r"elastograph\w*|motion analysis|acromiohumeral distance|subacromial space|motor unit\w*|"
            r"corticospinal|cortical excitab\w*|pain sensitivity|conditioned pain modulation|"
            r"pressure pain threshold\w*)\b")
RE_CASO = _R(r"\bcase reports?\b|\bcase series\b|\ba case of\b|\bcase study\b|\bcase presentation\b|: a case\b")
RE_CASO_CONTROLE = _R(r"case[- ]control")
RE_COORTE = _R(r"\bcohort\b|prospective (study|observational|longitudinal)|longitudinal (study|analysis|cohort)|"
               r"\bregistry\b|retrospective (study|analysis|review|cohort|chart)|prognostic (factors?|study|model)|"
               r"predict(ors?|ive factors?) of|follow-up study")
RE_TRANSVERSAL = _R(r"cross[- ]sectional|\bsurvey\b|\bprevalence\b|questionnaire study|observational study")
RE_MEDIDA = _R(r"\b(reliability|validity|validation|responsiveness|measurement properties|psychometric\w*|"
               r"minimal(ly)? (clinically )?important|cross-cultural adaptation|translation and)\b")
RE_QUALI = _R(r"\bqualitative\b|focus groups?|semi-structured interviews?|thematic analysis|mixed[- ]methods")
RE_NARRATIVA = _R(r"\b(narrative review|literature review|review|overview|current concepts?|clinical commentary|"
                  r"masterclass|state[- ]of[- ]the[- ]art|update on|viewpoint|perspective)\b")

PT_EDITORIAL = {"Editorial", "Comment", "Letter", "News", "Newspaper Article", "Interview", "Biography",
                "Patient Education Handout", "Introductory Journal Article", "Personal Narrative"}
PT_ERRATA = {"Published Erratum", "Retraction of Publication", "Expression of Concern"}
PT_CONSENSO = {"Consensus Development Conference", "Consensus Development Conference, NIH", "Consensus Statement"}
PT_ECR = {"Randomized Controlled Trial", "Pragmatic Clinical Trial", "Equivalence Trial",
          "Randomized Controlled Trial, Veterinary"}
PT_ENSAIO = {"Clinical Trial", "Controlled Clinical Trial", "Clinical Trial, Phase I", "Clinical Trial, Phase II",
             "Clinical Trial, Phase III", "Clinical Trial, Phase IV", "Clinical Study"}
MESH_COORTE = {"Cohort Studies", "Prospective Studies", "Longitudinal Studies"}
MESH_LAB = {"Biomechanical Phenomena", "Electromyography", "Cadaver", "Models, Animal", "Disease Models, Animal",
            "In Vitro Techniques", "Finite Element Analysis", "Elasticity Imaging Techniques"}


def classificar(reg: dict) -> tuple[str, str]:
    """Devolve (desenho, motivo). Ordem: tipos de publicação do PubMed (mais confiáveis), depois título,
    resumo, MeSH e, por último, o tipo de documento do Scopus/OpenAlex."""
    titulo = reg.get("titulo") or ""
    resumo = reg.get("resumo") or ""
    pts = set(reg.get("tipos_publicacao") or [])
    mesh = set(reg.get("mesh") or [])
    tipo_scopus = (reg.get("tipo_scopus") or "").lower()
    tipo_oa = (reg.get("tipo_openalex") or "").lower()

    if pts & PT_ERRATA or RE_ERRATA.search(titulo) or tipo_scopus in ("erratum", "retracted"):
        return "Outro", "errata, retratação ou nota de preocupação"
    if "Clinical Trial Protocol" in pts or RE_PROTOCOLO.search(titulo):
        return "Outro", "protocolo de estudo (sem resultados)"
    if pts & {"Practice Guideline", "Guideline"}:
        return "Diretriz", "tipo de publicação PubMed: " + ", ".join(sorted(pts & {"Practice Guideline", "Guideline"}))
    if pts & {"Meta-Analysis", "Systematic Review", "Network Meta-Analysis"}:
        return ("Revisao sistematica/meta-analise",
                "tipo de publicação PubMed: " + ", ".join(sorted(pts & {"Meta-Analysis", "Systematic Review",
                                                                        "Network Meta-Analysis"})))
    if (reg.get("doi") or "").startswith("10.1002/14651858") and "protocol" not in titulo.lower():
        return "Revisao sistematica/meta-analise", "revisão Cochrane (DOI 10.1002/14651858)"
    if RE_RS.search(titulo) and not (pts & PT_EDITORIAL) and not RE_COMENTARIO.search(titulo):
        return "Revisao sistematica/meta-analise", f"título: '{RE_RS.search(titulo).group(0)}'"
    if pts & PT_ECR:
        extra = " (análise secundária)" if RE_SECUNDARIA.search(titulo) else ""
        return "ECR", "tipo de publicação PubMed: Randomized Controlled Trial" + extra
    if pts & PT_EDITORIAL and not (pts & PT_CONSENSO):
        return "Editorial/comentario", "tipo de publicação PubMed: " + ", ".join(sorted(pts & PT_EDITORIAL))
    if RE_COMENTARIO.search(titulo) or (not pts and tipo_scopus in ("editorial", "letter", "note", "short survey")) \
            or (not pts and tipo_oa in ("editorial", "letter", "erratum", "paratext")):
        return "Editorial/comentario", "título ou tipo de documento indica carta, comentário ou editorial"
    if RE_DIRETRIZ.search(titulo) and not RE_DIRETRIZ_NAO.search(titulo):
        return "Diretriz", f"título: '{RE_DIRETRIZ.search(titulo).group(0)}'"
    if pts & PT_CONSENSO:
        return "Consenso/Delphi", "tipo de publicação PubMed: " + ", ".join(sorted(pts & PT_CONSENSO))
    if (RE_CONSENSO.search(titulo) and not RE_CONSENSO_NAO.search(titulo)) or (
            "Delphi Technique" in mesh and re.search(r"consensus", resumo, re.I)):
        return "Consenso/Delphi", "título ou MeSH indicam consenso/Delphi"
    if RE_ECR_TITULO.search(titulo):
        extra = " (análise secundária)" if RE_SECUNDARIA.search(titulo) else ""
        return "ECR", f"título: '{RE_ECR_TITULO.search(titulo).group(0)}'" + extra
    if RE_LAB_FORTE.search(titulo) and "Review" not in pts:
        return "Laboratorio/mecanistico", f"título: '{RE_LAB_FORTE.search(titulo).group(0)}'"
    if RE_ECR_RESUMO.search(resumo) and "Review" not in pts:
        return "ECR", f"resumo: '{RE_ECR_RESUMO.search(resumo).group(0)[:50]}'"
    if "Review" in pts and RE_RS_RESUMO.search(resumo) and re.search(r"systematic", resumo, re.I):
        return "Revisao sistematica/meta-analise", "tipo Review com método sistemático descrito no resumo"
    if RE_ACURACIA.search(titulo) or ("Sensitivity and Specificity" in mesh and re.search(
            r"diagnos|accuracy|\btests?\b", titulo, re.I)):
        return "Estudo de acuracia diagnostica", "título/MeSH indicam acurácia diagnóstica"
    if "Case Reports" in pts or RE_CASO.search(titulo):
        return "Relato/serie de casos", "tipo de publicação ou título indica relato/série de casos"
    if "Animals" in mesh and "Humans" not in mesh:
        return "Laboratorio/mecanistico", "MeSH: estudo em animais"
    if RE_LAB.search(titulo) and "Review" not in pts:
        return "Laboratorio/mecanistico", f"título: '{RE_LAB.search(titulo).group(0)}'"
    if "Review" in pts or (not pts and (tipo_scopus == "review" or tipo_oa == "review")):
        return "Revisao narrativa", "tipo Review sem método sistemático identificado"
    if RE_CASO_CONTROLE.search(titulo) or RE_CASO_CONTROLE.search(resumo[:1500]) and "Case-Control Studies" in mesh:
        return "Caso-controle", "título/resumo: caso-controle"
    if RE_QUALI.search(titulo):
        return "Outro", "estudo qualitativo ou de métodos mistos"
    if RE_MEDIDA.search(titulo) or "Validation Study" in pts:
        return "Outro", "estudo de propriedades de medida (confiabilidade/validade)"
    if RE_COORTE.search(titulo) or mesh & MESH_COORTE:
        base = RE_COORTE.search(titulo)
        return "Coorte", (f"título: '{base.group(0)}'" if base else "MeSH: " + ", ".join(sorted(mesh & MESH_COORTE)))
    if "Case-Control Studies" in mesh or RE_CASO_CONTROLE.search(resumo):
        return "Caso-controle", "MeSH/resumo: caso-controle (o MeSH é atribuído com folga; confira)"
    if RE_TRANSVERSAL.search(titulo) or "Cross-Sectional Studies" in mesh:
        return "Transversal", "título ou MeSH: transversal"
    if mesh & MESH_LAB:
        return "Laboratorio/mecanistico", "MeSH: " + ", ".join(sorted(mesh & MESH_LAB))
    if RE_COORTE.search(resumo[:2500]) or "Retrospective Studies" in mesh or "Follow-Up Studies" in mesh:
        return "Coorte", "resumo/MeSH indicam estudo longitudinal ou retrospectivo"
    if RE_TRANSVERSAL.search(resumo[:2500]) or "Observational Study" in pts:
        return "Transversal", "resumo indica estudo transversal/observacional"
    if RE_LAB.search(resumo[:2500]) and not resumo.lower().count("random"):
        return "Laboratorio/mecanistico", f"resumo: '{RE_LAB.search(resumo[:2500]).group(0)}'"
    if pts & PT_ENSAIO:
        return "Outro", "ensaio clínico sem randomização declarada"
    if RE_NARRATIVA.search(titulo):
        return "Revisao narrativa", f"título: '{RE_NARRATIVA.search(titulo).group(0)}'"
    return "Outro", "desenho não identificado pelos metadados; confira no resumo"


# --------------------------------------------------------------------------- chave SobrenomeAno

def base_da_chave(reg: dict) -> str:
    nome = reg.get("primeiro_autor") or (sobrenome_de(reg["autores"][0]) if reg.get("autores") else "")
    partes = [p for p in re.split(r"[^A-Za-z]+", sem_acento(nome)) if p]
    if len(partes) > 3:
        partes = partes[:1]  # autor coletivo ('American Physical Therapy Association')
    texto = "".join(p[0].upper() + p[1:] for p in partes) or "SemAutor"
    return f"{texto}{reg.get('ano') or 'sd'}"


def _ids_do_registro(reg: dict) -> list[str]:
    ids = []
    if reg.get("doi"):
        ids.append("doi:" + reg["doi"])
    if reg.get("pmid"):
        ids.append("pmid:" + str(reg["pmid"]))
    if reg.get("scopus_eid"):
        ids.append("eid:" + reg["scopus_eid"])
    ids.append("titulo:" + normalizar_titulo(reg.get("titulo") or "") + "|" + str(reg.get("ano") or ""))
    return ids


def atribuir_chaves(registros: list[dict], anteriores: list[dict]) -> int:
    """Chave SobrenomeAno sem colisão (b, c, ...). Reaproveita as chaves de uma rodada anterior, porque as
    outras skills usam a chave como nome de arquivo (pdf/<chave>.pdf)."""
    antigas: dict[str, str] = {}
    for a in anteriores or []:
        if a.get("chave"):
            for i in _ids_do_registro(a):
                antigas.setdefault(i, a["chave"])
    usadas: set[str] = set()
    reaproveitadas = 0
    pendentes = []
    for r in registros:
        chave = next((antigas[i] for i in _ids_do_registro(r) if i in antigas), None)
        if chave and chave not in usadas:
            r["chave"] = chave
            usadas.add(chave)
            reaproveitadas += 1
        else:
            pendentes.append(r)
    reservadas = set(antigas.values())
    pendentes.sort(key=lambda r: (base_da_chave(r), int(r["pmid"]) if r.get("pmid") else 10 ** 12,
                                  r.get("doi") or "", r.get("titulo") or ""))
    for r in pendentes:
        base = base_da_chave(r)
        chave, n = base, 1
        while chave in usadas or chave in reservadas:
            n += 1
            sufixo = ""
            k = n - 1
            while k > 0:  # b, c, ..., z, ba, bb...
                sufixo = chr(ord("a") + k % 26) + sufixo
                k //= 26
            chave = base + sufixo
        r["chave"] = chave
        usadas.add(chave)
    return reaproveitadas


# --------------------------------------------------------------------------- pontuação

def _fmt(numero: float) -> str:
    return f"{numero:.1f}".replace(".", ",")


def pontuar(reg: dict, recorte: str, hoje: date, conceitos: dict | None, issns_destaque: dict) -> None:
    cfg = PESOS[recorte]
    tetos = cfg["tetos"]
    motivos, total = [], 0.0

    fator = cfg["desenho"].get(reg["desenho"], 0.15)
    pts = tetos["desenho"] * fator
    total += pts
    motivos.append(f"Desenho: {reg['desenho']} (+{_fmt(pts)} de {tetos['desenho']})")

    idade = None
    if reg.get("ano"):
        idade = max(0, hoje.year - int(reg["ano"]))
        if idade <= cfg["idade_cheia"]:
            f = 1.0
        elif idade >= cfg["idade_zero"]:
            f = 0.0
        else:
            f = 1 - (idade - cfg["idade_cheia"]) / (cfg["idade_zero"] - cfg["idade_cheia"])
        pts = tetos["atualidade"] * f
        total += pts
        motivos.append(f"Atualidade: {reg['ano']}, {idade} ano(s) (+{_fmt(pts)} de {tetos['atualidade']})")
    else:
        motivos.append(f"Atualidade: ano desconhecido (+0 de {tetos['atualidade']})")

    cit = reg.get("citacoes")
    if cit is None:
        pts = tetos["citacoes"] * 0.3
        motivos.append(f"Citações: sem dado; valor neutro (+{_fmt(pts)} de {tetos['citacoes']})")
    else:
        anos = max(1, idade if idade is not None else 1)
        por_ano = cit / anos
        reg["citacoes_por_ano"] = round(por_ano, 1)
        f = min(1.0, math.log1p(por_ano) / math.log1p(25))
        if idade is not None and idade <= 1:
            f = max(f, 0.4)  # recente demais para ter acumulado citações: não penalizar
        pts = tetos["citacoes"] * f
        motivos.append(f"Citações: {cit} ({_fmt(por_ano)}/ano, {reg.get('citacoes_fonte') or '-'}) "
                       f"(+{_fmt(pts)} de {tetos['citacoes']})")
    total += pts

    alvo = next((issns_destaque[i] for i in reg.get("issn") or [] if i in issns_destaque), None)
    if alvo:
        total += tetos["revista"]
        motivos.append(f"Revista-alvo: {alvo} (+{tetos['revista']})")

    if reg.get("sentinela"):
        total += tetos["sentinela"]
        motivos.append(f"Artigo-sentinela (+{tetos['sentinela']})")
    elif reg.get("origem_citacao"):
        sentinelas = {o["sentinela"] for o in reg["origem_citacao"]}
        pts = tetos["sentinela"] * (0.7 if len(sentinelas) >= 2 else 0.4)
        total += pts
        motivos.append(f"Ligado por citação a {len(sentinelas)} sentinela(s) (+{_fmt(pts)} de {tetos['sentinela']})")

    if conceitos:
        blocos = conceitos["blocos"]
        soma, no_titulo, no_resumo = 0.0, 0, 0
        for b in blocos:
            if bloco_casa_texto(b, reg.get("titulo") or ""):
                soma += 1
                no_titulo += 1
            elif bloco_casa_texto(b, reg.get("resumo") or "", reg.get("mesh")):
                soma += 0.5
                no_resumo += 1
        pts = tetos["aderencia"] * soma / len(blocos)
        total += pts
        motivos.append(f"Aderência ao tema: {no_titulo} de {len(blocos)} blocos no título, {no_resumo} só no "
                       f"resumo/MeSH (+{_fmt(pts)} de {tetos['aderencia']})")

    if reg.get("retratado"):
        total = 0.0
        motivos.insert(0, "RETRATADO: não usar (pontuação zerada)")
    reg["pontuacao"] = round(total, 1)
    reg["motivos_pontuacao"] = motivos


# --------------------------------------------------------------------------- planilha de triagem

def ler_planilha_anterior(caminho: Path) -> tuple[dict, dict, list[dict]]:
    """Devolve (decisões por chave, estado aplicado pelo script por chave, decisões guardadas de artigos que
    já tinham saído da busca)."""
    from openpyxl import load_workbook
    wb = load_workbook(caminho)
    if "Triagem" not in wb.sheetnames:
        raise ValueError("a planilha existente não tem a aba 'Triagem'")
    ws = wb["Triagem"]
    titulos = {str(c.value).strip(): i for i, c in enumerate(ws[1]) if c.value}
    nome_campo = {titulo: campo for campo, titulo, _ in COLUNAS}
    indice = {nome_campo[t]: i for t, i in titulos.items() if t in nome_campo}
    if "chave" not in indice:
        raise ValueError("a aba 'Triagem' não tem a coluna 'Chave'")
    decisoes = {}
    for linha in ws.iter_rows(min_row=2, values_only=True):
        chave = linha[indice["chave"]]
        if not chave:
            continue
        d = {campo: (str(linha[indice[campo]]).strip() if campo in indice and linha[indice[campo]] is not None
                     else "") for campo in CAMPOS_DECISAO}
        d["decisao"] = d["decisao"].lower()
        d["_linha"] = {campo: linha[i] for campo, i in indice.items()}
        decisoes[str(chave).strip()] = d
    estado = {}
    if "_estado" in wb.sheetnames:
        for linha in wb["_estado"].iter_rows(min_row=2, values_only=True):
            if linha and linha[0]:
                estado[str(linha[0])] = {c: (linha[i + 1] or "") for i, c in enumerate(CAMPOS_DECISAO)}
    fora_antigas = []
    if "Fora da busca atual" in wb.sheetnames:
        ws2 = wb["Fora da busca atual"]
        cab = [nome_campo.get(str(c.value).strip(), str(c.value)) if c.value else "" for c in ws2[1]]
        for linha in ws2.iter_rows(min_row=2, values_only=True):
            if not linha or not linha[0]:
                continue
            bruta = dict(zip(cab, linha))
            d = {campo: (str(bruta.get(campo)).strip() if bruta.get(campo) is not None else "")
                 for campo in CAMPOS_DECISAO}
            d["chave"] = str(linha[0]).strip()
            d["_linha"] = bruta
            fora_antigas.append(d)
    return decisoes, estado, fora_antigas


def combinar_decisoes(registros: list[dict], planilha: dict, estado: dict, sugeridas: dict,
                      sobrescrever: bool) -> tuple[dict, dict, dict]:
    """Regra: o que o usuário digitou na planilha vale. Uma celula conta como 'do usuário' quando difere do
    que o script aplicou por último (aba oculta _estado). decisoes.json só preenche o que não é do usuário."""
    final, novo_estado = {}, {}
    conta = {"da_planilha": 0, "do_json": 0, "preservadas_do_usuario": 0}
    for r in registros:
        chave = r["chave"]
        atual = planilha.get(chave) or {c: "" for c in CAMPOS_DECISAO}
        aplicado = estado.get(chave) or {c: "" for c in CAMPOS_DECISAO}
        sug = sugeridas.get(chave)
        do_usuario = any((atual.get(c) or "") != (aplicado.get(c) or "") for c in CAMPOS_DECISAO)
        tem_algo = any(atual.get(c) for c in CAMPOS_DECISAO)
        if sug and (sobrescrever or not do_usuario):
            final[chave] = {c: (sug.get(c) or "") for c in CAMPOS_DECISAO}
            novo_estado[chave] = dict(final[chave])
            conta["do_json"] += 1
        else:
            final[chave] = {c: (atual.get(c) or "") for c in CAMPOS_DECISAO}
            if tem_algo:
                conta["da_planilha"] += 1
                if do_usuario:
                    conta["preservadas_do_usuario"] += 1
                elif chave in estado:
                    novo_estado[chave] = dict(aplicado)
    return final, novo_estado, conta


def carregar_decisoes_json(caminho: Path) -> dict:
    dados = ler_json(caminho)
    if dados is None:
        sair(f"arquivo de decisões não encontrado: {caminho}")
    if isinstance(dados, dict):
        dados = dados.get("decisoes") or [dict(v, chave=k) for k, v in dados.items() if isinstance(v, dict)]
    saida = {}
    for d in dados:
        if not isinstance(d, dict) or not d.get("chave"):
            continue
        decisao = str(d.get("decisao") or "").strip().lower()
        if decisao and decisao not in DECISOES:
            print(f"  aviso: decisão '{decisao}' inválida para {d['chave']} (use incluir, excluir ou talvez); ignorei.")
            continue
        saida[str(d["chave"])] = {"decisao": decisao, "motivo": str(d.get("motivo") or "").strip(),
                                  "papel": str(d.get("papel") or d.get("papel_na_aula") or "").strip(),
                                  "observacoes": str(d.get("observacoes") or "").strip()}
    return saida


def gravar_planilha(caminho: Path, registros: list[dict], decisoes: dict, estado: dict, fluxo: dict,
                    fora: list[dict], conceitos: dict | None, recorte: str) -> None:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    marinho, claro, borda_txt = "202081", "F7F9FA", "141A1A"
    wb = Workbook()
    ws = wb.active
    ws.title = "Triagem"
    cab_fonte = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
    cab_fundo = PatternFill("solid", fgColor=marinho)
    editavel = PatternFill("solid", fgColor="EAF6FA")
    for j, (_, titulo, largura) in enumerate(COLUNAS, 1):
        c = ws.cell(row=1, column=j, value=titulo)
        c.font, c.fill = cab_fonte, cab_fundo
        c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = largura
    ws.row_dimensions[1].height = 30
    col = {campo: j for j, (campo, _, _) in enumerate(COLUNAS, 1)}
    link = Font(color="007A99", underline="single")
    for i, r in enumerate(registros, 2):
        d = decisoes.get(r["chave"], {})
        valores = {
            "chave": r["chave"], "decisao": d.get("decisao") or None, "motivo": d.get("motivo") or None,
            "papel": d.get("papel") or None, "observacoes": d.get("observacoes") or None,
            "pontuacao": r["pontuacao"], "desenho": r["desenho"], "ano": r.get("ano"),
            "primeiro_autor": r.get("primeiro_autor"), "titulo": r.get("titulo"), "revista": r.get("revista"),
            "citacoes": r.get("citacoes"), "cit_ano": r.get("citacoes_por_ano"),
            "acesso_aberto": {True: "sim", False: "não"}.get(r.get("acesso_aberto"), "?"),
            "fontes": ", ".join(r.get("fontes") or []), "sentinela": "sim" if r.get("sentinela") else None,
            "doi": r.get("doi"), "pmid": r.get("pmid"),
            "motivos": " | ".join(r.get("motivos_pontuacao") or []) + f" || Desenho: {r.get('desenho_motivo', '')}",
            "resumo": (r.get("resumo") or "")[:32000],
        }
        for campo, valor in valores.items():
            c = ws.cell(row=i, column=col[campo], value=valor)
            c.alignment = Alignment(vertical="top", wrap_text=campo in ("titulo", "observacoes", "motivo", "papel"))
            if campo in CAMPOS_DECISAO:
                c.fill = editavel
        if r.get("doi"):
            c = ws.cell(row=i, column=col["doi"])
            c.hyperlink, c.font = f"https://doi.org/{r['doi']}", link
        if r.get("pmid"):
            c = ws.cell(row=i, column=col["pmid"])
            c.hyperlink, c.font = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/", link
    ultima = max(2, len(registros) + 1)
    ws.freeze_panes = "F2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS))}{ultima}"

    listas = wb.create_sheet("Listas")
    for j, (titulo, itens) in enumerate((("Decisão", DECISOES), ("Motivo da exclusão", MOTIVOS),
                                         ("Papel na aula", PAPEIS)), 1):
        listas.cell(row=1, column=j, value=titulo).font = Font(bold=True)
        for k, item in enumerate(itens, 2):
            listas.cell(row=k, column=j, value=item)
        listas.column_dimensions[get_column_letter(j)].width = 34
    for campo, coluna_lista, itens, estrito in (("decisao", "A", DECISOES, True), ("motivo", "B", MOTIVOS, False),
                                                ("papel", "C", PAPEIS, False)):
        dv = DataValidation(type="list", formula1=f"=Listas!${coluna_lista}$2:${coluna_lista}${len(itens) + 1}",
                            allow_blank=True, showErrorMessage=estrito)
        dv.error, dv.errorTitle = "Use incluir, excluir ou talvez.", "Decisão inválida"
        letra = get_column_letter(col[campo])
        dv.add(f"{letra}2:{letra}{max(ultima, 2000)}")
        ws.add_data_validation(dv)
    faixa = f"A2:{get_column_letter(len(COLUNAS))}{max(ultima, 2000)}"
    letra_dec = get_column_letter(col["decisao"])
    for valor, cor in (("incluir", "DDF3E4"), ("excluir", "E6E6E6"), ("talvez", "FFF3CC")):
        ws.conditional_formatting.add(faixa, FormulaRule(formula=[f'${letra_dec}2="{valor}"'],
                                                         fill=PatternFill("solid", bgColor=cor, fgColor=cor)))

    # ---- aba Fluxo (números tipo PRISMA; a parte de triagem é fórmula, atualiza sozinha)
    fx = wb.create_sheet("Fluxo")
    fx.column_dimensions["A"].width = 58
    fx.column_dimensions["B"].width = 14
    fx.column_dimensions["C"].width = 70
    negrito = Font(bold=True)
    linhas_fx: list[tuple] = [("Fluxo da busca (modelo PRISMA 2020, adaptado)", None, None, "titulo"),
                              (f"Tema: {(conceitos or {}).get('tema', '')}", None, None, None),
                              (f"Recorte: {recorte} | consolidado em {fluxo['data'][:10]}", None, None, None),
                              ("", None, None, None),
                              ("IDENTIFICAÇÃO", None, None, "secao")]
    nomes = {"pubmed": "PubMed", "crossref": "Crossref (JOSPT e revistas-alvo)", "scopus": "Scopus (exportação manual)",
             "openalex": "OpenAlex (perseguição de citações)"}
    for fonte in PRIORIDADE_FONTE:
        if fonte in fluxo["por_fonte"]:
            linhas_fx.append((f"Registros identificados: {nomes[fonte]}", fluxo["por_fonte"][fonte],
                              fluxo["notas_fonte"].get(fonte, ""), None))
    linhas_fx += [("Total identificado", fluxo["identificados"], "", "negrito"),
                  ("Duplicatas removidas", fluxo["duplicatas"], "DOI, PMID, EID, título + ano (tolerância de 1 ano)", None),
                  ("", None, None, None), ("TRIAGEM (título e resumo)", None, None, "secao"),
                  ("Registros únicos para triagem", fluxo["unicos"], "", "negrito")]
    L = letra_dec
    M = get_column_letter(col["motivo"])
    G = get_column_letter(col["desenho"])
    linhas_fx += [("Triados (com decisão)", f'=COUNTIF(Triagem!{L}:{L},"incluir")+COUNTIF(Triagem!{L}:{L},"excluir")'
                                           f'+COUNTIF(Triagem!{L}:{L},"talvez")', "", None),
                  ("Ainda sem decisão", f'={fluxo["unicos"]}-COUNTIF(Triagem!{L}:{L},"incluir")'
                                        f'-COUNTIF(Triagem!{L}:{L},"excluir")-COUNTIF(Triagem!{L}:{L},"talvez")', "", None),
                  ("Excluídos", f'=COUNTIF(Triagem!{L}:{L},"excluir")', "", "negrito")]
    for motivo in MOTIVOS:
        linhas_fx.append((f"    excluídos por: {motivo}",
                          f'=COUNTIFS(Triagem!{L}:{L},"excluir",Triagem!{M}:{M},"{motivo}")', "", None))
    linhas_fx += [("Talvez (decidir no texto completo)", f'=COUNTIF(Triagem!{L}:{L},"talvez")', "", None),
                  ("", None, None, None), ("INCLUSÃO", None, None, "secao"),
                  ("Incluídos na aula", f'=COUNTIF(Triagem!{L}:{L},"incluir")', "", "negrito")]
    for desenho in DESENHOS:
        linhas_fx.append((f"    incluídos: {desenho}",
                          f'=COUNTIFS(Triagem!{L}:{L},"incluir",Triagem!{G}:{G},"{desenho}")',
                          f"{fluxo['por_desenho'].get(desenho, 0)} entre os registros únicos", None))
    for i, (rotulo, valor, nota, estilo) in enumerate(linhas_fx, 1):
        a = fx.cell(row=i, column=1, value=rotulo)
        if valor is not None:
            fx.cell(row=i, column=2, value=valor)
        if nota:
            fx.cell(row=i, column=3, value=nota).font = Font(color="5A5F63", italic=True)
        if estilo == "titulo":
            a.font = Font(bold=True, size=14, color=marinho)
        elif estilo == "secao":
            a.font, a.fill = cab_fonte, cab_fundo
            fx.cell(row=i, column=2).fill = cab_fundo
            fx.cell(row=i, column=3).fill = cab_fundo
        elif estilo == "negrito":
            a.font = negrito
            fx.cell(row=i, column=2).font = negrito

    # ---- aba Leia-me
    lm = wb.create_sheet("Leia-me")
    lm.column_dimensions["A"].width = 120
    tetos = PESOS[recorte]["tetos"]
    texto = [
        ("Como usar esta planilha", "titulo"),
        ("1. Preencha só as colunas azuis da aba Triagem: Decisão, Motivo da exclusão, Papel na aula e Observações.", None),
        ("2. Decisão aceita três valores: incluir, excluir, talvez. 'Talvez' significa decidir depois de ler o texto completo.", None),
        ("3. Para quem foi excluído, escolha o motivo na lista (pode escrever outro). A aba Fluxo conta sozinha.", None),
        ("4. Para quem foi incluído, diga o papel na aula: é isso que vai para selecionados.json e orienta os slides.", None),
        ("5. A planilha vem ordenada por pontuação. Pontuação alta é prioridade de leitura, não certificado de qualidade.", None),
        ("6. Rodar consolidar.py de novo NÃO apaga o que você preencheu: as decisões são relidas pela coluna Chave.", None),
        ("   Feche o arquivo antes de rodar o script. Uma cópia da versão anterior fica em triagem.anterior.xlsx.", None),
        ("", None),
        (f"Como a pontuação é calculada (recorte: {recorte}; máximo 100)", "titulo"),
        (f"Desenho do estudo: até {tetos['desenho']} pontos, conforme a hierarquia de evidência do recorte.", None),
        (f"Atualidade: até {tetos['atualidade']} pontos; cheia até {PESOS[recorte]['idade_cheia']} ano(s), zero a partir de "
         f"{PESOS[recorte]['idade_zero']} anos.", None),
        (f"Citações por ano: até {tetos['citacoes']} pontos, em escala logarítmica (25 citações/ano já dá o teto).", None),
        (f"Revista-alvo: {tetos['revista']} pontos se a revista estiver na lista de revistas-alvo da aula.", None),
        (f"Sentinela: {tetos['sentinela']} pontos para artigo-sentinela; parte disso para quem cita ou é citado por sentinela.", None),
        (f"Aderência ao tema: até {tetos['aderencia']} pontos, pela presença dos blocos de conceito no título e no resumo.", None),
        ("A coluna 'Por que esta pontuação' mostra a conta de cada artigo.", None),
        ("", None),
        ("Limites que você precisa conhecer", "titulo"),
        ("O desenho é inferido de metadados (tipo de publicação, MeSH, título, resumo). Erra em casos limítrofes: confira no resumo.", None),
        ("Citações vêm do OpenAlex (ou Scopus/Crossref, na falta). Artigo recente tem poucas citações por definição.", None),
        ("'Acesso aberto: ?' significa que o OpenAlex não foi consultado ou não conhece o artigo.", None),
    ]
    for i, (linha, estilo) in enumerate(texto, 1):
        c = lm.cell(row=i, column=1, value=linha)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if estilo == "titulo":
            c.font = Font(bold=True, size=13, color=marinho)

    # ---- decisões de registros que saíram da busca (nada se perde)
    if fora:
        fb = wb.create_sheet("Fora da busca atual")
        campos = ["chave", "decisao", "motivo", "papel", "observacoes", "primeiro_autor", "ano", "titulo", "doi", "pmid"]
        nomes_col = {campo: titulo for campo, titulo, _ in COLUNAS}
        for j, campo in enumerate(campos, 1):
            c = fb.cell(row=1, column=j, value=nomes_col[campo])
            c.font, c.fill = cab_fonte, cab_fundo
            fb.column_dimensions[get_column_letter(j)].width = 22
        for i, d in enumerate(fora, 2):
            for j, campo in enumerate(campos, 1):
                fb.cell(row=i, column=j, value=d.get(campo) if campo in CAMPOS_DECISAO or campo == "chave"
                        else d.get("_linha", {}).get(campo))

    # ---- estado (o que o script aplicou a partir de decisoes.json), para reconhecer edições do usuário
    es = wb.create_sheet("_estado")
    es.append(["chave", *CAMPOS_DECISAO])
    for chave, d in estado.items():
        es.append([chave, *[d.get(c) or "" for c in CAMPOS_DECISAO]])
    es.sheet_state = "hidden"
    listas.sheet_state = "hidden"
    wb.properties.creator = "Boost Education - boost-pesquisa-artigos"
    wb.save(caminho)


def gravar_lote_md(caminho: Path, registros: list[dict], decisoes: dict, tamanho: int) -> int:
    """Escreve em Markdown os próximos registros sem decisão (maior pontuação primeiro), com resumo, para a
    triagem de titulo/resumo ser feita por leitura e devolvida em decisoes.json."""
    pendentes = [r for r in registros if not (decisoes.get(r["chave"]) or {}).get("decisao")][:tamanho]
    L = [f"# Lote de triagem ({len(pendentes)} registros sem decisão, por ordem de pontuação)", "",
         "Decida cada um por título e resumo e registre em `decisoes.json`: "
         "`{\"chave\": ..., \"decisao\": \"incluir|excluir|talvez\", \"motivo\": ..., \"papel\": ..., "
         "\"observações\": ...}`.", ""]
    for r in pendentes:
        ident = " | ".join(x for x in (f"PMID {r['pmid']}" if r.get("pmid") else "", f"DOI {r['doi']}" if r.get("doi") else "") if x)
        L += [f"## {r['chave']} | {r['desenho']} | {r['pontuacao']} pts" + (" | SENTINELA" if r.get("sentinela") else ""),
              f"**{r.get('titulo')}**", "",
              f"{', '.join((r.get('autores') or [])[:3])}{' et al.' if len(r.get('autores') or []) > 3 else ''} "
              f"{r.get('revista') or ''}. {r.get('ano') or ''}. {ident}",
              f"Desenho inferido por: {r.get('desenho_motivo', '')}. Citações: {r.get('citacoes')}. "
              f"Acesso aberto: {({True: 'sim', False: 'não'}).get(r.get('acesso_aberto'), '?')}.", "",
              (r.get("resumo") or "_(sem resumo nas fontes; decidir pelo título ou marcar 'talvez')_"), ""]
    caminho.write_text("\n".join(L), encoding="utf-8")
    return len(pendentes)


# --------------------------------------------------------------------------- principal

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Consolida as fontes: deduplica, classifica o desenho, gera a chave SobrenomeAno, pontua e "
                    "grava registros.json e triagem.xlsx (preservando decisões já preenchidas).")
    ap.add_argument("--pasta", required=True, help="pasta 01_busca da aula (com brutos/ e conceitos.json)")
    ap.add_argument("--recorte", choices=RECORTES, help="sobrepõe o recorte de conceitos.json")
    ap.add_argument("--hoje", help="data de referência AAAA-MM-DD para a atualidade (padrão: hoje)")
    ap.add_argument("--tolerancia-ano", type=int, default=1,
                    help="diferença de ano aceita ao deduplicar por título (padrão 1: online first x fascículo)")
    ap.add_argument("--decisoes", help="decisoes.json com a triagem proposta: lista de {chave, decisao, motivo, "
                                       "papel, observacoes}. Só preenche o que o usuário não editou na planilha")
    ap.add_argument("--sobrescrever-decisoes", action="store_true",
                    help="faz decisoes.json valer também sobre o que o usuário editou (use com cuidado)")
    ap.add_argument("--lote", type=int, default=0, metavar="N",
                    help="grava triagem_lote.md com os N registros de maior pontuação ainda sem decisão "
                         "(título, desenho, resumo), para a triagem por leitura")
    ap.add_argument("--sem-planilha", action="store_true", help="grava só os JSON")
    ap.add_argument("--forcar", action="store_true",
                    help="recria triagem.xlsx mesmo sem conseguir ler a anterior (as decisões antigas se perdem)")
    args = ap.parse_args(argv)

    pasta = Path(args.pasta).resolve()
    if not (pasta / "brutos").is_dir():
        sair(f"não achei {pasta / 'brutos'}. Rode as buscas antes (pubmed_busca.py, crossref_busca.py...).")
    conceitos = carregar_conceitos(pasta / "conceitos.json") if (pasta / "conceitos.json").exists() else None
    recorte = args.recorte or (conceitos["recorte"] if conceitos else "topo_mecanismos")
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()

    brutos, por_fonte, enriquecimento = carregar_fontes(pasta)
    if not brutos:
        sair("nenhum registro em brutos/*.json. Rode as buscas antes de consolidar.")

    grupos, criterios = deduplicar(brutos, args.tolerancia_ano)
    registros = [fundir(g, c) for g, c in zip(grupos, criterios)]
    pares = list(zip(registros, grupos))  # os dicionários são os mesmos: a chave final aparece na auditoria
    por_doi = {e["doi"]: e for e in enriquecimento if e.get("doi")}
    por_pmid = {str(e["pmid"]): e for e in enriquecimento if e.get("pmid")}

    sent_pmids = {s["pmid"] for s in (conceitos or {}).get("sentinelas", []) if s["pmid"]}
    sent_dois = {s["doi"] for s in (conceitos or {}).get("sentinelas", []) if s["doi"]}
    destaque = {i: JOSPT["nome"] for i in JOSPT["issn"]}
    for r in (conceitos or {}).get("revistas_alvo", []):
        for i in r["issn"]:
            destaque[i] = r["nome"] or i

    for r in registros:
        enriquecer(r, por_doi, por_pmid)
        r["sentinela"] = bool((r["pmid"] and r["pmid"] in sent_pmids) or (r["doi"] and r["doi"] in sent_dois))
        try:
            r["desenho"], r["desenho_motivo"] = classificar(r)
        except Exception as exc:  # noqa: BLE001 - um registro estranho não pode parar o lote
            r["desenho"], r["desenho_motivo"] = "Outro", f"falha ao classificar: {type(exc).__name__}"
        pontuar(r, recorte, hoje, conceitos, destaque)

    anteriores = ler_json(pasta / "registros.json", [])
    reaproveitadas = atribuir_chaves(registros, anteriores if isinstance(anteriores, list) else [])
    registros.sort(key=lambda r: (-r["pontuacao"], -(r.get("ano") or 0), r["chave"]))

    por_desenho = Counter(r["desenho"] for r in registros)
    notas_fonte = {}
    pubmed = ler_json(pasta / "brutos" / "pubmed.json") or {}
    cortes = [e for e in pubmed.get("execucoes", []) if e.get("total", 0) > e.get("baixados", 0) > 0]
    if cortes:
        notas_fonte["pubmed"] = "; ".join(f"variante {e['variante']}: {e['baixados']} baixados de {e['total']}"
                                          for e in cortes[-3:])
    fluxo = {"data": agora_iso(), "recorte": recorte, "por_fonte": por_fonte, "notas_fonte": notas_fonte,
             "identificados": len(brutos), "duplicatas": len(brutos) - len(registros), "unicos": len(registros),
             "por_desenho": {d: por_desenho.get(d, 0) for d in DESENHOS},
             "sentinelas_presentes": sum(1 for r in registros if r["sentinela"]),
             "sentinelas_esperados": len((conceitos or {}).get("sentinelas", []))}

    auditoria = [{"chave": r["chave"], "criterios": r["criterios_dedup"], "fontes": r["fontes"],
                  "titulos": sorted({x["titulo"] for x in g}),
                  "anos": sorted({x.get("ano") for x in g if x.get("ano")}),
                  "dois": sorted({x["doi"] for x in g if x.get("doi")}),
                  "pmids": sorted({x["pmid"] for x in g if x.get("pmid")})}
                 for r, g in pares if len(g) > 1]

    gravar_json(pasta / "registros.json", registros)
    gravar_json(pasta / "duplicatas.json", auditoria)
    gravar_json(pasta / "fluxo.json", fluxo)

    print(f"=== Consolidação | recorte '{recorte}' | referência {hoje.isoformat()} ===")
    print("Identificados: " + " + ".join(f"{n} {f}" for f, n in por_fonte.items()) + f" = {len(brutos)}")
    print(f"Duplicatas removidas: {fluxo['duplicatas']} | registros únicos: {len(registros)}")
    print(f"Chaves reaproveitadas da rodada anterior: {reaproveitadas} | novas: {len(registros) - reaproveitadas}")
    print("Por desenho: " + "; ".join(f"{d}: {n}" for d, n in por_desenho.most_common()))
    faltam = [s for s in (conceitos or {}).get("sentinelas", [])
              if not any((s["pmid"] and r["pmid"] == s["pmid"]) or (s["doi"] and r["doi"] == s["doi"]) for r in registros)]
    if conceitos and conceitos["sentinelas"]:
        print(f"Sentinelas presentes: {fluxo['sentinelas_presentes']} de {fluxo['sentinelas_esperados']}")
    for s in faltam:
        print(f"  ATENÇÃO: sentinela ausente dos registros: {s['pmid'] or s['doi']} {s['nota']}. "
              f"Rode teste_sentinela.py; para só acrescenta-lo: pubmed_busca.py --pmids {s['pmid'] or '<pmid>'}.")
    retratados = [r["chave"] for r in registros if r.get("retratado")]
    if retratados:
        print(f"  ATENÇÃO: {len(retratados)} artigo(s) retratado(s), pontuação zerada: {', '.join(retratados)}")
    print("\nTopo da lista:")
    for r in registros[:10]:
        print(f"  {str(r['pontuacao']).rjust(5)}  {r['chave'].ljust(20)} {r['desenho'][:22].ljust(22)} "
              f"{(r['titulo'] or '')[:70]}")
    print(f"\nGravado: {pasta / 'registros.json'}")
    print(f"Gravado: {pasta / 'duplicatas.json'} ({len(auditoria)} grupos fundidos, para auditoria)")
    print(f"Gravado: {pasta / 'fluxo.json'}")

    if args.sem_planilha:
        return 0
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("AVISO: openpyxl não está instalado; triagem.xlsx não foi gerada (pip install openpyxl).")
        return 1

    destino = pasta / "triagem.xlsx"
    planilha, estado, fora, fora_antigas = {}, {}, [], []
    if destino.exists():
        try:
            planilha, estado, fora_antigas = ler_planilha_anterior(destino)
        except Exception as exc:  # noqa: BLE001
            if not args.forcar:
                sair(f"não consegui ler a triagem.xlsx existente ({type(exc).__name__}: {exc}). Para não perder "
                     f"decisões, NÃO sobrescrevi. Feche o arquivo no Excel e rode de novo; se ele estiver "
                     f"corrompido, use --forcar.", 1)
            print(f"AVISO: triagem.xlsx anterior ilegível ({exc}); recriando por causa de --forcar.")
        else:
            shutil.copy2(destino, pasta / "triagem.anterior.xlsx")
    sugeridas = carregar_decisoes_json(Path(args.decisoes)) if args.decisoes else {}
    desconhecidas = [c for c in sugeridas if c not in {r["chave"] for r in registros}]
    if desconhecidas:
        print(f"  aviso: decisoes.json cita {len(desconhecidas)} chave(s) que não existem nos registros: "
              f"{', '.join(desconhecidas[:8])}")
    chaves_atuais = {r["chave"] for r in registros}
    for d in fora_antigas:  # artigo que tinha saído da busca: se voltou, a decisão volta junto
        if d["chave"] in chaves_atuais and not any((planilha.get(d["chave"]) or {}).get(c) for c in CAMPOS_DECISAO):
            planilha[d["chave"]] = d
        elif d["chave"] not in chaves_atuais:
            fora.append(d)
    for chave, d in planilha.items():
        if chave not in chaves_atuais and any(d.get(c) for c in CAMPOS_DECISAO):
            fora.append({**d, "chave": chave})
    decisoes, novo_estado, conta = combinar_decisoes(registros, planilha, estado, sugeridas,
                                                     args.sobrescrever_decisoes)
    try:
        gravar_planilha(destino, registros, decisoes, novo_estado, fluxo, fora, conceitos, recorte)
    except PermissionError:
        sair(f"não consegui gravar {destino}: o arquivo está aberto em outro programa. Feche e rode de novo.", 1)
    preenchidas = sum(1 for d in decisoes.values() if d.get("decisao"))
    print(f"Gravado: {destino} ({len(registros)} linhas; {preenchidas} com decisão)")
    if planilha:
        print(f"  decisões relidas da planilha anterior: {conta['da_planilha']} "
              f"(editadas pelo usuário: {conta['preservadas_do_usuario']}); cópia em triagem.anterior.xlsx")
    if sugeridas:
        print(f"  decisões aplicadas a partir de {Path(args.decisoes).name}: {conta['do_json']}")
    if fora:
        print(f"  {len(fora)} decisão(ões) de artigos que saíram da busca foram guardadas na aba 'Fora da busca atual'")
    if args.lote:
        n = gravar_lote_md(pasta / "triagem_lote.md", registros, decisoes, args.lote)
        print(f"Gravado: {pasta / 'triagem_lote.md'} ({n} registros sem decisão, para triagem por leitura)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
