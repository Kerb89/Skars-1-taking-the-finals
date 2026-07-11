#!/usr/bin/env python3
"""
quiz_history_build.py — Bootstrap dello storico canonico JSONL.

Parsa tutti i quiz_puntata*.html e quiz_puntata*.md in puntate/ ed estrae
le domande nel formato JSONL canonico usato dal nuovo dedup.

Ogni riga del file JSONL è un oggetto JSON:
{
  "puntata": "quiz_puntata13_misto",
  "num": 26,
  "question": "testo integrale della domanda normalizzato",
  "options": ["A", "B", "C", "D"],
  "answer": "testo dell'opzione corretta",
  "answer_idx": 2,
  "cat": "indovinelli"
}

Uso:
    python quiz_history_build.py
        Genera puntate/quiz_corpus.jsonl da tutti i file in puntate/

    python quiz_history_build.py --append <file.md>
        Parsa un singolo .md e appende le sue domande al corpus
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

PUNTATE_DIR = Path("puntate")
CORPUS_PATH = PUNTATE_DIR / "quiz_corpus.jsonl"


def normalize_text(text: str) -> str:
    """Normalizza testo per il confronto: NFKD, lowercase, strip."""
    text = text.replace("\ufeff", "").replace("\r", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip()


# --- Parser per HTML (estrae JSON da const questions = [...]) ----------------

def extract_from_html(html_path: Path) -> list[dict]:
    """Estrae le domande dal JSON inline di un file HTML quiz."""
    text = html_path.read_text(encoding="utf-8", errors="replace")

    # Cerca: const questions = [...]; o const quizData = [...];
    m = re.search(r'const\s+questions\s*=\s*(\[.*?\])\s*;', text, re.DOTALL)
    if not m:
        m = re.search(r'const\s+quizData\s*=\s*(\[.*?\])\s*;', text, re.DOTALL)
    if not m:
        return []

    try:
        questions = json.loads(m.group(1))
    except json.JSONDecodeError:
        raw = m.group(1)
        raw = re.sub(r'//[^\n]*', '', raw)
        try:
            questions = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  WARN: impossibile parsare JSON in {html_path.name}", file=sys.stderr)
            return []

    puntata = html_path.stem
    results = []
    for i, q in enumerate(questions):
        opts = q.get("opts", q.get("options", []))
        ans_raw = q.get("ans", q.get("answer", 0))

        # ans può essere int o lista (domande a doppia risposta)
        if isinstance(ans_raw, list):
            ans_idx = ans_raw[0] if ans_raw else 0
            answer_parts = [opts[idx] for idx in ans_raw if 0 <= idx < len(opts)]
            answer_text = " / ".join(answer_parts)
        else:
            ans_idx = ans_raw
            answer_text = opts[ans_idx] if 0 <= ans_idx < len(opts) else ""

        results.append({
            "puntata": puntata,
            "num": i + 1,
            "question": normalize_text(q.get("q", q.get("question", ""))),
            "options": [normalize_text(o) for o in opts],
            "answer": normalize_text(answer_text),
            "answer_idx": ans_idx,
            "cat": q.get("cat", ""),
        })
    return results


# --- Parser per .md (parse domande + soluzioni) ------------------------------

QUESTION_RE = re.compile(r'^\s*\**(\d{1,3})[\.\)]\**\s+(.+)$')
OPTION_RE = re.compile(r'^\s*[-*]?\s*\**([A-Da-d])[\.\)]\**\s+(.+)$')
SOL_HEADER_RE = re.compile(r'^\s*#{1,6}\s+.*[Ss]oluzion', re.IGNORECASE)
SOL_LINE_RE = re.compile(
    r'^\s*[-*]?\s*\**(\d{1,3})[\.\):]?\**\s*[\-\u2014:>]?\s*\**([A-D])\b',
    re.IGNORECASE
)
ANY_HEADER_RE = re.compile(r'^\s*#{1,6}\s+')


def extract_from_md(md_path: Path) -> list[dict]:
    """Estrae le domande da un file .md quiz."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Trova sezione soluzioni
    sol_start = None
    for i, line in enumerate(lines):
        if SOL_HEADER_RE.match(line):
            sol_start = i + 1
            break

    if sol_start is None:
        return []

    # Parse domande
    questions = {}
    cur_num = None
    cur_prompt = ""
    cur_options = {}

    for line in lines[:sol_start - 1]:
        line = line.rstrip()
        if not line:
            continue

        mo = OPTION_RE.match(line)
        mq = QUESTION_RE.match(line)

        if mo and cur_num is not None:
            cur_options[mo.group(1).upper()] = mo.group(2).strip()
            continue

        if mq:
            if cur_num is not None:
                questions[cur_num] = {"prompt": cur_prompt, "options": cur_options}
            cur_num = int(mq.group(1))
            cur_prompt = mq.group(2).strip()
            cur_options = {}
            continue

        if cur_num is not None and not line.lstrip().startswith(">") and not cur_options:
            cur_prompt += " " + line.strip()

    if cur_num is not None:
        questions[cur_num] = {"prompt": cur_prompt, "options": cur_options}

    # Parse soluzioni
    solutions = {}
    for line in lines[sol_start:]:
        if ANY_HEADER_RE.match(line) and not SOL_HEADER_RE.match(line):
            break
        m = SOL_LINE_RE.match(line)
        if m:
            solutions[int(m.group(1))] = m.group(2).upper()

    # Combina
    puntata = md_path.stem
    results = []
    for num in sorted(questions.keys()):
        q = questions[num]
        letter = solutions.get(num, "")
        opts = [q["options"].get(l, "") for l in "ABCD"]
        ans_idx = "ABCD".index(letter) if letter in "ABCD" else -1
        answer_text = opts[ans_idx] if 0 <= ans_idx < 4 else ""

        results.append({
            "puntata": puntata,
            "num": num,
            "question": normalize_text(q["prompt"]),
            "options": [normalize_text(o) for o in opts],
            "answer": normalize_text(answer_text),
            "answer_idx": ans_idx,
            "cat": "",
        })
    return results


# --- Comandi principali -------------------------------------------------------

def build_full():
    """Ricostruisce l'intero corpus da tutti i file in puntate/."""
    all_questions = []
    html_files = sorted(PUNTATE_DIR.glob("quiz_puntata*.html"))
    md_files = sorted(PUNTATE_DIR.glob("quiz_puntata*.md"))

    processed_stems = set()

    for f in html_files:
        print(f"  HTML: {f.name}", end="")
        qs = extract_from_html(f)
        print(f" -> {len(qs)} domande")
        all_questions.extend(qs)
        processed_stems.add(f.stem)

    for f in md_files:
        if f.stem in processed_stems:
            continue
        if "test" in f.stem.lower():
            continue
        print(f"  MD:   {f.name}", end="")
        qs = extract_from_md(f)
        print(f" -> {len(qs)} domande")
        all_questions.extend(qs)
        processed_stems.add(f.stem)

    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CORPUS_PATH.open("w", encoding="utf-8") as fh:
        for q in all_questions:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"\nOK: {len(all_questions)} domande da {len(processed_stems)} puntate -> {CORPUS_PATH}")
    return 0


def append_file(path_str: str):
    """Appende le domande di un singolo file al corpus esistente."""
    p = Path(path_str)
    if not p.is_file():
        print(f"ERRORE: file non trovato: {path_str}", file=sys.stderr)
        return 2

    if p.suffix == ".html":
        qs = extract_from_html(p)
    elif p.suffix == ".md":
        qs = extract_from_md(p)
    else:
        print(f"ERRORE: formato non supportato: {p.suffix}", file=sys.stderr)
        return 2

    if not qs:
        print(f"WARN: nessuna domanda estratta da {p.name}", file=sys.stderr)
        return 1

    # Rimuovi voci duplicate (stessa puntata) prima di appendere
    existing = []
    if CORPUS_PATH.exists():
        with CORPUS_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    if entry.get("puntata") != p.stem:
                        existing.append(line)

    with CORPUS_PATH.open("w", encoding="utf-8") as fh:
        for line in existing:
            fh.write(line + "\n")
        for q in qs:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"OK: {len(qs)} domande da {p.name} -> {CORPUS_PATH} (totale: {len(existing) + len(qs)})")
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--append":
        if len(sys.argv) < 3:
            print("Uso: python quiz_history_build.py --append <file>", file=sys.stderr)
            return 2
        return append_file(sys.argv[2])

    # Default: build completo
    return build_full()


if __name__ == "__main__":
    sys.exit(main())
