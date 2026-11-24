#!/usr/bin/env python3
"""Baixa, só por vias legais, os PDFs de acesso aberto dos artigos selecionados.

Para cada registro tenta, nesta ordem: PMC (repositório aberto oficial), Europe PMC,
Unpaywall (melhor localização aberta) e a URL aberta do OpenAlex. Valida cada arquivo
(%PDF, tamanho, abre, é o artigo certo), registra origem e licença em
02_artigos/manifest.json e escreve 02_artigos/pendentes.md com o que o usuário
precisa baixar à mão (agrupado por editora, com link DOI).

Uso:
  python3 baixar_artigos.py aulas/2026-11-tendinopatia-patelar
  python3 baixar_artigos.py AULA --apenas Breda2021 Rio2015 --refazer
  python3 baixar_artigos.py AULA --sem-rede        # só monta a lista de pendências
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402

BALDE_PMC = "https://pmc-oa-opendata.s3.amazonaws.com"
FONTES = ("pmc", "europepmc", "unpaywall", "openalex")
# Sites que barram clientes automatizados com desafio de navegador: não insistir nem contornar.
_COM_DESAFIO: set[str] = set()  # hosts que responderam com desafio nesta execução
HOSTS_SO_NAVEGADOR = {"www.jospt.org": "o JOSPT só entrega o PDF pelo navegador; baixar com a assinatura"}


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------
# Fontes: cada uma devolve uma lista de candidatos {fonte, url, licenca, md5, nota}
# --------------------------------------------------------------------------


def resolver_pmcid(rede: C.Rede, reg: dict, email: str) -> str | None:
    pmcid = (reg.get("pmcid") or "").strip().upper()
    if pmcid:
        return pmcid if pmcid.startswith("PMC") else f"PMC{pmcid}"
    doi = C.normalizar_doi(reg.get("doi"))
    pmid = str(reg.get("pmid") or "").strip()
    ident = doi or pmid
    if not ident:
        return None
    # 1) conversor de IDs do PMC; 2) E-utilities (PubMed -> PMC); 3) API REST do Europe PMC.
    # O conversor às vezes responde 403 a clientes que não são navegador; por isso há plano B.
    try:
        j = rede.json("https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/",
                      params={"ids": ident, "format": "json", "tool": C.FERRAMENTA, "email": email})
        for rec in j.get("records") or []:
            if rec.get("pmcid"):
                return str(rec["pmcid"]).upper()
            if not pmid and rec.get("pmid"):
                pmid = str(rec["pmid"])
    except C.ErroRede:
        pass
    eutils = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    try:
        if not pmid and doi:
            j = rede.json(eutils + "esearch.fcgi", params={"db": "pubmed", "term": f"{doi}[doi]", "retmode": "json",
                                                           "tool": C.FERRAMENTA, "email": email})
            ids = (j.get("esearchresult") or {}).get("idlist") or []
            pmid = ids[0] if len(ids) == 1 else ""
        if pmid:
            j = rede.json(eutils + "esummary.fcgi", params={"db": "pubmed", "id": pmid, "retmode": "json",
                                                            "tool": C.FERRAMENTA, "email": email})
            doc = (j.get("result") or {}).get(pmid) or {}
            for a in doc.get("articleids") or []:
                if a.get("idtype") == "pmc" and str(a.get("value", "")).upper().startswith("PMC"):
                    return str(a["value"]).upper()
            return None  # PubMed respondeu e não há PMCID: não está no PMC
    except C.ErroRede:
        pass
    try:
        consulta = f'DOI:"{doi}"' if doi else f"EXT_ID:{pmid} AND SRC:MED"
        j = rede.json("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                      params={"query": consulta, "format": "json", "resultType": "lite", "pageSize": 1},
                      timeout=20, tentativas=1)
        res = (j.get("resultList") or {}).get("result") or []
        if res and res[0].get("pmcid"):
            return str(res[0]["pmcid"]).upper()
    except C.ErroRede:
        pass
    return None


def fonte_pmc(rede: C.Rede, pmcid: str, info: dict) -> list[dict]:
    """Repositório aberto oficial do PMC (PMC Open Data na AWS): PMCxxxx.<versão>/PMCxxxx.<versão>.pdf"""
    r = rede.get(BALDE_PMC + "/", params={"list-type": "2", "prefix": f"{pmcid}."})
    if r.status_code != 200:
        raise C.ErroRede(f"repositório aberto do PMC respondeu HTTP {r.status_code}")
    chaves = re.findall(r"<Key>([^<]+)</Key>", r.text)
    versoes = sorted({int(m.group(1)) for k in chaves
                      if (m := re.match(rf"{pmcid}\.(\d+)/{pmcid}\.\1\.pdf$", k))}, reverse=True)
    if not versoes:
        if chaves:
            raise C.ErroRede("artigo está no PMC, mas sem PDF no repositório aberto")
        raise C.ErroRede("artigo não está no repositório aberto do PMC")
    v = versoes[0]
    base = f"{BALDE_PMC}/{pmcid}.{v}/{pmcid}.{v}"
    licenca, md5 = None, None
    try:
        meta = rede.json(base + ".json")
        licenca = C.normalizar_licenca(meta.get("license_code"))
        m = re.search(r"md5=([0-9a-f]{32})", str(meta.get("pdf_url") or ""))
        md5 = m.group(1) if m else None
        cit = str(meta.get("citation") or "")
        m = re.search(r";\s*(\d+[A-Za-z]?)(?:\(([^)]+)\))?:\s*([\w.\-–]+)", cit)
        if m:
            info.setdefault("volume", m.group(1))
            if m.group(2):
                info.setdefault("numero", m.group(2))
            info.setdefault("paginas_artigo", m.group(3).replace("–", "-").rstrip("."))
        if meta.get("is_retracted"):
            info["retratado"] = True
    except C.ErroRede:
        pass
    return [{"fonte": "pmc", "url": base + ".pdf", "licenca": licenca, "md5": md5}]


def fonte_europepmc(rede: C.Rede, reg: dict, pmcid: str | None, info: dict) -> list[dict]:
    cands, licenca = [], None
    doi = C.normalizar_doi(reg.get("doi"))
    consulta = f'DOI:"{doi}"' if doi else (f"EXT_ID:{reg['pmid']} AND SRC:MED" if reg.get("pmid") else None)
    if consulta:
        try:
            # A API do Europe PMC às vezes leva mais de um minuto: espera curta, uma tentativa só.
            j = rede.json("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                          params={"query": consulta, "format": "json", "resultType": "core", "pageSize": 1},
                          timeout=20, tentativas=1)
            res = (j.get("resultList") or {}).get("result") or []
            if res:
                x = res[0]
                pmcid = pmcid or x.get("pmcid")
                licenca = C.normalizar_licenca(x.get("license"))
                ji = x.get("journalInfo") or {}
                if ji.get("volume"):
                    info.setdefault("volume", str(ji["volume"]))
                if ji.get("issue"):
                    info.setdefault("numero", str(ji["issue"]))
                if x.get("pageInfo"):
                    info.setdefault("paginas_artigo", str(x["pageInfo"]))
                for ft in ((x.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
                    if ft.get("documentStyle") == "pdf" and ft.get("availabilityCode") in ("OA", "F"):
                        cands.append({"fonte": "europepmc", "url": ft["url"], "licenca": licenca})
        except C.ErroRede as e:
            info.setdefault("avisos_rede", []).append(f"Europe PMC (API): {e}")
    if pmcid:
        for url in (f"https://europepmc.org/articles/{pmcid}?pdf=render",
                    f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"):
            if not any(c["url"] == url for c in cands):
                cands.append({"fonte": "europepmc", "url": url, "licenca": licenca})
    return cands[:3]


def fonte_unpaywall(rede: C.Rede, reg: dict, email: str, info: dict) -> list[dict]:
    doi = C.normalizar_doi(reg.get("doi"))
    if not doi:
        return []
    r = rede.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email},
                 headers={"Accept": "application/json"})
    if r.status_code == 404:
        return []
    if r.status_code == 422:
        raise C.ErroRede("Unpaywall recusou o e-mail de contato; informe --email ou BOOST_EMAIL")
    if r.status_code != 200:
        raise C.ErroRede(f"Unpaywall respondeu HTTP {r.status_code}")
    j = r.json()
    if j.get("publisher"):
        info.setdefault("editora_api", j["publisher"])
    info["acesso_aberto_unpaywall"] = bool(j.get("is_oa"))
    locais = []
    if j.get("best_oa_location"):
        locais.append(j["best_oa_location"])
    locais += [loc for loc in (j.get("oa_locations") or []) if loc is not j.get("best_oa_location")]
    cands, vistos = [], set()
    for loc in locais:
        url = loc.get("url_for_pdf")
        if not url or url in vistos:
            continue
        vistos.add(url)
        cands.append({"fonte": "unpaywall", "url": url, "licenca": C.normalizar_licenca(loc.get("license")),
                      "nota": f"{loc.get('host_type') or ''} {loc.get('version') or ''}".strip()})
    return cands[:3]


def fonte_openalex(rede: C.Rede, reg: dict, email: str, info: dict) -> list[dict]:
    cands = []
    if reg.get("url_pdf_aberto"):
        cands.append({"fonte": "openalex", "url": reg["url_pdf_aberto"],
                      "licenca": C.normalizar_licenca(reg.get("licenca"))})
    doi = C.normalizar_doi(reg.get("doi"))
    if doi:
        try:
            j = rede.json(f"https://api.openalex.org/works/https://doi.org/{doi}",
                          params={"mailto": email,
                                  "select": "id,open_access,best_oa_location,primary_location,locations,biblio"})
            bib = j.get("biblio") or {}
            if bib.get("volume"):
                info.setdefault("volume", str(bib["volume"]))
            if bib.get("issue"):
                info.setdefault("numero", str(bib["issue"]))
            if bib.get("first_page"):
                pag = str(bib["first_page"])
                if bib.get("last_page") and bib["last_page"] != bib["first_page"]:
                    pag += f"-{bib['last_page']}"
                info.setdefault("paginas_artigo", pag)
            fonte = ((j.get("primary_location") or {}).get("source") or {})
            if fonte.get("host_organization_name"):
                info.setdefault("editora_api", fonte["host_organization_name"])
            locais = [j.get("best_oa_location") or {}] + list(j.get("locations") or [])
            for loc in locais:
                url = loc.get("pdf_url")
                if url and not any(c["url"] == url for c in cands):
                    cands.append({"fonte": "openalex", "url": url,
                                  "licenca": C.normalizar_licenca(loc.get("license"))})
        except C.ErroRede as e:
            info.setdefault("avisos_rede", []).append(f"OpenAlex: {e}")
    return cands[:3]


# --------------------------------------------------------------------------
# Download e validacao
# --------------------------------------------------------------------------


def baixar_para(rede: C.Rede, cand: dict, destino: Path, tamanho_minimo: int) -> tuple[bool, str]:
    """Baixa o candidato para 'destino' e valida. Devolve (ok, motivo)."""
    url = cand["url"]
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    host = urlparse(url).netloc.lower()
    if host in HOSTS_SO_NAVEGADOR:
        return False, HOSTS_SO_NAVEGADOR[host]
    if host in _COM_DESAFIO:
        return False, "o site exige navegador (desafio anti-robô); não contornado"
    try:
        r = rede.get(url, headers={"Accept": "application/pdf,*/*;q=0.5"}, stream=True)
    except C.ErroRede as e:
        return False, str(e)
    try:
        if r.status_code != 200:
            corpo = ""
            try:
                corpo = next(r.iter_content(2048), b"").decode("latin-1", "replace").lower()
            except Exception:
                pass
            if "just a moment" in corpo or "cloudflare" in corpo or "captcha" in corpo:
                _COM_DESAFIO.add(host)
                return False, f"HTTP {r.status_code}: o site exige navegador (desafio anti-robô); não contornado"
            return False, f"HTTP {r.status_code}"
        md5 = hashlib.md5()
        total = 0
        with open(destino, "wb") as f:
            for bloco in r.iter_content(1 << 16):
                if not bloco:
                    continue
                if total == 0 and b"%PDF-" not in bloco[:1024]:
                    ini = bloco[:400].decode("latin-1", "replace").lower()
                    if "preparing to download" in ini or "just a moment" in ini or "captcha" in ini:
                        _COM_DESAFIO.add(host)
                        return False, "o site exige navegador (desafio anti-robô); não contornado"
                    if "<html" in ini or "<!doctype" in ini:
                        return False, "veio uma página HTML em vez do PDF"
                    return False, "o conteúdo não é PDF"
                f.write(bloco)
                md5.update(bloco)
                total += len(bloco)
                if total > 150 * (1 << 20):
                    return False, "arquivo maior que 150 MB (abandonado)"
    except Exception as e:
        return False, f"download interrompido ({type(e).__name__})"
    finally:
        r.close()
    ok, motivo, _ = C.validar_pdf(destino, tamanho_minimo)
    if not ok:
        return False, motivo
    if cand.get("md5") and cand["md5"] != md5.hexdigest():
        return False, "o arquivo não confere com o MD5 informado pelo PMC"
    return True, "ok"


def processar(rede: C.Rede | None, reg: dict, ent: dict, aula: C.Aula, args, email: str) -> dict:
    chave = reg["chave"]
    destino = aula.pdf / f"{chave}.pdf"
    ent = C.entrada_manifest(reg, ent)

    if destino.exists() and not args.refazer:
        ok, motivo, n = C.validar_pdf(destino, args.tamanho_minimo)
        if ok:
            ent.update(status="ok", arquivo=f"pdf/{chave}.pdf", paginas=n, bytes=destino.stat().st_size)
            if not ent.get("origem"):
                ent["origem"] = "manual"
            ent.setdefault("sha256", C.sha256_arquivo(destino))
            if not ent.get("licenca"):
                ent["licenca"] = (C.normalizar_licenca(reg.get("licenca"))
                                  or C.licenca_no_texto(C.texto_inicial_pdf(destino, 2)) or C.LICENCA_DESCONHECIDA)
            ent.pop("motivo_pendencia", None)
            log(f"  já existe   {chave}  ({ent.get('origem')}, {ent.get('licenca')})")
            return ent
        log(f"  PDF existente inválido ({motivo}); vou tentar baixar de novo")

    tentativas: list[dict] = []
    info: dict = {}
    if rede is None:
        ent.update(status="pendente", motivo_pendencia="download não tentado (modo sem rede)")
        ent["editora"] = C.editora_de(reg, ent)
        log(f"  pendente    {chave}  (sem rede)")
        return ent

    pmcid = None
    for fonte in args.fontes:
        cands: list[dict] = []
        try:
            if fonte in ("pmc", "europepmc") and pmcid is None:
                pmcid = resolver_pmcid(rede, reg, email)
                if pmcid:
                    ent["pmcid"] = pmcid
            if fonte == "pmc":
                if not pmcid:
                    tentativas.append({"fonte": "pmc", "url": None, "resultado": "sem PMCID (artigo não está no PMC)"})
                    continue
                cands = fonte_pmc(rede, pmcid, info)
            elif fonte == "europepmc":
                cands = fonte_europepmc(rede, reg, pmcid, info)
            elif fonte == "unpaywall":
                cands = fonte_unpaywall(rede, reg, email, info)
            elif fonte == "openalex":
                cands = fonte_openalex(rede, reg, email, info)
        except C.ErroRede as e:
            tentativas.append({"fonte": fonte, "url": None, "resultado": str(e)})
            continue
        except Exception as e:  # resposta inesperada de uma API não pode derrubar o lote
            tentativas.append({"fonte": fonte, "url": None, "resultado": f"resposta inesperada ({type(e).__name__})"})
            continue
        if not cands:
            tentativas.append({"fonte": fonte, "url": None, "resultado": "nenhuma versão aberta em PDF"})
            continue
        ja = {t["url"].lower() for t in tentativas if t.get("url")}
        for cand in cands:
            if cand["url"].lower() in ja:
                continue
            ja.add(cand["url"].lower())
            tmp = destino.with_suffix(".baixando")
            ok, motivo = baixar_para(rede, cand, tmp, args.tamanho_minimo)
            if ok:
                confere, como = C.pdf_confere(reg, tmp)
                if confere is False:
                    ok, motivo = False, f"o PDF baixado não parece ser este artigo ({como})"
            if not ok:
                tmp.unlink(missing_ok=True)
                tentativas.append({"fonte": cand["fonte"], "url": cand["url"], "resultado": motivo})
                continue
            tmp.replace(destino)
            _, _, n = C.validar_pdf(destino, args.tamanho_minimo)
            licenca = (cand.get("licenca") or C.normalizar_licenca(reg.get("licenca"))
                       or C.licenca_no_texto(C.texto_inicial_pdf(destino, 2)) or C.LICENCA_DESCONHECIDA)
            tentativas.append({"fonte": cand["fonte"], "url": cand["url"], "resultado": "ok"})
            ent.update(status="ok", origem=cand["fonte"], url_origem=cand["url"], licenca=licenca,
                       arquivo=f"pdf/{chave}.pdf", bytes=destino.stat().st_size, paginas=n,
                       sha256=C.sha256_arquivo(destino), confere_artigo=confere, baixado_em=C.agora(),
                       tentativas=tentativas)
            ent.pop("motivo_pendencia", None)
            for k in ("volume", "numero", "paginas_artigo", "retratado"):
                if info.get(k):
                    ent[k] = info[k]
            ent["editora"] = C.editora_de(reg, {"editora": info.get("editora_api")})
            aviso = "" if confere else "  [sem camada de texto: conferir se é o artigo certo]"
            if ent.get("retratado"):
                aviso += "  [ATENÇÃO: o PMC marca este artigo como retratado]"
            log(f"  ok          {chave}  via {cand['fonte']}  licença {licenca}  {n} pág.{aviso}")
            return ent

    if info.get("acesso_aberto_unpaywall") is False:
        motivo = "sem versão de acesso aberto (artigo pago)"
    elif any(t.get("url") for t in tentativas):
        motivo = "há versão aberta, mas o download automático falhou nesta rede"
    else:
        motivo = "nenhuma versão aberta encontrada"
    ent.update(status="pendente", origem=None, motivo_pendencia=motivo, tentativas=tentativas)
    # Onde o usuário acha a versão gratuita no navegador (o PMC entrega o PDF a quem usa navegador).
    gratis = None
    if pmcid:
        gratis = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    else:
        for t in tentativas:
            u = t.get("url") or ""
            if u and urlparse(u).netloc.lower() not in HOSTS_SO_NAVEGADOR:
                gratis = u
                break
    if gratis and motivo.startswith("há versão aberta"):
        ent["url_gratuita"] = gratis
    else:
        ent.pop("url_gratuita", None)
    for k in ("volume", "numero", "paginas_artigo"):
        if info.get(k):
            ent[k] = info[k]
    ent["editora"] = C.editora_de(reg, {"editora": info.get("editora_api")})
    log(f"  pendente    {chave}  {motivo}")
    if args.detalhes:
        for t in tentativas:
            log(f"      - {t['fonte']}: {t['resultado']}" + (f"  <{t['url']}>" if t.get("url") else ""))
    return ent


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Baixa os PDFs de acesso aberto (PMC, Europe PMC, Unpaywall, OpenAlex) e lista os pagos em pendentes.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--registros", help="arquivo de registros (padrão: 01_busca/selecionados.json, depois registros.json)")
    ap.add_argument("--apenas", nargs="+", metavar="CHAVE", help="processa só estas chaves")
    ap.add_argument("--refazer", action="store_true", help="baixa de novo mesmo que o PDF já exista")
    ap.add_argument("--sem-rede", action="store_true", help="não acessa a rede: só atualiza manifest e pendentes.md")
    ap.add_argument("--fontes", default=",".join(FONTES),
                    help=f"fontes e ordem, separadas por vírgula (padrão: {','.join(FONTES)})")
    ap.add_argument("--email", help="e-mail de contato enviado às APIs (padrão: BOOST_EMAIL ou o genérico da Boost)")
    ap.add_argument("--pausa", type=float, default=1.0, help="pausa mínima entre requisições ao mesmo servidor, em s (padrão 1.0)")
    ap.add_argument("--tamanho-minimo", type=int, default=20_000, help="tamanho mínimo aceito para um PDF, em bytes")
    ap.add_argument("--detalhes", action="store_true", help="mostra cada tentativa dos artigos pendentes")
    args = ap.parse_args()
    args.fontes = [f.strip().lower() for f in args.fontes.split(",") if f.strip()]
    ruins = [f for f in args.fontes if f not in FONTES]
    if ruins:
        C.sair(f"Fonte desconhecida: {', '.join(ruins)}. Use: {', '.join(FONTES)}")

    aula = C.Aula(args.aula)
    aula.exigir()
    aula.criar_pastas()
    registros, origem = C.carregar_registros(aula, args.registros)
    manifest = C.carregar_manifest(aula)
    email = C.email_contato(args.email)
    rede = None if args.sem_rede else C.Rede(pausa=args.pausa)

    alvo = [r for r in registros if not args.apenas or r["chave"] in set(args.apenas)]
    if args.apenas:
        faltam = set(args.apenas) - {r["chave"] for r in alvo}
        if faltam:
            log(f"Aviso: chave(s) não encontrada(s) em {origem.name}: {', '.join(sorted(faltam))}")
    log(f"{len(alvo)} artigo(s) de {origem.name}" + ("  [sem rede]" if args.sem_rede else ""))

    for reg in alvo:
        try:
            manifest[reg["chave"]] = processar(rede, reg, manifest.get(reg["chave"]), aula, args, email)
        except KeyboardInterrupt:
            log("Interrompido; salvando o que já foi feito.")
            break
        except Exception as e:  # um registro ruim não derruba o lote
            ent = C.entrada_manifest(reg, manifest.get(reg["chave"]))
            ent.update(status="pendente", motivo_pendencia=f"erro inesperado ({type(e).__name__}: {e})")
            manifest[reg["chave"]] = ent
            log(f"  erro        {reg['chave']}  {type(e).__name__}: {e}")
        C.salvar_manifest(aula, manifest)

    for reg in registros:  # registros fora do --apenas também precisam constar
        manifest.setdefault(reg["chave"], C.entrada_manifest(reg))
    C.salvar_manifest(aula, manifest)
    n_pend = C.escrever_pendentes(aula, registros, manifest)

    ok = [r for r in registros if manifest[r["chave"]].get("status") == "ok"]
    log("")
    log(f"Resumo: {len(ok)} com PDF, {n_pend} pendente(s), de {len(registros)} selecionado(s).")
    por_origem: dict[str, int] = {}
    for r in ok:
        o = manifest[r["chave"]].get("origem") or "?"
        por_origem[o] = por_origem.get(o, 0) + 1
    if por_origem:
        log("  Origem: " + ", ".join(f"{k} {v}" for k, v in sorted(por_origem.items())))
    restritas = [r["chave"] for r in ok
                 if not C.licenca_permite_reproduzir(manifest[r["chave"]].get("licenca"))]
    if restritas:
        log("  Sem licença aberta registrada (figuras podem exigir permissão): " + ", ".join(restritas))
    if rede is not None and rede.bloqueados:
        log("  Servidores inacessíveis nesta rede: " + ", ".join(sorted(rede.bloqueados)))
    log(f"  Manifest: {aula.manifest}")
    if n_pend:
        log(f"  Pendências para o usuário baixar: {aula.pendentes}")
        log("  Depois que ele salvar os PDFs em 02_artigos/manual/, rode incorporar_manuais.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
