"""
Scarica quadri famosi dal Met Museum - cerca per artista e poi verifica i titoli.
"""
import urllib.request, urllib.parse, json, os, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "art_questions_images", "da_usare")
os.makedirs(OUT_DIR, exist_ok=True)

def api_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'QuizProject/1.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def search(query, dept_id=None):
    q = urllib.parse.quote(query)
    url = f'https://collectionapi.metmuseum.org/public/collection/v1/search?q={q}&hasImages=true&isPublicDomain=true'
    if dept_id:
        url += f'&departmentId={dept_id}'
    return api_get(url).get('objectIDs', [])

def get_obj(oid):
    return api_get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}')

def download(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': 'QuizProject/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)

# Strategia: cerca per artista nel dip. European Paintings (11)
# poi prendi i primi risultati con immagine
TARGETS = [
    ("Vincent van Gogh", "van_gogh", 11),
    ("Claude Monet", "monet", 11),
    ("Rembrandt", "rembrandt", 11),
    ("Johannes Vermeer", "vermeer", 11),
    ("Edgar Degas", "degas", 11),
    ("Paul Cezanne", "cezanne", 11),
    ("Gustav Klimt", "klimt", None),
    ("Katsushika Hokusai", "hokusai", None),
    ("Paul Gauguin", "gauguin", 11),
    ("Pierre-Auguste Renoir", "renoir", 11),
    ("Caravaggio", "caravaggio", 11),
    ("El Greco", "el_greco", 11),
]

all_results = []

for artist_name, prefix, dept in TARGETS:
    print(f"\n=== {artist_name} ===")
    ids = search(artist_name, dept)[:10]
    count = 0
    for oid in ids:
        if count >= 2:
            break
        try:
            obj = get_obj(oid)
            img = obj.get('primaryImageSmall', '')
            artist = obj.get('artistDisplayName', '')
            title = obj.get('title', '')
            date = obj.get('objectDate', '')
            
            # Verifica che sia dell'artista giusto
            if artist_name.split()[-1].lower() not in artist.lower():
                continue
            if not img:
                continue
            
            safe_title = title.replace(' ', '_').replace('/', '_')[:30]
            filename = f"{prefix}_{safe_title}_{date.replace(' ', '').replace('–', '-')[:10]}.jpg"
            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            filepath = os.path.join(OUT_DIR, filename)
            
            size = download(img, filepath)
            print(f"  OK ({size//1024} KB) ID {oid}: {title} ({date}) -> {filename}")
            all_results.append({
                'id': oid,
                'artist': artist,
                'title': title,
                'date': date,
                'filename': filename,
                'size_kb': size // 1024
            })
            count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  Errore ID {oid}: {e}")

# Salva un catalogo
catalog_path = os.path.join(OUT_DIR, "_catalogo.json")
with open(catalog_path, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n\n=== TOTALE: {len(all_results)} quadri scaricati ===")
print(f"Catalogo salvato in: {catalog_path}")
for r in all_results:
    print(f"  {r['filename']} = {r['title']} ({r['artist']}, {r['date']})")
