"""Funções comuns aos scripts do orquestrador boost-education.

Só biblioteca padrão. Caminhos relativos a este arquivo, para funcionar tanto no
repositório quanto na skill empacotada.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import unicodedata
from pathlib import Path

PASTA_SKILL = Path(__file__).resolve().parent.parent
PASTA_SKILLS = PASTA_SKILL.parent
PREFERENCIAS = PASTA_SKILL / "references" / "preferencias.md"

SKILLS_IRMAS = {
    "pesquisa": "boost-pesquisa-artigos",
    "leitura": "boost-leitura-figuras",
    "slides": "boost-aula-slides",
}

RECORTES = ("topo_mecanismos", "so_topo", "fronteira")

DESCRICAO_RECORTE = {
    "topo_mecanismos": "topo da pirâmide (diretrizes, revisões sistemáticas, ECRs recentes) mais estudos clássicos "
                       "e mecanísticos que explicam o porquê",
    "so_topo": "só diretrizes, revisões sistemáticas e ensaios clínicos",
    "fronteira": "o que saiu nos últimos 3 anos-calendário (atualização, controvérsias em aberto)",
}

INTERACOES = {
    "enquete": "ENQUETE · 1 MIN",
    "chat_cascata": "CHAT EM CASCATA · 2 MIN",
    "salas": "SALAS DE 3 · 4 MIN",
    "mao_camera": "MÃO NA CÂMERA",
    "chat": "CHAT · 2 MIN (bilhete de saída)",
}

CHECAGENS = {
    1: "Estratégia de busca aprovada e string do Scopus entregue",
    2: "Lista de artigos aprovada e pagos pedidos (pendentes.md)",
    3: "Roteiro com linha do tempo aprovado",
    4: "Deck revisado pelo usuário",
}

MARCA_PREENCHER = "A PREENCHER"

# Formatos pedagógicos da aula. Os limites que valem são os do validador da skill de slides
# (boost-aula-slides/scripts/_marca.py, FORMATOS); aqui ficam só os textos do briefing e dos relatórios.
FORMATOS = {
    "expositiva": {
        "nome": "expositiva com checagens",
        "duracao": "45 a 50 minutos (aviso abaixo de 42 e acima de 48; acima de 50 é erro)",
        "faixa": "40 a 50 min", "alvo": 46,
        "estrutura": "linha lógica do tema em 3 a 5 partes (meta.partes), mapa da aula e \"onde estamos\" em cada "
                     "parte, uma ideia por slide, exemplo resolvido antes da aplicação, síntese no fim de cada parte, "
                     "checagem rápida a cada 5 a 7 min e o caso só como aplicação no fim das partes",
        "exemplo": "assets/exemplo_expositiva/deck.json",
        "roteiro": "objetivos, partes da linha de raciocínio, exemplos resolvidos, checagens, aplicações e tempos; "
                   "modelo A em assets/roteiro_modelo.md",
        "checagem3": "objetivos, as partes da aula (linha de raciocínio), a linha do tempo (início, parte, slide, "
                     "checagem) e as figuras escolhidas; pergunte se a ordem, o tempo e o nível estão certos",
    },
    "caso": {
        "nome": "guiada por caso",
        "duracao": "30 a 35 minutos (acima de 35 é erro)",
        "faixa": "30 a 35 min", "alvo": 32,
        "estrutura": "um caso que evolui com revés, em 3 blocos prever → ver a evidência → decidir → conferir, "
                     "com a primeira decisão da turma antes de 3 min",
        "exemplo": "assets/exemplo/deck.json",
        "roteiro": "objetivos, caso, 3 blocos, tempos; modelo B em assets/roteiro_modelo.md",
        "checagem3": "objetivos, caso, linha do tempo (início, bloco, slide, interação) e as figuras escolhidas; "
                     "pergunte se o tempo e as decisões estão certos",
    },
}
FORMATO_DECK_SEM_CAMPO = "caso"   # deck.json sem meta.formato é validado como caso


def formato_padrao(prefs: dict[str, str] | None = None) -> str:
    """Formato das preferências ('Formato pedagógico'): o primeiro de 'expositiva' ou 'caso' que aparece."""
    prefs = ler_preferencias() if prefs is None else prefs
    txt = sem_acento(pref(prefs, "Formato pedagógico", "")).lower()
    achados = [(txt.find(k), k) for k in ("expositiva", "caso") if txt.find(k) >= 0]
    return min(achados)[1] if achados else "caso"


RE_FORMATO_BRIEFING = re.compile(r"^\*\*Formato pedag[oó]gico:\*\*.*?`(expositiva|caso)`", re.M)


def formato_do_briefing(pasta: Path) -> str | None:
    try:
        texto = (pasta / "00_briefing.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = RE_FORMATO_BRIEFING.search(texto)
    return m.group(1) if m else None


def formato_do_deck(deck) -> str | None:
    """meta.formato do deck.json (None se o deck não existe; 'caso' se existe sem o campo)."""
    if not isinstance(deck, dict) or "__erro__" in deck:
        return None
    f = (deck.get("meta") or {}).get("formato")
    return str(f).strip().lower() if f else FORMATO_DECK_SEM_CAMPO


def hoje() -> str:
    return _dt.date.today().isoformat()


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def fazer_slug(texto: str, limite: int = 48, literal: bool = False) -> str:
    """Slug sem acento. literal=True só limpa (para --slug dado pelo usuário)."""
    s = sem_acento(texto).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if literal:
        return s[:80].strip("-") or "aula"
    vazias = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "a", "o", "as", "os", "ao", "aos", "um", "uma", "para", "por", "pela", "pelo", "com", "sobre", "apos"}
    partes = [p for p in s.split("-") if p and p not in vazias] or [p for p in s.split("-") if p]
    saida = ""
    for p in partes:
        cand = f"{saida}-{p}" if saida else p
        if len(cand) > limite:
            break
        saida = cand
    return saida or "aula"


def ler_json(caminho: Path, padrao=None):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao
    except (OSError, ValueError) as e:
        return {"__erro__": f"{type(e).__name__}: {e}"}


def lista_de(dados, *chaves) -> list:
    """Aceita lista pura ou dict com a lista numa das chaves dadas."""
    if isinstance(dados, list):
        return [d for d in dados if isinstance(d, dict)]
    if isinstance(dados, dict):
        for k in chaves:
            if isinstance(dados.get(k), list):
                return [d for d in dados[k] if isinstance(d, dict)]
    return []


def caminho_irma(chave: str) -> Path | None:
    p = PASTA_SKILLS / SKILLS_IRMAS[chave] / "scripts"
    return p if p.is_dir() else None


def cmd_irma(chave: str, script: str) -> str:
    """Linha de comando para um script de skill irmã (ou um marcador, se ela não estiver aqui)."""
    p = caminho_irma(chave)
    base = str(p) if p else f"<skill {SKILLS_IRMAS[chave]}>/scripts"
    return f"python3 -I {base}/{script}"


def cmd_proprio(script: str) -> str:
    return f"python3 -I {PASTA_SKILL / 'scripts' / script}"


def ler_preferencias() -> dict[str, str]:
    """Lê a tabela 'Assunto | Decisão' de references/preferencias.md (fonte única dos padrões)."""
    prefs: dict[str, str] = {}
    try:
        texto = PREFERENCIAS.read_text(encoding="utf-8")
    except OSError:
        return prefs
    for linha in texto.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$", linha)
        if not m or set(m.group(1)) <= set("-: ") or m.group(1) == "Assunto":
            continue
        prefs[sem_acento(m.group(1)).lower()] = m.group(2)
    return prefs


def pref(prefs: dict[str, str], assunto: str, padrao: str) -> str:
    return prefs.get(sem_acento(assunto).lower(), padrao)


# --------------------------------------------------------------------------
# 00_andamento.md: pontos de checagem, modo e registro
# --------------------------------------------------------------------------

def texto_andamento(tema: str, sem_parar: bool, origem: str = "nova_aula.py") -> str:
    linhas = [
        f"# Andamento · {tema}",
        "",
        "Arquivo lido e atualizado por `situacao.py` (skill boost-education). Edite à mão se quiser:",
        "o script só olha as linhas `Modo:` e `- [x] N.`.",
        "",
        f"Modo: {'sem parar' if sem_parar else 'com checagens'}",
        "",
        "## Pontos de checagem",
        "",
    ]
    for n, txt in CHECAGENS.items():
        linhas.append(f"- [ ] {n}. {txt}")
    linhas += ["", "## Registro", "", f"- {hoje()} · pasta criada ({origem})", ""]
    return "\n".join(linhas)


def ler_andamento(pasta: Path) -> dict:
    arq = pasta / "00_andamento.md"
    estado = {"existe": arq.exists(), "modo": "com checagens", "checagens": {n: None for n in CHECAGENS}}
    if not arq.exists():
        return estado
    texto = arq.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^Modo:\s*(.+)$", texto, re.M)
    if m and "sem parar" in sem_acento(m.group(1)).lower():
        estado["modo"] = "sem parar"
    for m in re.finditer(r"^- \[([ xX])\]\s*(\d)\.\s*(.*)$", texto, re.M):
        n = int(m.group(2))
        if n in CHECAGENS:
            estado["checagens"][n] = m.group(3).strip() if m.group(1).lower() == "x" else None
    return estado


def atualizar_andamento(pasta: Path, *, marcar: int | None = None, desmarcar: int | None = None,
                        modo: str | None = None, nota: str | None = None, tema: str = "") -> list[str]:
    arq = pasta / "00_andamento.md"
    if not arq.exists():
        arq.write_text(texto_andamento(tema or pasta.name, modo == "sem parar", "situacao.py"), encoding="utf-8")
    texto = arq.read_text(encoding="utf-8")
    feitos: list[str] = []
    if modo:
        if re.search(r"^Modo:.*$", texto, re.M):
            texto = re.sub(r"^Modo:.*$", f"Modo: {modo}", texto, count=1, flags=re.M)
        else:
            texto = texto.replace("## Pontos de checagem", f"Modo: {modo}\n\n## Pontos de checagem", 1)
        feitos.append(f"modo: {modo}")
    for n, x in ((marcar, "x"), (desmarcar, " ")):
        if n is None:
            continue
        padrao = re.compile(rf"^- \[[ xX]\]\s*{n}\.\s*([^\n]*?)(\s+—\s+\d{{4}}-\d{{2}}-\d{{2}}.*)?$", re.M)
        base = CHECAGENS[n]
        sufixo = f" — {hoje()}" + (f" — {nota}" if nota else "") if x == "x" else ""
        nova = f"- [{x}] {n}. {base}{sufixo}"
        if padrao.search(texto):
            texto = padrao.sub(lambda _m: nova, texto, count=1)
        else:
            texto = texto.replace("## Registro", f"{nova}\n\n## Registro", 1)
        feitos.append(("marcada" if x == "x" else "desmarcada") + f" a checagem {n}")
    registro = []
    if feitos:
        registro.append(f"- {hoje()} · " + "; ".join(feitos) + (f" ({nota})" if nota else ""))
    elif nota:
        registro.append(f"- {hoje()} · {nota}")
    if registro:
        if "## Registro" not in texto:
            texto = texto.rstrip("\n") + "\n\n## Registro\n\n"
        texto = texto.rstrip("\n") + "\n" + "\n".join(registro) + "\n"
    arq.write_text(texto, encoding="utf-8")
    return feitos or ([f"registro: {nota}"] if nota else [])
