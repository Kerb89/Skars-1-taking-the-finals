import json, re, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [17, 18]:
    path = os.path.join(BASE, 'puntate', f'quiz_puntata{p}_misto.html')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'const questions=(\[.*?\]);', content, re.DOTALL)
    questions = json.loads(match.group(1))
    print(f'\n=== PUNTATA {p} ({len(questions)} domande) ===')
    for i, q in enumerate(questions):
        cat = q.get('cat', '?')
        if cat in ('geografia', 'cinema', 'arte'):
            text = q['q'][:80]
            print(f'  #{i+1} [{cat}] {text}')
