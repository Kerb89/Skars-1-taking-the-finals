"""
Aggiunge domande con immagine alle puntate 17 e 18.
- Puntata 17: bandiera Bhutan (geografia) + locandina Pulp Fiction (cinema)
- Puntata 18: quadro Van Gogh campo grano (arte) + bandiera Mozambico (geografia)
"""
import json, os, base64, io, re
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def img_to_b64(path, max_size=400, quality=55):
    """Converte immagine in data URI base64."""
    img = Image.open(path)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/jpeg;base64,{b64}"

def png_to_b64(path, max_size=320, quality=70):
    """Converte PNG (bandiera) in data URI base64."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    # Componi su sfondo bianco per evitare problemi con trasparenza
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
    buf = io.BytesIO()
    bg.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/jpeg;base64,{b64}"

# Prepara immagini
print("Convertendo immagini...")
flag_bhutan = png_to_b64(os.path.join(BASE, "geography_images", "flag_bhutan.png"))
flag_mozambico = png_to_b64(os.path.join(BASE, "geography_images", "flag_mozambico.png"))
pulp_fiction = img_to_b64(os.path.join(BASE, "cinema_posters", "pulp_fiction_notext.jpg"), max_size=450, quality=50)
van_gogh_campo = img_to_b64(os.path.join(BASE, "art_questions_images", "da_usare", "van_gogh_campo_grano_cipressi_1889.jpg"), max_size=500, quality=50)

print(f"  Bhutan flag: {len(flag_bhutan)} chars")
print(f"  Mozambico flag: {len(flag_mozambico)} chars")
print(f"  Pulp Fiction: {len(pulp_fiction)} chars")
print(f"  Van Gogh: {len(van_gogh_campo)} chars")

# Nuove domande
q_bhutan = {
    "q": "\U0001f5bc\ufe0f DOMANDA VISIVA \u2014 Quale paese asiatico ha questa bandiera, caratterizzata da un drago bianco su sfondo arancione e giallo?",
    "opts": ["Sri Lanka", "Bhutan", "Myanmar", "Nepal"],
    "ans": 1, "cat": "geografia", "img": flag_bhutan
}

q_pulp_fiction = {
    "q": "\U0001f5bc\ufe0f DOMANDA VISIVA \u2014 Quale celebre film del 1994 \u00e8 rappresentato in questa locandina?",
    "opts": ["Pulp Fiction", "Kill Bill", "Trainspotting", "Natural Born Killers"],
    "ans": 0, "cat": "cinema", "img": pulp_fiction
}

q_mozambico = {
    "q": "\U0001f5bc\ufe0f DOMANDA VISIVA \u2014 Quale paese africano ha questa bandiera, l'unica al mondo a raffigurare un fucile d'assalto?",
    "opts": ["Angola", "Mozambico", "Zimbabwe", "Eritrea"],
    "ans": 1, "cat": "geografia", "img": flag_mozambico
}

q_van_gogh = {
    "q": "\U0001f5bc\ufe0f DOMANDA VISIVA \u2014 Quale pittore post-impressionista ha dipinto questo \"Campo di grano con cipressi\", conservato al Metropolitan Museum di New York?",
    "opts": ["Claude Monet", "Paul C\u00e9zanne", "Vincent van Gogh", "Camille Pissarro"],
    "ans": 2, "cat": "arte", "img": van_gogh_campo
}

def patch_puntata(html_path, new_questions, replace_indices):
    """Sostituisce domande specifiche in un file HTML di puntata."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trova il JSON delle domande
    match = re.search(r'const questions=(\[.*?\]);', content, re.DOTALL)
    if not match:
        # Prova formato alternativo
        match = re.search(r'const questions = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print(f"  ERRORE: non trovo questions in {html_path}")
        return False
    
    questions_json = match.group(1)
    questions = json.loads(questions_json)
    
    print(f"  {html_path}: {len(questions)} domande trovate")
    
    # Sostituisci le domande agli indici specificati
    for idx, new_q in zip(replace_indices, new_questions):
        old_q = questions[idx]['q'][:50]
        print(f"    Sostituisco #{idx+1}: '{old_q}...' -> domanda con immagine")
        questions[idx] = new_q
    
    # Ricostruisci il JSON
    new_json = json.dumps(questions, ensure_ascii=False)
    new_content = content[:match.start(1)] + new_json + content[match.end(1):]
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    size_kb = os.path.getsize(html_path) // 1024
    print(f"  Salvato: {html_path} ({size_kb} KB)")
    return True

# Puntata 17: sostituisco domanda 9 (geografia) e domanda 34 (cinema)
print("\n=== Puntata 17 ===")
p17_path = os.path.join(BASE, "puntate", "quiz_puntata17_misto.html")
patch_puntata(p17_path, [q_bhutan, q_pulp_fiction], [8, 33])

# Puntata 18: sostituisco domanda 2 (arte) e domanda 14 (geografia)
print("\n=== Puntata 18 ===")
p18_path = os.path.join(BASE, "puntate", "quiz_puntata18_misto.html")
patch_puntata(p18_path, [q_van_gogh, q_mozambico], [1, 13])

print("\n=== FATTO ===")
