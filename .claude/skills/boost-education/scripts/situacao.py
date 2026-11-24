#!/usr/bin/env python3
"""Diz em que etapa está uma aula Boost e qual o próximo passo, lendo só a pasta da aula.

Serve para retomar o trabalho em outra sessão: cada sessão começa do zero, e a pasta é a memória.
Também marca os pontos de checagem e o modo em 00_andamento.md.
"""
from __future__ import annotations

import argparse
import json
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
        m = re.search(r"^#\s*(?:Briefing\s*[·:-]\s*)?(.+)$", brief.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            return m.group(1).strip()
    return pasta.name


def analisar(pasta: Path, validar: bool = True) -> Situacao:
    pasta = pasta.expanduser()
    and_ = C.ler_andamento(pasta)
    sem_parar = and_["modo"] == "sem parar"
    S = Situacao(pasta=str(pasta), tema=tema_de(pasta), modo=and_["modo"], checagens=and_["checagens"])
    P = S.passos
    A = str(pasta)
    B = pasta / "01_busca"
    for grupo in ("01_busca", "02_artigos", "03_figuras"):
        if (pasta / grupo).is_symlink():
            S.compartilhado[grupo] = str((pasta / grupo).resolve())

    def add(ordem, chave, texto, estado, comando=None, detalhe=None, bloqueia_de=None):
        P.append(Passo(ordem, chave, texto, estado, comando, detalhe, bloqueia_de))

    def checagem(n: int, ordem: float, bloqueia_de: float, como: str):
        feito = and_["checagens"].get(n)
        if feito:
            add(ordem, f"checagem{n}", f"Checagem {n}: {C.CHECAGENS[n]}", "ok",
                detalhe=feito.replace(C.CHECAGENS[n], "").strip(" —-") or None)
        elif sem_parar:
            add(ordem, f"checagem{n}", f"Checagem {n} pulada (modo sem parar)", "ok",
                detalhe="registre no fim o que o usuário precisa revisar")
        else:
            add(ordem, f"checagem{n}", f"CHECAGEM {n}: {C.CHECAGENS[n]}", "usuario",
                comando=f"{C.cmd_proprio('situacao.py')} {A} --marcar {n} --nota \"...\"  (depois que o usuário aprovar)",
                detalhe=como, bloqueia_de=bloqueia_de)

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
    if not conceitos.exists():
        add(1.0, "conceitos", "Escolher sentinelas e montar 01_busca/conceitos.json", "fazer",
            detalhe="boost-pesquisa-artigos, passos 2 e 3 (sentinelas conferidos no PubMed, blocos MeSH + texto livre)")
    else:
        conc = C.ler_json(conceitos, {})
        if isinstance(conc, dict) and "__erro__" in conc:
            add(1.0, "conceitos", "conceitos.json não abre", "fazer", detalhe=conc["__erro__"])
            conc = {}
        else:
            add(1.0, "conceitos", "conceitos.json", "ok", detalhe=f"recorte {conc.get('recorte', 'topo_mecanismos')}")
        n_sent = len(conc.get("sentinelas") or []) if isinstance(conc, dict) else 0
        if n_sent == 0:
            add(1.05, "sentinelas_lista", "Nenhum artigo-sentinela em conceitos.json: a busca fica sem teste de sensibilidade",
                "aviso")
        if mais_velho(B / "strings.json", conceitos):
            add(1.1, "strings", "Gerar as strings e conferir os descritores MeSH", "fazer",
                f"{pesq('montar_strings.py')} {conceitos} --verificar-mesh")
        else:
            add(1.1, "strings", "Strings geradas (estrategia.md, strings.json)", "ok")
        pub = brutos / "pubmed.json"
        if not pub.exists():
            add(1.2, "pubmed", "Rodar o PubMed (contar, diagnosticar, baixar)", "fazer",
                f"{pesq('pubmed_busca.py')} --conceitos {conceitos} --variante base --so-contar  &&  "
                f"{pesq('pubmed_busca.py')} --conceitos {conceitos}")
        else:
            dados = C.ler_json(pub, {})
            det = None
            if isinstance(dados, dict):
                n = len(dados.get("registros") or [])
                det = f"{n} registros"
            add(1.2, "pubmed", "PubMed", "ok", detalhe=det)
            if mtime(conceitos) > mtime(pub) + 2:
                add(1.21, "pubmed_velho", "conceitos.json mudou depois da busca no PubMed", "aviso",
                    f"{pesq('pubmed_busca.py')} --conceitos {conceitos} --substituir",
                    detalhe="se os blocos mudaram, rode de novo (strings, PubMed, sentinelas)")
        if n_sent:
            sj = B / "sentinelas.json"
            if not sj.exists():
                add(1.3, "teste_sentinela", "Testar os artigos-sentinela", "fazer",
                    f"{pesq('teste_sentinela.py')} --conceitos {conceitos} --variante base,rs,ecr,diretriz")
            else:
                d = C.ler_json(sj, {}) or {}
                base = (d.get("variantes") or {}).get("base") or {}
                rec = len(base.get("recuperados") or []) if base else d.get("recuperados")
                tot = base.get("testaveis") or d.get("total")
                est = "ok" if rec is not None and tot and rec >= tot else "aviso"
                add(1.3, "teste_sentinela", f"Sentinelas na variante base: {rec}/{tot}", est,
                    None if est == "ok" else f"{pesq('teste_sentinela.py')} --conceitos {conceitos} --variante base,rs,ecr,diretriz",
                    detalhe=None if est == "ok" else "meta é 100% na base; veja o relatório de perdas (passo 6 da pesquisa)")
                S.resumo["sentinelas"] = f"{rec}/{tot}"
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
        checagem(1, 1.6, 2.1, "mostre estrategia.md em poucas linhas (blocos, contagens, sentinelas) e a string "
                              "Scopus 'base' em bloco de código, com o passo a passo de exportação (passo 8 da pesquisa)")
        exports = [p for p in brutos.glob("scopus*") if p.suffix.lower() in (".csv", ".ris", ".bib", ".txt")] \
            if brutos.is_dir() else []
        sjson = brutos / "scopus.json"
        if exports:
            if mais_velho(sjson, *exports):
                add(1.7, "scopus", "Importar a exportação do Scopus", "fazer",
                    f"{pesq('importar_scopus.py')} --pasta {B}")
            else:
                add(1.7, "scopus", f"Scopus importado ({len(exports)} arquivo(s))", "ok")
        elif and_["checagens"].get(1) and not sem_parar:
            add(1.7, "scopus", "Exportação do Scopus ainda não chegou", "usuario",
                detalhe=f"siga sem ela; quando chegar, salve em {brutos}/scopus.csv e rode importar + consolidar de novo")
        elif sem_parar:
            add(1.7, "scopus", "Scopus fora desta rodada (modo sem parar)", "aviso",
                detalhe="registre em estrategia.md; a string fica pronta para o usuário colar depois")

    # ---------------------------------------------------------------- 2 seleção
    reg = B / "registros.json"
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
    sel = B / "selecionados.json"
    planilha = B / "triagem.xlsx"
    decis = B / "decisoes.json"
    if reg.exists() or sel.exists():
        if not sel.exists():
            if not decis.exists():
                add(2.1, "triagem", "Triar título e resumo (triagem_lote.md) e gravar decisoes.json", "fazer",
                    detalhe="6 a 12 artigos: 1-2 âncoras, 3-5 evidência principal, 2-3 mecanismo, 1 contraponto")
            else:
                add(2.1, "triagem", "Aplicar as decisões e exportar os selecionados", "fazer",
                    f"{pesq('consolidar.py')} --pasta {B} --decisoes {decis}  &&  {pesq('exportar_selecionados.py')} --pasta {B}")
        elif planilha.exists() and mtime(planilha) > mtime(sel) + 2:
            add(2.1, "triagem", "A planilha mudou depois de selecionados.json (o usuário pode ter editado)", "fazer",
                f"{pesq('exportar_selecionados.py')} --pasta {B}")
        else:
            itens = C.lista_de(C.ler_json(sel, []), "selecionados", "registros")
            sem_papel = [i.get("chave") for i in itens if not i.get("papel")]
            n = len(itens)
            est = "ok" if 6 <= n <= 12 and not sem_papel else "aviso"
            det = f"{n} artigos"
            if sem_papel:
                det += f"; sem papel: {', '.join(map(str, sem_papel[:6]))}"
            if not 6 <= n <= 12:
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
            checagem(2, 3.05, 5.0, "tabela curta dos selecionados (chave, desenho, ano, revista, papel, aberto/pago) "
                                   f"e o conteúdo de {art}/pendentes.md, com a pasta exata para salvar: {art}/manual/")
    elif not sel.exists() and man_arq.exists():
        add(3.0, "baixar", "Há manifest.json sem selecionados.json", "aviso",
            detalhe="o download foi feito a partir de registros.json? Confira; baixar sem seleção baixa a busca inteira")
    manual = art / "manual"
    soltos = [p for p in manual.iterdir() if p.is_file() and not p.name.startswith(".")] if manual.is_dir() else []
    if soltos:
        add(3.1, "incorporar", f"{len(soltos)} arquivo(s) em manual/ para incorporar", "fazer",
            f"{leit('incorporar_manuais.py')} {A}")
    if pend and man_arq.exists():
        if sem_parar:
            add(3.15, "pendentes", f"{len(pend)} PDF(s) pendente(s): entram como 'só resumo' (modo sem parar)", "aviso",
                detalhe=", ".join(pend[:10]))
        else:
            add(3.15, "pendentes", f"{len(pend)} PDF(s) pagos ou recusados esperando o usuário (pendentes.md)", "usuario",
                detalhe=", ".join(pend[:10]) + " · siga com os que já têm PDF; o que não chegar entra como 'só resumo'")
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
    if alvos_ficha and (ok_chaves or sel.exists()) and man_arq.exists():
        if sem_ficha:
            com_pdf = [k for k in sem_ficha if k in ok_chaves]
            add(3.3, "fichas", f"Escrever {len(sem_ficha)} ficha(s) de leitura crítica "
                f"({len(com_pdf)} com PDF, {len(sem_ficha) - len(com_pdf)} só resumo)", "fazer",
                detalhe="uma por artigo, de preferência em paralelo (subagentes); modelo em "
                        "boost-leitura-figuras/assets/ficha_leitura_modelo.md · faltam: " + ", ".join(sem_ficha[:10]))
        if incompletas:
            add(3.31, "fichas_incompletas", f"{len(incompletas)} ficha(s) com campos do modelo ainda abertos", "aviso",
                detalhe=", ".join(incompletas[:10]))
        if not sem_ficha:
            add(3.3, "fichas", f"Fichas: {len(fichas)}", "ok",
                detalhe=f"lidas só no resumo ou parcial: {', '.join(so_resumo)}" if so_resumo else "todas no texto completo")
    S.resumo["so_resumo"] = so_resumo

    # ---------------------------------------------------------------- 4 figuras
    fig = pasta / "03_figuras"
    cat_arq = fig / "catalogo.json"
    catalogo = C.lista_de(C.ler_json(cat_arq, []), "figuras")
    aprovadas = [e for e in catalogo if e.get("aprovada") is True]
    if ok_chaves:
        sem_det = [k for k in ok_chaves if not (fig / "paginas" / k).is_dir()]
        if not cat_arq.exists() or sem_det:
            add(4.0, "detectar", "Gerar miniaturas e candidatos de recorte" +
                (f" ({len(sem_det)} artigo(s) sem detecção)" if cat_arq.exists() else ""), "fazer",
                f"{leit('detectar_figuras.py')} {A}" + (f" --apenas {' '.join(sem_det)}" if cat_arq.exists() else ""))
        else:
            add(4.0, "detectar", "Candidatos de recorte gerados", "ok")
        if cat_arq.exists():
            if not aprovadas:
                add(4.1, "recortar", "Olhar, recortar e aprovar as figuras (nenhuma aprovada)", "fazer",
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
    aula4 = pasta / "04_aula"
    rot = aula4 / "roteiro.md"
    tem_leitura = bool(fichas) and not sem_ficha
    mapa = pasta / "00_mapa_evidencias.md"
    if mapa.exists():
        add(4.9, "mapa", "Mapa de evidências (00_mapa_evidencias.md)", "ok")
    if tem_leitura or rot.exists():
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
    deck_arq = aula4 / "deck.json"
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
            if pptx.exists():
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

    # Checagem não registrada, mas com trabalho já feito depois dela (pasta de outra sessão, aprovação só na
    # conversa): não trava; vira aviso para confirmar e registrar.
    for p in P:
        if p.estado == "usuario" and p.chave.startswith("checagem") and p.bloqueia_de is not None:
            if any(q.estado == "ok" and q.ordem >= p.bloqueia_de and not q.chave.startswith("checagem") for q in P):
                n = p.chave[-1]
                p.estado = "aviso"
                p.texto = f"Checagem {n} não registrada, mas o trabalho já passou dela"
                p.detalhe = "confirme com o usuário se ele aprovou; se sim, registre"
                p.comando = f"{C.cmd_proprio('situacao.py')} {A} --marcar {n} --nota \"aprovada antes (registro retroativo)\""
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
