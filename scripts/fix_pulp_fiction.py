"""Fix: aggiorna la locandina di Pulp Fiction nella puntata 17 con il blur corretto."""
import json, re, os, base64, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Riconverti l'immagine corretta in b64
img = Image.open(os.path.join(BASE, 'cinema_posters', 'pulp_fiction_notext.jpg'))
img.thumbnail((450, 450), Image.LANCZOS)
buf = io.BytesIO()
img.convert('RGB').save(buf, format='JPEG', quality=50, optimize=True)
b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
print(f'Nuova b64: {len(b64)} chars')

# Patch puntata 17
path = os.path.join(BASE, 'puntate', 'quiz_puntata17_misto.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'const questions=(\[.*?\]);', content, re.DOTALL)
questions = json.loads(match.group(1))

# Trova la domanda Pulp Fiction (indice 33)
q = questions[33]
print(f'Domanda trovata: {q["q"][:60]}')
q['img'] = b64
questions[33] = q

new_json = json.dumps(questions, ensure_ascii=False)
new_content = content[:match.start(1)] + new_json + content[match.end(1):]
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print(f'Puntata 17 aggiornata: {os.path.getsize(path)//1024} KB')
