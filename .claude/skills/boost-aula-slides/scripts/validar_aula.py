#!/usr/bin/env python3
"""Valida o desenho da aula descrita no deck.json e imprime a linha do tempo minuto a minuto.

Uso:
    python validar_aula.py aulas/2026-11-lca/04_aula/deck.json
    python validar_aula.py deck.json --json > relatorio.json

Erros reprovam a aula (codigo de saida 1). Avisos pedem uma decisao consciente.
As regras e o porque de cada uma estao em references/desenho-instrucional.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _marca as M  # noqa: E402

# ----------------------------------------------------------------------------- limites
DURACAO_MIN_S = 28 * 60
DURACAO_MAX_S = 35 * 60
PRIMEIRA_INTERACAO_MAX_S = 180
SEM_INTERACAO_AVISO_S = 6 * 60
SEM_INTERACAO_ERRO_S = 7 * 60
MIN_INTERACOES = 5
MIN_FORMATOS = 3
PALAVRAS_AVISO = 70
PALAVRAS_ERRO = 100
PARTE_ATIVA_MINIMA = 0.25
FIG_LARGURA_MIN_PX, FIG_ALTURA_MIN_PX = 500, 250

TIPOS_CONTEUDO = {"topicos", "tabela", "numeros", "barras", "linha", "etapas", "comparacao", "sintese", "cartoes"}
CHAVES_NAO_VISIVEIS = {
    "tipo", "notas", "tempo_s", "interacao", "bloco", "papel", "layout", "figura", "destaques", "fonte",
    "estilo", "fundo", "orientacao", "formato", "cor", "destaque", "revela", "larguras", "series",
    "categorias", "apoio", "id", "valores", "numerar", "origem", "evidencia", "gabarito", "sem_gabarito",
    "bilhete_saida", "destaque_linhas", "destaque_categorias", "titulo_sem_destaque", "largura_figura",
    "altura", "minimo", "maximo", "rotulos", "vao", "objetivo", "outras", "olho", "rotulo_pos",
}
RE_PALAVRA = re.compile(r"[0-9A-Za-zÀ-ÿ%°]+(?:[.,/×'’-][0-9A-Za-zÀ-ÿ%°]+)*")
RE_EVIDENCIA = re.compile(
    r"(\b(IC|OR|HR|RR|NNT|NNH|DMP|SMD|AUC|MCID|DMCI|GRADE|ECR)\b|\bp\s*[<=>]\s*0[,.]\d|\d\s*%|"
    r"ensaio|meta-?an[aá]lise|revis[aã]o sistem|coorte|\bestudos?\b|sensibilidade|especificidade|"
    r"raz[aã]o de (chances|risco|verossimilhan)|intervalo de confian|tamanho de efeito|diretriz|consenso)",
    re.I)
RE_CITACAO_LIVRE = re.compile(r"^[A-ZÀ-Ý][^;]*\b(19|20)\d{2}[a-z]?\b")
VERBOS_FRACOS = ("conhecer", "entender", "compreender", "saber", "aprender", "listar", "definir", "descrever",
                 "identificar", "citar", "familiarizar", "revisar", "apresentar")

# notas de enquete que pressupõem saber quem votou em quê (o Meet mostra só a contagem ao vivo)
RE_NOME_POR_VOTO = re.compile(
    r"(cham\w*|ped\w*|pergunt\w*|cit\w*)\b[^.]{0,90}\bpelo nome|pelo nome[^.]{0,60}\b(op[cç][aã]o|votou|votaram)|"
    r"\b(votou|votaram|op[cç][aã]o)\b[^.]{0,60}\bpelo nome", re.I)

# ----------------------------------------------------------------------------- tempo estimado pela fala
# O validador soma 'tempo_s'; esta estimativa confere se as notas cabem nele: palavras faladas das notas
# a ~130 por minuto mais a duração declarada da interação. É aviso, nunca erro: a nota é roteiro, não
# texto decorado, e o ritmo de cada apresentador muda.
FALA_PALAVRAS_MIN = 130
ESTIMADO_FOLGA = 1.5          # aviso quando o estimado passa de 1,5 × tempo_s ...
ESTIMADO_FOLGA_MIN_S = 30     # ... e de pelo menos 30 s a mais
RE_FRASE = re.compile(r"(?<=[.!?])\s+(?=[\"“(]?[A-ZÀ-Ý])")
# frases que são instrução ao apresentador, não fala: a rubrica "Interação: ..." (o tempo dela já está
# em 'duracao_s') e as ordens de condução que ninguém diz em voz alta
RE_INSTRUCAO = re.compile(
    r"^(Intera[cç][aã]o\s*:|Tempo\s*:|"
    r"N[aã]o (comentar|dar|corrigir|antecipar|interpretar|resolver|explicar|julgar|revelar|mostrar|ler|"
    r"responder|abrir|preencher|apressar)\b|"
    r"(Mostrar|Projetar) o resultado|Lan[cç]ar a enquete|Fechar (a enquete|as salas|no tempo)|Abrir as salas|"
    r"Entrar (em|nas|na|\d)|Copiar|Esperar|Dar \d+ segundos|Deixar \d+ segundos|Contar 3|Cronometrar|"
    r"Ter (a|o|um|uma) )", re.I)
# na capa, a logística de antes da aula não é falada: conta só o que se diz à turma ao abrir
RE_FALA_CAPA = re.compile(r"^(Dizer|Pedir|Perguntar|Explicar|Apresentar|Contar|Ler|Come[cç]ar|Abrir com|"
                          r"Lembrar|Avisar)\b", re.I)


def palavras_faladas(notas: str, capa: bool = False) -> int:
    """Palavras das notas que viram fala: sem a linha 'Tempo: ...', sem a rubrica 'Interação:' e as
    ordens de condução, e, na capa, sem a logística de pré-aula."""
    t = re.sub(r"^\s*Tempo\s*:[^\n]*?\(acumulado[^)]*\)\.?\s*", "", str(notas or ""), flags=re.I)
    n = 0
    for fr in RE_FRASE.split(t.strip()):
        fr = fr.strip()
        if not fr or RE_INSTRUCAO.match(fr):
            continue
        if capa and not RE_FALA_CAPA.match(fr):
            continue
        n += contar_palavras(fr)
    return n


def tempo_estimado(s: dict) -> tuple[int, int]:
    """(segundos de fala estimados, segundos de interação declarados) de um slide."""
    fala = palavras_faladas(s.get("notas") or "", capa=s.get("tipo") == "capa") * 60 / FALA_PALAVRAS_MIN
    inter = s.get("interacao") if isinstance(s.get("interacao"), dict) else None
    d = 0
    if inter and inter.get("tipo") in M.INTERACOES:
        d = int(inter.get("duracao_s") or M.INTERACOES[inter["tipo"]]["padrao_s"])
    return int(round(fala)), d


def contar_palavras(texto: str) -> int:
    return len(RE_PALAVRA.findall(M.sem_marcacao(texto)))


def textos_visiveis(obj, chave: str | None = None) -> list[str]:
    """Todo texto que aparece no slide (fora notas, fonte e campos de controle)."""
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in CHAVES_NAO_VISIVEIS:
                continue
            out += textos_visiveis(v, k)
    elif isinstance(obj, list):
        for v in obj:
            out += textos_visiveis(v, chave)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def titulo_curto(s: dict, n: int = 58) -> str:
    t = M.sem_marcacao(s.get("titulo") or s.get("pergunta") or s.get("olho") or s.get("tipo") or "").replace("\n", " ")
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower().replace("et al.", "et al")).strip()


def validar(deck: dict, base: Path) -> dict:
    erros: list[str] = []
    avisos: list[str] = []
    slides = [s for s in M.como_lista(deck.get("slides")) if isinstance(s, dict)]
    meta = deck.get("meta") or {}
    refs = M.indice_referencias(deck)
    curtas = {_norm(r.get("curta") or ""): k for k, r in refs.items() if r.get("curta")}
    catalogo, pasta_cat = M.carregar_catalogo(deck, base)

    def E(n, msg):
        erros.append(f"slide {n}: {msg}" if n else msg)

    def A(n, msg):
        avisos.append(f"slide {n}: {msg}" if n else msg)

    if not slides:
        return {"erros": ["o deck não tem slides."], "avisos": [], "linha": [], "resumo": {}, "interacoes": []}

    # ------------------------------------------------------------------ tempo e interacoes
    linha = []
    interacoes = []
    t = 0
    for n, s in enumerate(slides, 1):
        tipo = s.get("tipo")
        if tipo not in M.TIPOS:
            E(n, f"tipo desconhecido: {tipo!r}.")
        apoio = bool(s.get("apoio")) or tipo == "referencias"
        dur = int(s.get("tempo_s") or 0)
        if not apoio and dur <= 0:
            E(n, "falta 'tempo_s' (tempo previsto do slide, em segundos). Slides fora da conta levam \"apoio\": true.")
        if apoio:
            dur = 0
        inter = s.get("interacao")
        item = {"n": n, "tipo": tipo, "inicio": t, "fim": t + dur, "titulo": titulo_curto(s), "interacao": None,
                "bloco": s.get("bloco"), "apoio": apoio}
        if inter:
            if not isinstance(inter, dict) or inter.get("tipo") not in M.INTERACOES:
                E(n, f"interação inválida: {inter!r}. Tipos: {', '.join(M.INTERACOES)}.")
            elif apoio:
                A(n, "slide de apoio com interação: ela não entra na conta do tempo.")
            else:
                d = int(inter.get("duracao_s") or M.INTERACOES[inter["tipo"]]["padrao_s"])
                ini = t + int(inter.get("inicio_s") or 0)
                if d > dur:
                    E(n, f"a interação dura {M.tempo_extenso(d)}, mais que o tempo do slide ({M.tempo_extenso(dur)}).")
                    d = dur
                if inter["tipo"] == "salas" and dur - d < 60:
                    A(n, "salas precisam de cerca de 1 min a mais que a tarefa para abrir, fechar e ouvir os porta-vozes.")
                reg = {"n": n, "tipo": inter["tipo"], "inicio": ini, "fim": min(ini + d, t + dur), "duracao": d,
                       "rotulo": M.rotulo_interacao(inter)}
                interacoes.append(reg)
                item["interacao"] = reg
        if not apoio:
            fala_s, inter_s = tempo_estimado(s)
            item["estimado"] = fala_s + inter_s
            item["estimado_fala"] = fala_s
            if dur > 0 and item["estimado"] >= ESTIMADO_FOLGA * dur and item["estimado"] - dur >= ESTIMADO_FOLGA_MIN_S:
                A(n, f"tempo estimado de {M.tempo_extenso(item['estimado'])} (fala das notas a ~{FALA_PALAVRAS_MIN} "
                  f"palavras/min: {M.tempo_extenso(fala_s)}; interação: {M.tempo_extenso(inter_s)}) para "
                  f"{M.tempo_extenso(dur)} de 'tempo_s'. Corte a fala ou aumente o tempo do slide.")
        linha.append(item)
        t += dur
    total = t
    estimado_total = sum(it.get("estimado", 0) for it in linha)
    if estimado_total > DURACAO_MAX_S:
        A(0, f"tempo estimado da aula: {M.relogio(estimado_total)} min (fala das notas a ~{FALA_PALAVRAS_MIN} "
          f"palavras/min mais as interações declaradas), acima de 35 min, embora 'tempo_s' some "
          f"{M.relogio(total)}. As notas falam mais do que o tempo previsto: corte fala ou slides.")

    if total > DURACAO_MAX_S:
        E(0, f"a aula soma {M.relogio(total)} min: passa do teto de 35 min. Corte conteúdo, não corte interação.")
    elif total < DURACAO_MIN_S:
        A(0, f"a aula soma {M.relogio(total)} min: abaixo de 28 min. Confira se os tempos das interações estão realistas.")

    if not interacoes:
        E(0, "a aula não tem nenhuma interação.")
    else:
        if interacoes[0]["inicio"] > PRIMEIRA_INTERACAO_MAX_S:
            E(interacoes[0]["n"], f"a primeira interação começa em {M.relogio(interacoes[0]['inicio'])}: "
              "precisa acontecer nos primeiros 3 minutos (a turma decide antes de ouvir).")
        marcos = [(0, 0, 0)] + [(i["inicio"], i["fim"], i["n"]) for i in sorted(interacoes, key=lambda x: x["inicio"])] + [(total, total, 0)]
        for (a0, a1, na), (b0, b1, nb) in zip(marcos, marcos[1:]):
            vao = b0 - a1
            onde = f"entre {M.relogio(a1)} e {M.relogio(b0)}"
            if vao > SEM_INTERACAO_ERRO_S:
                E(0, f"{M.tempo_extenso(vao)} seguidos sem interação ({onde}). O limite é 7 min: "
                  "coloque uma pergunta com voto, chat em cascata ou mão na câmera nesse trecho.")
            elif vao > SEM_INTERACAO_AVISO_S:
                A(0, f"{M.tempo_extenso(vao)} sem interação ({onde}): acima de 6 min a atenção cai. Considere uma mão na câmera.")
        if len(interacoes) < MIN_INTERACOES:
            E(0, f"só {len(interacoes)} interação(ões); o mínimo é {MIN_INTERACOES} em 30 a 35 min.")
        formatos = sorted({i["tipo"] for i in interacoes})
        if len(formatos) < MIN_FORMATOS:
            E(0, f"só {len(formatos)} formato(s) de interação ({', '.join(formatos)}); use pelo menos {MIN_FORMATOS} "
              "para variar o estímulo.")
        ativa = sum(i["duracao"] for i in interacoes) / total if total else 0
        if ativa < PARTE_ATIVA_MINIMA:
            A(0, f"só {ativa:.0%} do tempo está em interação; abaixo de 25% a aula vira exposição com pausas.")

    # bilhete de saida
    # o bilhete de saída é o ÚLTIMO slide cronometrado: um 'chat' no meio da aula não fecha a aula
    crono_ = [it for it in linha if not it["apoio"]]
    ultimo = crono_[-1] if crono_ else None
    tem_bilhete = bool(ultimo) and (
        bool(slides[ultimo["n"] - 1].get("bilhete_saida"))
        or bool(ultimo["interacao"] and ultimo["interacao"]["tipo"] == "chat"))
    if not tem_bilhete:
        E(ultimo["n"] if ultimo else 0,
          "falta o bilhete de saída no último slide cronometrado: um slide do tipo 'pergunta' com interação "
          "'chat' e \"bilhete_saida\": true (\"O que você vai fazer diferente...\").")
    for it in crono_[:-1]:
        if slides[it["n"] - 1].get("bilhete_saida"):
            A(it["n"], "slide marcado como bilhete de saída, mas não é o último slide cronometrado.")

    # ------------------------------------------------------------------ por slide
    n_figuras = 0
    usa_papel = any(s.get("papel") for s in slides)
    for n, s in enumerate(slides, 1):
        tipo = s.get("tipo")
        apoio = bool(s.get("apoio")) or tipo == "referencias"
        dur = int(s.get("tempo_s") or 0)
        inter = s.get("interacao") if isinstance(s.get("interacao"), dict) else None

        # palavras
        if tipo != "referencias":
            alvo = s
            if tipo == "enquete" and s.get("revela") and isinstance(s.get("opcoes"), dict):
                # na revelação as opções já foram lidas: conta só a que fica em destaque
                alvo = dict(s)
                alvo["opcoes"] = {k: v for k, v in s["opcoes"].items() if str(k).upper() == str(s["revela"]).upper()}
            textos = textos_visiveis(alvo)
            if tipo == "figura":
                textos = [x for x in textos if x != s.get("legenda")]   # a legenda é apoio, não entra na conta
            np_ = sum(contar_palavras(x) for x in textos)
            if np_ > PALAVRAS_ERRO:
                E(n, f"{np_} palavras visíveis: muito acima de 70. Divida em dois slides ou passe o detalhe para as notas.")
            elif np_ > PALAVRAS_AVISO:
                A(n, f"{np_} palavras visíveis (alvo: até 70). Uma ideia por slide; o resto vai para a fala.")

        # notas
        notas = (s.get("notas") or "").strip()
        if not apoio:
            if not notas:
                E(n, "faltam as notas do apresentador (o que falar e como conduzir).")
            else:
                if contar_palavras(notas) < 20:
                    A(n, "notas muito curtas: diga o que falar, o que perguntar e o que não antecipar.")
                if re.match(r"^\s*tempo\s*:", notas, re.I):
                    A(n, "as notas já começam com 'Tempo:'; o script escreve essa linha sozinho. Apague do deck.json.")
                if inter and "intera" not in notas.lower():
                    A(n, "slide com interação, mas as notas não dizem 'Interação: ...' nem como conduzi-la.")
                if ((inter and inter.get("tipo") == "enquete") or (tipo == "enquete" and s.get("revela"))) \
                        and RE_NOME_POR_VOTO.search(notas):
                    A(n, "as notas mandam chamar pelo nome quem votou em uma opção, mas a enquete do Google Meet "
                      "não mostra ao vivo quem votou em quê. Peça um voluntário de cada opção (microfone ou mão "
                      "na câmera) e chame pelo nome quem se apresentar (ver references/interacoes.md).")
            if dur > 240 and not inter:
                A(n, f"{M.tempo_extenso(dur)} no mesmo slide sem interação: divida ou encurte.")
            if 0 < dur < 20:
                A(n, "menos de 20 s neste slide: provavelmente ele pode ser fundido com o vizinho.")

        # tipo x interacao
        if tipo == "pergunta" and not inter and not apoio:
            A(n, "slide de pergunta sem interação declarada: toda pergunta grande pede um formato de resposta.")
        if tipo == "enquete":
            ops = s.get("opcoes") or {}
            nops = len(ops)
            if nops < 3:
                A(n, f"enquete com {nops} opções: use 3 ou 4, cada distrator sendo um erro real de raciocínio.")
            if nops > 4:
                E(n, f"enquete com {nops} opções: o layout comporta até 4 (A–D).")
            if s.get("revela"):
                letras = [str(k).upper() for k in (ops.keys() if isinstance(ops, dict) else [chr(65 + i) for i in range(nops)])]
                if str(s["revela"]).upper() not in letras:
                    E(n, f"'revela' aponta para a opção {s['revela']!r}, que não existe.")
                if not s.get("justificativa"):
                    A(n, "revelação sem 'justificativa': diga em uma frase o que sustenta a resposta e de onde vem.")
            else:
                if not inter or inter.get("tipo") != "enquete":
                    A(n, "slide de enquete sem interação 'enquete' declarada.")
                if not s.get("gabarito") and not s.get("sem_gabarito"):
                    A(n, "enquete sem 'gabarito' (letra sustentada pela evidência). Se for de opinião, marque \"sem_gabarito\": true.")
        if tipo == "tarefa" and inter and inter.get("tipo") == "salas" and not s.get("entrega"):
            E(n, "tarefa de salas sem 'entrega': sem produto escrito no chat a sala vira conversa solta.")

        # graficos: series tracejadas e intervalos (barras de erro)
        if tipo in ("barras", "linha"):
            ncat = len(M.como_lista(s.get("categorias")))
            for k, se in enumerate(M.como_lista(s.get("series")), 1):
                if not isinstance(se, dict):
                    continue
                nome = f"série {k} ({M.sem_marcacao(se.get('nome') or '')[:30]})"
                if se.get("tracejado") and tipo != "linha":
                    A(n, f"{nome}: 'tracejado' só vale no gráfico de linha; nas barras ele é ignorado.")
                iv = se.get("intervalo")
                if iv is None:
                    continue
                vals = M.como_lista(se.get("valores"))
                if not isinstance(iv, list) or len(iv) != len(vals) or len(iv) != ncat:
                    E(n, f"{nome}: 'intervalo' precisa de uma entrada por categoria ({ncat}), null ou [inferior, superior].")
                    continue
                for j, (v, par_) in enumerate(zip(vals, iv)):
                    if par_ is None:
                        continue
                    ok = isinstance(par_, list) and len(par_) == 2 and all(isinstance(x, (int, float)) for x in par_)
                    if not ok or v is None or not (par_[0] <= v <= par_[1]):
                        E(n, f"{nome}, categoria {j + 1}: intervalo {par_!r} não contém o valor {v!r} "
                          "(use [inferior, superior] em valores absolutos, com o ponto dentro).")

        # fonte e evidencia
        fontes = [str(f) for f in M.como_lista(s.get("fonte"))]
        for f in fontes:
            if f in refs:
                continue
            if RE_CITACAO_LIVRE.match(f.strip()) and _norm(f) not in curtas:
                E(n, f"a fonte \"{f}\" está no rodapé, mas não aparece em 'referencias' "
                  "(use o id da referência ou acrescente-a).")
        if tipo in TIPOS_CONTEUDO or (tipo == "enquete" and s.get("revela")):
            ev = s.get("evidencia")
            if ev is None:
                ev = s.get("origem") != "caso" and bool(RE_EVIDENCIA.search(" ".join(textos_visiveis(s))))
            if ev and not fontes:
                E(n, "o slide afirma evidência (número, estudo ou medida de efeito) e não tem 'fonte'. "
                  "Se os dados são do caso fictício, marque \"origem\": \"caso\".")

        # figura
        if tipo == "figura":
            n_figuras += 1
            info = M.resolver_figura(s, catalogo, pasta_cat, base)
            if not info["existe"]:
                E(n, f"figura não encontrada: {info.get('caminho') or info.get('id')}.")
            else:
                lw, lh = info["largura_px"], info["altura_px"]
                total_ = (s.get("layout") or "meia") == "total"
                if lw < FIG_LARGURA_MIN_PX or lh < FIG_ALTURA_MIN_PX:
                    E(n, f"figura de baixa resolução ({lw} × {lh} px). Recorte de novo em 300 dpi.")
                elif (total_ and lw < 1250 and lh < 330) or (not total_ and lw < 750 and lh < 440):
                    A(n, f"figura com {lw} × {lh} px vai aparecer menor que a moldura; recorte em resolução maior se puder.")
            if not info.get("citacao"):
                E(n, "figura sem citação completa (autor, revista, ano, volume, páginas, número da figura).")
            if not info.get("legenda"):
                A(n, "figura sem legenda em português (uma linha dizendo o que os eixos e as cores mostram).")
            if info.get("chave") and str(info["chave"]) not in refs:
                E(n, f"o artigo da figura ({info['chave']}) não está em 'referencias'.")
            elif not info.get("chave"):
                A(n, "figura sem 'ref' (id da referência do artigo): não dá para conferir se ele está nas referências.")
            if info.get("no_catalogo") and info.get("aprovada") is False:
                E(n, "a figura está no catálogo como não aprovada.")
            lic = str(info.get("licenca") or "").lower()
            if "reservad" in lic:
                A(n, "figura com todos os direitos reservados: use só em aula interna, com citação completa, "
                  "ou redesenhe os dados como gráfico nativo.")
            pts = M.como_lista(s.get("o_que_olhar"))
            if not 2 <= len(pts) <= 3:
                E(n, f"'o_que_olhar' tem {len(pts)} ponto(s): use 2 ou 3, na ordem em que o olho deve percorrer a figura.")
            if contar_palavras(s.get("titulo") or "") < 4:
                A(n, "o título de um slide de figura diz a conclusão em uma frase (\"Passar na bateria é raro\"), não o assunto.")

    if n_figuras == 0:
        A(0, "nenhum slide de figura: a aula promete evidência e não mostra nenhuma figura dos artigos.")
    elif n_figuras > 6:
        A(0, f"{n_figuras} figuras em 30 a 35 min: cada figura pede cerca de 2 min bem conduzidos. Fique em 3 a 5.")

    cronometrados = [it for it in linha if not it["apoio"]]
    if len(cronometrados) > 26:
        A(0, f"{len(cronometrados)} slides cronometrados: mais de 26 vira corrida de slides.")
    if len(cronometrados) < 10:
        A(0, f"só {len(cronometrados)} slides cronometrados: provavelmente há slides com ideias demais.")

    # ------------------------------------------------------------------ blocos: pergunta antes da evidencia
    def eh_evidencia(s):
        if s.get("papel"):
            return s["papel"] in ("evidencia", "ver")
        return s.get("tipo") == "figura"

    def eh_pergunta(s):
        if s.get("papel") in ("prever", "decidir", "gancho", "recuperar"):
            return bool(s.get("interacao"))
        return bool(s.get("interacao")) and not s.get("revela")

    blocos: dict[str, list[int]] = {}
    for i, s in enumerate(slides):
        if s.get("bloco"):
            blocos.setdefault(str(s["bloco"]), []).append(i)
    if not blocos and n_figuras:
        A(0, "os slides não têm 'bloco': sem isso não dá para conferir o ciclo prever → ver → decidir → conferir.")
    for nome, idxs in blocos.items():
        evid = [i for i in idxs if eh_evidencia(slides[i])]
        if not evid:
            continue
        antes = [i for i in idxs if i < evid[0] and eh_pergunta(slides[i])]
        if not antes:
            E(evid[0] + 1, f"bloco '{nome}': a evidência aparece antes de qualquer pergunta à turma. "
              "Peça a previsão ou a decisão primeiro e só então mostre a figura.")
        depois = [i for i in idxs if i > evid[-1] and (slides[i].get("interacao") or slides[i].get("revela")
                                                         or slides[i].get("papel") in ("decidir", "conferir"))]
        ult = slides[evid[-1]].get("interacao")
        if isinstance(ult, dict) and int(ult.get("inicio_s") or 0) > 0:
            depois.append(evid[-1])     # a interação começa depois de a figura ser lida, no mesmo slide
        if not depois:
            A(evid[-1] + 1, f"bloco '{nome}': depois da evidência não há decisão nem conferência do voto. "
              "Feche o ciclo (revelar a enquete, mão na câmera, aplicar no caso).")
    if usa_papel and not any(s.get("papel") == "recuperar" for s in slides):
        A(0, "nenhum slide com papel 'recuperar': o fechamento pede recuperação ativa (a turma escreve de memória antes da síntese).")

    # ------------------------------------------------------------------ meta
    objetivos = M.como_lista(meta.get("objetivos"))
    if not objetivos:
        A(0, "meta.objetivos está vazio: escreva 2 ou 3 objetivos em nível de aplicação, análise ou avaliação.")
    elif len(objetivos) > 4:
        A(0, f"{len(objetivos)} objetivos para 30 a 35 min: fique em 2 ou 3.")
    for o in objetivos:
        primeiro = re.sub(r"^[^A-Za-zÀ-ÿ]+", "", str(o)).split(" ")[0].lower().strip(",.")
        if primeiro in VERBOS_FRACOS:
            A(0, f"objetivo em nível baixo (\"{primeiro}\"): troque por um verbo observável de decisão "
              "(decidir, calcular, interpretar, justificar, escolher, criticar).")
    if not any(s.get("tipo") == "referencias" for s in slides):
        E(0, "falta o slide de referências (tipo 'referencias').")
    if not any(("desafio" in s or "ancora" in s) for s in slides) and not re.search(
            r"desafio|para quem (est[aá] )?come[cç]", " ".join(str(s.get("notas") or "") for s in slides), re.I):
        A(0, "nenhum slide prevê níveis diferentes (campos 'ancora' e 'desafio', ou orientação nas notas).")
    sem_uso = [k for k in refs if not any(k in [str(f) for f in M.como_lista(s.get("fonte"))] for s in slides)
               and not any(M.resolver_figura(s, catalogo, pasta_cat, base).get("chave") == k for s in slides if s.get("tipo") == "figura")]
    if sem_uso:
        A(0, "referências que nenhum slide cita: " + ", ".join(sorted(sem_uso)) + ".")
    sem_conf = [r.get("curta") or k for k, r in refs.items() if not r.get("conferido")]
    if sem_conf:
        A(0, "referências sem o campo 'conferido' (texto completo | resumo | nao conferido): " + "; ".join(sorted(sem_conf)) + ".")

    resumo = {
        "duracao_s": total, "slides": len(slides), "slides_cronometrados": len(cronometrados),
        "interacoes": len(interacoes), "formatos": sorted({i["tipo"] for i in interacoes}),
        "tempo_em_interacao_s": sum(i["duracao"] for i in interacoes),
        "primeira_interacao_s": interacoes[0]["inicio"] if interacoes else None, "figuras": n_figuras,
        "duracao_estimada_s": estimado_total,
    }
    return {"erros": erros, "avisos": avisos, "linha": linha, "interacoes": interacoes, "resumo": resumo}


# ----------------------------------------------------------------------------- saida
def texto_linha_do_tempo(rel: dict) -> str:
    linha, inter = rel["linha"], rel["interacoes"]
    total = rel["resumo"].get("duracao_s", 0)
    out = ["== Linha do tempo (minuto a minuto) ==",
           " min  ativ.  slide  o que acontece"]
    nmin = (total + 59) // 60
    faixa = ""
    crono = [it for it in linha if not it["apoio"]]
    for m in range(nmin):
        a, b = m * 60, min((m + 1) * 60, total)
        ativos = [it for it in crono if it["inicio"] < b and it["fim"] > a]
        em_inter = [i for i in inter if i["inicio"] < b and i["fim"] > a]
        marca = "●" if em_inter else "·"
        faixa += marca
        entram = [it for it in ativos if it["inicio"] >= a]
        if not ativos:
            continue
        ns = f"{ativos[0]['n']}" if len(ativos) == 1 else f"{ativos[0]['n']}–{ativos[-1]['n']}"
        if entram:
            desc = []
            for it in entram:
                d = f"[{it['tipo']}] {it['titulo']}"
                if it["interacao"]:
                    d += f"  ◄ {it['interacao']['rotulo']}"
                desc.append(d)
            texto = desc[0]
            out.append(f" {m:>3}   {marca}    {ns:>5}  {texto}")
            for d in desc[1:]:
                out.append(f"{'':>19}{d}")
        else:
            it = ativos[0]
            cont = f"(continua: {it['titulo']})"
            if em_inter:
                cont = f"(continua: {em_inter[0]['rotulo']})"
            out.append(f" {m:>3}   {marca}    {ns:>5}  {cont}")
    out.append("")
    out.append(f" Minutos com interação (●) e sem (·): {faixa}")
    return "\n".join(out)


def imprimir(rel: dict, linha_do_tempo: bool = True) -> None:
    r = rel["resumo"]
    print("== Validação da aula ==")
    if r:
        print(f"Duração: {M.relogio(r['duracao_s'])} min | slides: {r['slides']} ({r['slides_cronometrados']} cronometrados) | "
              f"figuras: {r['figuras']}")
        pi = "—" if r["primeira_interacao_s"] is None else M.relogio(r["primeira_interacao_s"])
        pct = (r["tempo_em_interacao_s"] / r["duracao_s"]) if r["duracao_s"] else 0
        print(f"Interações: {r['interacoes']} em {len(r['formatos'])} formato(s) ({', '.join(r['formatos']) or '—'}) | "
              f"primeira aos {pi} | {pct:.0%} do tempo em atividade")
        if r.get("duracao_estimada_s") is not None:
            print(f"Tempo estimado pela fala das notas (~{FALA_PALAVRAS_MIN} palavras/min) + interações: "
                  f"{M.relogio(r['duracao_estimada_s'])} min (estimativa; quem manda é tempo_s)")
    if linha_do_tempo and rel["linha"]:
        print()
        print(texto_linha_do_tempo(rel))
    print()
    if rel["erros"]:
        print(f"ERROS ({len(rel['erros'])}) — a aula está reprovada até corrigir:")
        for e in rel["erros"]:
            print(f"  ✗ {e}")
    if rel["avisos"]:
        print(f"AVISOS ({len(rel['avisos'])}) — decida conscientemente cada um:")
        for a in rel["avisos"]:
            print(f"  ! {a}")
    if not rel["erros"] and not rel["avisos"]:
        print("Nenhum erro e nenhum aviso.")
    print("RESULTADO: " + ("REPROVADA" if rel["erros"] else "APROVADA" + (" com avisos" if rel["avisos"] else "")))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Valida o desenho da aula (deck.json) e imprime a linha do tempo.")
    ap.add_argument("deck", help="caminho do deck.json")
    ap.add_argument("--json", action="store_true", help="imprime o relatório em JSON")
    ap.add_argument("--sem-linha-do-tempo", action="store_true")
    a = ap.parse_args(argv)
    caminho = Path(a.deck).expanduser().resolve()
    deck = M.carregar_json(caminho)
    if not isinstance(deck, dict):
        M.sair("o deck.json precisa ser um objeto com 'meta', 'referencias' e 'slides'.")
    rel = validar(deck, caminho.parent)
    if a.json:
        print(json.dumps(rel, ensure_ascii=False, indent=2))
    else:
        imprimir(rel, linha_do_tempo=not a.sem_linha_do_tempo)
    return 1 if rel["erros"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
