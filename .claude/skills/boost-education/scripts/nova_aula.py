#!/usr/bin/env python3
"""Cria a pasta de uma aula Boost (contrato de pastas), o 00_briefing.md e o 00_andamento.md."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402

SUBPASTAS = {
    "01_busca": ["01_busca/brutos"],
    "02_artigos": ["02_artigos/pdf", "02_artigos/manual", "02_artigos/texto", "02_artigos/leitura"],
    "03_figuras": ["03_figuras"],
}

EXEMPLOS = """
exemplos:
  python3 nova_aula.py --tema "Retorno ao esporte após reconstrução do LCA" --recorte topo_mecanismos
  python3 nova_aula.py --tema "Tendinopatia patelar: dose de carga" --slug tendinopatia-patelar-carga \\
      --objetivo "Prescrever carga isométrica e isotônica com dose explícita" \\
      --p "atletas com tendinopatia patelar" --i "exercício de carga progressiva" --o "VISA-P, dor" \\
      --artigo "Breda 2021 (BJSM)" --artigo 10.1136/bjsports-2020-103403
  # aula 2 de uma trilha, usando a busca e os artigos da aula 1 e recuperando a aula 1 na abertura
  python3 nova_aula.py --tema "Cotovelo lateral: reabilitação com dose" --trilha aulas/trilha-cotovelo.md \\
      --posicao "2 de 3" --aula-anterior aulas/2026-11-cotovelo-lateral-1 --compartilhar-de aulas/2026-11-cotovelo-lateral-1
"""


def argumentos() -> argparse.Namespace:
    prefs = C.ler_preferencias()
    ap = argparse.ArgumentParser(
        description="Cria aulas/<AAAA-MM>-<slug>/ com as subpastas do contrato, o 00_briefing.md (tema, público, "
                    "objetivos, PICO, recorte) e o 00_andamento.md (pontos de checagem). Não sobrescreve nada que já exista.",
        epilog=EXEMPLOS, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tema", required=True, help="tema da aula, em português (vira o título do briefing)")
    ap.add_argument("--slug", help="nome curto da pasta, sem acento (padrão: derivado do tema)")
    ap.add_argument("--mes", help="AAAA-MM da aula (padrão: mês atual)")
    ap.add_argument("--raiz", help="pasta que guarda as aulas (padrão: $BOOST_AULAS ou ./aulas)")
    ap.add_argument("--publico", default=C.pref(prefs, "Público", "Fisioterapeutas da equipe ILLIC, em níveis diferentes."),
                    help="quem assiste (padrão: references/preferencias.md)")
    ap.add_argument("--nivel", default=C.pref(prefs, "Níveis", "Uma única aula em camadas; o nível técnico não baixa."),
                    help="como tratar níveis diferentes (padrão: aula única em camadas)")
    ap.add_argument("--recorte", choices=C.RECORTES, default="topo_mecanismos",
                    help="recorte de evidência (padrão: topo_mecanismos)")
    ap.add_argument("--apresentador", default=C.pref(prefs, "Apresentador", "Daniel Santos").split(",")[0].strip(),
                    help="quem apresenta (padrão: Daniel Santos)")
    ap.add_argument("--objetivo", action="append", default=[],
                    help="objetivo de aprendizagem (repita; verbo de aplicação, análise ou avaliação)")
    ap.add_argument("--p", dest="P", help="população / problema")
    ap.add_argument("--i", dest="I", help="intervenção, exposição ou teste")
    ap.add_argument("--c", dest="C", help="comparador")
    ap.add_argument("--o", dest="O", help="desfecho")
    ap.add_argument("--artigo", action="append", default=[],
                    help="artigo que o usuário já quer na aula: PMID, DOI ou 'Autor ano (revista)' (repita)")
    ap.add_argument("--material-base", help="aula, apostila ou slides já existentes que servem de base")
    ap.add_argument("--formatos", default="enquete,chat_cascata,salas,mao_camera,chat",
                    help="interações disponíveis na plataforma, separadas por vírgula "
                         f"(nomes canônicos: {', '.join(C.INTERACOES)})")
    ap.add_argument("--plataforma", default=C.pref(prefs, "Plataforma", "Google Meet").split(":")[0].strip(),
                    help="plataforma da aula ao vivo (padrão: Google Meet)")
    ap.add_argument("--uso", choices=("equipe", "venda"), default="equipe",
                    help="equipe = gravada para a equipe (padrão); venda = vendida fora da empresa")
    ap.add_argument("--trilha", help="arquivo do plano da trilha (criado a partir do modelo se não existir)")
    ap.add_argument("--posicao", help="posição na trilha, ex.: '2 de 3'")
    ap.add_argument("--aula-anterior", action="append", default=[],
                    help="pasta de aula anterior da trilha, para a recuperação espaçada na abertura (repita)")
    ap.add_argument("--compartilhar-de", metavar="PASTA",
                    help="usa 01_busca, 02_artigos e 03_figuras de outra aula por link simbólico")
    ap.add_argument("--sem-parar", action="store_true",
                    help="o usuário pediu para seguir sem as checagens (só acesso aberto, pendências registradas)")
    ap.add_argument("--forcar-briefing", action="store_true",
                    help="reescreve 00_briefing.md existente (o antigo vira 00_briefing.anterior.md)")
    ap.add_argument("--simular", action="store_true", help="mostra o que faria, sem gravar")
    return ap.parse_args()


def interacoes_validas(texto: str) -> tuple[list[str], list[str]]:
    itens = [t.strip() for t in re.split(r"[,;]", texto or "") if t.strip()]
    ok = [t for t in itens if t in C.INTERACOES]
    ruins = [t for t in itens if t not in C.INTERACOES]
    return ok, ruins


def recuperar_anterior(pasta: Path) -> dict:
    """Objetivos, pontos-chave e bilhete de saída de uma aula anterior (deck.json; senão briefing)."""
    info = {"pasta": str(pasta), "titulo": pasta.name, "objetivos": [], "pontos": [], "bilhete": None, "fonte": None}
    deck = C.ler_json(pasta / "04_aula" / "deck.json")
    if isinstance(deck, dict) and "__erro__" not in deck:
        meta = deck.get("meta") or {}
        info["titulo"] = re.sub(r"\*\*", "", str(meta.get("titulo") or pasta.name))
        info["objetivos"] = [str(o) for o in meta.get("objetivos") or []]
        info["pontos"] = [str(p) for p in (meta.get("resumo") or {}).get("pontos_chave") or []]
        for s in reversed(deck.get("slides") or []):
            inter = s.get("interacao") if isinstance(s, dict) else None
            if isinstance(inter, dict) and inter.get("tipo") == "chat":
                info["bilhete"] = re.sub(r"\*\*", "", str(s.get("titulo") or inter.get("pedido") or "")).strip() or None
                break
        info["fonte"] = "04_aula/deck.json"
        return info
    brief = pasta / "00_briefing.md"
    if brief.exists():
        texto = brief.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s*(.+)$", texto, re.M)
        if m:
            info["titulo"] = m.group(1).strip()
        sec = re.search(r"^##\s*Objetivos.*?$(.*?)(?=^##\s)", texto, re.M | re.S)
        if sec:
            info["objetivos"] = [re.sub(r"^\s*(\d+\.|-)\s*", "", l).strip()
                                 for l in sec.group(1).splitlines()
                                 if re.match(r"^\s*(\d+\.|-)\s+\S", l) and C.MARCA_PREENCHER not in l]
        info["fonte"] = "00_briefing.md (a aula anterior ainda não tem deck.json)"
    return info


def montar_briefing(a: argparse.Namespace, pasta: Path, raiz: Path, anteriores: list[dict], formatos: list[str]) -> str:
    P = C.MARCA_PREENCHER
    prefs = C.ler_preferencias()
    duracao = C.pref(prefs, "Duração", "30 a 35 minutos. Acima de 35 é erro.")
    linhas = [f"# Briefing · {a.tema}", ""]
    linhas.append(f"**Pasta:** `{pasta.name}` · criada em {C.hoje()} por `nova_aula.py` (skill boost-education).")
    if a.trilha:
        pos = f" (aula {a.posicao})" if a.posicao else ""
        linhas.append(f"**Trilha:**{pos} plano em `{a.trilha}`.")
    linhas += [
        f"**Público:** {a.publico}",
        f"**Níveis:** {a.nivel}",
        f"**Formato:** {a.plataforma}, {duracao.split('.')[0].strip()} (alvo 32 min). Nível técnico alto, aprendizagem ativa. "
        "Marca illic ACADEMY · BOOST Education.",
        f"**Apresentador:** {a.apresentador}.",
    ]
    if a.uso == "equipe":
        linhas.append("**Uso:** gravada e compartilhada com a equipe, sem venda externa. Figuras recortadas com citação; "
                      "licença no catálogo; o relatório final lista as de direitos reservados.")
    else:
        linhas.append("**Uso:** VENDIDA fora da empresa. Figura de artigo com direitos reservados, NC ou ND não entra "
                      "recortada: refazer como gráfico próprio \"Adaptado de\" ou pedir permissão ao editor. "
                      "Material de divulgação passa pela skill etica-fisioterapia.")
    rot = [f"{C.INTERACOES[f]}" for f in formatos]
    linhas.append(f"**Interações disponíveis:** {'; '.join(rot) if rot else P}.")
    if a.compartilhar_de:
        linhas.append(f"**Busca, artigos e figuras:** compartilhados com `{Path(a.compartilhar_de).name}` "
                      "(01_busca, 02_artigos e 03_figuras são links simbólicos).")
    linhas += ["", "## Objetivos de aprendizagem (2 ou 3; o aluno, ao fim, consegue)", ""]
    objs = a.objetivo or [f"{P}: verbo de aplicação, análise ou avaliação + objeto + condição + critério"] * 2
    linhas += [f"{n}. {o}" for n, o in enumerate(objs, 1)]
    linhas += ["", "Pelo menos um objetivo exige raciocínio quantitativo (tamanho de efeito com IC, NNT, DMCI, "
               "certeza, sensibilidade e especificidade).", ""]
    linhas += ["## Pergunta clínica (PICO)", ""]
    for rot_, val in (("P", a.P), ("I", a.I), ("C", a.C), ("O", a.O)):
        linhas.append(f"- **{rot_}:** {val or P}")
    linhas += ["", "Comparador e desfecho ficam fora da string de busca (muitos resumos não os citam) e viram "
               "critério de triagem.", ""]
    linhas += ["## Recorte de evidência", "",
               f"`{a.recorte}`: {C.DESCRICAO_RECORTE[a.recorte]}. Vai para `\"recorte\"` em `01_busca/conceitos.json`.", ""]
    linhas += ["## Artigos que o usuário já quer na aula", ""]
    linhas += [f"- {x}" for x in a.artigo] if a.artigo else ["- nenhum informado (entram como sentinelas se aparecerem)"]
    linhas += ["", "## Material de base", "", f"- {a.material_base}" if a.material_base else "- nenhum", ""]
    if anteriores:
        linhas += ["## Recuperação espaçada na abertura", "",
                   "A abertura desta aula começa com 1 ou 2 perguntas de recuperação sobre a aula anterior, "
                   "respondidas de memória (enquete ou chat em cascata), antes do caso novo. Não é revisão expositiva: "
                   "a turma tenta lembrar, depois confere. Use as respostas mais fracas do bilhete de saída anterior.", ""]
        for an in anteriores:
            linhas.append(f"### {an['titulo']}")
            linhas.append(f"Pasta: `{Path(an['pasta']).name}` · lido de {an['fonte'] or 'nada (aula anterior sem briefing nem deck)'}")
            if an["bilhete"]:
                linhas.append(f"- Bilhete de saída: {an['bilhete']}")
            for o in an["objetivos"][:3]:
                linhas.append(f"- Objetivo: {o}")
            for p in an["pontos"][:4]:
                linhas.append(f"- Ponto-chave: {p}")
            if not (an["objetivos"] or an["pontos"] or an["bilhete"]):
                linhas.append(f"- {P}: o que a turma precisa lembrar da aula anterior")
            linhas.append("")
    linhas += ["## Decisões e perguntas em aberto", "",
               f"- {C.hoje()} · briefing criado. Campos com \"{P}\" ainda dependem do usuário ou da busca.", ""]
    return "\n".join(linhas)


def criar_link(destino: Path, alvo: Path, simular: bool) -> str:
    rel = os.path.relpath(alvo.resolve(), destino.parent.resolve())
    if not simular:
        destino.symlink_to(rel, target_is_directory=True)
    return f"{destino.name} -> {rel}"


def main() -> int:
    a = argumentos()
    mes = a.mes or dt.date.today().strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-\d{2}", mes):
        print(f"ERRO: --mes deve ser AAAA-MM (recebi {mes!r}).", file=sys.stderr)
        return 2
    slug = C.fazer_slug(a.slug or a.tema)
    raiz = Path(a.raiz or os.environ.get("BOOST_AULAS") or "aulas").expanduser()
    pasta = raiz / f"{mes}-{slug}"
    formatos, ruins = interacoes_validas(a.formatos)
    avisos: list[str] = []
    if ruins:
        avisos.append(f"interações desconhecidas ignoradas: {', '.join(ruins)} (use {', '.join(C.INTERACOES)})")
    if len(formatos) < 3:
        avisos.append("menos de 3 formatos de interação: o validador da aula exige 3 formatos e o bilhete de saída (chat)")
    compartilhar = Path(a.compartilhar_de).expanduser() if a.compartilhar_de else None
    if compartilhar and not compartilhar.is_dir():
        print(f"ERRO: --compartilhar-de não encontrado: {compartilhar}", file=sys.stderr)
        return 2
    anteriores = []
    for ant in a.aula_anterior:
        p = Path(ant).expanduser()
        if not p.is_dir():
            avisos.append(f"aula anterior não encontrada: {p} (seção de recuperação fica para preencher)")
            anteriores.append({"pasta": str(p), "titulo": p.name, "objetivos": [], "pontos": [], "bilhete": None,
                               "fonte": None})
        else:
            anteriores.append(recuperar_anterior(p))

    feitos: list[str] = []
    if not a.simular:
        pasta.mkdir(parents=True, exist_ok=True)
    for grupo, subs in SUBPASTAS.items():
        alvo = pasta / grupo
        if compartilhar:
            origem = compartilhar / grupo
            if alvo.exists() or alvo.is_symlink():
                feitos.append(f"{grupo}: já existe, mantido")
                continue
            if not a.simular:
                for s in subs:
                    (compartilhar / s).mkdir(parents=True, exist_ok=True)
            feitos.append("link " + criar_link(alvo, origem, a.simular))
            continue
        for s in subs:
            if not (pasta / s).exists():
                feitos.append(f"pasta {s}/")
                if not a.simular:
                    (pasta / s).mkdir(parents=True, exist_ok=True)
    if not (pasta / "04_aula").exists():
        feitos.append("pasta 04_aula/")
        if not a.simular:
            (pasta / "04_aula").mkdir(parents=True, exist_ok=True)

    brief = pasta / "00_briefing.md"
    texto = montar_briefing(a, pasta, raiz, anteriores, formatos)
    if brief.exists() and not a.forcar_briefing:
        feitos.append("00_briefing.md: já existe, mantido (use --forcar-briefing para reescrever)")
    else:
        if brief.exists() and not a.simular:
            brief.replace(pasta / "00_briefing.anterior.md")
            feitos.append("00_briefing.md anterior guardado como 00_briefing.anterior.md")
        if not a.simular:
            brief.write_text(texto, encoding="utf-8")
        feitos.append("00_briefing.md")
    andam = pasta / "00_andamento.md"
    if andam.exists():
        if a.sem_parar and not a.simular:
            C.atualizar_andamento(pasta, modo="sem parar", nota="usuário pediu para seguir sem parar")
            feitos.append("00_andamento.md: já existia; modo trocado para 'sem parar'")
        else:
            feitos.append("00_andamento.md: já existe, mantido")
    else:
        if not a.simular:
            andam.write_text(C.texto_andamento(a.tema, a.sem_parar), encoding="utf-8")
        feitos.append("00_andamento.md" + (" (modo sem parar)" if a.sem_parar else ""))

    if a.trilha:
        trilha = Path(a.trilha).expanduser()
        if not trilha.exists():
            modelo = C.PASTA_SKILL / "assets" / "trilha_modelo.md"
            if not a.simular:
                trilha.parent.mkdir(parents=True, exist_ok=True)
                corpo = modelo.read_text(encoding="utf-8") if modelo.exists() else "# Trilha\n"
                trilha.write_text(corpo.replace("<nome da trilha>", a.tema), encoding="utf-8")
            feitos.append(f"plano da trilha criado do modelo: {trilha}")
        else:
            feitos.append(f"plano da trilha: {trilha} (existente; acrescente esta aula nele)")

    print(("SIMULAÇÃO: nada foi gravado.\n" if a.simular else "") + f"Aula: {pasta}")
    for f in feitos:
        print(f"  · {f}")
    faltam = [n for n, v in (("objetivos", a.objetivo), ("P", a.P), ("I", a.I), ("C", a.C), ("O", a.O)) if not v]
    if faltam:
        print(f"Campos do briefing ainda a preencher: {', '.join(faltam)} "
              f"(procure \"{C.MARCA_PREENCHER}\" em 00_briefing.md).")
    for av in avisos:
        print(f"AVISO: {av}")
    print(f"Próximo passo: {C.cmd_proprio('situacao.py')} {pasta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
