#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
valida_quiz.py — controllo meccanico di un file quiz .md del quizzone.

Cosa controlla (deterministico, nessun LLM coinvolto):

1. Parentesi '(' o ')' nel testo di domande e opzioni        -> ERRORE
2. Anno presente nella risposta corretta che ricompare        -> ERRORE
   anche nel testo della domanda (il bug "risposta-nell'anno")
3. Parola chiave significativa della risposta corretta che     -> WARNING
   ricompare nel testo della domanda (risposta anticipata)
4. Uniformita' strutturale delle 4 opzioni (lunghezza/incisi)  -> WARNING
5. Distribuzione A/B/C/D: min 6 per lettera, max 2 consecutive -> ERRORE/WARNING

Uso:
    python3 valida_quiz.py quiz_puntata1_misto.md

Exit code: 0 se nessun ERRORE, 1 se almeno un ERRORE (utile come step di build).
"""

import re
import sys
import unicodedata
from collections import Counter

# --- stopword italiane: token da ignorare nel confronto domanda<->risposta ---
STOPWORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "del", "dello",
    "della", "dei", "degli", "delle", "di", "da", "in", "con", "su", "per",
    "tra", "fra", "a", "e", "o", "ed", "ad", "al", "allo", "alla", "ai",
    "agli", "alle", "dal", "dalla", "che", "chi", "cui", "non", "ne", "si",
    "se", "ma", "come", "dove", "quando", "quale", "quali", "quanto", "qual",
    "questo", "questa", "questi", "queste", "quel", "quella", "suo", "sua",
    "loro", "nel", "nella", "nei", "negli", "nelle", "sono", "essere", "stato",
    "fu", "era", "anche", "piu", "meno", "detto", "detta", "anno", "evento",
    "citta", "paese", "film", "opera", "quadro", "canzone", "primo", "prima",
}

YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
PAREN_RE = re.compile(r"[()]")
QNUM_RE = re.compile(r"^\*\*\s*(\d+)\s*\.\s*\*\*\s*(.*)$")   # **1.** testo
OPT_RE = re.compile(r"^([ABCD])\)\s*(.*)$")                  # A) testo
SOL_RE = re.compile(r"^\s*(\d+)\s*\.\s*(.+)$")               # 1. C   /  2. A e D


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def tokenize(s: str):
    s = strip_accents(s.lower())
    toks = re.findall(r"[a-z0-9]+", s)
    return [t for t in toks if len(t) >= 4 and t not in STOPWORDS]


def parse_quiz(text: str):
    """Ritorna (questions, solutions).
    questions: dict num -> {'q': str, 'opts': {'A':..,'B':..,'C':..,'D':..}}
    solutions: dict num -> set di lettere corrette ({'C'} oppure {'A','D'})
    """
    lines = text.splitlines()
    questions, solutions = {}, {}
    in_solutions = False
    cur = None

    for raw in lines:
        line = raw.rstrip()

        # individua l'inizio della sezione soluzioni
        if re.match(r"^#+\s*Soluzioni", line, re.IGNORECASE):
            in_solutions = True
            cur = None
            continue

        if in_solutions:
            m = SOL_RE.match(line)
            if m:
                num = int(m.group(1))
                letters = set(re.findall(r"[ABCD]", m.group(2)))
                if letters:
                    solutions[num] = letters
            continue

        # parsing domande
        mq = QNUM_RE.match(line)
        if mq:
            cur = int(mq.group(1))
            questions[cur] = {"q": mq.group(2).strip(), "opts": {}}
            continue

        mo = OPT_RE.match(line)
        if mo and cur is not None:
            questions[cur]["opts"][mo.group(1)] = mo.group(2).strip()

    return questions, solutions


def check(text: str):
    questions, solutions = parse_quiz(text)
    errors, warnings = [], []
    correct_letters_seq = []  # per distribuzione, in ordine di numero domanda

    for num in sorted(questions):
        q = questions[num]
        qtext = q["q"]
        opts = q["opts"]
        sol = solutions.get(num, set())

        # --- 1. parentesi ---
        if PAREN_RE.search(qtext):
            errors.append(f"D{num}: parentesi nel testo della domanda.")
        for L, otext in opts.items():
            if PAREN_RE.search(otext):
                errors.append(f"D{num} opz {L}: parentesi nell'opzione.")

        # opzioni mancanti / soluzione mancante
        missing = [L for L in "ABCD" if L not in opts]
        if missing:
            errors.append(f"D{num}: opzioni mancanti {missing}.")
        if not sol:
            errors.append(f"D{num}: soluzione assente nella sezione Soluzioni.")
            continue

        correct_texts = [opts[L] for L in sol if L in opts]
        correct_letters_seq.append((num, "".join(sorted(sol))))

        # --- 2. anno della risposta che ricompare nella domanda ---
        q_years = set(YEAR_RE.findall(qtext))
        for ct in correct_texts:
            for y in YEAR_RE.findall(ct):
                if y in q_years:
                    errors.append(
                        f"D{num}: l'anno {y} della risposta corretta "
                        f"compare gia' nel testo della domanda.")

        # --- 3. parola chiave della risposta che ricompare nella domanda ---
        q_tokens = set(tokenize(qtext))
        for ct in correct_texts:
            shared = q_tokens.intersection(tokenize(ct))
            for tok in shared:
                warnings.append(
                    f"D{num}: la parola '{tok}' e' sia nella domanda "
                    f"sia nella risposta corretta (possibile leak).")

        # --- 4. uniformita' opzioni ---
        if not missing:
            lengths = [len(opts[L]) for L in "ABCD"]
            if min(lengths) > 0 and max(lengths) / min(lengths) >= 2.2:
                warnings.append(
                    f"D{num}: opzioni di lunghezza molto diversa "
                    f"({lengths}); rischio che la corretta spicchi.")
            commas = [("," in opts[L]) for L in "ABCD"]
            if 0 < sum(commas) < 4:
                warnings.append(
                    f"D{num}: incisi con virgola presenti solo in alcune "
                    f"opzioni; uniformare struttura.")

    # --- 5. distribuzione lettere corrette ---
    # conta solo domande a singola risposta per il min-per-lettera
    single = [lt for _, lt in correct_letters_seq if len(lt) == 1]
    dist = Counter(single)
    for L in "ABCD":
        if dist.get(L, 0) < 6:
            errors.append(
                f"Distribuzione: lettera {L} usata {dist.get(L,0)} volte "
                f"(minimo 6).")

    # max 2 consecutive uguali (sequenza per numero domanda)
    run, prev = 0, None
    for num, lt in correct_letters_seq:
        if lt == prev:
            run += 1
            if run >= 3:
                warnings.append(
                    f"Distribuzione: >=3 risposte consecutive '{lt}' "
                    f"attorno a D{num}.")
        else:
            run, prev = 1, lt

    return errors, warnings, dict(dist), len(questions)


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 valida_quiz.py <file.md>")
        sys.exit(2)

    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        text = f.read()

    errors, warnings, dist, n = check(text)

    print(f"== Validazione: {path} ==")
    print(f"Domande lette: {n}   Distribuzione corrette singole: {dist}\n")

    if errors:
        print(f"ERRORI ({len(errors)}) — vanno corretti prima di consegnare:")
        for e in errors:
            print("  [X] " + e)
        print()

    if warnings:
        print(f"WARNING ({len(warnings)}) — da controllare a mano:")
        for w in warnings:
            print("  [!] " + w)
        print()

    if not errors and not warnings:
        print("Nessun problema rilevato.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
