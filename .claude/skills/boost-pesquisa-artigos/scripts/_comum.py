#!/usr/bin/env python3
"""Funções compartilhadas pelos scripts da skill boost-pesquisa-artigos.

Não é um script de linha de comando. Reúne: cliente HTTP educado (intervalo mínimo
por host, novas tentativas com espera crescente), normalizadores (DOI, título, ISSN),
leitura/validação de conceitos.json e conversão de termos de busca em expressões
regulares para casar texto localmente.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

EMAIL_PADRAO = "contato@boosteducation.com.br"
FERRAMENTA = "boost_education"
RECORTES = ("topo_mecanismos", "so_topo", "fronteira")

DESENHOS = [
    "Diretriz",
    "Revisao sistematica/meta-analise",
    "ECR",
    "Coorte",
    "Caso-controle",
    "Transversal",
    "Estudo de acuracia diagnostica",
    "Consenso/Delphi",
    "Laboratorio/mecanistico",
    "Revisao narrativa",
    "Relato/serie de casos",
    "Editorial/comentario",
    "Outro",
]

# JOSPT é o padrão de revista-alvo (ISSN impresso e eletrônico conferidos no NLM Catalog e na Crossref).
JOSPT = {"nome": "J Orthop Sports Phys Ther", "issn": ["0190-6011", "1938-1344"]}


class ErroRede(Exception):
    """Falha de rede já explicada em português."""


def email_contato(valor: str | None = None) -> str:
    """E-mail enviado às APIs: --email, depois BOOST_EMAIL, depois o genérico."""
    return (valor or os.environ.get("BOOST_EMAIL") or EMAIL_PADRAO).strip()


def hoje_iso() -> str:
    return date.today().isoformat()


def agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- HTTP

class Cliente:
    """Sessão HTTP com intervalo mínimo entre chamadas ao mesmo host e novas tentativas.

    O NCBI bloqueia quem passa de 3 requisições por segundo sem chave; Crossref e
    OpenAlex pedem identificação por e-mail. Erros temporários (429, 5xx, queda de
    conexão) são repetidos com espera crescente; o que continuar falhando vira
    ErroRede com mensagem legível, para o script registrar e seguir adiante.
    """

    INTERVALOS = {
        "eutils.ncbi.nlm.nih.gov": 0.4,
        "api.crossref.org": 0.3,
        "api.openalex.org": 0.12,
    }

    def __init__(self, email: str | None = None, tentativas: int = 5, espera_base: float = 1.5,
                 tempo_limite: float = 60.0, silencioso: bool = False):
        if requests is None:
            raise ErroRede("A biblioteca 'requests' não está instalada (pip install requests).")
        self.email = email_contato(email)
        self.tentativas = tentativas
        self.espera_base = espera_base
        self.tempo_limite = tempo_limite
        self.silencioso = silencioso
        self._ultimo: dict[str, float] = {}
        self.sessao = requests.Session()
        self.sessao.headers["User-Agent"] = f"{FERRAMENTA}/1.0 (mailto:{self.email})"
        self.chamadas = 0

    def _aguardar(self, host: str) -> None:
        minimo = self.INTERVALOS.get(host, 0.05)
        if os.environ.get("NCBI_API_KEY") and host == "eutils.ncbi.nlm.nih.gov":
            minimo = 0.11
        decorrido = time.monotonic() - self._ultimo.get(host, 0.0)
        if decorrido < minimo:
            time.sleep(minimo - decorrido)
        self._ultimo[host] = time.monotonic()

    def pedir(self, metodo: str, url: str, params: dict | None = None, dados: dict | None = None,
              aceitar_404: bool = False):
        host = urlparse(url).netloc
        ultimo_erro = ""
        for tentativa in range(1, self.tentativas + 1):
            self._aguardar(host)
            self.chamadas += 1
            try:
                if metodo == "POST":
                    resp = self.sessao.post(url, params=params, data=dados, timeout=self.tempo_limite)
                else:
                    resp = self.sessao.get(url, params=params, timeout=self.tempo_limite)
            except requests.exceptions.ProxyError as exc:
                raise ErroRede(f"sem acesso a {host}: o proxy recusou a conexão (host bloqueado ou ambiente sem "
                               f"rede; veja 'Sem rede' no SKILL.md). Detalhe: {str(exc)[:110]}") from None
            except requests.exceptions.RequestException as exc:
                ultimo_erro = f"{type(exc).__name__}: {str(exc)[:160]}"
            else:
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 404 and aceitar_404:
                    return resp
                ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:160].strip()}"
                if resp.status_code not in (408, 425, 429, 500, 502, 503, 504):
                    raise ErroRede(f"{host} respondeu {ultimo_erro}")
                apos = resp.headers.get("Retry-After", "")
                if apos.isdigit():
                    time.sleep(min(int(apos), 60))
            if tentativa < self.tentativas:
                espera = self.espera_base * (2 ** (tentativa - 1))
                if not self.silencioso:
                    print(f"  [rede] {host}: {ultimo_erro} - nova tentativa em {espera:.0f} s "
                          f"({tentativa}/{self.tentativas})", file=sys.stderr)
                time.sleep(espera)
        raise ErroRede(f"{host} não respondeu depois de {self.tentativas} tentativas ({ultimo_erro}).")

    def get(self, url: str, params: dict | None = None, **kw):
        return self.pedir("GET", url, params=params, **kw)

    def post(self, url: str, dados: dict | None = None, **kw):
        return self.pedir("POST", url, dados=dados, **kw)


def json_com(resp, chave: str, servico: str) -> dict:
    """JSON da resposta, exigindo a chave esperada. Corpo vazio, HTML de erro ou '{}' viram ErroRede: sem isso
    uma resposta quebrada passava por 'zero resultados' e o script terminava como se tudo estivesse certo."""
    try:
        dados = resp.json()
    except ValueError:
        raise ErroRede(f"{servico} devolveu uma resposta que não é JSON (vazia ou página de erro).") from None
    if not isinstance(dados, dict) or chave not in dados:
        raise ErroRede(f"{servico} devolveu uma resposta incompleta (sem '{chave}').")
    return dados


# --------------------------------------------------------------------------- arquivos

def ler_json(caminho: str | Path, padrao=None):
    caminho = Path(caminho)
    if not caminho.exists():
        return padrao
    with caminho.open(encoding="utf-8-sig") as arq:
        return json.load(arq)


def gravar_json(caminho: str | Path, dados) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    provisorio = caminho.with_suffix(caminho.suffix + ".tmp")
    with provisorio.open("w", encoding="utf-8") as arq:
        json.dump(dados, arq, ensure_ascii=False, indent=2)
        arq.write("\n")
    provisorio.replace(caminho)


def sair(mensagem: str, codigo: int = 2):
    print(f"ERRO: {mensagem}", file=sys.stderr)
    raise SystemExit(codigo)


# --------------------------------------------------------------------------- normalização

# letras que a decomposição Unicode não separa em letra + acento
_LETRAS_ESPECIAIS = str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ł": "l", "Ł": "L",
                                   "đ": "d", "Đ": "D", "ð": "d", "Ð": "D", "þ": "th", "Þ": "Th", "ß": "ss", "ı": "i"})


def sem_acento(texto: str) -> str:
    """'Dubé' -> 'Dube'; 'Trøstrup' -> 'Trostrup'; 'Egebæk' -> 'Egebaek'."""
    texto = (texto or "").translate(_LETRAS_ESPECIAIS)
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


_DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)", re.I)


def normalizar_doi(valor) -> str | None:
    """Devolve o DOI em minúsculas, sem prefixo de URL nem pontuação final; None se não for DOI."""
    if not valor:
        return None
    texto = str(valor).strip()
    texto = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", texto, flags=re.I)
    texto = re.sub(r"^doi:\s*", "", texto, flags=re.I)
    achado = _DOI_RE.search(texto)
    if not achado:
        return None
    return achado.group(1).rstrip(".,;)]}").lower()


def normalizar_pmid(valor) -> str | None:
    if valor is None:
        return None
    achado = re.search(r"\d{1,9}", str(valor))
    if not achado:
        return None
    numero = achado.group(0).lstrip("0")
    return numero or None


def normalizar_issn(valor) -> str | None:
    """Aceita '01906011', '0190-6011', '0190-6011 (ISSN)' e devolve '0190-6011'."""
    if not valor:
        return None
    achado = re.search(r"(\d{4})-?(\d{3}[\dXx])", str(valor))
    if not achado:
        return None
    return f"{achado.group(1)}-{achado.group(2).upper()}"


def lista_issn(valor) -> list[str]:
    if not valor:
        return []
    if isinstance(valor, (list, tuple, set)):
        partes = list(valor)
    else:
        partes = re.split(r"[;,\s]+", str(valor))
    saida = []
    for parte in partes:
        issn = normalizar_issn(parte)
        if issn and issn not in saida:
            saida.append(issn)
    return saida


_ARTIGOS_INICIAIS = re.compile(r"^(the|a|an|o|os|as|um|uma|el|la|los|las)\s+")


def normalizar_titulo(titulo: str) -> str:
    """Título reduzido a letras e números, para comparar registros de bases diferentes."""
    texto = re.sub(r"<[^>]+>", " ", titulo or "")
    texto = sem_acento(texto).lower()
    texto = texto.replace("&amp;", " and ").replace("&", " and ")
    texto = re.sub(r"[^a-z0-9]+", " ", texto).strip()
    texto = _ARTIGOS_INICIAIS.sub("", texto)
    return re.sub(r"\s+", " ", texto)


def limpar_texto(texto: str | None) -> str:
    """Remove marcação (JATS/HTML) e espaços repetidos."""
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", str(texto))
    texto = (texto.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
             .replace("&quot;", '"').replace("&#x2019;", "'").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", texto).strip()


def sobrenome_de(autor: str) -> str:
    """'Cools AM' -> 'Cools'; 'Cools, Ann M.' -> 'Cools'; 'van der Windt DA' -> 'van der Windt'."""
    autor = (autor or "").strip()
    if not autor:
        return ""
    if "," in autor:
        return autor.split(",")[0].strip()
    partes = autor.split()
    while len(partes) > 1 and re.fullmatch(r"(?:[A-Z]\.?-?){1,4}|Jr\.?|Sr\.?|II|III|\d(?:st|nd|rd|th)", partes[-1]):
        partes.pop()
    return " ".join(partes)


def autor_curto(sobrenome: str, nomes: str) -> str:
    """Formata 'Cools' + 'Ann M.' como 'Cools AM' (padrão do PubMed)."""
    sobrenome = (sobrenome or "").strip()
    nomes = (nomes or "").strip()
    if not nomes:
        return sobrenome
    iniciais = "".join(p[0].upper() for p in re.split(r"[\s.\-]+", nomes) if p and p[0].isalpha())
    return f"{sobrenome} {iniciais}".strip()


def para_int(valor) -> int | None:
    if valor is None or valor == "":
        return None
    achado = re.search(r"-?\d+", str(valor))
    return int(achado.group(0)) if achado else None


# --------------------------------------------------------------------------- conceitos.json

def _como_lista(valor) -> list:
    if valor is None:
        return []
    if isinstance(valor, (list, tuple)):
        return list(valor)
    return [valor]


def limpar_termo(termo: str) -> str:
    """Tira aspas, chaves e espaços sobrando; a citação de frases é feita pelo gerador."""
    termo = str(termo).strip()
    termo = termo.strip('"').strip("“”").strip("{}").strip()
    return re.sub(r"\s+", " ", termo)


def normalizar_mesh(item) -> dict:
    if isinstance(item, str):
        item = {"termo": item}
    return {
        "termo": limpar_termo(item.get("termo", "")),
        "explodir": bool(item.get("explodir", True)),
        "principal": bool(item.get("principal", False)),
        "subtitulos": [str(s).strip() for s in _como_lista(item.get("subtitulos"))],
    }


def carregar_conceitos(caminho: str | Path) -> dict:
    """Lê conceitos.json, aplica padrões e valida. Encerra com mensagem clara se estiver inválido."""
    caminho = Path(caminho)
    if not caminho.exists():
        sair(f"Arquivo de conceitos não encontrado: {caminho}")
    try:
        bruto = ler_json(caminho)
    except json.JSONDecodeError as exc:
        sair(f"{caminho} não é JSON válido: {exc}")
    if not isinstance(bruto, dict):
        sair(f"{caminho} deve ser um objeto JSON com a chave 'blocos'.")
    erros: list[str] = []
    c = {
        "tema": str(bruto.get("tema", "")).strip(),
        "pergunta": bruto.get("pergunta") or {},
        "recorte": bruto.get("recorte") or "topo_mecanismos",
        "blocos": [],
        "excluir": None,
        "limites": {},
        "revistas_alvo": [],
        "sentinelas": [],
    }
    if c["recorte"] not in RECORTES:
        erros.append(f"recorte '{c['recorte']}' inválido; use um de: {', '.join(RECORTES)}")
    blocos = bruto.get("blocos")
    if not isinstance(blocos, list) or not blocos:
        erros.append("'blocos' precisa ser uma lista com pelo menos um bloco de conceito")
        blocos = []
    ids = set()
    for i, b in enumerate(blocos, 1):
        if not isinstance(b, dict):
            erros.append(f"bloco {i}: deve ser um objeto")
            continue
        bid = str(b.get("id") or f"bloco{i}").strip()
        if bid in ids:
            erros.append(f"bloco {i}: id repetido '{bid}'")
        ids.add(bid)
        campo = (b.get("campo") or "tiab").lower()
        if campo not in ("tiab", "ti", "tw"):
            erros.append(f"bloco '{bid}': campo '{campo}' inválido (use tiab, ti ou tw)")
        mesh = [normalizar_mesh(m) for m in _como_lista(b.get("mesh"))]
        livres = [limpar_termo(t) for t in _como_lista(b.get("livres")) if str(t).strip()]
        prox = []
        for j, p in enumerate(_como_lista(b.get("proximidade")), 1):
            lado_a = [limpar_termo(t) for t in _como_lista(p.get("a"))]
            lado_b = [limpar_termo(t) for t in _como_lista(p.get("b"))]
            n = p.get("n", p.get("distancia", 3))
            if not lado_a or not lado_b or not isinstance(n, int) or n < 0:
                erros.append(f"bloco '{bid}', proximidade {j}: precisa de 'a', 'b' (listas) e 'n' (inteiro >= 0)")
                continue
            prox.append({"a": lado_a, "b": lado_b, "n": n, "ordenado": bool(p.get("ordenado", False))})
        if not mesh and not livres and not prox:
            erros.append(f"bloco '{bid}': vazio (informe 'mesh', 'livres' ou 'proximidade')")
        c["blocos"].append({
            "id": bid,
            "rotulo": str(b.get("rotulo") or bid).strip(),
            "papel": str(b.get("papel") or "").strip(),
            "campo": campo,
            "mesh": mesh,
            "livres": livres,
            "proximidade": prox,
            "simples": [limpar_termo(t) for t in _como_lista(b.get("simples"))],
            "scopus_extra": [limpar_termo(t) for t in _como_lista(b.get("scopus_extra"))],
        })
    exc = bruto.get("excluir")
    if exc:
        c["excluir"] = {
            "mesh": [normalizar_mesh(m) for m in _como_lista(exc.get("mesh"))],
            "livres": [limpar_termo(t) for t in _como_lista(exc.get("livres"))],
            "campo": (exc.get("campo") or "ti").lower(),
        }
    lim = bruto.get("limites") or {}
    c["limites"] = {
        "ano_inicio": para_int(lim.get("ano_inicio")),
        "ano_fim": para_int(lim.get("ano_fim")),
        "idiomas": [str(x).strip().lower() for x in _como_lista(lim.get("idiomas"))],
        "somente_humanos": bool(lim.get("somente_humanos", False)),
        "tipos_scopus": [str(x).strip().lower() for x in _como_lista(lim.get("tipos_scopus"))],
    }
    for r in _como_lista(bruto.get("revistas_alvo")):
        if isinstance(r, str):
            r = {"nome": r, "issn": [r]}
        issns = lista_issn(r.get("issn"))
        if not issns:
            erros.append(f"revista-alvo '{r.get('nome')}': sem ISSN válido")
        c["revistas_alvo"].append({"nome": str(r.get("nome") or "").strip(), "issn": issns})
    for s in _como_lista(bruto.get("sentinelas")):
        if isinstance(s, (str, int)):
            texto = str(s)
            s = {"doi": texto} if normalizar_doi(texto) else {"pmid": texto}
        item = {"pmid": normalizar_pmid(s.get("pmid")), "doi": normalizar_doi(s.get("doi")),
                "nota": str(s.get("nota") or "").strip()}
        if not item["pmid"] and not item["doi"]:
            erros.append(f"sentinela sem PMID nem DOI válido: {s}")
        c["sentinelas"].append(item)
    if erros:
        sair("conceitos.json inválido:\n  - " + "\n  - ".join(erros))
    return c


def issns_alvo(conceitos: dict | None) -> list[str]:
    saida: list[str] = []
    for r in (conceitos or {}).get("revistas_alvo") or []:
        for issn in r["issn"]:
            if issn not in saida:
                saida.append(issn)
    return saida


# --------------------------------------------------------------------------- casar texto localmente

def termo_para_regex(termo: str) -> re.Pattern:
    """Converte um termo livre (com * de truncagem) em regex para casar titulo/resumo.

    'rotator cuff tendinopath*' casa 'rotator cuff tendinopathy' e 'rotator-cuff tendinopathies'.
    """
    termo = sem_acento(limpar_termo(termo)).lower()
    palavras = [p for p in re.split(r"[\s\-/]+", termo) if p]
    partes = []
    for palavra in palavras:
        if palavra.endswith("*"):
            partes.append(re.escape(palavra.rstrip("*")) + r"\w*")
        elif "*" in palavra or "?" in palavra:
            partes.append(re.escape(palavra).replace(r"\*", r"\w*").replace(r"\?", r"\w"))
        else:
            partes.append(re.escape(palavra))
    if not partes:
        return re.compile(r"(?!x)x")
    return re.compile(r"\b" + r"[\s\-/]+".join(partes) + r"\b")


def _prox_casa(texto: str, p: dict) -> bool:
    palavras = re.findall(r"\w+", texto)
    posicoes_a, posicoes_b = [], []
    for lado, destino in ((p["a"], posicoes_a), (p["b"], posicoes_b)):
        for termo in lado:
            partes = [x for x in re.split(r"[\s\-/]+", sem_acento(termo).lower()) if x]
            for i in range(len(palavras) - len(partes) + 1):
                ok = True
                for k, parte in enumerate(partes):
                    palavra = palavras[i + k]
                    if parte.endswith("*"):
                        ok = palavra.startswith(parte.rstrip("*"))
                    else:
                        ok = palavra == parte
                    if not ok:
                        break
                if ok:
                    destino.append((i, i + len(partes) - 1))
    for (a0, a1) in posicoes_a:
        for (b0, b1) in posicoes_b:
            if b0 > a1:
                distancia = b0 - a1 - 1
            elif a0 > b1:
                if p.get("ordenado"):
                    continue
                distancia = a0 - b1 - 1
            else:
                continue
            if distancia <= p["n"]:
                return True
    return False


def bloco_casa_texto(bloco: dict, texto: str, mesh_do_registro: list[str] | None = None) -> bool:
    """Diz se o texto (título + resumo) contém algum termo do bloco. MeSH conta se o registro o tiver."""
    texto = sem_acento(texto or "").lower()
    if mesh_do_registro:
        tem = {m.lower() for m in mesh_do_registro}
        for m in bloco.get("mesh", []):
            if m["termo"].lower() in tem:
                return True
    for termo in list(bloco.get("livres", [])) + list(bloco.get("scopus_extra", [])):
        if termo_para_regex(termo).search(texto):
            return True
    for p in bloco.get("proximidade", []):
        if _prox_casa(texto, p):
            return True
    # o nome do descritor MeSH escrito por extenso também conta como texto livre
    for m in bloco.get("mesh", []):
        nome = m["termo"].lower()
        if "," not in nome and termo_para_regex(nome).search(texto):
            return True
    return False


def blocos_casados(conceitos: dict | None, titulo: str, resumo: str = "", mesh: list[str] | None = None) -> list[str]:
    if not conceitos:
        return []
    texto = f"{titulo or ''} . {resumo or ''}"
    return [b["id"] for b in conceitos["blocos"] if bloco_casa_texto(b, texto, mesh)]


_TITULO_DIRETRIZ = re.compile(r"\b(guideline|guidelines|consensus|position statement|position stand|"
                              r"clinical practice recommendation)", re.I)


def passa_filtro_local(reg: dict, conceitos: dict | None, modo: str = "auto") -> bool:
    """Filtro pelos blocos de conceito para fontes sem busca booleana (Crossref, OpenAlex).

    Grava reg['blocos_casados']. Modos:
      nenhum  não filtra
      um      pelo menos um bloco no titulo/resumo
      todos   todos os blocos no titulo/resumo
      âncora  o bloco da condição (papel P; na falta, o primeiro) no titulo/resumo
      auto    com resumo, exige todos os blocos; sem resumo, exige a âncora no título. Diretrizes e
              consensos (pelo título) passam só com a âncora, porque o resumo de uma diretriz costuma
              falar em 'tratamento' ou 'reabilitacao' sem nomear cada intervenção.
    """
    if not conceitos or modo == "nenhum":
        return True
    casados = blocos_casados(conceitos, reg.get("titulo") or "", reg.get("resumo") or "")
    reg["blocos_casados"] = casados
    todos = [b["id"] for b in conceitos["blocos"]]
    ancora = next((b["id"] for b in conceitos["blocos"] if b["papel"].upper() == "P"), todos[0])
    if modo == "todos":
        return len(casados) == len(todos)
    if modo == "um":
        return bool(casados)
    if modo == "ancora":
        return ancora in casados
    if len(casados) == len(todos):
        return True
    if ancora not in casados:
        return False
    if not reg.get("resumo"):
        return bool(blocos_casados({"blocos": [b for b in conceitos["blocos"] if b["id"] == ancora]},
                                   reg.get("titulo") or ""))
    return bool(_TITULO_DIRETRIZ.search(reg.get("titulo") or ""))
