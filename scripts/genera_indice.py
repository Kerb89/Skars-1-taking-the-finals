#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genera_indice.py — Rigenera la home page (index.html) del Quizzone.

Scansiona la cartella delle puntate, estrae numero/tema/titolo da ogni file
HTML e riscrive da zero l'index.html nella root del repo. Da eseguire come
ULTIMO passo del workflow di approvazione, prima del push.

USO:
    python genera_indice.py                     # default: ./puntate → ./index.html
    python genera_indice.py --cartella puntate --output index.html

CONVENZIONI RICONOSCIUTE:
  - Nome file:  quiz_puntata<NUM>_<tema>.html   (es. quiz_puntata12_misto.html)
  - Titolo:     dal <title> dell'HTML se presente e non generico,
                altrimenti costruito da numero + tema.
  - Data:       da un eventuale <meta name="data" content="GG/MM/AAAA">,
                altrimenti data di ultima modifica del file.

Nessuna dipendenza esterna: solo libreria standard.

NOTA PER KIRO: questo script RIGENERA l'index da zero a ogni esecuzione.
Non modificare index.html a mano: ogni modifica manuale verrà sovrascritta.
Per cambiare l'aspetto, modificare il TEMPLATE qui sotto.
"""

import argparse
import html
import re
import sys
from datetime import datetime
from pathlib import Path

PATTERN_NOME = re.compile(r"quiz_puntata(\d+)_(.+)\.html$", re.IGNORECASE)
PATTERN_TITLE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
PATTERN_META_DATA = re.compile(
    r"<meta\s+name=[\"']data[\"']\s+content=[\"']([^\"']+)[\"']", re.IGNORECASE)

TITOLI_GENERICI = {"quiz", "quizzone", "document", "untitled", ""}


def leggi_puntata(path: Path):
    m = PATTERN_NOME.search(path.name)
    if not m:
        return None
    numero = int(m.group(1))
    tema = m.group(2).replace("_", " ").replace("-", " ").strip()

    testo = path.read_text(encoding="utf-8", errors="replace")

    titolo = None
    tm = PATTERN_TITLE.search(testo)
    if tm:
        t = re.sub(r"\s+", " ", tm.group(1)).strip()
        if t.lower() not in TITOLI_GENERICI:
            titolo = t
    if not titolo:
        titolo = tema.capitalize()

    dm = PATTERN_META_DATA.search(testo)
    if dm:
        data = dm.group(1)
    else:
        data = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y")

    return {
        "numero": numero,
        "tema": tema,
        "titolo": titolo,
        "data": data,
        "file": path.name,
    }


TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>il Quizzone — SKARS</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bungee&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #14111a;
    --card: #1d1926;
    --card-hover: #262031;
    --oro: #f2b544;
    --testo: #ece7dd;
    --muto: #8a8395;
    --bordo: #2e2839;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--testo);
    font-family: "Space Grotesk", system-ui, sans-serif;
    min-height: 100vh;
    padding: 0 24px 80px;
  }}
  header {{
    max-width: 960px;
    margin: 0 auto;
    padding: 64px 0 40px;
    border-bottom: 1px solid var(--bordo);
  }}
  .onair {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--oro);
    margin-bottom: 18px;
  }}
  .onair::before {{
    content: "";
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--oro);
    box-shadow: 0 0 10px var(--oro);
    animation: lampeggia 2.4s ease-in-out infinite;
  }}
  @keyframes lampeggia {{ 50% {{ opacity: 0.25; box-shadow: none; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .onair::before {{ animation: none; }}
    .card {{ transition: none !important; }}
  }}
  h1 {{
    font-family: "Bungee", "Space Grotesk", sans-serif;
    font-size: clamp(2.4rem, 7vw, 4.2rem);
    line-height: 1.05;
    color: var(--testo);
  }}
  h1 span {{ color: var(--oro); }}
  .sottotitolo {{
    margin-top: 14px;
    color: var(--muto);
    font-size: 1rem;
  }}
  main {{
    max-width: 960px;
    margin: 40px auto 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
    gap: 18px;
  }}
  .card {{
    display: flex;
    align-items: center;
    gap: 18px;
    background: var(--card);
    border: 1px solid var(--bordo);
    border-radius: 14px;
    padding: 20px 22px;
    text-decoration: none;
    color: var(--testo);
    transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
  }}
  .card:hover, .card:focus-visible {{
    transform: translateY(-3px);
    background: var(--card-hover);
    border-color: var(--oro);
    outline: none;
  }}
  .card:focus-visible {{ box-shadow: 0 0 0 3px rgba(242, 181, 68, 0.4); }}
  .numero {{
    font-family: "Bungee", sans-serif;
    font-size: 2.1rem;
    color: var(--oro);
    min-width: 62px;
    text-align: center;
    line-height: 1;
  }}
  .numero small {{
    display: block;
    font-family: "Space Grotesk", sans-serif;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: var(--muto);
    margin-bottom: 4px;
  }}
  .info h2 {{
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .info .meta {{
    font-size: 0.82rem;
    color: var(--muto);
  }}
  .vuoto {{
    grid-column: 1 / -1;
    text-align: center;
    color: var(--muto);
    padding: 60px 0;
  }}
  footer {{
    max-width: 960px;
    margin: 56px auto 0;
    color: var(--muto);
    font-size: 0.8rem;
    border-top: 1px solid var(--bordo);
    padding-top: 20px;
  }}
</style>
</head>
<body>
<header>
  <div class="onair">In onda</div>
  <h1>il <span>Quizzone</span></h1>
  <p class="sottotitolo">Scegli la puntata e si comincia. {n_puntate} puntate in archivio.</p>
</header>
<main>
{cards}
</main>
<footer>SKARS · aggiornato il {aggiornato}</footer>
</body>
</html>
"""

CARD = """  <a class="card" href="{href}">
    <div class="numero"><small>EP</small>{numero}</div>
    <div class="info">
      <h2>{titolo}</h2>
      <div class="meta">{tema} · {data}</div>
    </div>
  </a>"""

VUOTO = '  <p class="vuoto">Nessuna puntata ancora pubblicata. Torna presto.</p>'


def main():
    ap = argparse.ArgumentParser(description="Rigenera la home page del Quizzone")
    ap.add_argument("--cartella", default="puntate",
                    help="Cartella contenente gli HTML delle puntate (default: puntate)")
    ap.add_argument("--output", default="index.html",
                    help="File indice da generare (default: index.html nella root)")
    args = ap.parse_args()

    cartella = Path(args.cartella)
    if not cartella.is_dir():
        print(f"ERRORE: cartella non trovata: {cartella.resolve()}")
        sys.exit(2)

    puntate = []
    scartati = []
    for f in sorted(cartella.glob("*.html")):
        p = leggi_puntata(f)
        if p:
            puntate.append(p)
        else:
            scartati.append(f.name)

    puntate.sort(key=lambda p: p["numero"], reverse=True)  # più recente in alto

    if scartati:
        print(f"AVVISO: {len(scartati)} file ignorati (nome fuori convenzione "
              f"quiz_puntataNN_tema.html): {scartati}")

    if puntate:
        cards = "\n".join(CARD.format(
            href=f"{cartella.name}/{html.escape(p['file'])}",
            numero=p["numero"],
            titolo=html.escape(p["titolo"]),
            tema=html.escape(p["tema"]),
            data=html.escape(p["data"]),
        ) for p in puntate)
    else:
        cards = VUOTO

    out = Path(args.output)
    out.write_text(TEMPLATE.format(
        cards=cards,
        n_puntate=len(puntate),
        aggiornato=datetime.now().strftime("%d/%m/%Y"),
    ), encoding="utf-8")

    print(f"OK: {out} rigenerato con {len(puntate)} puntate.")
    sys.exit(0)


if __name__ == "__main__":
    main()
