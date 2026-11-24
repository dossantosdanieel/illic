#!/usr/bin/env python3
"""Incorpora os PDFs que o usuário baixou à mão e soltou em 02_artigos/manual/.

Casa cada arquivo com um registro (primeiro pelo DOI no texto, nos metadados ou no
nome do arquivo; depois pelo título aproximado nas primeiras páginas), move para
02_artigos/pdf/<chave>.pdf, atualiza manifest.json e pendentes.md e relata o que não
conseguiu casar.

Uso:
  python3 incorporar_manuais.py AULA
  python3 incorporar_manuais.py AULA --copiar                 # mantém o original em manual/
  python3 incorporar_manuais.py AULA --forcar "download (3).pdf=Rio2015"
  python3 incorporar_manuais.py AULA --simular                # só mostra o que faria
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _comum as C  # noqa: E402


def log(msg: str) -> None:
    print(msg, flush=True)


def _so_alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def casar(arquivo: Path, registros: list[dict]) -> tuple[dict | None, str, list[tuple[float, str]]]:
    """Devolve (registro, como_casou, ranking_de_titulos)."""
    inicio = C.texto_inicial_pdf(arquivo, 2)
    meta = C.metadados_pdf(arquivo)
    por_doi = {r["doi"]: r for r in registros if r.get("doi")}

    # 1) DOI nos metadados ou nas duas primeiras páginas (referências ficam no fim e não entram aqui)
    for origem, texto in (("metadados", meta), ("texto da primeira página", inicio)):
        achados = [d for d in C.achar_dois(texto) if d in por_doi]
        if len(set(achados)) == 1:
            return por_doi[achados[0]], f"DOI nos {origem}" if origem == "metadados" else f"DOI no {origem}", []
        if len(set(achados)) > 1:  # mais de um DOI conhecido: fica com o primeiro que aparece
            return por_doi[achados[0]], f"DOI ({origem}; havia mais de um, usei o primeiro)", []
    # DOI quebrado por espaços/linhas no PDF
    compacto = _so_alnum(inicio + meta)
    achados = [r for d, r in por_doi.items() if len(_so_alnum(d)) >= 12 and _so_alnum(d) in compacto]
    if len(achados) == 1:
        return achados[0], "DOI no texto (reconstruído)", []

    # 2) sufixo do DOI no nome do arquivo (ex.: jospt.2015.5987.pdf, bjsports-2014-094386.pdf)
    nome = _so_alnum(arquivo.stem)
    achados = [r for d, r in por_doi.items()
               if len(_so_alnum(d.split("/", 1)[-1])) >= 8 and _so_alnum(d.split("/", 1)[-1]) in nome]
    if len(achados) == 1:
        return achados[0], "DOI no nome do arquivo", []

    # 3) título aproximado nas primeiras páginas (com apoio do sobrenome do primeiro autor)
    texto = inicio + "\n" + meta
    if len(C.normalizar_texto(texto)) < 100:
        return None, "PDF sem camada de texto (digitalizado): não dá para identificar sozinho", []
    notas = []
    alvo = C.normalizar_texto(texto)
    palavras = set(alvo.split())
    for r in registros:
        titulo = r.get("titulo") or ""
        autor = C.normalizar_texto(str(r.get("primeiro_autor") or "")).split()
        tem_autor = bool(autor) and all(a in palavras for a in autor)
        if C.titulo_curto(titulo):
            # título curto: só a frase inteira conta (palavras soltas aparecem em qualquer artigo do tema)
            cob = 1.0 if C.titulo_exato(titulo, texto) else 0.5 * C.cobertura_titulo(titulo, texto)
            if cob == 1.0 and tem_autor:
                return r, "título curto completo + sobrenome do primeiro autor na primeira página", []
        else:
            cob = C.cobertura_titulo(titulo, texto)
        bonus = 0.05 if tem_autor else 0.0
        notas.append((min(cob + bonus, 1.0), r["chave"]))
    notas.sort(reverse=True)
    if notas:
        melhor, segundo = notas[0], (notas[1] if len(notas) > 1 else (0.0, ""))
        n_pal = len([p for p in C.normalizar_texto(
            next(r for r in registros if r["chave"] == melhor[1]).get("titulo") or "").split() if len(p) > 2])
        if melhor[0] >= 0.85 and n_pal >= 4 and melhor[0] - segundo[0] >= 0.12:
            reg = next(r for r in registros if r["chave"] == melhor[1])
            return reg, f"título aproximado ({melhor[0]:.0%} das palavras do título na primeira página)", notas[:3]
    dois = C.achar_dois(inicio)
    pista = f" (o PDF traz o DOI {dois[0]}, que não está nos registros)" if dois else ""
    return None, "nem DOI nem título bateram com segurança" + pista, notas[:3]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Casa os PDFs de 02_artigos/manual/ com os registros e os move para 02_artigos/pdf/<chave>.pdf.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    ap.add_argument("aula", help="pasta da aula (aulas/<AAAA-MM>-<slug>)")
    ap.add_argument("--registros", help="arquivo de registros (padrão: selecionados.json, depois registros.json)")
    ap.add_argument("--copiar", action="store_true", help="copia em vez de mover (o original fica em manual/)")
    ap.add_argument("--substituir", action="store_true", help="substitui o PDF que já existir em pdf/")
    ap.add_argument("--forcar", action="append", default=[], metavar="ARQUIVO=CHAVE",
                    help="casa um arquivo com uma chave à força (pode repetir)")
    ap.add_argument("--simular", action="store_true", help="mostra o que faria, sem mover nada")
    args = ap.parse_args()

    aula = C.Aula(args.aula)
    aula.exigir()
    aula.criar_pastas()
    registros, _ = C.carregar_registros(aula, args.registros)
    por_chave = {r["chave"]: r for r in registros}
    manifest = C.carregar_manifest(aula)

    forcados: dict[str, str] = {}
    for item in args.forcar:
        if "=" not in item:
            C.sair(f"--forcar espera ARQUIVO=CHAVE, recebi: {item}")
        arq, chave = item.rsplit("=", 1)
        forcados[Path(arq.strip()).name] = chave.strip()
    invalidas = sorted({c for c in forcados.values() if c not in por_chave})
    if invalidas:  # chave digitada errada criaria um artigo órfão no manifest
        C.sair(f"--forcar: chave(s) que não existem nos registros: {', '.join(invalidas)}. "
               f"Chaves válidas: {', '.join(sorted(por_chave))}")

    arquivos = sorted(p for p in aula.manual.rglob("*") if p.is_file() and not p.name.startswith("."))
    if not arquivos:
        log(f"Nenhum arquivo em {aula.manual}.")
        C.escrever_pendentes(aula, registros, manifest)
        return 0

    incorporados, problemas, ja_usadas = [], [], set()
    for arq in arquivos:
        rel = arq.relative_to(aula.manual)
        ok, motivo, n_pag = C.validar_pdf(arq, 10_000)
        if not ok:
            problemas.append((rel, f"arquivo ignorado: {motivo}", []))
            continue
        ranking: list[tuple[float, str]] = []
        if arq.name in forcados:
            chave = forcados[arq.name]
            reg = por_chave[chave]
            como = "forçado pelo usuário"
        else:
            try:
                reg, como, ranking = casar(arq, registros)
            except Exception as e:
                reg, como = None, f"erro ao ler o PDF ({type(e).__name__})"
        if reg is None:
            problemas.append((rel, como, ranking))
            continue
        chave = reg["chave"]
        destino = aula.pdf / f"{chave}.pdf"
        if chave in ja_usadas:
            problemas.append((rel, f"parece duplicata de {chave} (outro arquivo desta pasta já foi usado)", []))
            continue
        if destino.exists() and not args.substituir:
            problemas.append((rel, f"é {chave}, mas pdf/{chave}.pdf já existe (use --substituir para trocar)", []))
            ja_usadas.add(chave)
            continue
        ja_usadas.add(chave)
        if args.simular:
            log(f"  [simulação] {rel}  ->  pdf/{chave}.pdf   ({como})")
            incorporados.append(chave)
            continue
        if args.copiar:
            shutil.copy2(arq, destino)
        else:
            shutil.move(str(arq), str(destino))
        ent = C.entrada_manifest(reg, manifest.get(chave))
        licenca = (C.licenca_no_texto(C.texto_inicial_pdf(destino, 2))
                   or (C.normalizar_licenca(reg.get("licenca")) if reg.get("acesso_aberto") else None)
                   or C.LICENCA_RESERVADA)
        ent.update(status="ok", origem="manual", url_origem=None, licenca=licenca,
                   arquivo=f"pdf/{chave}.pdf", bytes=destino.stat().st_size, paginas=n_pag,
                   sha256=C.sha256_arquivo(destino), casado_por=como, arquivo_original=str(rel),
                   baixado_em=C.agora())
        ent.pop("motivo_pendencia", None)
        ent.setdefault("editora", C.editora_de(reg, ent))
        manifest[chave] = ent
        incorporados.append(chave)
        log(f"  ok  {rel}  ->  pdf/{chave}.pdf   ({como}; licença {licenca}; {n_pag} pág.)")

    if not args.simular:
        C.salvar_manifest(aula, manifest)
        n_pend = C.escrever_pendentes(aula, registros, manifest)
    else:
        n_pend = sum(1 for r in registros if manifest.get(r["chave"], {}).get("status") != "ok"
                     and r["chave"] not in incorporados)

    log("")
    log(f"Resumo: {len(incorporados)} incorporado(s), {len(problemas)} sem casar, {n_pend} ainda pendente(s).")
    if problemas:
        log("Não consegui incorporar:")
        for rel, motivo, ranking in problemas:
            log(f"  - {rel}: {motivo}")
            if ranking:
                log("      mais parecidos: " + ", ".join(f"{k} ({n:.0%})" for n, k in ranking))
        log('  Para resolver à mão: --forcar "NOME_DO_ARQUIVO.pdf=Chave"')
    if n_pend:
        faltam = [r["chave"] for r in registros if manifest.get(r["chave"], {}).get("status") != "ok"
                  and not (args.simular and r["chave"] in incorporados)]
        log("Ainda faltam: " + ", ".join(faltam) + f"  (ver {aula.pendentes})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
