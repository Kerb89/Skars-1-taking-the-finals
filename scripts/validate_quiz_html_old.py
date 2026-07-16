"""
Validate quiz HTML integrity.
Checks:
1. File not truncated (</html> present)
2. Questions JSON valid and contains 45 items
3. catBackgrounds JSON valid
4. All <script> blocks have balanced braces
5. Answer distribution (min 8 per letter)
6. No more than 2 consecutive same-letter answers

Usage: python scripts/validate_quiz_html.py <path_to_html>
Exit code 0 = OK, 1 = errors found
"""
import sys, re, json, os, shutil, subprocess, tempfile

# --- anti-regalo: stessi pattern di validate_quiz.py -------------------------
ENRICH_PATTERNS = [
    ("virgola/inciso",   re.compile(r",")),
    ("doppia lettura",   re.compile(
        r"\b(o|od|ovvero|oppure|ossia|cio[eè]|alias|anche dett[oa]"
        r"|dett[oa] anche|not[oa] come|not[oa] anche come)\b",
        re.IGNORECASE)),
    ("virgolette",       re.compile(r"[\"“”«»]")),
    ("inciso con dash",  re.compile(r"\s[–—-]\s")),
]
LEN_RATIO_MAX = 1.5
LEN_DIFF_MAX = 15

OPTION_KEYS = ("opts", "options", "answers", "choices", "opz")


def enrichment_tags(text):
    return {name for name, rx in ENRICH_PATTERNS if rx.search(text)}


def find_options(q):
    """Trova la lista delle 4 opzioni testuali dentro il dict domanda."""
    for k in OPTION_KEYS:
        v = q.get(k)
        if isinstance(v, list) and len(v) == 4 and all(
                isinstance(x, str) for x in v):
            return v
    # fallback: qualunque lista di 4 stringhe
    for v in q.values():
        if isinstance(v, list) and len(v) == 4 and all(
                isinstance(x, str) for x in v):
            return v
    return None


def giveaway_checks_html(idx, options, ans, errors):
    """ans: indice 0-3 della corretta. Ritorna anche eventuali errori."""
    correct = options[ans]
    distr = [o for i, o in enumerate(options) if i != ans]

    distr_tags = set()
    for d in distr:
        distr_tags |= enrichment_tags(d)
    for tag in enrichment_tags(correct) - distr_tags:
        errors.append(
            f"D{idx}: regalo formale — '{tag}' presente solo nella "
            f"risposta corretta e in nessun distrattore.")

    avg_d = sum(len(d) for d in distr) / len(distr)
    if (len(correct) > max(len(d) for d in distr)
            and avg_d > 0
            and (len(correct) / avg_d >= LEN_RATIO_MAX
                 or len(correct) - avg_d >= LEN_DIFF_MAX)):
        errors.append(
            f"D{idx}: regalo formale — corretta di {len(correct)} caratteri "
            f"contro media distrattori di {avg_d:.0f}.")


def check_js_syntax(scripts, errors):
    """Valida ogni blocco <script> con `node --check`. Non-bloccante se
    node non e' installato (stampa solo un avviso)."""
    node = shutil.which("node")
    if not node:
        print("AVVISO: node non trovato, salto la validazione sintattica JS")
        return
    for i, s in enumerate(scripts):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".js", delete=False, encoding="utf-8") as tf:
            tf.write(s)
            tmp = tf.name
        try:
            r = subprocess.run(
                [node, "--check", tmp],
                capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                first = (r.stderr or "errore sconosciuto").strip().splitlines()
                errors.append(f"Script {i}: sintassi JS non valida — "
                              f"{first[-1] if first else '?'}")
            else:
                print(f"   Script {i}: sintassi JS OK (node --check)")
        finally:
            os.unlink(tmp)

def validate(path):
    errors = []

    if not os.path.exists(path):
        print(f"ERRORE: File non trovato: {path}")
        return 1

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"File: {path}")
    print(f"Size: {size_mb:.2f} MB")

    # 1. Check file not truncated
    if "</html>" not in content:
        errors.append("File troncato: manca </html>")
    if "</script>" not in content:
        errors.append("File troncato: manca </script>")

    # 2. Questions JSON
    m = re.search(r'const questions = (\[.*?\]);', content, re.DOTALL)
    if not m:
        errors.append("const questions non trovato")
    else:
        try:
            questions = json.loads(m.group(1))
            if len(questions) != 45:
                errors.append(f"Numero domande: {len(questions)} (attese 45)")
            else:
                print(f"OK: 45 domande trovate")

                # 5. Answer distribution
                ans_count = {0: 0, 1: 0, 2: 0, 3: 0}
                answers_seq = []
                for q in questions:
                    ans_count[q["ans"]] += 1
                    answers_seq.append(q["ans"])

                labels = {0: "A", 1: "B", 2: "C", 3: "D"}
                for k, v in ans_count.items():
                    if v < 8:
                        errors.append(f"Lettera {labels[k]} ha solo {v} risposte (min 8)")
                print(f"   Distribuzione: A={ans_count[0]}, B={ans_count[1]}, C={ans_count[2]}, D={ans_count[3]}")

                # 6. Max 2 consecutive
                consecutive = 1
                for i in range(1, len(answers_seq)):
                    if answers_seq[i] == answers_seq[i - 1]:
                        consecutive += 1
                        if consecutive > 2:
                            errors.append(
                                f"3+ risposte consecutive uguali ({labels[answers_seq[i]]}) "
                                f"alle domande {i}-{i+2}"
                            )
                            break
                    else:
                        consecutive = 1

                # Anti-regalo: pattern formali e outlier di lunghezza
                skipped = 0
                for i, q in enumerate(questions, start=1):
                    options = find_options(q)
                    if options is None or "ans" not in q:
                        skipped += 1
                        continue
                    giveaway_checks_html(i, options, q["ans"], errors)
                if skipped:
                    errors.append(
                        f"Anti-regalo: {skipped} domande senza lista opzioni "
                        f"riconoscibile (chiavi cercate: {OPTION_KEYS}).")
                else:
                    print("   Anti-regalo: check eseguito su 45 domande")

                # Check categories
                cats = set(q["cat"] for q in questions)
                print(f"   Categorie: {len(cats)}")

                # Check images/audio
                imgs = sum(1 for q in questions if "img" in q)
                audios = sum(1 for q in questions if "audio" in q)
                print(f"   Immagini: {imgs}, Audio: {audios}")

        except json.JSONDecodeError as e:
            errors.append(f"Questions JSON non valido: {e}")

    # 3. catBackgrounds JSON
    m2 = re.search(r'const catBackgrounds = (\{.*?\});', content, re.DOTALL)
    if not m2:
        errors.append("catBackgrounds non trovato")
    else:
        try:
            bg = json.loads(m2.group(1))
            print(f"OK: catBackgrounds valido ({len(bg)} categorie)")
        except json.JSONDecodeError as e:
            errors.append(f"catBackgrounds JSON non valido: {e}")

    # 4. Braces balance in all script blocks
    scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
    print(f"Script blocks: {len(scripts)}")
    for i, s in enumerate(scripts):
        opens = s.count("{")
        closes = s.count("}")
        if opens != closes:
            errors.append(
                f"Script {i}: parentesi sbilanciate (open={opens}, close={closes}, "
                f"diff={opens - closes})"
            )
        else:
            print(f"   Script {i}: parentesi bilanciate ({opens})")

    # 7. Sintassi JS reale (il conteggio graffe non basta: stringhe/regex)
    check_js_syntax(scripts, errors)

    # Report
    print()
    if errors:
        print("=" * 50)
        print(f"ERRORI TROVATI: {len(errors)}")
        print("=" * 50)
        for e in errors:
            print(f"  X {e}")
        return 1
    else:
        print("=" * 50)
        print("VALIDAZIONE OK - nessun errore")
        print("=" * 50)
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_quiz_html.py <path_to_html>")
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))
