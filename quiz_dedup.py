#!/usr/bin/env python3
"""
quiz_dedup.py — Controllo anti-duplicati per il Quizzone (v3, corpus-based).

Uso:
    python quiz_dedup.py index
        Rigenera puntate/answers_index.txt (indice leggibile per l'umano)
        dai file quiz_history*.md. NON usato dal check.

    python quiz_dedup.py check <nuovo_quiz.md>
        Confronto testo-contro-testo sul corpus JSONL canonico:
        1) Domanda vs domande storiche: similarita fuzzy sul testo integrale.
           Soglia WARN >= 70, soglia ERR >= 85.
        2) Risposta corretta vs risposte storiche: match esatto normalizzato.
        3) Leakage interno e doppi interni (invariati da v2).

        Se il corpus (puntate/quiz_corpus.jsonl) non esiste, lo genera
        automaticamente con quiz_history_build.py.

    python quiz_dedup.py rebuild
        Rigenera il corpus JSONL (equivale a: python quiz_history_build.py).

Design v3:
- Il check lavora sul SORGENTE (testo domanda integrale), non su parafrasi.
- Usa difflib.SequenceMatcher come fallback (stdlib, zero dipendenze).
  Se rapidfuzz e' installato, usa token_set_ratio (piu' robusto).
- La lettera della risposta (A/B/C/D) non e' MAI parte dell'identita'.
- L'indice answers_index.txt resta per l'umano e per il workflow
  pre-generazione (blacklist in contesto). Il check non lo legge.
"""

import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

# --- Configurazione -----------------------------------------------------------

CORPUS_PATH = Path("puntate/quiz_corpus.jsonl")
INDEX_PATH = Path("puntate/answers_index.txt")

HISTORY_GLOBS = ["quiz_history*.md"]
SEARCH_DIRS = [Path("."), Path("puntate"), Path("storico")]

# Soglie similarita domanda (0-100)
WARN_THRESHOLD = 70   # segnala come warning
ERR_THRESHOLD = 85    # segnala come errore (quasi certamente duplicato)

# Soglie per risposte (confronto piu stretto)
ANSWER_WARN_THRESHOLD = 80
ANSWER_ERR_THRESHOLD = 95

MIN_QUESTIONS = 5
MIN_SOLVED_RATIO = 0.7

STOPWORDS = {
    "della", "delle", "dello", "degli", "nella", "nelle", "nello", "negli",
    "sulla", "sulle", "sullo", "sugli", "dalla", "dalle", "dallo", "dagli",
    "alla", "alle", "allo", "agli", "come", "quale", "quali", "quando",
    "dove", "perche", "cosa", "chi", "che", "con", "per", "tra", "fra",
    "una", "uno", "un", "il", "lo", "la", "le", "gli", "i", "di", "da",
    "in", "su", "a", "e", "o", "non", "piu", "meno", "sono", "era",
    "anno", "anni", "mondo", "grande",
    "spiegazione", "soluzione", "soluzioni", "seguenti", "corretta",
    "the", "of", "and", "audio", "testo", "esatto",
}

# --- Utilita ------------------------------------------------------------------

def normalize(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.casefold().strip()


def normalize_for_compare(text: str) -> str:
    """Normalizzazione aggressiva per similarita: solo alfanumerici + spazi."""
    t = normalize(text)
    # Normalizza numeri ordinali scritti in lettere
    replacements = [
        ("settimo", "7"), ("sette", "7"),
        ("decimo", "10"), ("dieci", "10"),
        ("primo", "1"), ("secondo", "2"), ("terzo", "3"),
        ("quarto", "4"), ("quinto", "5"), ("sesto", "6"),
        ("ottavo", "8"), ("nono", "9"),
    ]
    for old, new in replacements:
        t = t.replace(old, new)
    # Mantieni solo alfanumerici e spazi
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def similarity(a: str, b: str) -> float:
    """Similarita 0-100 tra due stringhe. Usa rapidfuzz se disponibile."""
    na = normalize_for_compare(a)
    nb = normalize_for_compare(b)
    if not na or not nb:
        return 0.0

    try:
        from rapidfuzz.fuzz import token_set_ratio
        return token_set_ratio(na, nb)
    except ImportError:
        pass

    # Fallback: SequenceMatcher su token set (ordine-invariante)
    ta = set(na.split())
    tb = set(nb.split())
    sa = " ".join(sorted(ta))
    sb = " ".join(sorted(tb))
    return SequenceMatcher(None, sa, sb).ratio() * 100


def answer_match(a: str, b: str) -> float:
    """Match tra risposte corrette."""
    na = normalize_for_compare(a)
    nb = normalize_for_compare(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 100.0

    try:
        from rapidfuzz.fuzz import token_set_ratio
        return token_set_ratio(na, nb)
    except ImportError:
        pass

    return SequenceMatcher(None, na, nb).ratio() * 100


def tokens(text: str) -> set[str]:
    """Token set per overlap legacy."""
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


# --- Corpus -------------------------------------------------------------------

def load_corpus() -> list[dict]:
    """Carica il corpus JSONL. Se non esiste, lo genera."""
    if not CORPUS_PATH.exists():
        print("Corpus non trovato, lo genero...", file=sys.stderr)
        result = subprocess.run(
            [sys.executable, "quiz_history_build.py"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"ERRORE generazione corpus:\n{result.stderr}", file=sys.stderr)
            return []
        print(result.stdout, file=sys.stderr)

    if not CORPUS_PATH.exists():
        return []

    entries = []
    with CORPUS_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


# --- Parse quiz ---------------------------------------------------------------

QUESTION_RE = re.compile(r"^\s*\**(\d{1,3})[\.\)]\**\s+(.*)$")
OPTION_RE = re.compile(r"^\s*[-*]?\s*\**([A-Da-d])[\.\)]\**\s+(.*)$")
ANY_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.*)$")
SOL_LINE_RE = re.compile(
    r"^\s*[-*]?\s*\**(\d{1,3})[\.\):]?\**\s*[-\u2014:>]?\s*\**([A-D])\b\**\s*(.*)",
    re.IGNORECASE
)
EXTRA_LETTER_RE = re.compile(r"^[,e/+\s]+([A-D])\b\s*(.*)$", re.IGNORECASE)


@dataclass
class Question:
    num: int
    prompt: str = ""
    expl: str = ""
    options: dict[str, str] = field(default_factory=dict)
    letters: set[str] = field(default_factory=set)
    sol_text: str = ""
    answer_text: str = ""


def _is_solutions_header(line: str) -> bool:
    m = ANY_HEADER_RE.match(line)
    if not m:
        return False
    h = normalize(m.group(1))
    return "soluzion" in h or "rispost" in h


def parse_quiz(text: str) -> tuple[list[Question], bool]:
    lines = text.splitlines()

    sol_start = None
    for i, line in enumerate(lines):
        if _is_solutions_header(line):
            sol_start = i + 1
            break

    if sol_start is None:
        return [], False

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
            cur.prompt += " " + line.strip()

    for line in lines[sol_start:]:
        if ANY_HEADER_RE.match(line) and not _is_solutions_header(line):
            break
        m = SOL_LINE_RE.match(line)
        if not m:
            continue
        num = int(m.group(1))
        if num not in questions:
            continue
        q = questions[num]
        q.letters.add(m.group(2).upper())
        rest = m.group(3) or ""
        m2 = EXTRA_LETTER_RE.match(rest)
        if m2:
            q.letters.add(m2.group(1).upper())
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

    for q in qs:
        ans_texts = [q.options[l] for l in q.letters if l in q.options]
        q.answer_text = " / ".join(ans_texts) if ans_texts else q.sol_text

    return solved, True


# --- cmd_index (per l'umano) --------------------------------------------------

LINE_RE = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)$")
HEADER_RE = re.compile(r"^###\s+(.*)$")


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
        print("ERRORE: nessun file quiz_history*.md trovato", file=sys.stderr)
        return 2
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as fh:
        fh.write("# Indice risposte usate - GENERATO, non editare a mano\n")
        fh.write("# Queste voci sono VIETATE come risposta corretta di nuove domande\n")
        for punt, num, text in entries:
            fh.write(f"{normalize(text)}  [{punt} D{num}]\n")
    print(f"OK: indicizzate {len(entries)} voci da {len(find_history_files())} file -> {INDEX_PATH}")
    return 0


# --- cmd_check (v3) -----------------------------------------------------------

def cmd_check(quiz_path: str) -> int:
    p = Path(quiz_path)
    if not p.is_file():
        print(f"ERRORE: file non trovato: {quiz_path}", file=sys.stderr)
        return 2
    quiz_text = p.read_text(encoding="utf-8", errors="replace")

    questions, parse_ok = parse_quiz(quiz_text)
    if not parse_ok:
        print("ERRORE: impossibile parsare il quiz (sezione soluzioni assente?)", file=sys.stderr)
        return 2

    # Carica corpus (escludendo la puntata corrente)
    corpus = load_corpus()
    quiz_stem = p.stem
    corpus = [e for e in corpus if e.get("puntata") != quiz_stem]

    if not corpus:
        print("WARN: corpus vuoto. Esegui: python quiz_history_build.py", file=sys.stderr)

    errs: list[str] = []
    warns: list[str] = []

    # 1) Confronto domanda vs corpus: similarita fuzzy
    for q in questions:
        for entry in corpus:
            sim = similarity(q.prompt, entry["question"])
            if sim >= ERR_THRESHOLD:
                errs.append(
                    f"D{q.num}: DUPLICATO (sim={sim:.0f}%) con "
                    f"[{entry['puntata']} D{entry['num']}] "
                    f"\"{entry['question'][:80]}...\""
                )
            elif sim >= WARN_THRESHOLD:
                warns.append(
                    f"D{q.num}: SIMILE (sim={sim:.0f}%) a "
                    f"[{entry['puntata']} D{entry['num']}] "
                    f"\"{entry['question'][:80]}...\""
                )

    # 2) Risposta corretta vs risposte storiche (con correlazione domanda)
    for q in questions:
        if not q.answer_text:
            continue
        for entry in corpus:
            if not entry.get("answer"):
                continue
            am = answer_match(q.answer_text, entry["answer"])
            if am >= ANSWER_ERR_THRESHOLD:
                q_sim = similarity(q.prompt, entry["question"])
                if q_sim >= 40:
                    errs.append(
                        f"D{q.num}: stessa risposta \"{q.answer_text[:50]}\" "
                        f"(match={am:.0f}%) + domanda correlata (sim={q_sim:.0f}%) "
                        f"in [{entry['puntata']} D{entry['num']}]"
                    )

    # 3) Leakage interno
    for qi in questions:
        if not qi.answer_text or len(qi.answer_text) < 5:
            continue
        ans_norm = normalize(qi.answer_text)
        for qj in questions:
            if qi.num == qj.num:
                continue
            prompt_norm = normalize(qj.prompt + " " + qj.expl)
            if ans_norm in prompt_norm:
                errs.append(
                    f"D{qj.num}: il testo contiene la risposta di "
                    f"D{qi.num} (\"{qi.answer_text[:40]}\")"
                )

    # 4) Stessa risposta in due domande del quiz
    for qi, qj in combinations(questions, 2):
        if not qi.answer_text or not qj.answer_text:
            continue
        am = answer_match(qi.answer_text, qj.answer_text)
        if am >= 90:
            warns.append(
                f"D{qi.num}/D{qj.num}: stessa risposta corretta "
                f"\"{qi.answer_text[:40]}\" - ok se i fatti sono diversi"
            )

    # Deduplica
    errs = list(dict.fromkeys(errs))
    warns = list(dict.fromkeys(warns))

    if not errs and not warns:
        print(f"PULITO: {len(questions)} domande, nessun problema rilevato "
              f"(corpus: {len(corpus)} domande storiche).")
        return 0

    if errs:
        print(f"ERRORI ({len(errs)}) — da sistemare:")
        for e in errs[:50]:
            print(f"  x {e}")
        if len(errs) > 50:
            print(f"  ... e altri {len(errs) - 50}")
    if warns:
        print(f"\nAVVISI ({len(warns)}) — giudica tu:")
        for w in warns[:30]:
            print(f"  ~ {w}")
        if len(warns) > 30:
            print(f"  ... e altri {len(warns) - 30}")

    return 1 if errs else 0


# --- cmd_rebuild --------------------------------------------------------------

def cmd_rebuild() -> int:
    result = subprocess.run(
        [sys.executable, "quiz_history_build.py"],
        capture_output=False
    )
    return result.returncode


# --- cmd_precheck (risposte candidate vs indice) -----------------------------

def cmd_precheck(answers_file: str) -> int:
    """Confronta risposte candidate con l'indice PRIMA della scrittura del quiz.

    Input: file di testo con una risposta candidata per riga (formato: "N. risposta")
    Output: lista di conflitti trovati. Exit 0 = nessun conflitto, 1 = conflitti.
    """
    if not INDEX_PATH.exists():
        print("ERRORE: answers_index.txt non trovato. Esegui 'python quiz_dedup.py index' prima.", file=sys.stderr)
        return 2

    # Carica indice
    index_entries = []
    with INDEX_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # formato: "argomento (risposta) → lettera  [sorgente]"
            # Estrai la parte prima di → come entry completa
            if "\u2192" in line:
                answer_part = line.split("\u2192")[0].strip()
            elif " [" in line:
                answer_part = line.split(" [")[0].strip()
            else:
                answer_part = line
            # Estrai anche il contenuto tra parentesi (è la risposta vera)
            import re
            paren_match = re.search(r'\(([^)]+)\)', answer_part)
            if paren_match:
                # Aggiungi sia l'entry completa sia la risposta tra parentesi
                index_entries.append(answer_part)
                index_entries.append(paren_match.group(1))
            else:
                index_entries.append(answer_part)

    # Carica risposte candidate
    candidates = []
    with open(answers_file, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # formato atteso: "N. risposta" o solo "risposta"
            if "." in line[:4]:
                parts = line.split(".", 1)
                num = parts[0].strip()
                answer = parts[1].strip()
            else:
                num = "?"
                answer = line
            candidates.append((num, answer))

    # Confronta
    conflicts = []
    for num, candidate in candidates:
        cand_norm = normalize(candidate)
        for idx_entry in index_entries:
            # Match esatto o quasi (answer_match restituisce 0-100)
            score = answer_match(cand_norm, idx_entry)
            # Anche check contenimento: se la candidata è contenuta nell'entry o viceversa
            idx_norm = normalize(idx_entry)
            contained = False
            if len(cand_norm) > 3 and len(idx_norm) > 3:
                contained = (cand_norm in idx_norm or idx_norm in cand_norm)
            if score >= 75 or contained:
                conflicts.append((num, candidate, idx_entry, max(score, 100.0 if contained else 0)))
                break  # un conflitto per candidata basta

    if conflicts:
        print(f"CONFLITTI ({len(conflicts)}) \u2014 risposte gi\u00e0 usate:\n")
        for num, cand, idx, score in conflicts:
            print(f"  x D{num}: \"{cand}\" \u2248 \"{idx}\" (match={score:.0f}%)")
        print(f"\n{len(conflicts)} risposte da cambiare su {len(candidates)} candidate.")
        return 1
    else:
        print(f"OK: tutte le {len(candidates)} risposte candidate sono nuove.")
        return 0


# --- main ---------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"index", "check", "rebuild", "precheck"}:
        print("Uso: python quiz_dedup.py {index|check|rebuild|precheck} [file]")
        print("  index    - rigenera answers_index.txt (indice leggibile)")
        print("  check    - confronto fuzzy sul corpus JSONL")
        print("  rebuild  - rigenera il corpus JSONL da tutti i quiz")
        print("  precheck - verifica risposte candidate vs indice (pre-write)")
        return 2
    if sys.argv[1] == "index":
        return cmd_index()
    if sys.argv[1] == "rebuild":
        return cmd_rebuild()
    if sys.argv[1] == "precheck":
        if len(sys.argv) < 3:
            print("Uso: python quiz_dedup.py precheck <risposte_candidate.txt>", file=sys.stderr)
            return 2
        return cmd_precheck(sys.argv[2])
    if len(sys.argv) < 3:
        print("Uso: python quiz_dedup.py check <nuovo_quiz.md>", file=sys.stderr)
        return 2
    return cmd_check(sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
