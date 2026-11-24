#!/usr/bin/env python3
"""Gera 04_aula/entrega.md: arquivos entregues, tabela de evidências, figuras e licenças, e o que não foi conferido.

Só lê arquivos da pasta da aula; não usa rede. Não inventa: o que não estiver nos arquivos sai como "sem registro".
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402
import situacao as SIT  # noqa: E402

LIVRES = {"cc-by", "cc0", "dominio publico", "domínio público"}


def celula(x) -> str:
    s = "" if x is None else str(x)
    return s.replace("|", "/").replace("\n", " ").strip() or "—"


def texto_lido(ficha: Path) -> str:
    if not ficha.exists():
        return "sem ficha"
    t = ficha.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Texto lido:\s*(.+)", t)
    if not m:
        return "ficha sem o campo 'Texto lido'"
    val = m.group(1).strip()
    if "|" in val and "complet" in val and "resumo" in val:
        return "campo não preenchido"
    val = re.sub(r"\(`?02_artigos/texto/[^)]*`?\)", "", val).strip()
    return val[:80]


def secoes(md: str) -> dict[str, str]:
    partes: dict[str, str] = {}
    atual = None
    for linha in md.splitlines():
        m = re.match(r"^##\s+(.*)$", linha)
        if m:
            atual = m.group(1).strip()
            partes[atual] = ""
        elif atual:
            partes[atual] += linha + "\n"
    return partes


def refs_por_slide(deck: dict) -> tuple[dict[str, list[int]], list[tuple[int, str]]]:
    usos: dict[str, list[int]] = {}
    figuras: list[tuple[int, str]] = []
    for n, s in enumerate(deck.get("slides") or [], 1):
        if not isinstance(s, dict):
            continue
        fontes = s.get("fonte") or []
        if isinstance(fontes, str):
            fontes = [fontes]
        for f in fontes:
            usos.setdefault(str(f), []).append(n)
        fig = s.get("figura")
        figs = fig if isinstance(fig, list) else [fig]
        for f in figs:
            if isinstance(f, dict):
                ident = f.get("id") or f.get("arquivo")
                if ident:
                    figuras.append((n, str(ident)))
                if f.get("ref"):
                    usos.setdefault(str(f["ref"]), []).append(n)
    return usos, figuras


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Gera 04_aula/entrega.md com os arquivos da entrega, a tabela de evidências, as figuras com licença "
                    "e a lista do que não foi conferido. Rode depois de montar o deck e escrever verificacao.md.",
        epilog="exemplo:\n  python3 relatorio_final.py aulas/2026-11-lca-retorno-esporte",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--saida", help="arquivo de saída (padrão: 04_aula/entrega.md)")
    ap.add_argument("--imprimir", action="store_true", help="mostra o relatório em vez de gravar")
    a = ap.parse_args()
    pasta = Path(a.aula).expanduser()
    if not pasta.is_dir():
        print(f"ERRO: pasta não encontrada: {pasta}", file=sys.stderr)
        return 2
    aula4 = pasta / "04_aula"
    B = pasta / "01_busca"
    art = pasta / "02_artigos"
    S = SIT.analisar(pasta, validar=True)
    deck = C.ler_json(aula4 / "deck.json", {}) or {}
    if "__erro__" in deck:
        deck = {}
    meta = deck.get("meta") or {}
    refs = {str(r.get("id")): r for r in deck.get("referencias") or [] if isinstance(r, dict) and r.get("id")}
    usos, figs_deck = refs_por_slide(deck)
    sel = C.lista_de(C.ler_json(B / "selecionados.json", []), "selecionados", "registros")
    manifest = {str(m.get("chave")): m for m in C.lista_de(C.ler_json(art / "manifest.json", []), "artigos")
                if m.get("chave")}
    catalogo = {str(e.get("id")): e for e in C.lista_de(C.ler_json(pasta / "03_figuras" / "catalogo.json", []), "figuras")
                if e.get("id")}
    avisos_gerais: list[str] = []

    L: list[str] = []
    titulo = re.sub(r"\*\*", "", str(meta.get("titulo") or S.tema))
    L += [f"# Entrega · {titulo}", "",
          f"Gerado em {C.hoje()} por `relatorio_final.py` a partir dos arquivos da pasta `{pasta.name}`. "
          "Nada aqui foi digitado à mão: o que não estiver nos arquivos aparece como \"sem registro\".", ""]
    v = S.resumo.get("validacao") or {}
    if v:
        L.append(f"**Deck:** {v.get('slides')} slides · {v.get('duracao')} · validação: "
                 f"{v.get('erros')} erro(s), {v.get('avisos')} aviso(s).")
    ch = ", ".join(f"{n} {'feita' if x else 'ABERTA'}" for n, x in S.checagens.items())
    L += [f"**Modo:** {S.modo} · **Checagens:** {ch}.", ""]

    # ------------------------------------------------------------ arquivos
    pptx = Path(S.resumo.get("pptx") or aula4 / "aula.pptx")
    itens = [
        ("Apresentação (.pptx)", pptx),
        ("Folha(s) de contato do deck", sorted((aula4 / "previa").glob("folha-*.png"))),
        ("Folha de contato das figuras", pasta / "03_figuras" / "folha_contato.png"),
        ("Enquetes para o Meet", aula4 / "enquetes.md"),
        ("Pré e pós-teste (Forms)", aula4 / "pre_pos_teste.md"),
        ("Resumo para o aluno", aula4 / "resumo_aluno.md"),
        ("Roteiro com linha do tempo", aula4 / "roteiro.md"),
        ("Verificação (o que foi conferido)", aula4 / "verificacao.md"),
        ("Estratégia de busca", B / "estrategia.md"),
        ("Planilha de triagem e fluxo", B / "triagem.xlsx"),
        ("PDFs que faltam", art / "pendentes.md"),
    ]
    L += ["## Arquivos", "", "| O quê | Caminho | Situação |", "|---|---|---|"]
    for nome, alvo in itens:
        if isinstance(alvo, list):
            ok = bool(alvo)
            cam = ", ".join(f"`{p.relative_to(pasta)}`" for p in alvo) if alvo else "`04_aula/previa/folha-*.png`"
        else:
            ok = alvo.exists()
            cam = f"`{alvo.relative_to(pasta) if alvo.is_relative_to(pasta) else alvo}`"
        L.append(f"| {nome} | {cam} | {'ok' if ok else 'FALTA'} |")
        if not ok and nome in ("Apresentação (.pptx)", "Verificação (o que foi conferido)", "Enquetes para o Meet",
                               "Pré e pós-teste (Forms)", "Resumo para o aluno"):
            avisos_gerais.append(f"falta {nome.lower()}")
    L.append("")

    # ------------------------------------------------------------ tabela de evidências
    L += ["## Tabela de evidências", "",
          "Artigos selecionados para a aula. \"Texto lido\" vem da ficha de leitura; \"Na aula\" são os slides do "
          "deck.json que citam o artigo no rodapé ou na figura; \"Conferido\" é o que o deck declara nas referências.", "",
          "| Chave | Desenho | Ano | Revista | Papel | PDF | Licença | Texto lido | Na aula (slides) | Conferido |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    chaves = [str(r.get("chave")) for r in sel if r.get("chave")] or list(manifest)
    por_sel = {str(r.get("chave")): r for r in sel}
    for k in chaves:
        r = por_sel.get(k, {})
        m = manifest.get(k, {})
        pdf = f"ok ({m.get('origem')})" if m.get("status") == "ok" else ("pendente" if m else "sem registro")
        slides = ", ".join(map(str, sorted(set(usos.get(k, []))))) or "—"
        conf = (refs.get(k) or {}).get("conferido") or ("não citado no deck" if k not in refs else "sem registro")
        L.append("| " + " | ".join(celula(x) for x in (
            k, r.get("desenho"), r.get("ano") or m.get("ano"), r.get("revista") or m.get("revista"), r.get("papel"),
            pdf, m.get("licenca") or r.get("licenca") or "desconhecida", texto_lido(art / "leitura" / f"{k}.md"),
            slides, conf)) + " |")
    extras = [k for k in refs if k not in chaves]
    if extras:
        L += ["", f"Referências do deck fora de `selecionados.json`: {', '.join(extras)} "
                  "(entraram depois da triagem; confira se estão em verificacao.md)."]
    L.append("")

    # ------------------------------------------------------------ figuras
    L += ["## Figuras usadas no deck", ""]
    restritas = []
    if figs_deck:
        L += ["| Slide | Figura | Licença | Aprovada | Citação |", "|---|---|---|---|---|"]
        for n, ident in figs_deck:
            e = catalogo.get(ident, {})
            lic = str(e.get("licenca") or "desconhecida")
            if lic.lower() not in LIVRES:
                restritas.append(f"{ident} (slide {n}, {lic})")
            L.append("| " + " | ".join(celula(x) for x in (
                n, ident, lic, "sim" if e.get("aprovada") is True else ("NÃO" if e else "fora do catálogo"),
                e.get("citacao"))) + " |")
    else:
        L.append("Nenhuma figura de artigo no deck.json.")
    L += ["", "**Figuras de artigos sem licença CC BY (direitos reservados, NC, ND ou desconhecida):** " +
          ("; ".join(restritas) if restritas else "nenhuma") + ".",
          "Uso atual: aula gravada para a equipe, com citação completa. Se a aula for vendida fora da empresa, refazer "
          "essas figuras como gráfico próprio \"Adaptado de\" ou pedir permissão ao editor.", ""]

    # ------------------------------------------------------------ não conferido
    L += ["## O que não foi conferido", ""]
    nao: list[str] = []
    pend = [k for k in chaves if manifest.get(k, {}).get("status") not in ("ok",)]
    if pend:
        nao.append(f"Sem PDF (só resumo ou nada): {', '.join(pend)}. Lista para baixar em `02_artigos/pendentes.md`.")
    so_res = [k for k in chaves if (art / "leitura" / f"{k}.md").exists()
              and "complet" not in texto_lido(art / "leitura" / f"{k}.md").lower()]
    if so_res:
        nao.append(f"Fichas lidas só no resumo ou em parte: {', '.join(so_res)}.")
    sem_ficha = [k for k in chaves if not (art / "leitura" / f"{k}.md").exists()]
    if sem_ficha:
        nao.append(f"Sem ficha de leitura: {', '.join(sem_ficha)}.")
    ref_nao = [f"{k} ({r.get('conferido') or 'sem campo conferido'})" for k, r in refs.items()
               if str(r.get("conferido") or "").lower() != "texto completo"]
    if ref_nao:
        nao.append(f"Referências do deck não conferidas no texto completo: {', '.join(ref_nao)}.")
    if not (B / "brutos" / "scopus.json").exists() and (B / "conceitos.json").exists():
        nao.append("A busca não incluiu o Scopus (exportação não importada).")
    abertas = [str(n) for n, x in S.checagens.items() if not x]
    if abertas:
        nao.append(f"Checagens com o usuário não registradas: {', '.join(abertas)}"
                   + (" (modo sem parar: peça a revisão agora)." if S.modo == "sem parar" else "."))
    for p in S.passos:
        if p.estado in ("fazer", "aviso") and p.etapa >= 3 and p.chave not in ("entrega", "licencas"):
            nao.append(f"Etapa {p.etapa} pendente: {p.texto}" + (f" ({p.detalhe})" if p.detalhe else "") + ".")
    if avisos_gerais:
        nao.append("Arquivos que faltam: " + "; ".join(avisos_gerais) + ".")
    L += [f"- {x}" for x in nao] or ["- Nada pendente nos arquivos."]
    ver = aula4 / "verificacao.md"
    if ver.exists():
        sec = secoes(ver.read_text(encoding="utf-8", errors="replace"))
        for nome, corpo in sec.items():
            if re.search(r"resumo|proposta|pend[eê]ncia", nome, re.I) and corpo.strip():
                L += ["", f"### Da verificacao.md: {nome}", "", corpo.strip()]
    else:
        L += ["", "Sem `04_aula/verificacao.md`: a lista acima é só o que os arquivos mostram."]
    L.append("")

    texto = "\n".join(L)
    if a.imprimir:
        print(texto)
        return 0
    saida = Path(a.saida) if a.saida else aula4 / "entrega.md"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(texto, encoding="utf-8")
    print(f"Relatório de entrega: {saida}")
    print(f"  artigos na tabela: {len(chaves)} · figuras no deck: {len(figs_deck)} · sem CC BY: {len(restritas)} · "
          f"itens não conferidos: {len(nao)}")
    if avisos_gerais:
        print("AVISO: " + "; ".join(avisos_gerais))
    return 0


if __name__ == "__main__":
    sys.exit(main())
