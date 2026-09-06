"""
Scarica immagini tematiche da Unsplash per 15 serie TV e le salva come .webp.
Le immagini sono generiche/evocative (non screenshot), usate come sfondo con overlay scuro.
Richiede: Pillow, requests, python-dotenv
"""
import os
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "assets", "img", "serie-tv")
os.makedirs(OUT_DIR, exist_ok=True)

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# Serie TV con keyword di ricerca evocativa per Unsplash
# Formato: (nome_file, soggetto, query_unsplash)
SERIES = [
    ("lost.webp", "Lost", "tropical island beach wreckage"),
    ("the_wire.webp", "The Wire", "baltimore city night urban"),
    ("stranger_things.webp", "Stranger Things", "dark forest red lights fog"),
    ("peaky_blinders.webp", "Peaky Blinders", "vintage cap smoke dark"),
    ("dexter.webp", "Dexter", "miami skyline night neon"),
    ("mad_men.webp", "Mad Men", "retro office 1960s whiskey"),
    ("the_office.webp", "The Office", "office desk paper work"),
    ("greys_anatomy.webp", "Grey's Anatomy", "hospital corridor dark"),
    ("house_of_cards.webp", "House of Cards", "american flag dark moody"),
    ("westworld.webp", "Westworld", "desert western landscape"),
    ("homeland.webp", "Homeland", "map pins intelligence dark"),
    ("black_mirror.webp", "Black Mirror", "dark screen reflection technology"),
    ("the_mandalorian.webp", "The Mandalorian", "desert starry night helmet"),
    ("chernobyl.webp", "Chernobyl", "nuclear power plant abandoned"),
    ("true_detective.webp", "True Detective", "louisiana swamp fog dark"),
]

manifest = []
total_size = 0

for filename, soggetto, query in SERIES:
    out_path = os.path.join(OUT_DIR, filename)
    
    # Se esiste gia ed e valido, skip
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        size_kb = os.path.getsize(out_path) / 1024
        total_size += size_kb
        manifest.append({"file": filename, "soggetto": soggetto})
        print(f"{soggetto}: gia presente ({size_kb:.0f} KB), skip")
        continue
    
    print(f"Scaricando {soggetto} (query: '{query}')... ", end="")
    try:
        # Cerca su Unsplash
        search_url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape",
            "content_filter": "high"
        }
        headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("results"):
            print("NESSUN RISULTATO")
            continue
        
        img_url = data["results"][0]["urls"]["regular"]  # 1080px
        
        # Scarica immagine
        img_resp = requests.get(img_url, timeout=15)
        img_resp.raise_for_status()
        
        img = Image.open(BytesIO(img_resp.content))
        # Ridimensiona a max 800px larghezza
        if img.width > 800:
            ratio = 800 / img.width
            new_h = int(img.height * ratio)
            img = img.resize((800, new_h), Image.LANCZOS)
        
        img.convert("RGB").save(out_path, format="WEBP", quality=55, method=4)
        size_kb = os.path.getsize(out_path) / 1024
        total_size += size_kb
        print(f"OK ({size_kb:.0f} KB)")
        
        manifest.append({"file": filename, "soggetto": soggetto})
    except Exception as e:
        print(f"ERRORE: {e}")

# Salva manifest
manifest_path = os.path.join(OUT_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n--- Totale: {total_size:.0f} KB ({total_size/1024:.1f} MB) ---")
print(f"Manifest salvato in {manifest_path}")
print(f"{len(manifest)}/15 immagini scaricate")
print("Immagini da Unsplash (unsplash.com) - licenza Unsplash (uso libero)")
