#!/usr/bin/env python3
"""
quiz_dedup.py — Indice e controllo anti-duplicati per il Quizzone.

Uso:
    python quiz_dedup.py index
        Rigenera puntate/answers_index.txt da tutti i file quiz_history*.md
        (cerca in ./, ./puntate/, ./storico/). Output: una voce per riga,
        normalizzata (no accenti, lowercase), con riferimento puntata.

    python quiz_dedup.py check <nuovo_quiz.md>
        Confronta il nuovo quiz contro lo storico con matching normalizzato
        (format-agnostic: non serve parsare il formato del quiz).
        Exit 0 = pulito. Exit 1 = duplicati potenziali (report su stdout).

Design:
- Normalizzazione NFKD: "García Márquez" == "garcia marquez". BOM e \r rimossi.
- Matching a co-occorrenza di token: una voce dello storico viene segnalata se
  i suoi token significativi ricompaiono nel nuovo quiz (>=2 token, oppure 1
  token "raro" lungo >=8 caratteri, es. "tordesillas", "ouagadougou").
- Nessuna dipendenza esterna, solo stdlib.
"""

import re
import sys
import unicodedata
from pathlib import Path

HISTORY_GLOBS = ["quiz_history*.md"]
SEARCH_DIRS = [Path("."), Path("puntate"), Path("storico")]
INDEX_PATH = Path("puntate/answers_index.txt")

STOPWORDS = {
    # italiano
    "della", "delle", "dello", "degli", "nella", "nelle", "nello", "negli",
    "sulla", "sulle", "sullo", "sugli", "dalla", "dalle", "dallo", "dagli",
    "alla", "alle", "allo", "agli", "come", "quale", "quali", "quando",
    "dove", "perche", "cosa", "chi", "che", "con", "per", "tra", "fra",
    "una", "uno", "un", "il", "lo", "la", "le", "gli", "i", "di", "da",
    "in", "su", "a", "e", "o", "non", "piu", "meno", "primo", "prima",
    "secondo", "seconda", "terzo", "terza", "solo", "anche", "sono", "era",
    "anno", "anni", "mondo", "mondiale", "grande", "citta", "paese",
    "capitale", "autore", "scrittore", "regista", "film", "libro", "opera",
    "significato", "termine", "parola", "quiz", "domanda", "risposta",
    "trattato", "guerra", "premio", "francese", "inglese", "tedesco",
    "significa", "espressione", "chiamato", "chiamata", "quanti", "quante",
    "nome", "quale", "questo", "questa", "essere", "stato", "stata",
    "italiano", "italiana", "famoso", "famosa", "celebre", "vero", "falso",
    # inglese di servizio
    "the", "of", "and", "audio", "testo", "esatto",
}

# categorie/emoji e marcatori da ignorare
LINE_RE = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)$")
HEADER_RE = re.compile(r"^###\s+(.*)$")


def normalize(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.casefold()
    return text


def tokens(text: str) -> set[str]:
    text = normalize(text)
    raw = re.findall(r"[a-z0-9]+", text)
    out = set()
    for t in raw:
        if t in STOPWORDS:
            continue
        if t.isdigit():
            # numeri: teniamo solo quelli "informativi" (anni, costanti)
            if len(t) >= 3:
                out.add(t)
            continue
        if len(t) >= 4:
            out.add(t)
    return out


def find_history_files() -> list[Path]:
    files: list[Path] = []
    for d in SEARCH_DIRS:
        if d.is_dir():
            for g in HISTORY_GLOBS:
                files.extend(sorted(d.glob(g)))
    # dedup path
    seen, out = set(), []
    for f in files:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            out.append(f)
    return out


def parse_history() -> list[tuple[str, str, str]]:
    """Ritorna lista di (puntata, num, testo_voce)."""
    entries = []
    for f in find_history_files():
        current = f.name
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.replace("\ufeff", "").rstrip("\r")
            h = HEADER_RE.match(line)
            if h:
                current = h.group(1).strip()
                continue
            m = LINE_RE.match(line)
            if m:
                entries.append((current, m.group(1), m.group(2).strip()))
    return entries


def cmd_index() -> int:
    entries = parse_history()
    if not entries:
        print("ERRORE: nessun file quiz_history*.md trovato in ./, puntate/, storico/", file=sys.stderr)
        return 2
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as fh:
        fh.write("# Indice risposte usate — GENERATO, non editare a mano\n")
        fh.write("# Queste voci sono VIETATE come risposta corretta di nuove domande\n")
        for punt, num, text in entries:
            fh.write(f"{normalize(text)}  [{punt} D{num}]\n")
    print(f"OK: indicizzate {len(entries)} voci da {len(find_history_files())} file → {INDEX_PATH}")
    return 0


def cmd_check(quiz_path: str) -> int:
    p = Path(quiz_path)
    if not p.is_file():
        print(f"ERRORE: file non trovato: {quiz_path}", file=sys.stderr)
        return 2
    quiz_text = p.read_text(encoding="utf-8", errors="replace")
    quiz_toks = tokens(quiz_text)

    entries = parse_history()
    if not entries:
        print("ERRORE: storico non trovato — impossibile fare il check", file=sys.stderr)
        return 2

    flagged = []
    for punt, num, text in entries:
        etoks = tokens(text)
        if not etoks:
            continue
        overlap = etoks & quiz_toks
        rare_hit = any(len(t) >= 9 for t in overlap if not t.isdigit())
        if len(overlap) >= 2 or rare_hit:
            flagged.append((punt, num, text, sorted(overlap)))

    if not flagged:
        print("PULITO: nessuna sovrapposizione rilevata con lo storico.")
        return 0

    print(f"ATTENZIONE: {len(flagged)} voci dello storico si sovrappongono al nuovo quiz.")
    print("Per ciascuna: verifica se nel nuovo quiz c'è una domanda con la STESSA")
    print("risposta corretta / stessa angolazione. In tal caso SOSTITUISCILA.\n")
    for punt, num, text, ov in flagged[:80]:
        print(f"- [{punt} D{num}] {text}")
        print(f"  token in comune: {', '.join(ov)}")
    if len(flagged) > 80:
        print(f"... e altre {len(flagged) - 80} voci.")
    return 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"index", "check"}:
        print(__doc__)
        return 2
    if sys.argv[1] == "index":
        return cmd_index()
    if len(sys.argv) < 3:
        print("Uso: python quiz_dedup.py check <nuovo_quiz.md>", file=sys.stderr)
        return 2
    return cmd_check(sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
