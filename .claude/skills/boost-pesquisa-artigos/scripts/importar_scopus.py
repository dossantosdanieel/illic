#!/usr/bin/env python3
"""Importa a exportação manual do Scopus (CSV, RIS ou BibTeX) e grava brutos/scopus.json.

O Scopus não tem API aberta para o usuário: ele roda a string no site, exporta, e este script
le o arquivo. Aceita as variações de cabeçalho entre versões do Scopus (por exemplo 'Open Access'
x 'Access Type', autores separados por vírgula ou ponto e vírgula) e arquivos regravados pelo
Excel (ponto e vírgula como separador, codificação Windows).

Uso:
  python3 importar_scopus.py --pasta aulas/x/01_busca                 # lê brutos/scopus*.csv|.ris|.bib
  python3 importar_scopus.py ~/Downloads/scopus.csv outro.ris --saida aulas/x/01_busca/brutos/scopus.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import csv
import io
import re
from collections import Counter

from _comum import (agora_iso, autor_curto, gravar_json, ler_json, limpar_texto, lista_issn, normalizar_doi,
                    normalizar_pmid, para_int, sair)

# cabeçalho do CSV (em minúsculas) -> campo interno. Várias grafias por causa das versões do Scopus.
COLUNAS = {
    "authors": "autores", "author": "autores",
    "author full names": "autores_completos",
    "title": "titulo", "document title": "titulo",
    "year": "ano",
    "source title": "revista_completa",
    "abbreviated source title": "revista",
    "volume": "volume", "issue": "fasciculo",
    "art. no.": "artigo_numero", "article number": "artigo_numero",
    "page start": "pagina_inicio", "page end": "pagina_fim",
    "cited by": "citacoes_scopus", "citations": "citacoes_scopus",
    "doi": "doi", "link": "link",
    "abstract": "resumo",
    "author keywords": "palavras_chave", "index keywords": "termos_indice",
    "issn": "issn", "pubmed id": "pmid",
    "language of original document": "idioma",
    "document type": "tipo_scopus", "publication stage": "estagio",
    "open access": "acesso_aberto_scopus", "access type": "acesso_aberto_scopus",
    "eid": "scopus_eid", "source": "base",
}
SEM_RESUMO = re.compile(r"^\[?no abstract available\]?\.?$", re.I)


def _eid_do_link(link: str | None) -> str | None:
    achado = re.search(r"eid=(2-s2\.0-\d+)", link or "")
    return achado.group(1) if achado else None


def _revista_curta(abreviada: str) -> str:
    """'J. Orthop. Sports Phys. Ther.' -> 'J Orthop Sports Phys Ther' (como no PubMed)."""
    return re.sub(r"\s+", " ", (abreviada or "").replace(".", " ")).strip()


def _e_iniciais(pedaco: str) -> bool:
    """'A.M.', 'J.-P.', 'MÁ' são iniciais; 'Silva' não."""
    letras = pedaco.replace(".", "").replace("-", "")
    return bool(letras) and len(letras) <= 4 and letras.isalpha() and letras.isupper()


def separar_autores(texto: str) -> list[str]:
    """Devolve autores no padrão 'Sobrenome IN'.

    Formatos reais do Scopus: 'Cools A.M.; Struyf F.' (atual), 'Cools A.M., Struyf F.' (antigo),
    'Cools, A.M.; Struyf, F.' e 'Cools, Ann M. (6603124466); ...' (coluna de nomes completos).
    """
    texto = (texto or "").strip()
    if not texto or texto.lower().startswith("[no author"):
        return []
    if ";" in texto:
        pedacos = texto.split(";")
    elif re.search(r",\s*[A-Z]\.", texto) and not re.search(r"[A-Z]\.,\s*[A-Z][a-z]", texto):
        pedacos = [texto]  # um único autor no formato 'Sobrenome, A.B.'
    else:
        pedacos = texto.split(",")
    autores = []
    for p in pedacos:
        p = re.sub(r"\(\d+\)", "", p).strip()
        if not p:
            continue
        if "," in p:
            sobrenome, nomes = p.split(",", 1)
        else:
            partes = p.split()
            corte = len(partes)
            while corte > 1 and _e_iniciais(partes[corte - 1]):
                corte -= 1
            sobrenome, nomes = " ".join(partes[:corte]), " ".join(partes[corte:])
        autores.append(autor_curto(sobrenome.strip(), nomes.strip()))
    return autores


def montar_registro(d: dict) -> dict | None:
    """Converte um dicionário de campos internos em registro normalizado."""
    titulo = limpar_texto(d.get("titulo"))
    if not titulo:
        return None
    autores = separar_autores(d.get("autores") or "") or separar_autores(d.get("autores_completos") or "")
    resumo = limpar_texto(d.get("resumo"))
    if SEM_RESUMO.match(resumo):
        resumo = ""
    resumo = re.sub(r"\s*(©|Copyright ©|\(c\))\s*\d{4}.*$", "", resumo).strip()
    inicio, fim = (d.get("pagina_inicio") or "").strip(), (d.get("pagina_fim") or "").strip()
    paginas = f"{inicio}-{fim}" if inicio and fim else (inicio or (d.get("artigo_numero") or "").strip())
    chaves = [limpar_texto(k) for k in re.split(r";", d.get("palavras_chave") or "") if k.strip()]
    indice = [limpar_texto(k) for k in re.split(r";", d.get("termos_indice") or "") if k.strip()]
    oa = limpar_texto(d.get("acesso_aberto_scopus"))
    return {
        "fonte": "scopus",
        "scopus_eid": (d.get("scopus_eid") or "").strip() or _eid_do_link(d.get("link")),
        "doi": normalizar_doi(d.get("doi")),
        "pmid": normalizar_pmid(d.get("pmid")),
        "titulo": titulo,
        "autores": autores,
        "primeiro_autor": autores[0].rsplit(" ", 1)[0] if autores and " " in autores[0] else (autores[0] if autores else ""),
        "ano": para_int(d.get("ano")),
        "revista": _revista_curta(d.get("revista") or "") or limpar_texto(d.get("revista_completa")),
        "revista_completa": limpar_texto(d.get("revista_completa")),
        "issn": lista_issn(d.get("issn")),
        "volume": (d.get("volume") or "").strip(),
        "fasciculo": (d.get("fasciculo") or "").strip(),
        "paginas": paginas,
        "resumo": resumo,
        "tipo_scopus": limpar_texto(d.get("tipo_scopus")),
        "estagio": limpar_texto(d.get("estagio")),
        "idioma": limpar_texto(d.get("idioma")),
        "palavras_chave": chaves,
        "termos_indice": indice,
        "citacoes_scopus": para_int(d.get("citacoes_scopus")),
        "acesso_aberto_scopus": oa or None,
    }


# --------------------------------------------------------------------------- CSV

def ler_texto(caminho: Path) -> str:
    bruto = caminho.read_bytes()
    if bruto[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return bruto.decode("utf-16", errors="replace")
    try:
        return bruto.decode("utf-8-sig")
    except UnicodeError:
        return bruto.decode("cp1252", errors="replace")  # CSV regravado pelo Excel no Windows


def ler_csv(texto: str) -> tuple[list[dict], list[str]]:
    avisos = []
    csv.field_size_limit(50_000_000)
    primeira = texto.split("\n", 1)[0]
    separador = max([",", ";", "\t"], key=primeira.count)
    leitor = csv.reader(io.StringIO(texto), delimiter=separador)
    try:
        cabecalho = next(leitor)
    except StopIteration:
        return [], ["arquivo CSV vazio"]
    mapa = {}
    for i, nome in enumerate(cabecalho):
        campo = COLUNAS.get(nome.strip().strip('"').lower())
        if campo and campo not in mapa.values():
            mapa[i] = campo
    presentes = set(mapa.values())
    if "titulo" not in presentes:
        return [], [f"não achei a coluna 'Title' (cabeçalho lido: {', '.join(cabecalho[:8])}...). "
                    f"É mesmo uma exportação CSV do Scopus?"]
    faltas = {"resumo": "Abstract", "doi": "DOI", "pmid": "PubMed ID", "tipo_scopus": "Document Type",
              "scopus_eid": "EID", "issn": "ISSN", "palavras_chave": "Author Keywords"}
    for campo, coluna in faltas.items():
        if campo not in presentes:
            avisos.append(f"coluna '{coluna}' ausente: refaca a exportação marcando esse campo"
                          + (" (sem resumo não há triagem)" if campo == "resumo" else ""))
    registros = []
    for n, linha in enumerate(leitor, 2):
        if not any(c.strip() for c in linha):
            continue
        try:
            d = {campo: linha[i] for i, campo in mapa.items() if i < len(linha)}
            reg = montar_registro(d)
        except Exception as exc:  # noqa: BLE001 - uma linha ruim não para o arquivo
            avisos.append(f"linha {n}: {type(exc).__name__}: {exc}")
            continue
        if reg:
            registros.append(reg)
        else:
            avisos.append(f"linha {n}: sem título, ignorada")
    return registros, avisos


# --------------------------------------------------------------------------- RIS

def ler_ris(texto: str) -> tuple[list[dict], list[str]]:
    registros, avisos = [], []
    atual: dict[str, list[str]] = {}
    ultima = None

    def fechar():
        nonlocal atual
        if not atual:
            return
        um = lambda *tags: next((atual[t][0] for t in tags if atual.get(t)), "")  # noqa: E731
        notas = " ; ".join(atual.get("N1", []))
        citacoes = re.search(r"Cited By\s*:?\s*(\d+)", notas, re.I)
        issn = next((re.sub(r"\(.*?\)", "", v) for v in atual.get("SN", []) if "ISBN" not in v.upper()), "")
        pmid = next((v for v in atual.get("C2", []) + atual.get("AN", []) if re.fullmatch(r"\d{6,9}", v.strip())), "")
        tipo = um("M3") or {"JOUR": "Article", "CONF": "Conference paper", "CHAP": "Book chapter",
                            "BOOK": "Book"}.get(um("TY"), um("TY"))
        d = {"autores": "; ".join(atual.get("AU", []) + atual.get("A1", [])),
             "titulo": um("TI", "T1"), "ano": um("PY", "Y1"),
             "revista_completa": um("T2", "JO", "JF"), "revista": um("J2", "JA"),
             "volume": um("VL"), "fasciculo": um("IS"), "artigo_numero": um("C7"),
             "pagina_inicio": um("SP"), "pagina_fim": um("EP"), "doi": um("DO"), "link": um("UR"),
             "resumo": um("AB", "N2"), "palavras_chave": "; ".join(atual.get("KW", [])),
             "issn": issn, "pmid": pmid, "idioma": um("LA"), "tipo_scopus": tipo,
             "citacoes_scopus": citacoes.group(1) if citacoes else ""}
        try:
            reg = montar_registro(d)
            if reg:
                registros.append(reg)
        except Exception as exc:  # noqa: BLE001
            avisos.append(f"registro RIS '{um('TI')[:50]}': {type(exc).__name__}: {exc}")
        atual = {}

    for linha in texto.splitlines():
        achado = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", linha)
        if achado:
            tag, valor = achado.group(1), achado.group(2).strip()
            if tag == "ER":
                fechar()
                ultima = None
                continue
            if tag == "TY" and atual:
                fechar()
            atual.setdefault(tag, []).append(valor)
            ultima = tag
        elif linha.strip() and ultima and atual.get(ultima):
            atual[ultima][-1] += " " + linha.strip()
    fechar()
    return registros, avisos


# --------------------------------------------------------------------------- BibTeX

_ACENTOS = {"'": "́", "`": "̀", "^": "̂", '"': "̈", "~": "̃", "c": "̧",
            "v": "̌", "=": "̄", ".": "̇", "u": "̆", "H": "̋", "k": "̨", "r": "̊"}
_ESPECIAIS = {"ss": "ß", "o": "ø", "O": "Ø", "aa": "å", "AA": "Å", "ae": "æ", "AE": "Æ", "l": "ł", "L": "Ł",
              "i": "ı", "oe": "œ", "OE": "Œ"}


def _tirar_latex(texto: str) -> str:
    import unicodedata

    def acento(m):
        return unicodedata.normalize("NFC", m.group(2) + _ACENTOS[m.group(1)])

    texto = re.sub(r"\{?\\(['`^\"~=.])\s*\{?\\?([A-Za-z])\}?\}?", acento, texto)
    texto = re.sub(r"\{?\\([cvuHkr])\s*\{([A-Za-z])\}\}?", acento, texto)
    texto = re.sub(r"\{?\\(ss|aa|AA|ae|AE|oe|OE|o|O|l|L|i)\b\s*\}?", lambda m: _ESPECIAIS[m.group(1)], texto)
    texto = re.sub(r"\\([&%_#$])", r"\1", texto)
    texto = texto.replace("\\textendash", "-").replace("\\textemdash", "-").replace("--", "-").replace("~", " ")
    return re.sub(r"[{}]", "", texto)


def _campos_bibtex(corpo: str) -> dict:
    campos, i, n = {}, 0, len(corpo)
    while i < n:
        achado = re.compile(r"\s*,?\s*([A-Za-z_][\w\-]*)\s*=\s*").match(corpo, i)
        if not achado:
            break
        nome = achado.group(1).lower()
        i = achado.end()
        if i >= n:
            break
        if corpo[i] == "{":
            nivel, j = 0, i
            while j < n:
                if corpo[j] == "{" and (j == 0 or corpo[j - 1] != "\\"):
                    nivel += 1
                elif corpo[j] == "}" and corpo[j - 1] != "\\":
                    nivel -= 1
                    if nivel == 0:
                        break
                j += 1
            valor, i = corpo[i + 1:j], j + 1
        elif corpo[i] == '"':
            j = i + 1
            while j < n and not (corpo[j] == '"' and corpo[j - 1] != "\\"):
                j += 1
            valor, i = corpo[i + 1:j], j + 1
        else:
            j = i
            while j < n and corpo[j] not in ",\n":
                j += 1
            valor, i = corpo[i:j].strip(), j
        campos[nome] = re.sub(r"\s+", " ", valor).strip()
    return campos


def ler_bibtex(texto: str) -> tuple[list[dict], list[str]]:
    registros, avisos = [], []
    for achado in re.finditer(r"@(\w+)\s*\{", texto):
        tipo_entrada = achado.group(1).lower()
        if tipo_entrada in ("comment", "string", "preamble"):
            continue
        nivel, j = 1, achado.end()
        while j < len(texto) and nivel:
            if texto[j] == "{" and texto[j - 1] != "\\":
                nivel += 1
            elif texto[j] == "}" and texto[j - 1] != "\\":
                nivel -= 1
            j += 1
        corpo = texto[achado.end():j - 1]
        if "," not in corpo:
            continue
        corpo = corpo.split(",", 1)[1]
        try:
            c = {k: _tirar_latex(v) for k, v in _campos_bibtex(corpo).items()}
            nota = c.get("note", "")
            citacoes = re.search(r"Cited by\s*:?\s*(\d+)", nota, re.I)
            oa = re.search(r"((?:All |Gold |Green |Bronze |Hybrid Gold )Open Access.*)$", nota)
            paginas = re.split(r"\s*-+\s*|\s*–\s*", c.get("pages", ""))
            tipo = c.get("type") or {"article": "Article", "conference": "Conference paper",
                                     "inproceedings": "Conference paper", "book": "Book",
                                     "incollection": "Book chapter"}.get(tipo_entrada, tipo_entrada)
            d = {"autores": "; ".join(a.strip() for a in re.split(r"\s+and\s+", c.get("author", "")) if a.strip()),
                 "titulo": c.get("title", ""), "ano": c.get("year", ""),
                 "revista_completa": c.get("journal") or c.get("booktitle", ""),
                 "revista": c.get("abbrev_source_title", ""),
                 "volume": c.get("volume", ""), "fasciculo": c.get("number", ""),
                 "pagina_inicio": paginas[0] if paginas else "", "pagina_fim": paginas[1] if len(paginas) > 1 else "",
                 "artigo_numero": c.get("art_number", ""),
                 "doi": c.get("doi", ""), "link": c.get("url", ""), "resumo": c.get("abstract", ""),
                 "palavras_chave": c.get("author_keywords", ""), "termos_indice": c.get("keywords", ""),
                 "issn": c.get("issn", ""), "pmid": c.get("pmid", ""), "idioma": c.get("language", ""),
                 "tipo_scopus": tipo, "estagio": c.get("publication_stage", ""),
                 "citacoes_scopus": citacoes.group(1) if citacoes else "",
                 "acesso_aberto_scopus": oa.group(1) if oa else ""}
            reg = montar_registro(d)
            if reg:
                registros.append(reg)
        except Exception as exc:  # noqa: BLE001
            avisos.append(f"entrada BibTeX perto de '{texto[achado.start():achado.start() + 40]}': "
                          f"{type(exc).__name__}: {exc}")
    return registros, avisos


# --------------------------------------------------------------------------- principal

def detectar_formato(caminho: Path, texto: str) -> str:
    ext = caminho.suffix.lower()
    inicio = texto.lstrip()[:400]
    if ext == ".ris" or re.match(r"^TY  - ", inicio):
        return "ris"
    if ext in (".bib", ".bibtex") or inicio.startswith("@"):
        return "bibtex"
    if re.search(r"^TY  - ", texto, re.M) and "ER  -" in texto:
        return "ris"
    return "csv"


def importar_arquivo(caminho: Path) -> tuple[list[dict], list[str], str]:
    texto = ler_texto(caminho)
    formato = detectar_formato(caminho, texto)
    leitor = {"csv": ler_csv, "ris": ler_ris, "bibtex": ler_bibtex}[formato]
    registros, avisos = leitor(texto)
    return registros, avisos, formato


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Lê a exportação do Scopus (CSV, RIS ou BibTeX) e grava brutos/scopus.json no formato dos "
                    "outros scripts.")
    ap.add_argument("arquivos", nargs="*", help="arquivos exportados do Scopus (.csv, .ris, .bib)")
    ap.add_argument("--pasta", help="pasta 01_busca da aula: lê todos os brutos/scopus*.csv|.ris|.bib|.txt")
    ap.add_argument("--saida", help="arquivo de saída (padrão: <pasta>/brutos/scopus.json)")
    ap.add_argument("--acumular", action="store_true",
                    help="soma ao scopus.json existente (padrão: recria a partir dos arquivos lidos)")
    args = ap.parse_args(argv)

    arquivos = [Path(a) for a in args.arquivos]
    if args.pasta:
        brutos = Path(args.pasta) / "brutos"
        for padrao in ("scopus*.csv", "scopus*.ris", "scopus*.bib", "scopus*.txt"):
            arquivos += sorted(brutos.glob(padrao))
    if not arquivos:
        sair("nenhum arquivo para importar. Salve a exportação do Scopus como brutos/scopus.csv e use --pasta, "
             "ou passe os arquivos na linha de comando.")
    if args.saida:
        destino = Path(args.saida)
    elif args.pasta:
        destino = Path(args.pasta) / "brutos" / "scopus.json"
    else:
        sair("informe --saida ou --pasta")

    saida = ler_json(destino) if args.acumular else None
    if not saida or not isinstance(saida, dict):
        saida = {"fonte": "scopus", "execucoes": [], "registros": []}
    indice: dict[str, dict] = {}
    for r in saida["registros"]:
        indice[r.get("scopus_eid") or r.get("doi") or r["titulo"].lower()] = r

    falhas = 0
    for caminho in arquivos:
        print(f"=== Scopus | {caminho.name} ===")
        if not caminho.exists():
            print("  arquivo não encontrado; pulei.")
            falhas += 1
            continue
        try:
            registros, avisos, formato = importar_arquivo(caminho)
        except Exception as exc:  # noqa: BLE001 - um arquivo ruim não impede os outros
            print(f"  FALHA ao ler: {type(exc).__name__}: {exc}")
            falhas += 1
            continue
        novos = 0
        for r in registros:
            chave = r.get("scopus_eid") or r.get("doi") or r["titulo"].lower()
            if chave not in indice:
                novos += 1
            indice[chave] = r
        tipos = Counter(r["tipo_scopus"] or "(sem tipo)" for r in registros)
        anos = [r["ano"] for r in registros if r["ano"]]
        print(f"  formato: {formato} | registros lidos: {len(registros)} | novos: {novos}")
        if registros:
            print(f"  com DOI: {sum(1 for r in registros if r['doi'])} | com PMID: "
                  f"{sum(1 for r in registros if r['pmid'])} | com resumo: {sum(1 for r in registros if r['resumo'])}"
                  f" | com EID: {sum(1 for r in registros if r['scopus_eid'])}")
            print(f"  anos: {min(anos) if anos else '-'} a {max(anos) if anos else '-'} | tipos: "
                  + ", ".join(f"{t} ({n})" for t, n in tipos.most_common()))
        for a in avisos[:15]:
            print(f"  aviso: {a}")
        if len(avisos) > 15:
            print(f"  ... e mais {len(avisos) - 15} avisos")
        if not registros:
            falhas += 1
        saida["execucoes"].append({"data": agora_iso(), "arquivo": caminho.name, "formato": formato,
                                   "registros": len(registros), "novos": novos, "avisos": avisos[:50]})
    saida["registros"] = list(indice.values())
    gravar_json(destino, saida)
    print(f"\nGravado: {destino} ({len(saida['registros'])} registros únicos do Scopus)")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
