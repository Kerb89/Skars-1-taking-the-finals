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
import sys, re, json, os

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
