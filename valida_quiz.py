#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
valida_quiz.py — Validatore statico del SORGENTE .md di una puntata
(livello 0, prima della conversione in HTML).

Copre le regole di quizzone-01-domande.md, quizzone-02-fonti.md e
quizzone-04-spiegazioni.md che riguardano il testo del .md e che
validate_quiz_html.py NON può controllare (quello valida il JSON/HTML
finale, generato solo dopo approvazione — a questo stadio non esiste
ancora). Non sostituisce quiz_dedup.py (anti-duplicato): i due si
usano insieme, in questo ordine, dall'hook "Validazione unica
post-creazione quiz":

    python valida_quiz.py <file.md>
    python quiz_dedup.py check <file.md>

USO:
    python valida_quiz.py puntate/quiz_puntataN_tema.md [--num-domande 45]

EXIT CODE: 0 = PASS, 1 = FAIL (errori bloccanti), 2 = errore di esecuzione.

CHECK IMPLEMENTATI:
  [STRUTTURA]
   1. Header "# Quizzone — ... — <data>" presente
   2. Conteggio domande == attese (default 45)
   3. Numerazione 1..N senza buchi né duplicati
   4. Ogni domanda ha esattamente 4 opzioni A)-D), non vuote
   5. Ogni domanda ha una soluzione con 1 o 2 lettere valide (mai 0, mai 3+)
  [DISTRIBUZIONE — stessa soglia di validate_quiz_html.py, gate anticipato]
   6. Ogni lettera A-D >= 8 occorrenze su N domande
   7. Max 2 risposte consecutive con la stessa lettera
  [SPIEGAZIONI — quizzone-04]
   8. Ogni domanda ha una riga "> Spiegazione: ..." dopo la soluzione
   9. Spiegazione <= 60 parole
  10. Spiegazione 2-3 frasi (WARN, euristico)
  [FONTI — quizzone-02]
  11. Sezione "## Fonti" presente e non vuota
  [STILE — quizzone-01]
  12. Niente parentesi tonde nel testo domanda/opzioni
  13. Niente "tutte le precedenti" / "nessuna delle precedenti"

LIMITE NOTO: la distribuzione per CATEGORIA (18 categorie, min 2 domande
ciascuna) non è verificabile qui — il .md non porta un tag categoria per
domanda (le categorie emergono dalle manche o vengono assegnate in fase
HTML). Quel vincolo resta affidato alla pianificazione della griglia in
Fase 1 del workflow, non a un check automatico.

NOTA: i selettori/soglie qui non sono configurabili via JSON esterno
(a differenza di validate_quiz_html.py) perché operano su testo Markdown
libero, non su DOM/JSON strutturato — non c'è un "selettore" da tarare.
Se un check sembra sbagliato: segnalare e fermarsi, non disattivarlo.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

QUESTION_RE = re.compile(r"^\s*\**(\d{1,3})[\.\)]\**\s+(.*)$")
OPTION_RE = re.compile(r"^\s*[-*]?\s*\**([A-Da-d])[\.\)]\**\s+(.*)$")
ANY_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.*)$")
HEADER_MAIN_RE = re.compile(r"^\s*#\s+Quizzone\s+.+\s+\d")
SOL_LINE_RE = re.compile(
    r"^\s*[-*]?\s*\**(\d{1,3})[\.\):]?\**\s*[-—:>]?\s*\**([A-D])\b\**\s*(.*)",
    re.IGNORECASE,
)
EXTRA_LETTER_RE = re.compile(r"^[,e/+\s]+([A-D])\b\s*(.*)$", re.IGNORECASE)
SPIEGAZIONE_RE = re.compile(r"^\s*>\s*Spiegazione:\s*(.*)$", re.IGNORECASE)
FONTI_HEADER_RE = re.compile(r"^\s*#{1,6}\s+Fonti\s*$", re.IGNORECASE)
SOLUZIONI_HEADER_RE = re.compile(r"^\s*#{1,6}\s+Soluzioni\s*$", re.IGNORECASE)
BANNED_OPTIONS = re.compile(
    r"tutte le (precedenti|risposte)|nessuna delle precedenti", re.IGNORECASE
)
SENTENCE_SPLIT_RE = re.compile(r"[.!?]+(?:\s|$)")


class Report:
    def __init__(self):
        self.errori = []
        self.warning = []
        self.ok = []

    def err(self, check, msg):
        self.errori.append(f"[{check}] {msg}")

    def warn(self, check, msg):
        self.warning.append(f"[{check}] {msg}")

    def passed(self, check, msg=""):
        self.ok.append(f"[{check}] {msg}".rstrip())

    def stampa(self):
        print("=" * 70)
        for r in self.ok:
            print(f"  OK    {r}")
        for w in self.warning:
            print(f"  WARN  {w}")
        for e in self.errori:
            print(f"  FAIL  {e}")
        print("=" * 70)
        tot = len(self.ok) + len(self.warning) + len(self.errori)
        print(f"Totale check: {tot} | OK: {len(self.ok)} | "
              f"WARN: {len(self.warning)} | FAIL: {len(self.errori)}")
        print("ESITO: " + ("PASS" if not self.errori else "FAIL"))


@dataclass
class Question:
    num: int
    prompt: str = ""
    options: dict = field(default_factory=dict)
    option_lines: list = field(default_factory=list)
    letters: set = field(default_factory=set)
    spiegazione: str = ""
    has_spiegazione_line: bool = False


def find_solutions_start(lines):
    for i, line in enumerate(lines):
        if SOLUZIONI_HEADER_RE.match(line):
            return i + 1
    return None


def find_fonti_start(lines):
    for i, line in enumerate(lines):
        if FONTI_HEADER_RE.match(line):
            return i + 1
    return None


def parse_questions(lines, sol_start):
    """Parsa le domande 1..sol_start-1 (esclusi header di sezione/manche)."""
    questions = {}
    cur = None
    for raw in lines[: sol_start - 1 if sol_start else len(lines)]:
        line = raw.rstrip()
        if not line:
            continue
        if ANY_HEADER_RE.match(line):
            continue
        mo = OPTION_RE.match(line)
        mq = QUESTION_RE.match(line)
        if mo and not (mq and not mo.group(1).isalpha()):
            if cur is not None:
                letter = mo.group(1).upper()
                cur.options[letter] = mo.group(2).strip()
                cur.option_lines.append(mo.group(2).strip())
            continue
        if mq:
            cur = Question(num=int(mq.group(1)), prompt=mq.group(2).strip())
            questions[cur.num] = cur
            continue
        if cur is not None and not cur.options:
            cur.prompt += " " + line.strip()
    return questions


def parse_solutions(lines, sol_start, fonti_start, questions):
    end = fonti_start - 1 if fonti_start else len(lines)
    block = lines[sol_start:end]
    cur_q = None
    for line in block:
        m = SOL_LINE_RE.match(line)
        if m:
            num = int(m.group(1))
            cur_q = questions.get(num)
            if cur_q is None:
                continue
            cur_q.letters.add(m.group(2).upper())
            rest = m.group(3) or ""
            m2 = EXTRA_LETTER_RE.match(rest)
            if m2:
                cur_q.letters.add(m2.group(1).upper())
            continue
        sm = SPIEGAZIONE_RE.match(line)
        if sm and cur_q is not None:
            cur_q.has_spiegazione_line = True
            cur_q.spiegazione = sm.group(1).strip()
            cur_q = None  # una spiegazione per soluzione, non accumulare righe successive


def check_struttura(text, lines, questions, attese, rep):
    if HEADER_MAIN_RE.match(lines[0]) or any(HEADER_MAIN_RE.match(l) for l in lines[:5]):
        rep.passed("HEADER", "riga titolo # Quizzone — ... presente")
    else:
        rep.err("HEADER", "manca la riga titolo '# Quizzone — <tema> — <data>' "
                "nelle prime righe del file")

    nums = sorted(questions.keys())
    if len(nums) != attese:
        rep.err("CONTEGGIO", f"trovate {len(nums)} domande, attese {attese}")
    else:
        rep.passed("CONTEGGIO", f"{attese} domande trovate")

    attesi = list(range(1, attese + 1))
    mancanti = [n for n in attesi if n not in questions]
    duplicati_check = len(nums) != len(set(nums))
    if mancanti:
        rep.err("NUMERAZIONE", f"numeri mancanti nella sequenza 1..{attese}: {mancanti}")
    elif duplicati_check:
        rep.err("NUMERAZIONE", "numeri di domanda duplicati rilevati")
    else:
        rep.passed("NUMERAZIONE", "sequenza 1..N senza buchi né duplicati")


def check_opzioni(questions, rep):
    problemi = []
    for i, q in sorted(questions.items()):
        lettere = set(q.options.keys())
        if lettere != {"A", "B", "C", "D"} or any(
            not q.options.get(l, "").strip() for l in "ABCD"
        ):
            problemi.append(i)
    if problemi:
        rep.err("OPZIONI", f"domande senza esattamente 4 opzioni A-D non vuote: {problemi}")
    else:
        rep.passed("OPZIONI", "tutte le domande hanno 4 opzioni A-D non vuote")


def check_soluzioni(questions, rep):
    zero = [i for i, q in sorted(questions.items()) if len(q.letters) == 0]
    troppe = [i for i, q in sorted(questions.items()) if len(q.letters) >= 3]
    invalide = [
        i for i, q in sorted(questions.items())
        if any(l not in "ABCD" for l in q.letters)
    ]
    if zero:
        rep.err("SOLUZIONI", f"domande senza risposta corretta nella sezione Soluzioni: {zero}")
    if troppe:
        rep.err("SOLUZIONI", f"domande con 3+ risposte corrette (vietato, max 2): {troppe}")
    if invalide:
        rep.err("SOLUZIONI", f"domande con lettera soluzione fuori A-D: {invalide}")
    if not zero and not troppe and not invalide:
        rep.passed("SOLUZIONI", "ogni domanda ha 1 o 2 risposte corrette valide (A-D)")


def check_distribuzione(questions, attese, rep):
    seq = []
    for i in range(1, attese + 1):
        q = questions.get(i)
        if not q or not q.letters:
            continue
        # per doppia risposta conta la prima lettera in ordine alfabetico (deterministico)
        seq.append(sorted(q.letters)[0])

    conteggio = {l: seq.count(l) for l in "ABCD"}
    sotto_soglia = [f"{l}={c}" for l, c in conteggio.items() if c < 8]
    if sotto_soglia:
        rep.err("DISTRIBUZIONE", f"lettere sotto il minimo di 8/{attese}: {', '.join(sotto_soglia)} "
                f"(A={conteggio['A']} B={conteggio['B']} C={conteggio['C']} D={conteggio['D']})")
    else:
        rep.passed("DISTRIBUZIONE",
                   f"A={conteggio['A']} B={conteggio['B']} C={conteggio['C']} D={conteggio['D']}")

    consecutive = 1
    violazione = False
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            consecutive += 1
            if consecutive > 2:
                rep.err("CONSECUTIVE", f"3+ risposte consecutive uguali ({seq[i]}) "
                        f"intorno alla posizione {i + 1} nella sequenza")
                violazione = True
                break
        else:
            consecutive = 1
    if not violazione:
        rep.passed("CONSECUTIVE", "max 2 consecutive con la stessa lettera")


def check_spiegazioni(questions, attese, rep):
    mancanti = [i for i in range(1, attese + 1)
                if not questions.get(i) or not questions[i].has_spiegazione_line
                or not questions[i].spiegazione.strip()]
    if mancanti:
        rep.err("SPIEGAZIONI", f"domande senza riga '> Spiegazione:' non vuota: {mancanti}")
    else:
        rep.passed("SPIEGAZIONI", f"{attese} spiegazioni presenti")

    troppo_lunghe = []
    frasi_sospette = []
    for i, q in sorted(questions.items()):
        if not q.spiegazione:
            continue
        n_parole = len(q.spiegazione.split())
        if n_parole > 60:
            troppo_lunghe.append((i, n_parole))
        n_frasi = len([s for s in SENTENCE_SPLIT_RE.split(q.spiegazione) if s.strip()])
        if not (2 <= n_frasi <= 3):
            frasi_sospette.append((i, n_frasi))

    if troppo_lunghe:
        rep.err("SPIEGAZIONI_LUNGHEZZA",
                f"spiegazioni oltre 60 parole: {troppo_lunghe}")
    else:
        rep.passed("SPIEGAZIONI_LUNGHEZZA", "tutte le spiegazioni <= 60 parole")

    if frasi_sospette:
        rep.warn("SPIEGAZIONI_FRASI",
                 f"spiegazioni con conteggio frasi fuori 2-3 (euristico, verificare a mano): "
                 f"{frasi_sospette[:15]}")
    else:
        rep.passed("SPIEGAZIONI_FRASI", "tutte le spiegazioni hanno 2-3 frasi")


def check_fonti(lines, fonti_start, rep):
    if fonti_start is None:
        rep.err("FONTI", "sezione '## Fonti' assente")
        return
    righe = [l.strip() for l in lines[fonti_start:] if l.strip()]
    con_url = [l for l in righe if "http://" in l or "https://" in l]
    if not con_url:
        rep.err("FONTI", "sezione Fonti presente ma senza nessun URL: "
                "segnale che la verifica non è stata fatta")
    else:
        rep.passed("FONTI", f"{len(con_url)} righe con URL nella sezione Fonti")


def check_stile(questions, rep):
    parentesi = []
    banned = []
    for i, q in sorted(questions.items()):
        testi = [q.prompt] + list(q.options.values())
        if any("(" in t or ")" in t for t in testi):
            parentesi.append(i)
        if any(BANNED_OPTIONS.search(t) for t in q.options.values()):
            banned.append(i)
    if parentesi:
        rep.err("PARENTESI", f"domande con parentesi tonde nel testo/opzioni (vietate "
                f"da quizzone-01): {parentesi}")
    else:
        rep.passed("PARENTESI", "nessuna parentesi tonda nel testo delle domande/opzioni")

    if banned:
        rep.err("OPZIONI_SCHERZO", f"domande con 'tutte/nessuna delle precedenti' "
                f"come opzione (vietato): {banned}")
    else:
        rep.passed("OPZIONI_SCHERZO", "nessuna opzione 'tutte/nessuna delle precedenti'")


def main():
    ap = argparse.ArgumentParser(description="Validatore statico del sorgente .md di una puntata")
    ap.add_argument("md", help="Path del file .md della puntata")
    ap.add_argument("--num-domande", type=int, default=45,
                    help="Numero di domande attese (default 45; puntate 1-12 storiche: 35)")
    args = ap.parse_args()

    path = Path(args.md)
    if not path.is_file():
        print(f"ERRORE: file non trovato: {path}")
        sys.exit(2)

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    sol_start = find_solutions_start(lines)
    if sol_start is None:
        print("ERRORE: sezione '## Soluzioni' non trovata — impossibile validare")
        sys.exit(2)
    fonti_start = find_fonti_start(lines)

    questions = parse_questions(lines, sol_start)
    parse_solutions(lines, sol_start, fonti_start, questions)

    rep = Report()
    print(f"\nValidazione sorgente: {path.name}\n")

    check_struttura(text, lines, questions, args.num_domande, rep)
    check_opzioni(questions, rep)
    check_soluzioni(questions, rep)
    check_distribuzione(questions, args.num_domande, rep)
    check_spiegazioni(questions, args.num_domande, rep)
    check_fonti(lines, fonti_start, rep)
    check_stile(questions, rep)

    rep.stampa()
    sys.exit(0 if not rep.errori else 1)


if __name__ == "__main__":
    main()
