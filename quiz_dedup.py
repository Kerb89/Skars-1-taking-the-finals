#!/usr/bin/env python3
"""
quiz_dedup.py — Indice e controllo anti-duplicati per il Quizzone (v2, role-aware).

Uso:
    python quiz_dedup.py index
        (invariato) Rigenera puntate/answers_index.txt da tutti i file
        quiz_history*.md (cerca in ./, ./puntate/, ./storico/).

    python quiz_dedup.py check <nuovo_quiz.md>
        Controllo consapevole del RUOLO delle entità nel nuovo quiz:

        ERR  (bloccante, exit 1)
          - una risposta corretta del nuovo quiz coincide con una voce dello
            storico (risposta riusata);
          - leakage interno: la risposta di una domanda compare nel testo
            (o nella spiegazione) di un'altra domanda dello stesso quiz.
        WARN (non bloccante, exit 0)
          - stessa entità come risposta corretta in due domande del nuovo
            quiz: lecito se i fatti chiesti sono diversi — giudica tu.
        SILENZIO
          - entità condivise solo nei testi delle domande o nei distrattori
            (es. stesso regista citato in due domande su film diversi):
            non regalano punti a nessuno.

        Se il parser non riconosce il formato del quiz (niente sezione
        soluzioni, o troppe domande senza soluzione), ricade nel vecchio
        check format-agnostic su tutto il testo e lo dichiara con un banner
        MODALITÀ LEGACY.

Design:
- Normalizzazione NFKD: "García Márquez" == "garcia marquez". BOM e \r rimossi.
- Matching a co-occorrenza di token: overlap significativo = >=2 token
  significativi in comune, oppure 1 token "raro" lungo >=9 caratteri
  (es. "tordesillas", "ouagadougou").
- Nessuna dipendenza esterna, solo stdlib.

Assunzioni sul formato del nuovo quiz (correggere le regex se non tornano):
- Domande:   "N. testo" o "N) testo"  (grassetto ** tollerato)
- Opzioni:   "A) testo" ... "D) testo" (anche "- A)" o "A.")
- Spiegazioni: righe "> Spiegazione: ..."
- Soluzioni: sezione con intestazione contenente "soluzion" o "rispost",
  righe tipo "N. B", "N) B — testo", "N: B, D". La sezione termina alla
  prossima intestazione (es. "## Fonti").
"""

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

HISTORY_GLOBS = ["quiz_history*.md"]
SEARCH_DIRS = [Path("."), Path("puntate"), Path("storico")]
INDEX_PATH = Path("puntate/answers_index.txt")

RARE_LEN = 9          # lunghezza minima di un token "raro" che basta da solo
MIN_OVERLAP = 2       # token in comune perché l'overlap sia significativo
MIN_QUESTIONS = 5     # sotto questa soglia il parse è considerato fallito
MIN_SOLVED_RATIO = 0.7  # quota minima di domande con soluzione trovata

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
    # aggiunte v2: parole-cornice del formato
    "spiegazione", "soluzione", "soluzioni", "seguenti", "corretta",
    # inglese di servizio
    "the", "of", "and", "audio", "testo", "esatto",
}

LINE_RE = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)$")
HEADER_RE = re.compile(r"^###\s+(.*)$")

# --- regex per il parse del NUOVO quiz -------------------------------------
QUESTION_RE = re.compile(r"^\s*\**(\d{1,3})[\.\)]\**\s+(.*)$")
OPTION_RE = re.compile(r"^\s*[-*]?\s*\**([A-Da-d])[\.\)]\**\s+(.*)$")
ANY_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.*)$")
SOL_LINE_RE = re.compile(
    r"^\s*[-*]?\s*\**(\d{1,3})[\.\):]?\**\s*[\-—:>]?\s*\**([A-D])\b\**\s*(.*)$"
)
EXTRA_LETTER_RE = re.compile(r"^[,e/+\s]+([A-D])\b\s*(.*)$")


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
            if len(t) >= 3:
                out.add(t)
            continue
        if len(t) >= 4:
            out.add(t)
    return out


def sig_overlap(a: set[str], b: set[str]) -> set[str] | None:
    """Overlap 'significativo' secondo le soglie storiche dello script."""
    ov = a & b
    if not ov:
        return None
    rare_hit = any(len(t) >= RARE_LEN and not t.isdigit() for t in ov)
    if len(ov) >= MIN_OVERLAP or rare_hit:
        return ov
    return None


def sig_overlap_answers(a: set[str], b: set[str]) -> set[str] | None:
    """Overlap tra due RISPOSTE: set piccoli e specifici, basta un solo
    token >=5 caratteri (cattura "canberra", "kubrick", "milano";
    esclude rumore corto tipo "cent", "roma")."""
    ov = a & b
    if not ov:
        return None
    if len(ov) >= MIN_OVERLAP or any(len(t) >= 5 and not t.isdigit() for t in ov):
        return ov
    return None


# --- storico (invariato) ----------------------------------------------------

def find_history_files() -> list[Path]:
    files: list[Path] = []
    for d in SEARCH_DIRS:
        if d.is_dir():
            for g in HISTORY_GLOBS:
                files.extend(sorted(d.glob(g)))
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


# --- parse del nuovo quiz (v2) ----------------------------------------------

@dataclass
class Question:
    num: int
    prompt: str = ""
    expl: str = ""
    options: dict[str, str] = field(default_factory=dict)
    letters: set[str] = field(default_factory=set)   # lettere corrette
    sol_text: str = ""                               # testo extra sulla riga soluzione
    # token calcolati a posteriori:
    answer_toks: set[str] = field(default_factory=set)
    leak_toks: set[str] = field(default_factory=set)  # prompt + spiegazione


def _is_solutions_header(line: str) -> bool:
    m = ANY_HEADER_RE.match(line)
    if not m:
        return False
    h = normalize(m.group(1))
    return "soluzion" in h or "rispost" in h


def parse_quiz(text: str) -> tuple[list[Question], bool]:
    """Ritorna (domande, parse_ok). parse_ok=False → usare fallback legacy."""
    lines = text.splitlines()

    sol_start = None
    for i, line in enumerate(lines):
        if _is_solutions_header(line):
            sol_start = i + 1
            break

    if sol_start is None:
        return [], False

    # -- domande (prima della sezione soluzioni)
    questions: dict[int, Question] = {}
    cur: Question | None = None
    for line in lines[:sol_start - 1]:
        line = line.rstrip()
        if not line or ANY_HEADER_RE.match(line):
            continue
        mo = OPTION_RE.match(line)
        mq = QUESTION_RE.match(line)
        if mo and not (mq and not mo.group(1).isalpha()):
            if cur is not None:
                cur.options[mo.group(1).upper()] = mo.group(2).strip()
            continue
        if mq:
            cur = Question(num=int(mq.group(1)), prompt=mq.group(2).strip())
            questions[cur.num] = cur
            continue
        if line.lstrip().startswith(">"):
            if cur is not None:
                cur.expl += " " + line.lstrip("> ").strip()
            continue
        if cur is not None and not cur.options:
            # continuazione del testo della domanda su più righe
            cur.prompt += " " + line.strip()

    # -- soluzioni (fino alla prossima intestazione, es. "## Fonti")
    for line in lines[sol_start:]:
        if ANY_HEADER_RE.match(line):
            break
        m = SOL_LINE_RE.match(line)
        if not m:
            continue
        num = int(m.group(1))
        if num not in questions:
            continue
        q = questions[num]
        q.letters.add(m.group(2))
        rest = m.group(3) or ""
        m2 = EXTRA_LETTER_RE.match(rest)
        if m2:
            q.letters.add(m2.group(1))
            rest = m2.group(2)
        q.sol_text = rest.strip()

    qs = sorted(questions.values(), key=lambda q: q.num)
    solved = [q for q in qs if q.letters]
    parse_ok = (
        len(qs) >= MIN_QUESTIONS
        and len(solved) >= MIN_SOLVED_RATIO * len(qs)
    )
    if not parse_ok:
        return qs, False

    # -- token per ruolo
    # La RISPOSTA è l'entità: solo il testo dell'opzione corretta.
    # La prosa nella sezione Soluzioni (dopo "N. B — ...") è SPIEGAZIONE:
    # non è la risposta, ma è mostrata in gioco → superficie di leak.
    for q in qs:
        ans_texts = [q.options[l] for l in q.letters if l in q.options]
        if not ans_texts and q.sol_text:
            # fallback quando le opzioni non sono nel file: prendo solo la
            # parte breve prima del primo separatore, non tutta la prosa.
            short = re.split(r"[.—–:]", q.sol_text, maxsplit=1)[0]
            ans_texts = [short]
        q.answer_toks = tokens(" ".join(ans_texts))
        # la spiegazione: se non c'era una riga ">", usa la prosa della soluzione
        if not q.expl:
            q.expl = q.sol_text
        q.leak_toks = tokens(q.prompt + " " + q.expl)
        # i distrattori restano fuori da entrambi i set: riciclo lecito

    return solved, True


# --- check (v2) ---------------------------------------------------------------

def legacy_check(quiz_text: str, entries) -> int:
    """Vecchio comportamento format-agnostic, tenuto come paracadute."""
    quiz_toks = tokens(quiz_text)
    flagged = []
    for punt, num, text in entries:
        etoks = tokens(text)
        if not etoks:
            continue
        ov = sig_overlap(etoks, quiz_toks)
        if ov:
            flagged.append((punt, num, text, sorted(ov)))
    if not flagged:
        print("PULITO (legacy): nessuna sovrapposizione rilevata con lo storico.")
        return 0
    print(f"ATTENZIONE (legacy): {len(flagged)} voci dello storico si sovrappongono al nuovo quiz.")
    for punt, num, text, ov in flagged[:80]:
        print(f"- [{punt} D{num}] {text}")
        print(f"  token in comune: {', '.join(ov)}")
    if len(flagged) > 80:
        print(f"... e altre {len(flagged) - 80} voci.")
    return 1


def cmd_check(quiz_path: str) -> int:
    p = Path(quiz_path)
    if not p.is_file():
        print(f"ERRORE: file non trovato: {quiz_path}", file=sys.stderr)
        return 2
    quiz_text = p.read_text(encoding="utf-8", errors="replace")

    entries = parse_history()
    if not entries:
        print("ERRORE: storico non trovato — impossibile fare il check", file=sys.stderr)
        return 2

    questions, parse_ok = parse_quiz(quiz_text)
    if not parse_ok:
        print("=" * 68)
        print("MODALITÀ LEGACY: non ho riconosciuto il formato del quiz")
        print("(sezione soluzioni assente o troppe domande senza soluzione).")
        print("Il check torna format-agnostic: aspettati più falsi positivi.")
        print("=" * 68)
        return legacy_check(quiz_text, entries)

    errs: list[str] = []
    warns: list[str] = []

    # 1) storico → solo contro le RISPOSTE CORRETTE del nuovo quiz
    for punt, num, text in entries:
        etoks = tokens(text)
        if not etoks:
            continue
        for q in questions:
            ov = sig_overlap_answers(etoks, q.answer_toks)
            if ov:
                errs.append(
                    f"D{q.num}: risposta già usata nello storico [{punt} D{num}] "
                    f"«{text}» — token: {', '.join(sorted(ov))}"
                )

    # 2) leakage interno: risposta di Qi nel testo/spiegazione di Qj
    for qi in questions:
        for qj in questions:
            if qi.num == qj.num:
                continue
            ov = sig_overlap(qi.answer_toks, qj.leak_toks)
            if ov:
                errs.append(
                    f"D{qj.num}: il testo (o la spiegazione) contiene la risposta "
                    f"di D{qi.num} — token: {', '.join(sorted(ov))}"
                )

    # 3) stessa entità come risposta in due domande: giudizio umano
    for qi, qj in combinations(questions, 2):
        ov = sig_overlap_answers(qi.answer_toks, qj.answer_toks)
        if ov:
            warns.append(
                f"D{qi.num}/D{qj.num}: stessa entità come risposta corretta "
                f"— ok se i fatti chiesti sono diversi. Token: {', '.join(sorted(ov))}"
            )

    if not errs and not warns:
        print(f"PULITO: {len(questions)} domande, nessun problema rilevato.")
        return 0

    if errs:
        print(f"ERRORI ({len(errs)}) — da sistemare prima dell'approvazione:")
        for e in errs:
            print(f"  ✗ {e}")
    if warns:
        print(f"\nAVVISI ({len(warns)}) — non bloccanti, giudica tu:")
        for w in warns:
            print(f"  ~ {w}")

    return 1 if errs else 0


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
