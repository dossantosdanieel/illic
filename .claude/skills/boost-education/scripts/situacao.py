#!/usr/bin/env python3
"""Diz em que etapa está uma aula Boost e qual o próximo passo, lendo só a pasta da aula.

Serve para retomar o trabalho em outra sessão: cada sessão começa do zero, e a pasta é a memória.
Também marca os pontos de checagem e o modo em 00_andamento.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402

ETAPAS = {
    0: "Briefing",
    1: "Busca",
    2: "Seleção dos artigos",
    3: "Artigos: download e leitura",
    4: "Figuras",
    5: "Roteiro",
    6: "Deck e materiais",
    7: "Entrega",
}

LICENCAS_LIVRES = {"cc-by", "cc0", "dominio publico", "domínio público"}
PLACEHOLDER = re.compile(r"<[A-Za-zÀ-ÿ][^<>\n]{2,90}>")


@dataclass
class Passo:
    ordem: float            # etapa + posição dentro dela
    chave: str
    texto: str
    estado: str             # ok | fazer | usuario | aviso
    comando: str | None = None
    detalhe: str | None = None
    bloqueia_de: float | None = None   # para 'usuario': a partir de que ordem o trabalho para

    @property
    def etapa(self) -> int:
        return int(self.ordem)


@dataclass
class Situacao:
    pasta: str
    tema: str
    modo: str
    checagens: dict
    passos: list[Passo] = field(default_factory=list)
    resumo: dict = field(default_factory=dict)
    compartilhado: dict = field(default_factory=dict)


def mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def mais_velho(arq: Path, *fontes: Path) -> bool:
    """True se arq não existe ou é mais antigo que alguma fonte existente (folga de 2 s)."""
    if not arq.exists():
        return True
    t = mtime(arq)
    return any(f.exists() and mtime(f) > t + 2 for f in fontes)


def tema_de(pasta: Path) -> str:
    brief = pasta / "00_briefing.md"
    if brief.exists():
        texto = brief.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#(?!#)\s*(?:Briefing\s*[·:-]\s*)?(.+)$", texto, re.M)
        if m:
            tema = m.group(1).strip()
            # briefing escrito à mão: "# Briefing · Aula 3 da trilha" seguido do tema real em negrito
            seg = re.match(r"\s*\*\*([^*\n]{8,200})\*\*\s*$", texto[m.end():].lstrip("\n").split("\n", 1)[0])
            if seg and seg.group(1).strip().lower() not in tema.lower():
                tema = f"{tema} · {seg.group(1).strip()}"
            return tema
    return pasta.name


def execucoes_pubmed(pub: Path) -> tuple[int, list[dict]]:
    """(nº de registros, execuções) de brutos/pubmed.json."""
    d = C.ler_json(pub, {})
    if not isinstance(d, dict) or "__erro__" in d:
        return 0, []
    return len(d.get("registros") or []), [e for e in d.get("execucoes") or [] if isinstance(e, dict)]


def pubmed_desatualizado(conceitos: Path, strings: Path, pub: Path) -> bool:
    """A busca rodada no PubMed difere da string atual? Compara a consulta gravada com strings.json;
    sem como comparar (variantes de outro formato, arquivo antigo), cai na data de modificação."""
    _, execs = execucoes_pubmed(pub)
    atuais = (C.ler_json(strings, {}) or {}).get("pubmed") if strings.exists() else None
    ultimas = {}
    for e in execs:
        if not e.get("so_contagem") and e.get("consulta"):
            ultimas[str(e.get("variante"))] = e["consulta"]
    if isinstance(atuais, dict) and not mais_velho(strings, conceitos):
        comparaveis = {v: q for v, q in ultimas.items() if v in atuais}
        if comparaveis:
            return any(atuais[v] != q for v, q in comparaveis.items())
    return mtime(conceitos) > mtime(pub) + 2


def truncadas_pubmed(pub: Path) -> list[tuple[str, int, int]]:
    """Variantes cuja última execução baixou menos que o total (corte por --max)."""
    _, execs = execucoes_pubmed(pub)
    ult = {}
    for e in execs:
        if not e.get("so_contagem"):
            ult[str(e.get("variante"))] = e
    saida = []
    for v, e in ult.items():
        tot, baix = e.get("total") or 0, e.get("baixados") or 0
        if isinstance(tot, int) and isinstance(baix, int) and tot > (e.get("max") or 0) and baix < tot:
            saida.append((v, tot, baix))
    return saida


def pmids_manuais(*pubs: Path) -> set[str]:
    """PMIDs acrescentados à mão (pubmed_busca.py --pmids): execuções 'manual' e registros marcados 'manual'."""
    saida: set[str] = set()
    for pub in pubs:
        d = C.ler_json(pub, {}) if pub.exists() else {}
        if not isinstance(d, dict) or "__erro__" in d:
            continue
        for e in d.get("execucoes") or []:
            if isinstance(e, dict) and e.get("variante") == "manual" and str(e.get("consulta", "")).startswith("PMIDs:"):
                saida |= set(re.findall(r"\d+", str(e["consulta"])))
        for r in d.get("registros") or []:
            if isinstance(r, dict) and "manual" in (r.get("variantes") or []) and r.get("pmid"):
                saida.add(str(r["pmid"]))
    return saida


def ler_sentinelas(sj: Path, manuais: set[str] | None = None) -> tuple[int, int, list[str], list[str]]:
    """(recuperados pela string base, testáveis, acrescentados à mão por --pmids, perdidos de fato).

    Só conta como acrescentado o sentinela que entrou por --pmids (o caminho do passo 6 da pesquisa para sentinela
    mais amplo que a pergunta). Estar nos brutos porque outra variante ou outra base o trouxe não basta: a meta é
    100% na variante base."""
    manuais = manuais or set()
    d = C.ler_json(sj, {}) or {}
    if not isinstance(d, dict) or "__erro__" in d:
        return 0, 0, [], []
    base = (d.get("variantes") or {}).get("base") or {}
    rec_ids = {str(x) for x in base.get("recuperados") or []}
    rec = len(rec_ids) if base else (d.get("recuperados") or 0)
    tot = base.get("testaveis") or d.get("total") or 0
    acresc, perd = [], []
    for r in d.get("resultados") or []:
        if not isinstance(r, dict) or str(r.get("situacao", "")).lower() in ("ok", "recuperado") \
                or str(r.get("pmid")) in rec_ids or not r.get("pmid"):
            continue   # sem PMID: fora do PubMed, não conta nos testáveis da base
        nome = f"{r.get('primeiro_autor') or ''}{r.get('ano') or ''}".strip() or str(r.get("pmid") or r.get("doi"))
        (acresc if str(r.get("pmid")) in manuais else perd).append(nome)
    if not d.get("resultados") and rec < tot:
        perd = [f"{tot - rec} sem detalhe"]
    return rec, tot, acresc, perd


def analisar(pasta: Path, validar: bool = True) -> Situacao:
    pasta = Path(os.path.abspath(pasta.expanduser()))   # absoluto: os comandos impressos valem de qualquer pasta
    and_ = C.ler_andamento(pasta)
    sem_parar = and_["modo"] == "sem parar"
    S = Situacao(pasta=str(pasta), tema=tema_de(pasta), modo=and_["modo"], checagens=dict(and_["checagens"]))
    P = S.passos
    A = str(pasta)
    B = pasta / "01_busca"
    for grupo in ("01_busca", "02_artigos", "03_figuras"):
        if (pasta / grupo).is_symlink():
            S.compartilhado[grupo] = str((pasta / grupo).resolve())
    # Aula que usa a busca de outra (--compartilhar-de): as checagens 1 e 2 são da aula dona.
    dona = Path(S.compartilhado["01_busca"]).parent if "01_busca" in S.compartilhado else None
    and_dona = C.ler_andamento(dona) if dona else None
    dona_avancou = bool(dona) and ((dona / "04_aula" / "roteiro.md").exists() or (dona / "04_aula" / "deck.json").exists()
                                   or bool(and_dona["checagens"].get(3)))

    def add(ordem, chave, texto, estado, comando=None, detalhe=None, bloqueia_de=None):
        P.append(Passo(ordem, chave, texto, estado, comando, detalhe, bloqueia_de))

    def checagem(n: int, ordem: float, bloqueia_de: float, como: str):
        feito = and_["checagens"].get(n)
        alvo, onde = A, ""
        if n in (1, 2) and dona is not None:
            alvo, onde = str(dona), f" (na aula dona, {dona.name})"
            if not feito and and_dona["checagens"].get(n):
                feito = and_dona["checagens"][n] + onde
                S.checagens[n] = feito
        marcar = f"{C.cmd_proprio('situacao.py')} {alvo} --marcar {n} --nota"
        if feito:
            add(ordem, f"checagem{n}", f"Checagem {n}: {C.CHECAGENS[n]}", "ok",
                detalhe=feito.replace(C.CHECAGENS[n], "").strip(" —-") or None)
        elif sem_parar:
            add(ordem, f"checagem{n}", f"Checagem {n} pulada (modo sem parar)", "ok",
                detalhe="registre no fim o que o usuário precisa revisar")
        elif onde and dona_avancou:
            add(ordem, f"checagem{n}", f"Checagem {n} não registrada{onde}, mas a aula dona já passou dela", "aviso",
                comando=f"{marcar} \"aprovada antes (registro retroativo)\"",
                detalhe="busca e artigos são compartilhados: confirme com o usuário e registre na aula dona")
        else:
            add(ordem, f"checagem{n}", f"CHECAGEM {n}: {C.CHECAGENS[n]}", "usuario",
                comando=f"{marcar} \"...\"  (depois que o usuário aprovar)" + (f"  · registre{onde}" if onde else ""),
                detalhe=como, bloqueia_de=bloqueia_de)

    quebrados = [g for g in S.compartilhado if not (pasta / g).exists()]
    if quebrados:
        # 'fazer' e não aviso: sem o link, as etapas abaixo parecem vazias e mandariam refazer a busca inteira.
        add(0.3, "links", f"Consertar o link simbólico quebrado: {', '.join(quebrados)} (não refaça a busca)", "fazer",
            detalhe=f"aponta para {S.compartilhado[quebrados[0]]}; a aula dona mudou de lugar ou a pasta foi copiada sem "
                    "ela. Refaça o link (ln -sfn ../<aula dona>/<pasta> <pasta>) ou copie as pastas da aula dona; "
                    "as etapas seguintes só valem depois disso")

    # ---------------------------------------------------------------- 0 briefing
    brief = pasta / "00_briefing.md"
    if not brief.exists():
        m = re.match(r"^(\d{4}-\d{2})-(.+)$", pasta.name)
        extra = f" --mes {m.group(1)} --slug {m.group(2)}" if m else ""
        add(0.0, "briefing", "Criar " + ("o 00_briefing.md (a pasta já existe; nada é apagado)" if pasta.is_dir()
                                         else "a pasta da aula e o 00_briefing.md"), "fazer",
            f"{C.cmd_proprio('nova_aula.py')} --tema \"...\" --raiz {pasta.parent}{extra}")
        if not pasta.is_dir():
            return S
        texto_brief = ""
    else:
        texto_brief = brief.read_text(encoding="utf-8", errors="replace")
    faltam = texto_brief.count(C.MARCA_PREENCHER)
    if not brief.exists():
        pass
    elif faltam:
        add(0.1, "briefing", f"Completar o briefing ({faltam} campo(s) \"{C.MARCA_PREENCHER}\")",
            "aviso" if sem_parar else "fazer",
            detalhe="pergunte ao usuário só o que o pedido não diz (perguntas mínimas no SKILL.md); "
                    "no modo sem parar, preencha com o padrão e registre a suposição")
    else:
        add(0.1, "briefing", "Briefing completo", "ok")
    if not (pasta / "00_andamento.md").exists():
        add(0.2, "andamento", "Sem 00_andamento.md (checagens não registradas)", "aviso",
            f"{C.cmd_proprio('situacao.py')} {A} --registrar \"andamento criado\"")

    # ---------------------------------------------------------------- 1 busca
    pesq = lambda s: C.cmd_irma("pesquisa", s)  # noqa: E731
    conceitos = B / "conceitos.json"
    brutos = B / "brutos"
    reg = B / "registros.json"
    sel = B / "selecionados.json"
    # Busca por ramos (01_busca/ramos/<ramo>/ com conceitos, strings, sentinelas e brutos próprios; a raiz guarda a união).
    ramos = sorted(d for d in (B / "ramos").iterdir() if d.is_dir() and (d / "conceitos.json").exists()) \
        if (B / "ramos").is_dir() else []
    if not conceitos.exists():
        add(1.0, "conceitos", "Escolher sentinelas e montar 01_busca/conceitos.json", "fazer",
            detalhe="boost-pesquisa-artigos, passos 2 e 3 (sentinelas conferidos no PubMed, blocos MeSH + texto livre)")
    else:
        conc = C.ler_json(conceitos, {})
        if isinstance(conc, dict) and "__erro__" in conc:
            add(1.0, "conceitos", "conceitos.json não abre", "fazer", detalhe=conc["__erro__"])
            conc = {}
        else:
            det = f"recorte {conc.get('recorte', 'topo_mecanismos')}"
            if ramos:
                det += f"; busca em {len(ramos)} ramos ({', '.join(r.name for r in ramos)}), união na raiz de 01_busca"
            add(1.0, "conceitos", "conceitos.json", "ok", detalhe=det)
        n_sent = len(conc.get("sentinelas") or []) if isinstance(conc, dict) else 0
        if n_sent == 0 and not ramos:
            add(1.05, "sentinelas_lista", "Nenhum artigo-sentinela em conceitos.json: a busca fica sem teste de sensibilidade",
                "aviso")
        if mais_velho(B / "strings.json", conceitos):
            add(1.1, "strings", "Gerar as strings e conferir os descritores MeSH", "fazer",
                f"{pesq('montar_strings.py')} {conceitos} --verificar-mesh")
        else:
            add(1.1, "strings", "Strings geradas (estrategia.md, strings.json)", "ok")
        pub = brutos / "pubmed.json"
        n_pub, execs = execucoes_pubmed(pub) if pub.exists() else (0, [])
        pub_ok = pub.exists() and n_pub > 0
        if not pub_ok:
            add(1.2, "pubmed", "Rodar o PubMed (contar, diagnosticar, baixar)" +
                (" — pubmed.json só tem contagem, sem registros" if pub.exists() else ""), "fazer",
                f"{pesq('pubmed_busca.py')} --conceitos {conceitos} --variante base --so-contar  &&  "
                f"{pesq('pubmed_busca.py')} --conceitos {conceitos}")
        else:
            add(1.2, "pubmed", "PubMed", "ok", detalhe=f"{n_pub} registros" + (" (união dos ramos)" if ramos else ""))
            # Ramos: cada um é comparado com a própria string; a raiz é a união e não roda no PubMed.
            alvos = [(r.name, r / "conceitos.json", r / "strings.json", r / "brutos" / "pubmed.json") for r in ramos
                     if (r / "brutos" / "pubmed.json").exists()] if ramos else \
                    [("", conceitos, B / "strings.json", pub)]
            velhos = [nome or "raiz" for nome, c, st, pb in alvos if pubmed_desatualizado(c, st, pb)]
            if velhos:
                add(1.21, "pubmed_velho", "A string mudou depois da busca no PubMed" +
                    (f" (ramos: {', '.join(velhos)})" if ramos else ""), "aviso",
                    f"{pesq('pubmed_busca.py')} --conceitos {conceitos} --substituir" if not ramos else None,
                    detalhe="se os blocos mudaram, rode de novo (strings, PubMed, sentinelas)")
            cortes = [(nome, v, tot, baix) for nome, _c, _s, pb in alvos for v, tot, baix in truncadas_pubmed(pb)]
            if cortes:
                nome, v, tot, baix = cortes[0]
                cabe = all(tot <= 5000 for *_x, tot, _b in cortes)
                conc_alvo = (B / "ramos" / nome / "conceitos.json") if nome else conceitos
                cedo = cabe and not and_["checagens"].get(1) and not reg.exists()   # antes da triagem: corrigir já
                add(1.22, "pubmed_corte", "PubMed cortado por --max: " + "; ".join(
                    f"{(n + ':') if n else ''}{vv} {b} de {t}" for n, vv, t, b in cortes[:4]), "fazer" if cedo else "aviso",
                    f"{pesq('pubmed_busca.py')} --conceitos {conc_alvo} --variante {v} --max 5000" if cabe else None,
                    detalhe="relevância do PubMed não é importância: até uns 5.000, baixe tudo; acima, aperte a busca "
                            "(passo 5 da pesquisa)")
        # sentinelas: na raiz ou em cada ramo
        arqs_sent = [r / "sentinelas.json" for r in ramos if (r / "sentinelas.json").exists()] if ramos \
            else [B / "sentinelas.json"] if (B / "sentinelas.json").exists() else []
        teste_feito = bool(arqs_sent)
        if n_sent or ramos:
            if not arqs_sent:
                add(1.3, "teste_sentinela", "Testar os artigos-sentinela", "fazer",
                    f"{pesq('teste_sentinela.py')} --conceitos {conceitos} --variante base,rs,ecr,diretriz" if not ramos
                    else None, detalhe="um teste por ramo (ramos/<ramo>/conceitos.json)" if ramos else None)
            else:
                rec = tot = 0
                acresc: list[str] = []
                perd: list[str] = []
                for sj in arqs_sent:
                    r_, t_, a_, p_ = ler_sentinelas(sj, pmids_manuais(sj.parent / "brutos" / "pubmed.json", pub))
                    rec, tot = rec + r_, tot + t_
                    acresc += a_
                    perd += p_
                est = "ok" if tot and not perd else "aviso"
                det = []
                if ramos:
                    det.append(f"soma de {len(arqs_sent)} ramo(s)")
                if acresc:
                    det.append(f"fora da string, mas acrescentado(s) por --pmids nos brutos: {', '.join(acresc[:6])}")
                if perd:
                    det.append(f"perdido(s): {', '.join(perd[:6])}; meta é 100% na base, veja o relatório de perdas "
                               "(passo 6 da pesquisa)")
                add(1.3, "teste_sentinela", f"Sentinelas na variante base: {rec}/{tot}", est,
                    f"{pesq('teste_sentinela.py')} --conceitos {conceitos} --variante base,rs,ecr,diretriz"
                    if perd and not ramos else None, detalhe="; ".join(det) or None)
                S.resumo["sentinelas"] = f"{rec}/{tot}" + (f" (+{len(acresc)} por PMID)" if acresc else "")
        if not (brutos / "crossref.json").exists():
            add(1.4, "crossref", "Crossref (JOSPT e revistas-alvo)", "fazer",
                f"{pesq('crossref_busca.py')} --conceitos {conceitos}")
        else:
            add(1.4, "crossref", "Crossref", "ok")
        if not (brutos / "openalex.json").exists():
            add(1.5, "openalex", "OpenAlex (citações, acesso aberto, perseguição dos sentinelas)", "fazer",
                f"{pesq('openalex_enriquecer.py')} --pasta {B} --perseguir sentinelas --de-ano 2018")
        else:
            add(1.5, "openalex", "OpenAlex", "ok")
        # A checagem 1 só aparece quando há o que mostrar: sentinelas testados (ou trabalho já depois dela).
        # Contagens em estrategia.md logo depois dos sentinelas (1.35), antes da Crossref: assim a checagem 1 sai
        # cedo e a Crossref e o OpenAlex rodam enquanto o usuário vai ao Scopus (references/checagens.md).
        pronto_c1 = teste_feito or (pub_ok and n_sent == 0 and not ramos) or reg.exists() or sel.exists()
        estr = B / "estrategia.md"
        contagens_pendentes = False
        if pronto_c1 and not ramos and not and_["checagens"].get(1) and not sel.exists() and estr.exists() and \
                mais_velho(estr, pub, B / "sentinelas.json"):
            add(1.35, "estrategia_contagens", "Registrar contagens e sentinelas em estrategia.md (antes de mostrar a checagem 1)",
                "fazer", f"{pesq('montar_strings.py')} {conceitos}")
            contagens_pendentes = True
        if pronto_c1 and not contagens_pendentes:
            checagem(1, 1.6, 2.1, "mostre estrategia.md em poucas linhas (blocos, contagens, sentinelas) e a string "
                                  "Scopus 'base' em bloco de código, com o passo a passo de exportação (passo 8 da pesquisa)")
        exports = [p for p in brutos.glob("scopus*") if p.suffix.lower() in (".csv", ".ris", ".bib", ".txt")] \
            if brutos.is_dir() else []
        sjson = brutos / "scopus.json"
        c1_feita = S.checagens.get(1)
        if exports:
            if mais_velho(sjson, *exports):
                add(1.7, "scopus", "Importar a exportação do Scopus", "fazer",
                    f"{pesq('importar_scopus.py')} --pasta {B}")
            else:
                add(1.7, "scopus", f"Scopus importado ({len(exports)} arquivo(s))", "ok")
        elif sem_parar:
            add(1.7, "scopus", "Scopus fora desta rodada (modo sem parar)", "aviso",
                detalhe="registre em estrategia.md; a string fica pronta para o usuário colar depois")
        elif c1_feita or reg.exists():
            add(1.7, "scopus", "Exportação do Scopus ainda não chegou", "usuario",
                detalhe=f"siga sem ela; quando chegar, salve em {brutos.resolve()}/scopus.csv e rode importar + consolidar de novo")

    # ---------------------------------------------------------------- 2 seleção
    brutos_json = list(brutos.glob("*.json")) if brutos.is_dir() else []
    if conceitos.exists():
        if not reg.exists() or mais_velho(reg, *brutos_json):
            add(2.0, "consolidar", "Consolidar (deduplicar, classificar, pontuar, planilha)", "fazer",
                f"{pesq('consolidar.py')} --pasta {B} --lote 60")
        else:
            fl = C.ler_json(B / "fluxo.json", {}) or {}
            det = f"{fl.get('unicos', '?')} únicos de {fl.get('identificados', '?')}" if isinstance(fl, dict) else None
            add(2.0, "consolidar", "Registros consolidados", "ok", detalhe=det)
            S.resumo["registros"] = det
    planilha = B / "triagem.xlsx"
    decis = B / "decisoes.json"
    if reg.exists() or sel.exists():
        if not sel.exists():
            if not decis.exists():
                add(2.1, "triagem", "Triar título e resumo (triagem_lote.md) e gravar decisoes.json", "fazer",
                    detalhe="boost-pesquisa-artigos, passo 10: 6 a 12 artigos (1-2 âncoras, 3-5 evidência principal, "
                            "2-3 mecanismo, 1 contraponto), cada um com papel e uma frase de por que entra")
            else:
                add(2.1, "triagem", "Aplicar as decisões e exportar os selecionados", "fazer",
                    f"{pesq('consolidar.py')} --pasta {B} --decisoes {decis}  &&  {pesq('exportar_selecionados.py')} --pasta {B}"
                    + ("" if ramos else f"  &&  {pesq('montar_strings.py')} {conceitos}"),
                    detalhe="o último comando atualiza estrategia.md com contagens, sentinelas e fluxo (passo 11)")
        elif planilha.exists() and mtime(planilha) > mtime(sel) + 2:
            add(2.1, "triagem", "A planilha é mais nova que selecionados.json (edição do usuário ou nova consolidação)", "fazer",
                f"{pesq('exportar_selecionados.py')} --pasta {B}")
        else:
            itens = C.lista_de(C.ler_json(sel, []), "selecionados", "registros")
            sem_papel = [i.get("chave") for i in itens if not i.get("papel")]
            n = len(itens)
            # seleção compartilhada por várias aulas (--compartilhar-de): o teto é 12 por aula
            dona_b = B.resolve()
            n_aulas = max(1, sum(1 for d in pasta.parent.iterdir() if d.is_dir() and (d / "01_busca").is_dir()
                                 and (d / "01_busca").resolve() == dona_b))
            est = "ok" if 6 <= n <= 12 * n_aulas and not sem_papel else "aviso"
            det = f"{n} artigos" + (f", seleção de {n_aulas} aulas (cada roteiro usa só os seus)" if n_aulas > 1 else "")
            if sem_papel:
                det += f"; sem papel: {', '.join(map(str, sem_papel[:6]))}"
            if not 6 <= n <= 12 * n_aulas:
                det += " (o recomendado para uma aula é 6 a 12)"
            add(2.1, "triagem", "Selecionados", est, detalhe=det)
            S.resumo["selecionados"] = n
    chaves_sel = [str(i.get("chave")) for i in C.lista_de(C.ler_json(sel, []), "selecionados", "registros")
                  if i.get("chave")] if sel.exists() else []

    # ---------------------------------------------------------------- 3 artigos
    leit = lambda s: C.cmd_irma("leitura", s)  # noqa: E731
    art = pasta / "02_artigos"
    man_arq = art / "manifest.json"
    manifest = C.lista_de(C.ler_json(man_arq, []), "artigos", "itens")
    por_chave = {str(m.get("chave")): m for m in manifest if m.get("chave")}
    ok_chaves = [k for k, m in por_chave.items() if m.get("status") == "ok"]
    pend = [k for k, m in por_chave.items() if m.get("status") != "ok"]
    if sel.exists():
        if not man_arq.exists():
            add(3.0, "baixar", "Baixar os PDFs de acesso aberto e gerar pendentes.md", "fazer",
                f"{leit('baixar_artigos.py')} {A}")
        else:
            novos = [k for k in chaves_sel if k not in por_chave]
            if novos:
                add(3.0, "baixar", f"Seleção mudou: {len(novos)} artigo(s) sem tentativa de download", "fazer",
                    f"{leit('baixar_artigos.py')} {A}", detalhe=", ".join(novos[:8]))
            else:
                add(3.0, "baixar", f"PDFs: {len(ok_chaves)} com PDF, {len(pend)} pendente(s)", "ok")
            S.resumo["pdfs"] = f"{len(ok_chaves)} ok, {len(pend)} pendentes"
        if man_arq.exists():
            real = art.resolve()
            checagem(2, 3.05, 5.0, "tabela curta dos selecionados (chave, desenho, ano, revista, papel, aberto/pago) "
                                   f"e o conteúdo de {real}/pendentes.md, com a pasta exata para salvar: {real}/manual/")
    elif not sel.exists() and man_arq.exists():
        add(3.0, "baixar", "Há manifest.json sem selecionados.json", "aviso",
            detalhe="o download foi feito a partir de registros.json? Confira; baixar sem seleção baixa a busca inteira")
    manual = art / "manual"
    soltos = [p for p in manual.iterdir() if p.is_file() and not p.name.startswith(".")] if manual.is_dir() else []
    if soltos:
        add(3.1, "incorporar", f"{len(soltos)} arquivo(s) em manual/ para incorporar", "fazer",
            f"{leit('incorporar_manuais.py')} {A}")
    sem_texto = [k for k in ok_chaves if not (art / "texto" / f"{k}.md").exists()]
    if sem_texto:
        add(3.2, "texto", f"Extrair o texto de {len(sem_texto)} PDF(s)", "fazer", f"{leit('extrair_texto.py')} {A}",
            detalhe=", ".join(sem_texto[:8]))
    elif ok_chaves:
        add(3.2, "texto", "Texto extraído", "ok")
    alvos_ficha = chaves_sel or list(por_chave)
    fichas = {k: art / "leitura" / f"{k}.md" for k in alvos_ficha}
    sem_ficha = [k for k, f in fichas.items() if not f.exists()]
    so_resumo, incompletas = [], []
    for k, f in fichas.items():
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if len(PLACEHOLDER.findall(t)) >= 5:
            incompletas.append(k)
        m = re.search(r"Texto lido:\s*(.+)", t)
        if m and "complet" not in m.group(1).lower().split("|")[0]:
            so_resumo.append(k)
        elif not m:
            so_resumo.append(k)
    if pend and man_arq.exists():
        ja_resumo = [k for k in pend if k in so_resumo]
        extra = (f" · {len(ja_resumo)} já com ficha só do resumo; quando o PDF chegar: incorporar, extrair e reler"
                 if ja_resumo else "")
        if sem_parar:
            add(3.15, "pendentes", f"{len(pend)} PDF(s) pendente(s): entram como 'só resumo' (modo sem parar)", "aviso",
                detalhe=", ".join(pend[:10]) + extra)
        else:
            add(3.15, "pendentes", f"{len(pend)} PDF(s) pagos ou recusados esperando o usuário (pendentes.md)", "usuario",
                detalhe=", ".join(pend[:10]) + (extra or " · siga com os que já têm PDF; o que não chegar entra como "
                                                         "'só resumo'"))
    reler = [k for k in ok_chaves if k in so_resumo and (art / "texto" / f"{k}.md").exists()]
    if reler:
        add(3.32, "reler", f"{len(reler)} ficha(s) só do resumo, mas o PDF já está na pasta: releia no texto completo",
            "aviso", detalhe=", ".join(reler[:10]) + " · atualize 'Texto lido' e os números com página")
    # Os candidatos de figura saem antes das fichas: quem lê o artigo já escolhe e recorta as figuras dele.
    fig = pasta / "03_figuras"
    cat_arq = fig / "catalogo.json"
    if ok_chaves:
        sem_det = [k for k in ok_chaves if not (fig / "paginas" / k).is_dir()]
        if not cat_arq.exists() or sem_det:
            add(3.25, "detectar", "Gerar miniaturas e candidatos de recorte" +
                (f" ({len(sem_det)} artigo(s) sem detecção)" if cat_arq.exists() else ""), "fazer",
                f"{leit('detectar_figuras.py')} {A}" + (f" --apenas {' '.join(sem_det)}" if cat_arq.exists() else ""),
                detalhe="uma vez, no principal, antes de distribuir as fichas (references/subagentes.md)")
        else:
            add(3.25, "detectar", "Candidatos de recorte gerados", "ok")
    if alvos_ficha and (ok_chaves or sel.exists()) and man_arq.exists():
        if sem_ficha:
            com_pdf = [k for k in sem_ficha if k in ok_chaves]
            add(3.3, "fichas", f"Escrever {len(sem_ficha)} ficha(s) de leitura crítica "
                f"({len(com_pdf)} com PDF, {len(sem_ficha) - len(com_pdf)} só resumo)", "fazer",
                detalhe="uma por artigo, de preferência em paralelo (subagentes; modelo de pedido em "
                        "references/subagentes.md); ficha em boost-leitura-figuras/assets/ficha_leitura_modelo.md · "
                        "faltam: " + ", ".join(sem_ficha[:10]))
        if incompletas:
            add(3.31, "fichas_incompletas", f"{len(incompletas)} ficha(s) com campos do modelo ainda abertos", "aviso",
                detalhe=", ".join(incompletas[:10]))
        if not sem_ficha:
            add(3.3, "fichas", f"Fichas: {len(fichas)}", "ok",
                detalhe=f"lidas só no resumo ou parcial: {', '.join(so_resumo)}" if so_resumo else "todas no texto completo")
    S.resumo["so_resumo"] = so_resumo

    # ---------------------------------------------------------------- 4 figuras
    catalogo = C.lista_de(C.ler_json(cat_arq, []), "figuras")
    aprovadas = [e for e in catalogo if e.get("aprovada") is True]
    aula4 = pasta / "04_aula"
    rot = aula4 / "roteiro.md"
    deck_arq = aula4 / "deck.json"
    if ok_chaves or aprovadas:
        if cat_arq.exists():
            if not aprovadas:
                adiante = rot.exists() or deck_arq.exists()
                add(4.1, "recortar", "Nenhuma figura aprovada" + (": a aula segue sem figura de artigo" if adiante else
                    "; olhar, recortar e aprovar"), "aviso" if adiante else "fazer",
                    detalhe="ciclo olhar → recortar → conferir da boost-leitura-figuras (passo 5); "
                            "parta das figuras apontadas nas fichas; 3 a 5 entram na aula")
            else:
                add(4.1, "recortar", f"{len(aprovadas)} figura(s) aprovada(s)", "ok")
                sem_qc = [e["id"] for e in aprovadas if not isinstance(e.get("qc"), dict)]
                problemas = [e["id"] for e in aprovadas if isinstance(e.get("qc"), dict)
                             and (e["qc"].get("erros") or e["qc"].get("ok") is False)]
                if sem_qc or not (fig / "folha_contato.png").exists():
                    add(4.2, "conferir", f"Conferir os recortes e gerar a folha de contato ({len(sem_qc)} sem conferência)",
                        "fazer", f"{leit('conferir_recortes.py')} {A}")
                elif problemas:
                    add(4.2, "conferir", f"{len(problemas)} figura(s) aprovada(s) com PROBLEMA na conferência", "fazer",
                        f"{leit('conferir_recortes.py')} {A}", detalhe=", ".join(problemas[:8]))
                else:
                    add(4.2, "conferir", "Recortes conferidos; folha de contato gerada", "ok")
                restritas = [f"{e['id']} ({e.get('licenca') or 'desconhecida'})" for e in aprovadas
                             if str(e.get("licenca") or "desconhecida").lower() not in LICENCAS_LIVRES]
                if restritas:
                    add(4.3, "licencas", f"{len(restritas)} figura(s) aprovada(s) sem licença CC BY", "aviso",
                        detalhe="; ".join(restritas[:8]) + " · uso interno gravado ok; venda exige permissão ou 'Adaptado de'")
    S.resumo["figuras_aprovadas"] = len(aprovadas)

    # ---------------------------------------------------------------- 5 roteiro
    tem_leitura = bool(fichas) and not sem_ficha
    mapa = pasta / "00_mapa_evidencias.md"
    if mapa.exists():
        add(4.9, "mapa", "Mapa de evidências (00_mapa_evidencias.md)", "ok")
    if not rot.exists() and deck_arq.exists():
        # pasta em que o deck foi escrito direto (sem roteiro.md): não manda voltar ao roteiro
        add(5.0, "roteiro", "Sem 04_aula/roteiro.md: o deck foi escrito direto", "aviso",
            detalhe="a linha do tempo está no deck (validar_aula.py mostra); se quiser o roteiro para a gravação, "
                    "escreva-o a partir do deck")
        if and_["checagens"].get(3):
            add(5.1, "checagem3", f"Checagem 3: {C.CHECAGENS[3]}", "ok")
        elif not sem_parar:
            add(5.1, "checagem3", "Checagem 3 sem roteiro para aprovar", "aviso",
                f"{C.cmd_proprio('situacao.py')} {A} --marcar 3 --nota \"linha do tempo aprovada junto com o deck\"",
                detalhe="mostre os objetivos, o caso e a linha do tempo do deck junto com a checagem 4")
    elif tem_leitura or rot.exists():
        if not rot.exists():
            add(5.0, "roteiro", "Escrever 04_aula/roteiro.md com a linha do tempo", "fazer",
                detalhe="boost-aula-slides, passos 1 a 3 (objetivos, caso, 3 blocos, tempos); modelo em assets/roteiro_modelo.md")
        else:
            abertos = len(PLACEHOLDER.findall(rot.read_text(encoding="utf-8", errors="replace")))
            add(5.0, "roteiro", "Roteiro escrito" + (f" ({abertos} campo(s) do modelo abertos)" if abertos else ""),
                "aviso" if abertos else "ok")
            checagem(3, 5.1, 6.0, "objetivos, caso, linha do tempo (início, bloco, slide, interação) e as figuras "
                                  "escolhidas; pergunte se o tempo e as decisões estão certos")

    # ---------------------------------------------------------------- 6 deck e materiais
    sl = lambda s: C.cmd_irma("slides", s)  # noqa: E731
    if rot.exists() or deck_arq.exists():
        if not deck_arq.exists():
            add(6.0, "deck", "Escrever deck.json e questoes.json", "fazer",
                detalhe="copie boost-aula-slides/assets/exemplo/deck.json e reescreva (passo 4 da skill de slides)")
        else:
            deck = C.ler_json(deck_arq, {})
            if isinstance(deck, dict) and "__erro__" in deck:
                add(6.0, "deck", "deck.json não abre", "fazer", detalhe=deck["__erro__"])
                deck = {}
            else:
                add(6.0, "deck", "deck.json escrito", "ok")
            slug = str(((deck or {}).get("meta") or {}).get("slug") or "")
            pptx = aula4 / f"{slug}.pptx" if slug else next(iter(sorted(aula4.glob("*.pptx"))), aula4 / "aula.pptx")
            S.resumo["pptx"] = str(pptx)
            if not (aula4 / "questoes.json").exists():
                add(6.05, "questoes", "Escrever questoes.json (enquetes e pré/pós-teste)", "fazer",
                    detalhe="boost-aula-slides/references/questoes.md; modelo em assets/exemplo/questoes.json")
            if validar and deck:
                v = rodar_validador(deck_arq)
                if v is not None:
                    erros, avisos, dur, n = v
                    S.resumo["validacao"] = {"erros": len(erros), "avisos": len(avisos), "duracao": dur, "slides": n}
                    if erros:
                        add(6.1, "validar", f"Validação pedagógica com {len(erros)} erro(s)", "fazer",
                            f"{sl('validar_aula.py')} {deck_arq}", detalhe="; ".join(erros[:4]))
                    else:
                        add(6.1, "validar", f"Validação sem erros ({dur}, {n} slides, {len(avisos)} aviso(s))", "ok")
            if mais_velho(pptx, deck_arq, cat_arq):
                add(6.2, "montar", "Montar o .pptx", "fazer", f"{sl('montar_deck.py')} {deck_arq}")
            else:
                add(6.2, "montar", f"{pptx.name} montado", "ok")
            folhas = sorted((aula4 / "previa").glob("folha-*.png"))
            if not folhas or (pptx.exists() and mtime(pptx) > min(mtime(f) for f in folhas) + 2):
                add(6.3, "render", "Renderizar e olhar cada slide", "fazer", f"{sl('renderizar.py')} {pptx}")
            else:
                add(6.3, "render", f"Prévia renderizada ({len(folhas)} folha(s) de contato)", "ok",
                    detalhe="renderizar não prova que alguém olhou: abra as folhas e os PNGs")
            andam_txt = (pasta / "00_andamento.md").read_text(encoding="utf-8", errors="replace") \
                if (pasta / "00_andamento.md").exists() else ""
            if pptx.exists() and "conferir_pptx" not in andam_txt:
                add(6.35, "conferir_pptx", "Conferir o .pptx por dentro (notas, acumulado, gráficos, XML)", "fazer",
                    f"{sl('conferir_pptx.py')} {deck_arq} {pptx}  &&  {C.cmd_proprio('situacao.py')} {A} "
                    "--registrar \"conferir_pptx: OK\"")
            mats = [aula4 / n for n in ("enquetes.md", "pre_pos_teste.md", "resumo_aluno.md")]
            if any(mais_velho(m, deck_arq, aula4 / "questoes.json") for m in mats):
                add(6.4, "materiais", "Gerar enquetes, pré/pós-teste e resumo do aluno", "fazer",
                    f"{sl('materiais.py')} {deck_arq}")
            else:
                add(6.4, "materiais", "Materiais gerados", "ok")
            ver = aula4 / "verificacao.md"
            if not ver.exists():
                add(6.5, "verificacao", "Escrever 04_aula/verificacao.md", "fazer",
                    detalhe="modelo em boost-aula-slides/assets/verificacao_modelo.md: cada número, onde foi conferido")
            else:
                ab = len(PLACEHOLDER.findall(ver.read_text(encoding="utf-8", errors="replace")))
                add(6.5, "verificacao", "verificacao.md" + (f" ({ab} campo(s) do modelo abertos)" if ab else ""),
                    "aviso" if ab else "ok")
            # A checagem 4 só aparece com o deck pronto para revisar: montado, renderizado, conferido, materiais e
            # verificacao.md feitos (ou já com a entrega gerada, para o registro retroativo).
            falta6 = any(p.estado == "fazer" and 6.0 <= p.ordem < 6.6 for p in P)
            if pptx.exists() and (not falta6 or (aula4 / "entrega.md").exists() or and_["checagens"].get(4)):
                checagem(4, 6.6, 7.0, "caminho do .pptx, duração e linha do tempo resumida, folha de contato do deck, "
                                      "o que não foi conferido e os avisos que ficaram de pé")

    # ---------------------------------------------------------------- 7 entrega
    if deck_arq.exists():
        ent = aula4 / "entrega.md"
        pptx = Path(S.resumo.get("pptx", aula4 / "x.pptx"))
        if mais_velho(ent, pptx, deck_arq, aula4 / "verificacao.md", cat_arq):
            add(7.0, "entrega", "Gerar o relatório de entrega (tabela de evidências, figuras e licenças, não conferido)",
                "fazer", f"{C.cmd_proprio('relatorio_final.py')} {A}")
        else:
            add(7.0, "entrega", "Relatório de entrega gerado (04_aula/entrega.md)", "ok")

    # O próximo passo é o primeiro 'fazer' na ordem do pipeline, não na ordem em que o código acrescentou.
    P.sort(key=lambda p: p.ordem)

    # Checagem não registrada, mas com trabalho já feito depois dela (pasta de outra sessão, aprovação só na
    # conversa): não trava; vira aviso para confirmar e registrar.
    for p in P:
        if p.estado == "usuario" and p.chave.startswith("checagem") and p.bloqueia_de is not None:
            if any(q.estado == "ok" and q.ordem >= p.bloqueia_de and not q.chave.startswith("checagem") for q in P):
                n = p.chave[-1]
                # checagens 1 e 2 de aula com busca compartilhada se registram na aula dona (references/trilha.md)
                alvo = str(dona) if dona is not None and n in ("1", "2") else A
                p.estado = "aviso"
                p.texto = f"Checagem {n} não registrada, mas o trabalho já passou dela"
                p.detalhe = "confirme com o usuário se ele aprovou; se sim, registre" + \
                    (f" na aula dona ({dona.name})" if alvo != A else "")
                p.comando = f"{C.cmd_proprio('situacao.py')} {alvo} --marcar {n} --nota \"aprovada antes (registro retroativo)\""
                p.bloqueia_de = None
    return S


def rodar_validador(deck_arq: Path):
    pasta = C.caminho_irma("slides")
    if not pasta:
        return None
    try:
        r = subprocess.run([sys.executable, "-I", str(pasta / "validar_aula.py"), str(deck_arq), "--json"],
                           capture_output=True, text=True, timeout=120)
        d = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    linha = [x for x in d.get("linha") or [] if not x.get("apoio")]
    fim = max((x.get("fim") or 0 for x in linha), default=0)
    dur = f"{int(fim) // 60}:{int(fim) % 60:02d} min"
    txt = lambda e: e if isinstance(e, str) else (e.get("msg") or e.get("mensagem") or json.dumps(e, ensure_ascii=False))  # noqa: E731
    return [txt(e) for e in d.get("erros") or []], [txt(e) for e in d.get("avisos") or []], dur, len(d.get("linha") or [])


def proximo(S: Situacao) -> tuple[Passo | None, list[Passo], list[Passo]]:
    """Primeiro passo a fazer (ou a checagem que o bloqueia), esperas do usuário e avisos."""
    esperas = [p for p in S.passos if p.estado == "usuario"]
    avisos = [p for p in S.passos if p.estado == "aviso"]
    fazer = [p for p in S.passos if p.estado == "fazer"]
    for p in fazer:
        bloqueio = next((u for u in esperas if u.bloqueia_de is not None and u.ordem < p.ordem
                         and p.ordem >= u.bloqueia_de), None)
        if bloqueio is None:
            return p, esperas, avisos
        return bloqueio, esperas, avisos
    # nada a fazer: a próxima coisa é uma checagem ainda aberta, se houver
    aberta = next((u for u in esperas if u.bloqueia_de is not None), None)
    return aberta, esperas, avisos


def etapa_atual(S: Situacao, prox: Passo | None) -> int:
    if prox is not None:
        return prox.etapa
    return max((p.etapa for p in S.passos), default=0)


def imprimir(S: Situacao) -> None:
    prox, esperas, avisos = proximo(S)
    marca = {"ok": "feito", "fazer": "a fazer", "usuario": "usuário", "aviso": "atenção"}
    print(f"Aula: {S.pasta}")
    print(f"Tema: {S.tema}")
    ch = " · ".join(f"{n} {'feita' if v else 'aberta'}" for n, v in S.checagens.items())
    print(f"Modo: {S.modo} · Checagens: {ch}")
    for g, alvo in S.compartilhado.items():
        print(f"Compartilhado: {g} -> {alvo}")
    print()
    for e, nome in ETAPAS.items():
        passos = [p for p in S.passos if p.etapa == e]
        if not passos:
            continue
        estados = {p.estado for p in passos}
        geral = "feito" if estados <= {"ok"} else ("a fazer" if "fazer" in estados else
                                                     "usuário" if "usuario" in estados else "atenção")
        print(f"[{geral:^8}] {e} {nome}")
        for p in passos:
            extra = f" — {p.detalhe}" if p.detalhe and p.estado != "fazer" else ""
            print(f"           {'✓' if p.estado == 'ok' else '·'} {p.texto}{extra}")
    print()
    if prox is None:
        print("Etapa atual: concluída. Entregue ao usuário o que está em 04_aula/entrega.md.")
    else:
        print(f"Etapa atual: {prox.etapa} {ETAPAS[prox.etapa]}")
        if prox.estado == "usuario":
            print(f"Próximo passo: apresentar a {prox.texto.split(':')[0].lower()} ao usuário e esperar a resposta.")
            print(f"  O que mostrar: {prox.detalhe}")
        else:
            print(f"Próximo passo: {prox.texto}")
            if prox.detalhe:
                print(f"  {prox.detalhe}")
        if prox.comando:
            print(f"  $ {prox.comando}")
    outras = [p for p in esperas if p is not prox]
    if outras:
        print("\nEsperando o usuário (não pare por isso, a menos que seja checagem que bloqueia o passo):")
        for p in outras:
            print(f"  - {p.texto}" + (f" — {p.detalhe}" if p.detalhe else ""))
    if avisos:
        print("\nAtenção:")
        for p in avisos:
            print(f"  - {p.texto}" + (f" — {p.detalhe}" if p.detalhe else ""))
            if p.comando:
                print(f"    $ {p.comando}")


def eh_aula(p: Path) -> bool:
    return p.is_dir() and ((p / "00_briefing.md").exists() or (p / "01_busca").exists()
                           or bool(re.match(r"\d{4}-\d{2}-", p.name)))


def listar(raiz: Path, como_json: bool) -> int:
    aulas = sorted(p for p in raiz.iterdir() if eh_aula(p)) if raiz.is_dir() else []
    trilhas = sorted(raiz.glob("trilha*.md")) if raiz.is_dir() else []
    saida = []
    for a in aulas:
        S = analisar(a, validar=False)
        prox, esperas, _ = proximo(S)
        saida.append({"aula": a.name, "tema": S.tema, "etapa": etapa_atual(S, prox),
                      "proximo": prox.texto if prox else "concluída",
                      "checagens": [n for n, v in S.checagens.items() if v], "esperas": len(esperas),
                      "compartilhado": sorted(S.compartilhado)})
    if como_json:
        print(json.dumps({"raiz": str(raiz), "trilhas": [str(t) for t in trilhas], "aulas": saida},
                         ensure_ascii=False, indent=2))
        return 0
    print(f"Aulas em {raiz}: {len(saida)}")
    for t in trilhas:
        print(f"Plano de trilha: {t}")
    for s in saida:
        comp = f" · usa {', '.join(s['compartilhado'])} de outra aula" if s["compartilhado"] else ""
        print(f"- {s['aula']}: etapa {s['etapa']} ({ETAPAS[s['etapa']]}) · próximo: {s['proximo']} · "
              f"checagens feitas: {s['checagens'] or 'nenhuma'}{comp}")
    if not saida:
        print("Nenhuma aula encontrada. Crie uma com nova_aula.py.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Lê a pasta de uma aula Boost e diz em que etapa ela está e qual o próximo passo "
                    "(com o comando). Com uma pasta de aulas, lista todas. Também marca as checagens em 00_andamento.md.",
        epilog="exemplos:\n"
               "  python3 situacao.py aulas/2026-11-lca-retorno-esporte\n"
               "  python3 situacao.py aulas                       # todas as aulas e trilhas\n"
               "  python3 situacao.py AULA --marcar 1 --nota \"Daniel aprovou; vai exportar o Scopus\"\n"
               "  python3 situacao.py AULA --modo sem-parar --nota \"pediu para seguir sem parar\"\n"
               "  python3 situacao.py AULA --registrar \"conferir_pptx: OK\"\n"
               "  python3 situacao.py AULA --json",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", help="pasta da aula (aulas/<AAAA-MM>-<slug>) ou a pasta que guarda as aulas")
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    ap.add_argument("--sem-validar", action="store_true", help="não roda o validador pedagógico do deck.json")
    ap.add_argument("--marcar", type=int, choices=sorted(C.CHECAGENS), action="append", default=[],
                    help="marca a checagem N como feita (pode repetir)")
    ap.add_argument("--desmarcar", type=int, choices=sorted(C.CHECAGENS), action="append", default=[],
                    help="reabre a checagem N (pode repetir)")
    ap.add_argument("--modo", choices=("sem-parar", "com-checagens"), help="troca o modo de condução")
    ap.add_argument("--nota", help="texto curto que acompanha --marcar/--modo no registro")
    ap.add_argument("--registrar", metavar="TEXTO", help="acrescenta uma linha ao registro de 00_andamento.md")
    a = ap.parse_args()
    pasta = Path(a.pasta).expanduser()
    if not pasta.exists():
        print(f"ERRO: pasta não encontrada: {pasta}", file=sys.stderr)
        return 2
    if a.marcar or a.desmarcar or a.modo or a.registrar:
        if not (pasta / "00_briefing.md").exists() and not (pasta / "00_andamento.md").exists():
            print(f"ERRO: {pasta} não parece ser a pasta de uma aula (sem 00_briefing.md).", file=sys.stderr)
            return 2
        feitos: list[str] = []
        acoes = [("marcar", n) for n in a.marcar] + [("desmarcar", n) for n in a.desmarcar]
        if a.modo:
            acoes.append(("modo", a.modo.replace("-", " ")))
        for tipo, valor in acoes:
            feitos += C.atualizar_andamento(pasta, nota=a.nota, tema=tema_de(pasta), **{tipo: valor})
        if a.registrar or (a.nota and not acoes):
            feitos += C.atualizar_andamento(pasta, nota=a.registrar or a.nota, tema=tema_de(pasta))
        print(f"00_andamento.md atualizado: {'; '.join(feitos)}")
        print()
    if not (pasta / "00_briefing.md").exists() and not (pasta / "01_busca").exists() and \
            any(eh_aula(p) for p in pasta.iterdir() if p.is_dir()):
        return listar(pasta, a.json)
    S = analisar(pasta, validar=not a.sem_validar)
    if a.json:
        prox, esperas, avisos = proximo(S)
        d = asdict(S)
        d["etapa_atual"] = etapa_atual(S, prox)
        d["proximo"] = asdict(prox) if prox else None
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        imprimir(S)
    return 0


if __name__ == "__main__":
    sys.exit(main())
