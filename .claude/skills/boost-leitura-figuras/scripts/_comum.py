"""Funcoes compartilhadas pelos scripts da skill boost-leitura-figuras.

Cuida do contrato de pastas da aula, da leitura dos registros, do manifest,
do catalogo de figuras, da normalizacao de licencas e do acesso educado a rede.
Nao tem efeito colateral ao ser importado.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

EMAIL_PADRAO = "contato@boosteducation.com.br"
FERRAMENTA = os.environ.get("BOOST_TOOL", "boost_education")
AGENTE = "leitor-artigos-academicos/1.0 (python-requests; uso educacional)"

# --------------------------------------------------------------------------
# Pastas e arquivos do contrato
# --------------------------------------------------------------------------


class Aula:
    """Caminhos de uma pasta de aula (aulas/<AAAA-MM>-<slug>/)."""

    def __init__(self, pasta: str | os.PathLike):
        self.raiz = Path(pasta).expanduser().resolve()
        self.busca = self.raiz / "01_busca"
        self.artigos = self.raiz / "02_artigos"
        self.pdf = self.artigos / "pdf"
        self.manual = self.artigos / "manual"
        self.texto = self.artigos / "texto"
        self.leitura = self.artigos / "leitura"
        self.manifest = self.artigos / "manifest.json"
        self.pendentes = self.artigos / "pendentes.md"
        self.figuras = self.raiz / "03_figuras"
        self.paginas = self.figuras / "paginas"
        self.catalogo = self.figuras / "catalogo.json"

    def criar_pastas(self) -> None:
        for p in (self.pdf, self.manual, self.texto, self.leitura, self.figuras, self.paginas):
            p.mkdir(parents=True, exist_ok=True)

    def exigir(self) -> None:
        if not self.raiz.is_dir():
            sair(f"Pasta da aula não encontrada: {self.raiz}")


def sair(msg: str, codigo: int = 2) -> None:
    print(f"ERRO: {msg}", file=sys.stderr)
    raise SystemExit(codigo)


def agora() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def ler_json(caminho: Path, padrao=None):
    if not caminho.exists():
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def gravar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # nome temporário único: vários processos podem gravar a mesma pasta ao mesmo tempo
    tmp = caminho.with_suffix(f"{caminho.suffix}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(caminho)


# --------------------------------------------------------------------------
# Texto
# --------------------------------------------------------------------------


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalizar_texto(s: str) -> str:
    """Minusculas, sem acento, so letras e numeros separados por um espaco."""
    s = sem_acento(s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalizar_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = str(doi).strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    d = d.rstrip(".,;)")
    return d or None


RE_DOI = re.compile(r"10\.\d{4,9}/[^\s\"<>\]\[{}|^`\\]+", re.I)


def achar_dois(texto: str) -> list[str]:
    """DOIs presentes em um texto, normalizados, na ordem em que aparecem."""
    vistos, saida = set(), []
    for m in RE_DOI.finditer(texto or ""):
        d = normalizar_doi(m.group(0))
        # sufixos comuns colados ao DOI no PDF
        d = re.sub(r"(/-/dcsupplemental|\.pdf|/full|/abstract)$", "", d or "")
        if d and d not in vistos:
            vistos.add(d)
            saida.append(d)
    return saida


# --------------------------------------------------------------------------
# Registros
# --------------------------------------------------------------------------


def _chave_de(reg: dict) -> str:
    autor = reg.get("primeiro_autor") or ""
    if not autor and reg.get("autores"):
        autor = str(reg["autores"][0]).split(",")[0].split(" ")[0]
    autor = re.sub(r"[^A-Za-z]", "", sem_acento(autor)) or "Artigo"
    ano = reg.get("ano") or ""
    return f"{autor[:1].upper()}{autor[1:]}{ano}"


def carregar_registros(aula: Aula, caminho: str | None = None) -> tuple[list[dict], Path]:
    """Le selecionados.json (preferido) ou registros.json. Garante 'chave' unica."""
    candidatos = [Path(caminho)] if caminho else [aula.busca / "selecionados.json", aula.busca / "registros.json"]
    origem = next((c for c in candidatos if c.exists()), None)
    if origem is None:
        sair("Não encontrei 01_busca/selecionados.json nem 01_busca/registros.json. "
             "Rode antes a skill boost-pesquisa-artigos ou informe --registros.")
    dados = ler_json(origem)
    if isinstance(dados, dict):
        for k in ("selecionados", "registros", "artigos", "itens"):
            if isinstance(dados.get(k), list):
                dados = dados[k]
                break
    if not isinstance(dados, list):
        sair(f"{origem} não contém uma lista de registros.")
    usados: set[str] = set()
    registros = []
    for reg in dados:
        if not isinstance(reg, dict):
            continue
        chave = str(reg.get("chave") or _chave_de(reg))
        chave = re.sub(r"[^A-Za-z0-9_-]", "", sem_acento(chave)) or "Artigo"
        base, n = chave, 0
        while chave in usados:
            n += 1
            chave = f"{base}{chr(ord('a') + n)}"
        usados.add(chave)
        reg = dict(reg)
        reg["chave"] = chave
        reg["doi"] = normalizar_doi(reg.get("doi"))
        registros.append(reg)
    return registros, origem


def papel_na_aula(reg: dict) -> str:
    """Por que o artigo importa para a aula, no que o registro trouxer."""
    for k in ("papel", "papel_na_aula", "por_que_importa", "por_que", "motivo", "justificativa", "nota"):
        v = reg.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    mot = reg.get("motivos_pontuacao")
    if isinstance(mot, list) and mot:
        return "; ".join(str(m) for m in mot[:3])
    des = reg.get("desenho")
    return f"Selecionado para a aula ({des})." if des else "Selecionado para a aula."


def autores_curto(reg: dict) -> str:
    autores = reg.get("autores") or []
    if isinstance(autores, str):
        autores = [a.strip() for a in re.split(r";|,(?=\s*[A-Z][a-z])", autores) if a.strip()]
    if not autores:
        return reg.get("primeiro_autor") or "Autor não informado"
    primeiro = str(autores[0]).strip().rstrip(".")
    return f"{primeiro} et al" if len(autores) > 1 else primeiro


def citacao_curta(reg: dict, extra: dict | None = None, rotulo: str | None = None) -> str:
    """Ex.: 'Cools AM et al. Ann Phys Rehabil Med. 2021;64(4):101384. Fig. 2.'"""
    extra = extra or {}
    partes = [autores_curto(reg) + "."]
    revista = (reg.get("revista") or extra.get("revista") or "").strip().rstrip(".")
    if revista:
        partes.append(revista + ".")
    ano = reg.get("ano") or extra.get("ano")
    vol = reg.get("volume") or extra.get("volume")
    num = reg.get("numero") or reg.get("fasciculo") or extra.get("numero")
    pag = reg.get("paginas") or extra.get("paginas_artigo")
    bib = str(ano) if ano else ""
    if vol:
        bib += f";{vol}"
        if num:
            bib += f"({num})"
    if pag:
        bib += f":{pag}"
    if bib:
        partes.append(bib + ".")
    if rotulo:
        partes.append(rotulo_curto(rotulo) + ".")
    return " ".join(partes)


def rotulo_curto(rotulo: str) -> str:
    """'Figure 2' -> 'Fig. 2'; 'Table 1' -> 'Tab. 1'."""
    m = re.match(r"\s*(\D+?)\.?\s*(S?\d+[A-Za-z]?|[IVXLC]+)\s*$", rotulo or "")
    if not m:
        return (rotulo or "").strip().rstrip(".")
    nome = normalizar_texto(m.group(1))
    if nome.startswith(("tab", "quadro")):
        return f"Tab. {m.group(2)}"
    return f"Fig. {m.group(2)}"


# --------------------------------------------------------------------------
# Licencas
# --------------------------------------------------------------------------

LICENCA_RESERVADA = "todos os direitos reservados"
LICENCA_DESCONHECIDA = "desconhecida"


def normalizar_licenca(valor: str | None) -> str | None:
    """Converte as varias grafias (API, URL, texto) em um rotulo unico.

    Retorna 'cc-by', 'cc-by-nc', 'cc-by-nc-nd', 'cc-by-nc-sa', 'cc-by-sa', 'cc-by-nd',
    'cc0', 'dominio publico', 'todos os direitos reservados', 'desconhecida' ou None.
    """
    if not valor:
        return None
    v = str(valor).strip().lower()
    if not v or v in {"none", "null", "unknown"}:
        return None
    if "reservad" in v or "all rights reserved" in v:
        return LICENCA_RESERVADA
    if "desconhecid" in v:
        return LICENCA_DESCONHECIDA
    if "cc0" in v or "publicdomain/zero" in v:
        return "cc0"
    if "public-domain" in v or "public domain" in v or v == "pd" or "dominio publico" in sem_acento(v):
        return "dominio publico"
    m = re.search(r"(?:licenses/|cc[\s_-]*)(by(?:[\s_-]*(?:nc|nd|sa))*)", v)
    if m:
        partes = re.findall(r"by|nc|nd|sa", m.group(1))
        ordem = [p for p in ("by", "nc", "nd", "sa") if p in partes]
        return "cc-" + "-".join(ordem)
    return LICENCA_DESCONHECIDA


def licenca_no_texto(texto: str) -> str | None:
    """Procura a declaracao de licenca Creative Commons no texto do proprio PDF."""
    t = (texto or "").lower()
    m = re.search(r"creativecommons\.org/\s*licen[sc]es/\s*(by(?:-(?:nc|nd|sa))*)", t)
    if m:
        return normalizar_licenca("cc-" + m.group(1))
    if "creativecommons.org/publicdomain/zero" in t:
        return "cc0"
    m = re.search(r"\(?\bcc[\s-]by((?:[\s-](?:nc|nd|sa))*)\b", t)
    if m:
        return normalizar_licenca("cc-by" + m.group(1))
    m = re.search(r"creative\s+commons\s+attribution((?:[\s-]+(?:non[\s-]?commercial|no[\s-]?derivat\w+|share[\s-]?alike))*)", t)
    if m:
        resto = m.group(1)
        lic = "cc-by"
        if re.search(r"non[\s-]?commercial", resto):
            lic += "-nc"
        if re.search(r"no[\s-]?derivat", resto):
            lic += "-nd"
        if re.search(r"share[\s-]?alike", resto):
            lic += "-sa"
        return lic
    return None


def licenca_permite_reproduzir(lic: str | None) -> bool:
    return bool(lic) and (lic.startswith("cc") or lic == "dominio publico")


# --------------------------------------------------------------------------
# Manifest (lista de objetos, uma entrada por artigo)
# --------------------------------------------------------------------------


def carregar_manifest(aula: Aula) -> dict[str, dict]:
    dados = ler_json(aula.manifest, [])
    if isinstance(dados, dict):
        dados = dados.get("artigos") or list(dados.values())
    return {str(e["chave"]): e for e in dados if isinstance(e, dict) and e.get("chave")}


def salvar_manifest(aula: Aula, entradas: dict[str, dict]) -> None:
    gravar_json(aula.manifest, list(entradas.values()))


def entrada_manifest(reg: dict, existente: dict | None = None) -> dict:
    e = dict(existente or {})
    e.setdefault("chave", reg["chave"])
    for campo in ("titulo", "doi", "pmid", "pmcid", "revista", "ano"):
        if reg.get(campo) not in (None, ""):
            e[campo] = reg[campo]
    e.setdefault("status", "pendente")
    e.setdefault("origem", None)
    e.setdefault("licenca", None)
    return e


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Catalogo de figuras (lista de objetos)
# --------------------------------------------------------------------------


# Vários agentes podem trabalhar artigos diferentes da mesma aula em paralelo. Cada processo guarda
# o catálogo como estava quando o leu; ao salvar, relê o arquivo sob trava e aplica só o que ele
# mesmo mudou (entradas novas, alteradas ou removidas), sem apagar o que outro processo gravou.
_CATALOGO_LIDO: dict[str, dict[str, str]] = {}


def _ler_catalogo_arquivo(caminho: Path) -> list[dict]:
    dados = ler_json(caminho, [])
    if isinstance(dados, dict):
        dados = dados.get("figuras") or []
    return [e for e in dados if isinstance(e, dict) and e.get("id")]


def _assinatura(e: dict) -> str:
    return json.dumps(e, ensure_ascii=False, sort_keys=True)


def carregar_catalogo(aula: Aula) -> list[dict]:
    itens = _ler_catalogo_arquivo(aula.catalogo)
    _CATALOGO_LIDO[str(aula.catalogo)] = {e["id"]: _assinatura(e) for e in itens}
    return itens


def salvar_catalogo(aula: Aula, itens: list[dict]) -> None:
    def ordem(e):
        m = re.search(r"(\d+)", str(e.get("rotulo") or e["id"].split("_", 1)[-1]))
        return (str(e.get("chave")), int(e.get("pagina") or 0), int(m.group(1)) if m else 0, e["id"])

    caminho = aula.catalogo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    trava = open(caminho.with_suffix(caminho.suffix + ".lock"), "a")
    try:
        try:
            import fcntl
            fcntl.flock(trava, fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass  # sem trava disponível (ex.: Windows): segue com a mesclagem simples
        lido = _CATALOGO_LIDO.get(str(caminho))
        if lido is None:
            final = list(itens)
        else:
            meus = {e["id"]: e for e in itens}
            removidos = set(lido) - set(meus)
            mudados = {i: e for i, e in meus.items() if lido.get(i) != _assinatura(e)}
            atual = {e["id"]: e for e in _ler_catalogo_arquivo(caminho)}
            for i in removidos:
                atual.pop(i, None)
            atual.update(mudados)
            final = list(atual.values())
        gravar_json(caminho, sorted(final, key=ordem))
        _CATALOGO_LIDO[str(caminho)] = {e["id"]: _assinatura(e) for e in final}
    finally:
        trava.close()


# --------------------------------------------------------------------------
# Editoras (para agrupar as pendencias)
# --------------------------------------------------------------------------

PREFIXOS_EDITORA = {
    "10.2519": "JOSPT (Journal of Orthopaedic & Sports Physical Therapy)",
    "10.1016": "Elsevier (ScienceDirect)",
    "10.1053": "Elsevier (ScienceDirect)",
    "10.1054": "Elsevier (ScienceDirect)",
    "10.1177": "SAGE",
    "10.1136": "BMJ",
    "10.1007": "Springer",
    "10.1186": "BMC (Springer Nature)",
    "10.1038": "Nature Portfolio",
    "10.1080": "Taylor & Francis",
    "10.3109": "Taylor & Francis",
    "10.1111": "Wiley",
    "10.1002": "Wiley",
    "10.1113": "Wiley",
    "10.1097": "Wolters Kluwer (LWW)",
    "10.1249": "Wolters Kluwer (LWW) · ACSM",
    "10.1519": "Wolters Kluwer (LWW) · NSCA",
    "10.2106": "JBJS",
    "10.1093": "Oxford University Press",
    "10.1055": "Thieme",
    "10.1123": "Human Kinetics",
    "10.4085": "NATA (Journal of Athletic Training)",
    "10.1001": "JAMA Network",
    "10.1056": "NEJM",
    "10.1152": "American Physiological Society",
    "10.1371": "PLOS",
    "10.3390": "MDPI",
    "10.3389": "Frontiers",
    "10.26603": "IJSPT",
    "10.1590": "SciELO",
    "10.1589": "J-STAGE",
    "10.1302": "Bone & Joint",
    "10.2340": "Medical Journals Sweden",
    "10.1310": "Thomas Land / Taylor & Francis",
    "10.1179": "Maney / Taylor & Francis",
    "10.1258": "SAGE",
    "10.3233": "IOS Press",
    "10.1159": "Karger",
    "10.1589/jpts": "J-STAGE",
    "10.7717": "PeerJ",
    "10.7759": "Cureus",
}

DICA_EDITORA = {
    "JOSPT": "Entre com a sua assinatura do JOSPT, abra o artigo e use o botão PDF.",
    "Elsevier": "No ScienceDirect, entre pelo acesso institucional (Access through your institution) e use View PDF.",
    "SAGE": "Entre pelo acesso institucional e use Download PDF.",
    "BMJ": "Entre pelo acesso institucional (ou conta BMJ) e use o link PDF na barra do artigo.",
    "Springer": "Entre pelo acesso institucional e use Download PDF.",
    "Taylor & Francis": "Entre pelo acesso institucional e use Download PDF.",
    "Wiley": "Entre pelo acesso institucional e use PDF.",
    "Wolters Kluwer": "Entre pelo acesso institucional (Ovid/LWW) e use Download PDF.",
    "Human Kinetics": "Entre pelo acesso institucional e use Download PDF.",
    "Thieme": "Entre pelo acesso institucional e use PDF.",
}


def editora_de(reg: dict, manifest_ent: dict | None = None) -> str:
    doi = normalizar_doi(reg.get("doi")) or ""
    prefixo = doi.split("/")[0]
    if prefixo in PREFIXOS_EDITORA:
        return PREFIXOS_EDITORA[prefixo]
    if manifest_ent and manifest_ent.get("editora"):
        return str(manifest_ent["editora"])
    if reg.get("editora"):
        return str(reg["editora"])
    return "Editora não identificada"


def dica_editora(nome: str) -> str:
    for chave, dica in DICA_EDITORA.items():
        if chave.lower() in nome.lower():
            return dica
    return "Entre pelo acesso institucional (ou pela sua assinatura) e baixe o PDF do editor."


def escrever_pendentes(aula: Aula, registros: list[dict], manifest: dict[str, dict]) -> int:
    """Reescreve 02_artigos/pendentes.md com o que ainda falta. Devolve a contagem."""
    pend = [r for r in registros if manifest.get(r["chave"], {}).get("status") != "ok"]
    linhas = ["# Artigos para baixar à mão", ""]
    if not pend:
        linhas += ["Nenhuma pendência: todos os artigos selecionados já têm PDF em `02_artigos/pdf/`.", ""]
        aula.pendentes.parent.mkdir(parents=True, exist_ok=True)
        aula.pendentes.write_text("\n".join(linhas), encoding="utf-8")
        return 0
    total = len(registros)
    linhas += [
        f"Faltam **{len(pend)}** de {total} artigos. O download automático não conseguiu estes "
        "(o motivo está em cada item). Os da seção \"Gratuitos\" não pedem login; os outros pedem a sua "
        "assinatura ou o acesso institucional.",
        "",
        "Como fazer:",
        "",
        "1. Abra o link de cada artigo (\"Versão gratuita\" quando houver), entre com a sua conta se pedir, e baixe o PDF.",
        f"2. Salve em `02_artigos/manual/` (pasta completa: `{aula.manual}`), com qualquer nome de arquivo.",
        "3. Avise quando terminar: eu identifico cada PDF pelo DOI ou pelo título e renomeio "
        "(`incorporar_manuais.py`).",
        "",
        f"Atualizado em {agora()[:16].replace('T', ' ')}.",
        "",
    ]
    gratis = [r for r in pend if manifest.get(r["chave"], {}).get("url_gratuita")]
    grupos: dict[str, list[dict]] = {}
    for r in pend:
        if r in gratis:
            continue
        grupos.setdefault(editora_de(r, manifest.get(r["chave"])), []).append(r)
    secoes: list[tuple[str, str, list[dict]]] = []
    if gratis:
        secoes.append(("Gratuitos: só abrir no navegador e salvar (sem login)",
                       "Estes têm versão gratuita legal (PMC ou página do editor), mas o servidor recusou o "
                       "download automático. Abra o link \"Versão gratuita\", clique em PDF e salve.", gratis))
    for nome in sorted(grupos, key=lambda n: (n.startswith("Editora não"), n.lower())):
        secoes.append((nome, dica_editora(nome), grupos[nome]))
    for nome, dica, itens in secoes:
        linhas += [f"## {nome}", "", f"_{dica}_", ""]
        for r in itens:
            ent = manifest.get(r["chave"], {})
            doi = normalizar_doi(r.get("doi"))
            if doi:
                link = f"https://doi.org/{doi}"
            elif r.get("pmid"):
                link = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
            else:
                link = "(sem DOI nem PMID: procurar pelo título)"
            revista = (r.get("revista") or "").strip()
            ref = f"{autores_curto(r)}. {revista + '. ' if revista else ''}{r.get('ano') or ''}".strip()
            linhas.append(f"- [ ] **{r['chave']}** — {r.get('titulo') or '(sem título)'}")
            linhas.append(f"  - {ref}")
            if ent.get("url_gratuita"):
                linhas.append(f"  - Versão gratuita: {ent['url_gratuita']}")
                linhas.append(f"  - Página do editor: {link}")
            else:
                linhas.append(f"  - Link: {link}")
            linhas.append(f"  - Por que importa para a aula: {papel_na_aula(r)}")
            motivo = ent.get("motivo_pendencia")
            if motivo:
                linhas.append(f"  - Situação: {motivo}")
            linhas.append("  - Salvar em: `02_artigos/manual/`")
        linhas.append("")
    aula.pendentes.parent.mkdir(parents=True, exist_ok=True)
    aula.pendentes.write_text("\n".join(linhas), encoding="utf-8")
    return len(pend)


# --------------------------------------------------------------------------
# Rede educada
# --------------------------------------------------------------------------


class ErroRede(Exception):
    pass


class Rede:
    """Sessao HTTP com pausa minima por host, novas tentativas com espera crescente
    e mensagens de erro legiveis. Nunca envia dados pessoais: so o User-Agent generico."""

    PAUSA_HOST = {"eutils.ncbi.nlm.nih.gov": 0.4, "pmc.ncbi.nlm.nih.gov": 0.4, "www.ncbi.nlm.nih.gov": 0.4}

    def __init__(self, pausa: float = 1.0, tentativas: int = 3, timeout: float = 45.0):
        import requests  # importado aqui para que --help funcione sem a biblioteca

        self._requests = requests
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": AGENTE, "Accept-Language": "en;q=0.9,pt-BR;q=0.8"})
        self.pausa = pausa
        self.tentativas = tentativas
        self.timeout = timeout
        self._ultimo: dict[str, float] = {}
        self.bloqueados: set[str] = set()

    def _esperar(self, host: str) -> None:
        minimo = max(self.PAUSA_HOST.get(host, self.pausa), 0.0)
        falta = self._ultimo.get(host, 0.0) + minimo - time.monotonic()
        if falta > 0:
            time.sleep(falta)

    def get(self, url: str, *, params=None, headers=None, stream: bool = False,
            timeout: float | None = None, tentativas: int | None = None):
        host = urlparse(url).netloc
        if host in self.bloqueados:
            raise ErroRede(f"{host} está bloqueado nesta rede (pulado)")
        ultimo_erro = "sem resposta"
        tentativas = tentativas or self.tentativas
        for n in range(tentativas):
            self._esperar(host)
            try:
                r = self.s.get(url, params=params, headers=headers, stream=stream,
                               timeout=timeout or self.timeout, allow_redirects=True)
            except self._requests.exceptions.ProxyError as e:
                self._ultimo[host] = time.monotonic()
                self.bloqueados.add(host)
                raise ErroRede(f"{host} inacessível pelo proxy desta rede") from e
            except self._requests.exceptions.RequestException as e:
                self._ultimo[host] = time.monotonic()
                txt = str(e)
                if "ProxyError" in txt or "Tunnel connection failed" in txt:
                    self.bloqueados.add(host)
                    raise ErroRede(f"{host} inacessível pelo proxy desta rede") from e
                ultimo_erro = f"falha de conexão ({type(e).__name__})"
                time.sleep(2.0 * (2.5 ** n))
                continue
            self._ultimo[host] = time.monotonic()
            if r.status_code in (429, 500, 502, 503, 504):
                ultimo_erro = f"HTTP {r.status_code}"
                espera = 2.0 * (2.5 ** n)
                ra = r.headers.get("Retry-After", "")
                if ra.isdigit():
                    espera = min(max(espera, float(ra)), 60.0)
                r.close()
                if n + 1 < tentativas:
                    time.sleep(espera)
                continue
            return r
        raise ErroRede(f"{host}: {ultimo_erro} após {tentativas} tentativas")

    def json(self, url: str, *, params=None, timeout: float | None = None, tentativas: int | None = None):
        r = self.get(url, params=params, headers={"Accept": "application/json"},
                     timeout=timeout, tentativas=tentativas)
        if r.status_code != 200:
            raise ErroRede(f"{urlparse(url).netloc}: HTTP {r.status_code}")
        try:
            return r.json()
        except ValueError as e:
            raise ErroRede(f"{urlparse(url).netloc}: resposta não é JSON") from e


def email_contato(arg: str | None) -> str:
    return (arg or os.environ.get("BOOST_EMAIL") or EMAIL_PADRAO).strip()


# --------------------------------------------------------------------------
# Validacao de PDF
# --------------------------------------------------------------------------


def validar_pdf(caminho: Path, tamanho_minimo: int = 20_000) -> tuple[bool, str, int]:
    """Confere cabecalho %PDF, tamanho minimo e se o arquivo abre. (ok, motivo, paginas)."""
    try:
        tam = caminho.stat().st_size
        with open(caminho, "rb") as f:
            inicio = f.read(1024)
    except OSError as e:
        return False, f"não consegui ler o arquivo ({e})", 0
    if b"%PDF-" not in inicio:
        amostra = inicio[:60].decode("latin-1", "replace").strip().replace("\n", " ")
        return False, f"não é PDF (começa com: {amostra!r})", 0
    if tam < tamanho_minimo:
        return False, f"PDF pequeno demais ({tam} bytes; mínimo {tamanho_minimo})", 0
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(caminho))
        n = len(doc)
        doc.close()
    except Exception as e:  # PDF corrompido ou protegido
        return False, f"PDF não abre ({type(e).__name__})", 0
    if n < 1:
        return False, "PDF sem páginas", 0
    return True, "ok", n


def texto_inicial_pdf(caminho: Path, paginas: int = 2) -> str:
    """Texto das primeiras paginas (para conferir DOI/titulo). Nunca levanta excecao."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(str(caminho))
        partes = []
        for i in range(min(paginas, len(doc))):
            tp = doc[i].get_textpage()
            partes.append(tp.get_text_bounded())
            tp.close()
        doc.close()
        return "\n".join(partes)
    except Exception:
        return ""


def metadados_pdf(caminho: Path) -> str:
    """Campos de metadados (titulo, assunto, doi, XMP) concatenados em um texto."""
    try:
        from pypdf import PdfReader

        leitor = PdfReader(str(caminho))
        partes = []
        info = leitor.metadata or {}
        for k, v in info.items():
            partes.append(f"{k}: {v}")
        try:
            xmp = leitor.xmp_metadata
            if xmp is not None and getattr(xmp, "stream", None) is not None:
                partes.append(xmp.stream.get_data().decode("utf-8", "replace")[:20000])
        except Exception:
            pass
        return "\n".join(partes)
    except Exception:
        return ""


def cobertura_titulo(titulo: str, texto: str) -> float:
    """Fracao das palavras significativas do titulo presentes, em ordem aproximada, no texto."""
    t = [p for p in normalizar_texto(titulo).split() if len(p) > 2]
    if not t:
        return 0.0
    alvo = normalizar_texto(texto)
    if " ".join(normalizar_texto(titulo).split()) in alvo:
        return 1.0
    palavras = set(alvo.split())
    junto = alvo.replace(" ", "")
    achadas = sum(1 for p in t if p in palavras or (len(p) > 5 and p in junto))
    return achadas / len(t)


def titulo_curto(titulo: str) -> bool:
    """Título com menos de 4 palavras significativas: palavras soltas batem em qualquer artigo do tema."""
    return len([p for p in normalizar_texto(titulo).split() if len(p) > 2]) < 4


def titulo_exato(titulo: str, texto: str) -> bool:
    t = normalizar_texto(titulo)
    return bool(t) and t in normalizar_texto(texto)


def pdf_confere(reg: dict, caminho: Path) -> tuple[bool | None, str]:
    """O PDF parece ser o artigo do registro? (True/False/None quando nao da para saber)."""
    texto = texto_inicial_pdf(caminho, 2) + "\n" + metadados_pdf(caminho)
    if len(normalizar_texto(texto)) < 200:
        return None, "PDF sem camada de texto nas primeiras páginas"
    doi = normalizar_doi(reg.get("doi"))
    if doi and doi in [d for d in achar_dois(texto)]:
        return True, "DOI encontrado no PDF"
    if doi and doi.replace("/", "").replace(".", "") in re.sub(r"[^a-z0-9]", "", texto.lower()):
        return True, "DOI encontrado no PDF"
    titulo = reg.get("titulo") or ""
    if titulo_curto(titulo):  # título curto: exige a frase inteira, senão qualquer artigo do tema passa
        if titulo_exato(titulo, texto):
            return True, "título (curto) encontrado por inteiro no PDF"
        return False, "título curto não aparece por inteiro nas primeiras páginas"
    cob = cobertura_titulo(titulo, texto)
    if cob >= 0.8:
        return True, f"título encontrado no PDF ({cob:.0%})"
    return False, f"nem o DOI nem o título aparecem nas primeiras páginas (título {cob:.0%})"
