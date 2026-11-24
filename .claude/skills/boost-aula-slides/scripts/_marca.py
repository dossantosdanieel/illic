"""Marca Boost Education: medidas, cores, formatos de interacao e medicao de texto.

Tudo aqui foi medido no deck de referencia ("Caso Marina"). Os outros scripts
importam este modulo; ele nao tem efeito colateral ao ser importado.
Unidades: polegadas para posicao e tamanho, pontos para tipografia.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"
LOGO_CLARO = ASSETS / "logo_sobre_claro.png"      # logo escuro, para fundo claro
LOGO_ESCURO = ASSETS / "logo_sobre_escuro.png"    # logo branco, para fundo marinho

# --------------------------------------------------------------------------
# Pagina e grade (polegadas)
# --------------------------------------------------------------------------
LARGURA, ALTURA = 13.333, 7.5
ME = 0.889                 # margem esquerda
LC = 11.556                # largura util do conteudo
MD = ME + LC               # borda direita do conteudo (12,445)
Y_OLHO = 0.889
Y_TITULO = 1.186
Y_CORPO = 1.939
Y_LIMITE = 6.55            # nada do corpo passa daqui (logo e fonte ficam abaixo)
LOGO_RODAPE = (0.889, 6.833, 2.194, 0.278)
LOGO_CAPA = (0.889, 0.889, 3.069, 0.389)
CAIXA_FONTE = (3.861, 6.861, 8.583, 0.228)   # "Fonte: ..." alinhada a direita
Y_PILULA, H_PILULA = 0.792, 0.347
RAIO = 0.0833              # raio dos cantos dos cartoes (6 pt), constante
ESPACO_COLUNAS = 0.167     # vao entre cartoes lado a lado

# --------------------------------------------------------------------------
# Cores
# --------------------------------------------------------------------------
COR = {
    "marinho": "202081",
    "marinho_escuro": "1D1D69",
    "petroleo": "007A99",
    "ciano_claro": "7FD4EA",
    "ciano": "009AC0",
    "lavanda": "C7D0EE",
    "fundo": "F7F9FA",
    "cartao": "EAEFF2",
    "borda": "D5DDE2",
    "borda_forte": "C3CCD2",
    "borda_tabela": "CBCBCB",
    "texto": "141A1A",
    "texto2": "4B5358",
    "texto_fonte": "5A5F63",
    "cinza_grafico": "8A949A",
    "eixo": "7D7D7D",
    "alerta": "B23A3A",
    "branco": "FFFFFF",
}
CORES_SERIES = ["marinho", "cinza_grafico", "ciano", "petroleo", "lavanda"]
FONTE = "Lato"

# --------------------------------------------------------------------------
# Interacoes canonicas
# --------------------------------------------------------------------------
INTERACOES = {
    "enquete":      {"rotulo": "ENQUETE",         "nome": "enquete",         "padrao_s": 60,  "mostra_tempo": True},
    "chat_cascata": {"rotulo": "CHAT EM CASCATA", "nome": "chat em cascata", "padrao_s": 120, "mostra_tempo": True},
    "salas":        {"rotulo": "SALAS DE 3",      "nome": "salas de 3",      "padrao_s": 240, "mostra_tempo": True},
    "mao_camera":   {"rotulo": "MÃO NA CÂMERA",   "nome": "mão na câmera",   "padrao_s": 30,  "mostra_tempo": False},
    "chat":         {"rotulo": "CHAT",            "nome": "chat",            "padrao_s": 120, "mostra_tempo": True},
}

TIPOS = ["capa", "pergunta", "enquete", "tarefa", "topicos", "cartoes", "figura", "tabela",
         "numeros", "barras", "linha", "etapas", "comparacao", "citacao", "sintese", "referencias"]


def tempo_extenso(seg: int) -> str:
    """90 -> '1 min 30 s'; 120 -> '2 min'; 30 -> '30 s' (como nas notas do deck de referencia)."""
    seg = int(round(seg))
    m, s = divmod(seg, 60)
    if m and s:
        return f"{m} min {s} s"
    if m:
        return f"{m} min"
    return f"{s} s"


def num(x: float, casas: int = 1) -> str:
    """1.25 -> '1,3' (vírgula decimal nas mensagens)."""
    return f"{x:.{casas}f}".replace(".", ",")


def relogio(seg: int) -> str:
    seg = int(round(seg))
    return f"{seg // 60}:{seg % 60:02d}"


def rotulo_interacao(inter: dict) -> str:
    """Texto da pilula: 'ENQUETE · 1 MIN', 'SALAS DE 3 · 4 MIN', 'MÃO NA CÂMERA'."""
    if inter.get("rotulo"):
        return str(inter["rotulo"]).upper()
    info = INTERACOES[inter["tipo"]]
    rot = info["rotulo"]
    if inter["tipo"] == "salas" and inter.get("tamanho"):
        rot = f"SALAS DE {int(inter['tamanho'])}"
    if not info["mostra_tempo"]:
        return rot
    d = int(inter.get("duracao_s") or info["padrao_s"])
    m, s = divmod(d, 60)
    if m and s:
        t = f"{m} MIN {s} S"
    elif m:
        t = f"{m} MIN"
    else:
        t = f"{s} S"
    return f"{rot} · {t}"


# --------------------------------------------------------------------------
# Marcacao **negrito**
# --------------------------------------------------------------------------
_RE_NEG = re.compile(r"\*\*(.+?)\*\*", re.S)


def partes(texto: str, negrito_base: bool = False) -> list[tuple[str, bool]]:
    """'a **b** c' -> [('a ', False), ('b', True), (' c', False)]."""
    texto = "" if texto is None else str(texto)
    out, pos = [], 0
    for m in _RE_NEG.finditer(texto):
        if m.start() > pos:
            out.append((texto[pos:m.start()], negrito_base))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(texto):
        out.append((texto[pos:], negrito_base))
    return [p for p in out if p[0]] or [("", negrito_base)]


def sem_marcacao(texto) -> str:
    return _RE_NEG.sub(r"\1", "" if texto is None else str(texto))


def titulo_com_destaque(titulo: str) -> str:
    """A marca pede uma palavra-chave em negrito no titulo. Sem marcacao, destaca a ultima palavra."""
    titulo = (titulo or "").strip()
    if "**" in titulo or not titulo:
        return titulo
    m = re.match(r"^(.*?)(\S+?)([\s?!.:;,”\"’)]*)$", titulo, re.S)
    if not m or not m.group(2):
        return titulo
    return f"{m.group(1)}**{m.group(2)}**{m.group(3)}"


# --------------------------------------------------------------------------
# Medicao de texto
# --------------------------------------------------------------------------
_DIRS_FONTES = [
    "~/.fonts", "~/.local/share/fonts", "/usr/share/fonts", "/usr/local/share/fonts",
    "/Library/Fonts", "~/Library/Fonts", "/System/Library/Fonts", "C:/Windows/Fonts",
]
_CANDIDATAS = [
    ("Lato", ("Lato-Regular.ttf", "Lato-Bold.ttf")),
    ("Inter", ("Inter-Regular.otf", "Inter-Bold.otf")),
    ("Inter", ("Inter-Regular.ttf", "Inter-Bold.ttf")),
    ("DejaVu Sans", ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")),
    ("Arial", ("arial.ttf", "arialbd.ttf")),
    ("Liberation Sans", ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf")),
]


def _achar_arquivos(nomes: tuple[str, str]) -> tuple[str, str] | None:
    achados: dict[str, str] = {}
    alvo = {n.lower(): n for n in nomes}
    for d in _DIRS_FONTES:
        base = Path(os.path.expanduser(d))
        if not base.is_dir():
            continue
        for raiz, _dirs, arqs in os.walk(base):
            for a in arqs:
                if a.lower() in alvo and alvo[a.lower()] not in achados:
                    achados[alvo[a.lower()]] = os.path.join(raiz, a)
            if len(achados) == len(nomes):
                return achados[nomes[0]], achados[nomes[1]]
    return None


class Medidor:
    """Mede largura de texto para decidir quebras de linha e alturas de caixa.

    Usa Lato se estiver instalada; senao Inter ou DejaVu (um pouco mais largas, entao a
    medida erra para o lado seguro); sem nenhuma fonte, usa largura media por caractere.
    """

    BASE = 200  # tamanho em px em que a fonte e carregada

    def __init__(self) -> None:
        self.familia = "estimativa"
        self._reg = self._neg = None
        try:
            from PIL import ImageFont
        except Exception:  # pragma: no cover
            return
        for familia, nomes in _CANDIDATAS:
            par = _achar_arquivos(nomes)
            if not par:
                continue
            try:
                self._reg = ImageFont.truetype(par[0], self.BASE)
                self._neg = ImageFont.truetype(par[1], self.BASE)
                self.familia = familia
                break
            except Exception:
                self._reg = self._neg = None

    # largura em polegadas
    def largura(self, texto: str, pt: float, negrito: bool = False, spc: float = 0.0) -> float:
        if not texto:
            return 0.0
        if self._reg is None:
            fator = 0.58 if negrito else 0.55
            w_pt = len(texto) * pt * fator
        else:
            f = self._neg if negrito else self._reg
            w_pt = f.getlength(texto) / self.BASE * pt
        w_pt += spc * len(texto)
        return w_pt / 72.0 * 1.02

    def quebrar(self, trechos: list[tuple[str, bool]], pt: float, largura: float,
                spc: float = 0.0) -> list[list[tuple[str, bool]]]:
        """Quebra uma sequencia de trechos (texto, negrito) em linhas que cabem em `largura`."""
        tokens: list[tuple[str, bool]] = []
        for texto, neg in trechos:
            for bloco in texto.split("\n"):
                for tok in re.findall(r"\S+|\s+", bloco):
                    tokens.append((tok, neg))
                tokens.append(("\n", neg))
            if tokens and tokens[-1][0] == "\n":
                tokens.pop()
        linhas: list[list[tuple[str, bool]]] = [[]]
        w_linha = 0.0
        for tok, neg in tokens:
            if tok == "\n":
                linhas.append([])
                w_linha = 0.0
                continue
            w = self.largura(tok, pt, neg, spc)
            if tok.isspace():
                if linhas[-1]:
                    linhas[-1].append((tok, neg))
                    w_linha += w
                continue
            if linhas[-1] and w_linha + w > largura:
                while linhas[-1] and linhas[-1][-1][0].isspace():
                    linhas[-1].pop()
                linhas.append([])
                w_linha = 0.0
            linhas[-1].append((tok, neg))
            w_linha += w
        return linhas

    def n_linhas(self, texto: str, pt: float, largura: float, negrito: bool = False,
                 spc: float = 0.0) -> int:
        if not sem_marcacao(texto).strip():
            return 0
        return len(self.quebrar(partes(texto, negrito), pt, largura, spc))

    def altura(self, texto: str, pt: float, largura: float, entrelinha: float,
               negrito: bool = False) -> float:
        """Altura em polegadas de um paragrafo com entrelinha exata (em pontos)."""
        return self.n_linhas(texto, pt, largura, negrito) * entrelinha / 72.0

    def largura_texto(self, texto: str, pt: float, negrito: bool = False, spc: float = 0.0) -> float:
        return sum(self.largura(t, pt, n or negrito, spc) for t, n in partes(texto))


# --------------------------------------------------------------------------
# Leitura do deck e utilidades comuns
# --------------------------------------------------------------------------

def carregar_json(caminho: Path):
    import json
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sair(f"Arquivo não encontrado: {caminho}")
    except json.JSONDecodeError as e:
        sair(f"JSON inválido em {caminho}: linha {e.lineno}, coluna {e.colno}: {e.msg}")


def sair(msg: str, codigo: int = 2):
    print(f"ERRO: {msg}", file=sys.stderr)
    raise SystemExit(codigo)


def como_lista(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def indice_referencias(deck: dict) -> dict[str, dict]:
    return {str(r.get("id")): r for r in como_lista(deck.get("referencias")) if isinstance(r, dict) and r.get("id")}


def carregar_catalogo(deck: dict, base: Path) -> tuple[dict[str, dict], Path | None]:
    """Devolve ({id: entrada}, pasta das figuras). O caminho vem de meta.catalogo, relativo ao deck.json."""
    meta = deck.get("meta") or {}
    cam = meta.get("catalogo")
    candidatos = [base / cam] if cam else [base / "../03_figuras/catalogo.json", base / "figuras/catalogo.json"]
    for c in candidatos:
        c = c.resolve()
        if c.is_file():
            import json
            try:
                dados = json.loads(c.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"AVISO: não consegui ler o catálogo {c}: {e}", file=sys.stderr)
                return {}, None
            if isinstance(dados, dict):
                dados = dados.get("figuras") or list(dados.values())
            return {str(d.get("id")): d for d in dados if isinstance(d, dict) and d.get("id")}, c.parent
    return {}, None


def resolver_figura(slide: dict, catalogo: dict[str, dict], pasta_cat: Path | None, base: Path) -> dict:
    """Junta o que o slide diz com o que o catalogo sabe. Devolve dict com
    caminho (Path ou None), citacao, legenda, chave, licenca, largura_px, altura_px, aprovada, id."""
    fig = slide.get("figura") or {}
    if isinstance(fig, str):
        fig = {"id": fig}
    ent = catalogo.get(str(fig.get("id"))) if fig.get("id") else None
    ent = ent or {}
    arq = fig.get("arquivo") or ent.get("arquivo")
    caminho = None
    if arq:
        tentativas = [base / arq]
        if pasta_cat:
            tentativas.insert(0 if not fig.get("arquivo") else 1, pasta_cat / arq)
        for t in tentativas:
            if t.is_file():
                caminho = t.resolve()
                break
        if caminho is None:
            caminho = tentativas[0]
    info = {
        "id": fig.get("id"),
        "caminho": caminho,
        "existe": bool(caminho and Path(caminho).is_file()),
        "citacao": fig.get("citacao") or ent.get("citacao"),
        "legenda": slide.get("legenda") or fig.get("legenda") or ent.get("legenda_pt"),
        "chave": fig.get("ref") or ent.get("chave"),
        "licenca": fig.get("licenca") or ent.get("licenca"),
        "aprovada": ent.get("aprovada", True) if ent else True,
        "no_catalogo": bool(ent),
        "largura_px": None, "altura_px": None,
    }
    if info["existe"]:
        try:
            from PIL import Image
            with Image.open(info["caminho"]) as im:
                info["largura_px"], info["altura_px"] = im.size
        except Exception:
            info["existe"] = False
    return info


# Densidade minima de pixels por polegada de slide: abaixo disso a figura fica borrada
# num compartilhamento de tela em 1080p. E o teto de ampliacao de qualquer figura.
PPP_MINIMO = 110
