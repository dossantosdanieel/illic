#!/usr/bin/env python3
"""Gera os materiais de apoio da aula a partir do deck.json e do banco de questões.

Uso:
    python materiais.py aulas/2026-11-lca/04_aula/deck.json
    python materiais.py deck.json --questoes questoes.json --saida 04_aula/

Gera, na pasta do deck (ou em --saida):
    enquetes.md        enquetes prontas para cadastrar no Google Meet antes da aula,
                       com gabarito para o professor e o roteiro das outras interações
    pre_pos_teste.md   questões de aplicação/análise em formato de colar no Google Forms,
                       com gabarito comentado e a referência de cada resposta
    resumo_aluno.md    1 a 2 páginas: objetivos, pontos-chave, algoritmo de decisão, referências

O banco de questões (padrão: questoes.json ao lado do deck.json) segue o esquema de
references/questoes.md. O script também confere a qualidade das questões e avisa.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _marca as M  # noqa: E402

NIVEIS_ALTOS = ("aplicacao", "aplicação", "analise", "análise", "avaliacao", "avaliação", "criacao", "criação")
RE_PROIBIDAS = re.compile(r"todas as (alternativas|anteriores)|nenhuma das (alternativas|anteriores)|"
                          r"\bsempre\b|\bnunca\b|\bexceto\b", re.I)
RE_NAO_CAIXA_ALTA = re.compile(r"\bNÃO\b")
PALAVRAS_RESUMO_MAX = 900
LIM_PERGUNTA_ENQUETE = 300    # caracteres; pergunta longa demais não se lê em 1 minuto
LIM_OPCAO_ENQUETE = 100


def limpo(t) -> str:
    return M.sem_marcacao("" if t is None else str(t)).strip()


def opcoes_de(obj) -> dict[str, str]:
    ops = obj.get("opcoes") or {}
    if isinstance(ops, list):
        ops = {chr(65 + i): t for i, t in enumerate(ops)}
    return {str(k).upper(): limpo(v) for k, v in ops.items()}


def linha_do_tempo(slides: list[dict]) -> list[int]:
    """Segundo em que cada slide começa (slides de apoio não contam)."""
    inicio, t = [], 0
    for s in slides:
        inicio.append(t)
        if not (s.get("apoio") or s.get("tipo") == "referencias"):
            t += int(s.get("tempo_s") or 0)
    return inicio


def texto_ref(ref: dict) -> str:
    t = limpo(ref.get("texto") or ref.get("curta") or ref.get("id")).rstrip(".")
    if ref.get("pmid"):
        t += f". PMID {ref['pmid']}"
    if ref.get("doi"):
        t += f". DOI {ref['doi']}"
    return t + "."


# ----------------------------------------------------------------------------- enquetes
def gerar_enquetes(deck: dict, avisos: list[str]) -> str:
    slides = [s for s in M.como_lista(deck.get("slides")) if isinstance(s, dict)]
    meta = deck.get("meta") or {}
    ini = linha_do_tempo(slides)
    out = [f"# Enquetes e interações — {limpo(meta.get('titulo'))}", "",
           "Entre na chamada do Google Meet 10 minutos antes, crie as enquetes em Atividades → Enquetes e use "
           "*Salvar* (não *Lançar*). Na aula, lance cada uma no slide indicado. Se a sua conta não tiver enquetes, "
           "use a votação por letra no chat em cascata (todo mundo escreve a letra e envia no 3). O gabarito é só para o professor: não comente as "
           "opções antes do voto.", ""]
    n_enq = 0
    revelacoes = {}
    for i, s in enumerate(slides):
        if s.get("tipo") == "enquete" and s.get("revela"):
            revelacoes.setdefault(limpo(s.get("pergunta"))[:60], (i + 1, str(s["revela"]).upper()))
    for i, s in enumerate(slides):
        inter = s.get("interacao") if isinstance(s.get("interacao"), dict) else None
        if not inter or inter.get("tipo") != "enquete":
            continue
        ops = opcoes_de(s)
        if not ops:
            avisos.append(f"slide {i + 1}: interação 'enquete' sem 'opcoes'; a enquete não foi gerada.")
            continue
        n_enq += 1
        perg = limpo(inter.get("pergunta") or s.get("pergunta") or s.get("titulo"))
        contexto = limpo(s.get("titulo")) if s.get("pergunta") else ""
        if not perg.rstrip().endswith("?") and contexto and contexto.lower() not in perg.lower():
            # a enquete precisa terminar em pergunta; o título do slide costuma ser a pergunta curta
            perg = f"{perg} {contexto.rstrip('.:')}" + ("" if contexto.endswith("?") else "?")
            contexto = ""
        if len(perg) > LIM_PERGUNTA_ENQUETE:
            avisos.append(f"enquete {n_enq} (slide {i + 1}): pergunta com {len(perg)} caracteres; encurte para ler em 1 minuto.")
        out.append(f"## Enquete {n_enq} · slide {i + 1} · aos {M.relogio(ini[i])}")
        out.append("")
        if contexto and contexto.lower() not in perg.lower():
            out.append(f"*No slide:* {contexto}")
            out.append("")
        out.append("**Pergunta (colar no Meet):**")
        out.append("")
        out.append("```text")
        out.append(perg)
        out.append("```")
        out.append("")
        out.append("**Opções (uma por campo, com a letra para bater com o slide):**")
        out.append("")
        out.append("```text")
        for L, t in ops.items():
            if len(t) > LIM_OPCAO_ENQUETE:
                avisos.append(f"enquete {n_enq}, opção {L}: {len(t)} caracteres; opção longa demais para ler no celular.")
            out.append(f"{L}) {t}")
        out.append("```")
        out.append("")
        gab = str(s.get("gabarito") or "").upper()
        rev = None
        for j in range(i + 1, len(slides)):
            sj = slides[j]
            if sj.get("tipo") == "enquete" and sj.get("revela") and opcoes_de(sj) == ops:
                rev = (j + 1, str(sj["revela"]).upper())
                break
        if s.get("sem_gabarito"):
            out.append("- **Gabarito:** enquete de opinião, sem resposta certa.")
        elif gab or rev:
            letra = gab or rev[1]
            out.append(f"- **Gabarito (só professor):** {letra}) {ops.get(letra, '?')}")
            if rev:
                out.append(f"- **Revelação:** slide {rev[0]}.")
        else:
            avisos.append(f"enquete {n_enq} (slide {i + 1}): sem 'gabarito' nem slide de revelação.")
        d = int(inter.get("duracao_s") or 60)
        out.append(f"- **Aberta por:** {M.tempo_extenso(d)}. Feche, mostre o resultado e chame uma pessoa de cada opção pelo nome.")
        out.append("")
    if n_enq == 0:
        out.append("*Esta aula não tem enquetes.*")
        out.append("")

    out.append("## Roteiro de todas as interações")
    out.append("")
    out.append("| Quando | Slide | Formato | O que a turma faz |")
    out.append("|---|---|---|---|")
    for i, s in enumerate(slides):
        inter = s.get("interacao") if isinstance(s.get("interacao"), dict) else None
        if not inter or inter.get("tipo") not in M.INTERACOES:
            continue
        quando = ini[i] + int(inter.get("inicio_s") or 0)
        o_que = limpo(inter.get("pedido") or s.get("instrucao") or s.get("entrega") or s.get("pergunta") or s.get("titulo"))
        if inter["tipo"] == "salas" and s.get("entrega") and not inter.get("pedido"):
            o_que = "Entrega: " + limpo(s["entrega"])
        out.append(f"| {M.relogio(quando)} | {i + 1} | {M.rotulo_interacao(inter)} | {o_que.replace('|', '/')} |")
    out.append("")
    out.append("## Antes de abrir a sala")
    out.append("")
    out.append("- Enquetes criadas e salvas no Meet, sem lançar.")
    if any((s.get("interacao") or {}).get("tipo") == "salas" for s in slides if isinstance(s.get("interacao"), dict)):
        out.append("- Salas temáticas configuradas com 3 pessoas por sala e tempo limite ligado.")
    out.append("- Cronômetro visível para você; chat aberto numa segunda tela ou com um colega acompanhando.")
    out.append("- Gravação ligada (a aula fica para a equipe).")
    out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------- pre/pos-teste
def conferir_questoes(qs: list[dict], refs: dict, avisos: list[str]) -> None:
    letras_certas = []
    certa_mais_longa = 0
    for n, q in enumerate(qs, 1):
        nome = f"questão {q.get('id') or n}"
        ops = opcoes_de(q)
        if len(ops) < 3 or len(ops) > 5:
            avisos.append(f"{nome}: {len(ops)} opções; use 4 (uma melhor resposta e três distratores plausíveis).")
        gab = str(q.get("gabarito") or "").upper()
        if gab not in ops:
            avisos.append(f"{nome}: o gabarito {gab!r} não está entre as opções.")
            continue
        letras_certas.append(gab)
        if ops and len(ops[gab]) == max(len(t) for t in ops.values()) and \
                len(ops[gab]) > 1.3 * sorted(len(t) for t in ops.values())[-2]:
            certa_mais_longa += 1
        if not limpo(q.get("cenario")):
            avisos.append(f"{nome}: sem 'cenario' clínico; questão sem caso mede memória, não decisão.")
        nivel = str(q.get("nivel") or "").lower()
        if nivel and not nivel.startswith(NIVEIS_ALTOS):
            avisos.append(f"{nome}: nível '{q.get('nivel')}'; o pré/pós-teste pede aplicação, análise ou avaliação.")
        if not limpo(q.get("comentario")):
            avisos.append(f"{nome}: sem 'comentario' (por que a certa é certa).")
        dis = q.get("distratores") or {}
        faltam = [L for L in ops if L != gab and not limpo(dis.get(L))]
        if faltam:
            avisos.append(f"{nome}: falta dizer que erro de raciocínio cada distrator representa ({', '.join(faltam)}).")
        r = q.get("referencia")
        if not r:
            avisos.append(f"{nome}: sem 'referencia' que sustente o gabarito.")
        else:
            for rr in M.como_lista(r):
                if str(rr) not in refs:
                    avisos.append(f"{nome}: a referência {rr!r} não está em 'referencias' do deck.")
        texto_todo = " ".join([limpo(q.get("pergunta"))] + list(ops.values()))
        m = RE_PROIBIDAS.search(texto_todo) or RE_NAO_CAIXA_ALTA.search(texto_todo)
        if m:
            avisos.append(f"{nome}: contém \"{m.group(0)}\"; essas construções dão pista ou confundem (ver references/questoes.md).")
    if len(letras_certas) >= 4:
        mais = max(set(letras_certas), key=letras_certas.count)
        if letras_certas.count(mais) / len(letras_certas) > 0.5:
            avisos.append(f"gabarito concentrado na letra {mais} ({letras_certas.count(mais)} de {len(letras_certas)}); distribua.")
    if qs and certa_mais_longa / len(qs) > 0.34:
        avisos.append(f"a resposta certa é a opção mais longa em {certa_mais_longa} de {len(qs)} questões: isso vira pista.")


def gerar_pre_pos(deck: dict, banco: dict, avisos: list[str]) -> str:
    meta = deck.get("meta") or {}
    refs = M.indice_referencias(deck)
    qs = [q for q in M.como_lista(banco.get("questoes")) if isinstance(q, dict)]
    conferir_questoes(qs, refs, avisos)
    objetivos = M.como_lista(meta.get("objetivos"))
    out = [f"# Pré e pós-teste — {limpo(meta.get('titulo'))}", "",
           "**Como usar no Google Forms.** Crie um formulário, vá em Configurações → *Transformar em teste*. "
           "Para cada questão, escolha *Múltipla escolha*, cole o enunciado no título da pergunta (ou na descrição, "
           "se for longo) e cole o bloco de opções **inteiro** no primeiro campo de opção: o Forms cria uma opção por "
           "linha. Marque a resposta certa em *Chave de resposta* e cole o comentário em *Adicionar feedback*. "
           "Ative *Ordem aleatória das opções* (as opções não têm letra por isso).", "",
           "**Pré-teste:** envie 1 a 3 dias antes da aula, sem nota e sem gabarito; serve para a turma chegar com a "
           "pergunta na cabeça e para você ver onde está o erro mais comum. **Pós-teste:** as mesmas questões, "
           "7 a 14 dias depois (o intervalo mede o que ficou, não o que foi decorado na hora); libere o feedback "
           "só depois do envio.", ""]
    if objetivos:
        out.append("Objetivos medidos:")
        for i, o in enumerate(objetivos, 1):
            out.append(f"{i}. {limpo(o)}")
        out.append("")
    if not qs:
        avisos.append("banco de questões vazio: o pré/pós-teste saiu sem questões.")
        out.append("*Sem questões no banco.*")
        return "\n".join(out)

    out.append("## Parte 1 — Questões (para colar)")
    out.append("")
    for n, q in enumerate(qs, 1):
        ops = opcoes_de(q)
        out.append(f"### Questão {n}")
        out.append("")
        enun = " ".join(x for x in (limpo(q.get("cenario")), limpo(q.get("pergunta"))) if x)
        out.append("Enunciado:")
        out.append("")
        out.append("```text")
        out.append(enun)
        out.append("```")
        out.append("")
        out.append("Opções:")
        out.append("")
        out.append("```text")
        for t in ops.values():
            out.append(t)
        out.append("```")
        out.append("")

    out.append("## Parte 2 — Gabarito comentado (professor e feedback do Forms)")
    out.append("")
    for n, q in enumerate(qs, 1):
        ops = opcoes_de(q)
        gab = str(q.get("gabarito") or "").upper()
        obj = q.get("objetivo")
        cab = f"### Questão {n}"
        det = []
        if q.get("nivel"):
            det.append(f"nível: {q['nivel']}")
        if obj:
            det.append(f"objetivo {obj}")
        if det:
            cab += " · " + " · ".join(det)
        out.append(cab)
        out.append("")
        out.append(f"**Resposta:** {ops.get(gab, '?')}")
        out.append("")
        if limpo(q.get("comentario")):
            out.append(limpo(q["comentario"]))
            out.append("")
        dis = q.get("distratores") or {}
        for L, t in ops.items():
            if L == gab or not limpo(dis.get(L)):
                continue
            out.append(f"- *{t}* — {limpo(dis[L])}")
        rs = [refs[str(r)] for r in M.como_lista(q.get("referencia")) if str(r) in refs]
        if rs:
            out.append("")
            out.append("Referência: " + "; ".join(texto_ref(r) for r in rs))
        out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------- resumo do aluno
def gerar_resumo(deck: dict, avisos: list[str]) -> str:
    meta = deck.get("meta") or {}
    slides = [s for s in M.como_lista(deck.get("slides")) if isinstance(s, dict)]
    refs = M.indice_referencias(deck)
    res = meta.get("resumo") or {}
    out = [f"# {limpo(meta.get('titulo'))}", ""]
    linha = " · ".join(x for x in (limpo(meta.get("autor")), "Boost Education",
                                    f"aula de {meta['duracao_alvo_min']} min" if meta.get("duracao_alvo_min") else "") if x)
    out.append(f"*{linha}*")
    out.append("")
    if meta.get("objetivos"):
        out.append("## Ao fim da aula, você deve conseguir")
        out.append("")
        for o in M.como_lista(meta["objetivos"]):
            out.append(f"- {limpo(o)}")
        out.append("")
    pontos = M.como_lista(res.get("pontos_chave"))
    if not pontos:
        for s in slides:
            if s.get("tipo") == "sintese":
                for p in M.como_lista(s.get("pontos")):
                    if isinstance(p, dict):
                        pontos.append(f"**{limpo(p.get('titulo'))}.** {limpo(p.get('texto'))}".strip())
                    else:
                        pontos.append(limpo(p))
        if pontos:
            avisos.append("meta.resumo.pontos_chave vazio: o resumo usou os pontos do slide de síntese. "
                          "Escreva pontos com os números e as fontes (ver references/deck-json.md).")
    if pontos:
        out.append("## Pontos-chave")
        out.append("")
        for i, p in enumerate(pontos, 1):
            out.append(f"{i}. {p if '**' in str(p) else limpo(p)}")
        out.append("")
    alg = M.como_lista(res.get("algoritmo"))
    if alg:
        out.append("## Algoritmo de decisão")
        out.append("")
        for i, p in enumerate(alg, 1):
            out.append(f"{i}. {limpo(p)}")
        out.append("")
    else:
        avisos.append("meta.resumo.algoritmo vazio: o resumo do aluno saiu sem o algoritmo de decisão.")
    prat = M.como_lista(res.get("para_praticar"))
    if prat:
        out.append("## Para praticar nesta semana")
        out.append("")
        for p in prat:
            out.append(f"- {limpo(p)}")
        out.append("")
    props = M.como_lista(meta.get("propostas_clinicas"))
    if props:
        out.append("## O que é proposta clínica (sem ensaio que teste)")
        out.append("")
        for p in props:
            out.append(f"- {limpo(p)[0:1].upper() + limpo(p)[1:]}.".replace("..", "."))
        out.append("")
    if refs:
        out.append("## Referências")
        out.append("")
        for r in sorted(refs.values(), key=lambda x: limpo(x.get("texto") or x.get("id")).lower()):
            out.append(f"- {texto_ref(r)}")
        out.append("")
    if meta.get("caso_ficticio"):
        out.append("*O paciente do caso e seus dados são fictícios.*")
        out.append("")
    txt = "\n".join(out)
    n = len(re.findall(r"\w+", M.sem_marcacao(txt)))
    if n > PALAVRAS_RESUMO_MAX:
        avisos.append(f"resumo do aluno com {n} palavras: passa de 2 páginas. Corte pontos-chave ou referências.")
    return txt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gera enquetes.md, pre_pos_teste.md e resumo_aluno.md a partir do deck.json.")
    ap.add_argument("deck", help="caminho do deck.json")
    ap.add_argument("--questoes", help="banco de questões (padrão: questoes.json ao lado do deck.json)")
    ap.add_argument("--saida", help="pasta de saída (padrão: a pasta do deck.json)")
    a = ap.parse_args(argv)

    cam = Path(a.deck).expanduser().resolve()
    deck = M.carregar_json(cam)
    if not isinstance(deck, dict):
        M.sair("o deck.json precisa ser um objeto com 'meta', 'referencias' e 'slides'.")
    saida = Path(a.saida).expanduser().resolve() if a.saida else cam.parent
    saida.mkdir(parents=True, exist_ok=True)
    cam_q = Path(a.questoes).expanduser().resolve() if a.questoes else cam.parent / "questoes.json"
    banco = {}
    if cam_q.is_file():
        banco = M.carregar_json(cam_q)
        if isinstance(banco, list):
            banco = {"questoes": banco}
    avisos: list[str] = []
    if not banco:
        avisos.append(f"banco de questões não encontrado ({cam_q}); o pré/pós-teste saiu vazio.")

    arquivos = {
        "enquetes.md": gerar_enquetes(deck, avisos),
        "pre_pos_teste.md": gerar_pre_pos(deck, banco, avisos),
        "resumo_aluno.md": gerar_resumo(deck, avisos),
    }
    print("== Materiais de apoio ==")
    for nome, txt in arquivos.items():
        p = saida / nome
        p.write_text(txt.rstrip() + "\n", encoding="utf-8")
        print(f"  {p}  ({len(re.findall(r'[0-9A-Za-zÀ-ÿ]+', txt))} palavras)")
    if avisos:
        print(f"\nAVISOS ({len(avisos)}):")
        for x in avisos:
            print(f"  ! {x}")
    else:
        print("\nNenhum aviso.")
    print("Releia os três arquivos antes de enviar: o script confere a forma, não o conteúdo clínico.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
