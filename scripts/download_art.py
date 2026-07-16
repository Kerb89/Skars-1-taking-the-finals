"""
Scarica quadri famosi dal Met Museum Open Access API.
Salva in art_questions_images/da_usare/
"""
import urllib.request, urllib.parse, json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "art_questions_images", "da_usare")
os.makedirs(OUT_DIR, exist_ok=True)

def search_met(query):
    q = urllib.parse.quote(query)
    url = f'https://collectionapi.metmuseum.org/public/collection/v1/search?q={q}&hasImages=true&isPublicDomain=true'
    req = urllib.request.Request(url, headers={'User-Agent': 'QuizProject/1.0'})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data.get('objectIDs', [])

def get_object(oid):
    url = f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}'
    req = urllib.request.Request(url, headers={'User-Agent': 'QuizProject/1.0'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def download_image(url, filepath):
    req = urllib.request.Request(url, headers={'User-Agent': 'QuizProject/1.0'})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    with open(filepath, 'wb') as f:
        f.write(data)
    return len(data)

# Quadri da cercare con ID noti (verificati manualmente sul sito del Met)
KNOWN_PAINTINGS = [
    # (object_id, filename, descrizione per verifica)
    (436535, "van_gogh_campo_grano_cipressi_1889.jpg", "Van Gogh - Wheat Field with Cypresses"),
    (436532, "van_gogh_autoritratto_cappello_1887.jpg", "Van Gogh - Self-Portrait with Straw Hat"),
    (437984, "monet_ninfee_1919.jpg", "Monet - Water Lilies (cerca)"),
    (438009, "monet_passeggiata_1875.jpg", "Monet - La Passeggiata"),
    (459027, "hokusai_grande_onda.jpg", "Hokusai - Grande Onda"),
    (436575, "el_greco_vista_toledo_1600.jpg", "El Greco - View of Toledo"),
    (437826, "degas_classe_danza_1874.jpg", "Degas - The Dance Class"),
    (436105, "cezanne_monte_sainte_victoire.jpg", "Cezanne - Mont Sainte-Victoire"),
    (438815, "velazquez_ritratto.jpg", "Velazquez - Ritratto"),
    (437397, "turner_venezia.jpg", "Turner - Venezia"),
    (436965, "gauguin_ia_orana_maria.jpg", "Gauguin - Ia Orana Maria"),
    (438722, "renoir_madame_charpentier.jpg", "Renoir"),
]

downloaded = []
for oid, filename, desc in KNOWN_PAINTINGS:
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        print(f"  SKIP (esiste): {filename}")
        downloaded.append((filename, desc))
        continue
    
    try:
        obj = get_object(oid)
        img_url = obj.get('primaryImageSmall', '')
        title = obj.get('title', '?')
        artist = obj.get('artistDisplayName', '?')
        
        if not img_url:
            print(f"  NO IMAGE: ID {oid} - {title} ({artist})")
            continue
        
        size = download_image(img_url, filepath)
        size_kb = size / 1024
        print(f"  OK ({size_kb:.0f} KB): {filename} = {title} by {artist}")
        downloaded.append((filename, f"{title} - {artist}"))
    except Exception as e:
        print(f"  ERRORE ID {oid}: {e}")

print(f"\n=== Scaricate {len(downloaded)} immagini ===")
for fn, desc in downloaded:
    print(f"  {fn} -> {desc}")
