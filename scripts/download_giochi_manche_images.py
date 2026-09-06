"""
Scarica immagini tematiche da Unsplash per la manche monotematica "Giochi
senza tempo" (Puntata 37, domande 16-30) piu' uno sfondo di categoria
generico per "giochi", e le salva come .webp in una cartella di output.

Le immagini sono foto generiche del gioco gia' nominato nel testo della
domanda (es. pedine di scacchi per la domanda sugli scacchi) — mai un
dettaglio che riveli la risposta specifica testata (nome dell'inventore,
paese, numero esatto, ecc.), sullo stesso principio gia' applicato alla
manche Rock di P36.

Richiede: Pillow, requests, python-dotenv
"""
import os
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = os.environ.get(
    "GIOCHI_IMG_OUT_DIR",
    r"C:\Users\Aldor\AppData\Local\Temp\claude\C--Progetti-PROGETTO-SKARS\2a7fbc9a-c54f-45cf-a394-40a6001c3b6e\scratchpad\giochi_manche_images",
)
os.makedirs(OUT_DIR, exist_ok=True)

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# (nome_file, riferimento, query Unsplash — generica, non spoiler)
ITEMS = [
    ("cat_giochi.webp", "Sfondo categoria Giochi", "board games table top view colorful"),
    ("d16_scacchi.webp", "D16 - Scacchi/Chaturanga", "chess pieces macro dark background"),
    ("d17_sudoku.webp", "D17 - Sudoku", "sudoku puzzle grid closeup"),
    ("d18_monopoly.webp", "D18 - Monopoly", "monopoly board game pieces"),
    ("d19_risiko.webp", "D19 - Risiko/Risk", "world map board game pieces strategy"),
    ("d20_scarabeo.webp", "D20 - Scarabeo/Scrabble", "scrabble letter tiles closeup"),
    ("d21_cluedo.webp", "D21 - Cluedo", "magnifying glass mystery board game"),
    ("d22_poker.webp", "D22 - Poker", "playing cards poker chips table"),
    ("d23_backgammon.webp", "D23 - Backgammon", "backgammon board pieces closeup"),
    ("d24_dama.webp", "D24 - Dama internazionale", "checkers draughts board game"),
    ("d25_trivial.webp", "D25 - Trivial Pursuit", "trivia board game wedge pieces"),
    ("d26_mahjong.webp", "D26 - Mahjong", "mahjong tiles closeup"),
    ("d27_uno.webp", "D27 - Uno", "colorful uno cards game"),
    ("d28_carte_italiane.webp", "D28 - Carte italiane/Scopa", "italian playing cards"),
    ("d29_dama_cinese.webp", "D29 - Dama cinese", "chinese checkers colorful marbles board"),
    ("d30_rubik.webp", "D30 - Cubo di Rubik", "rubiks cube macro"),
]

manifest = []
total_size = 0

for filename, riferimento, query in ITEMS:
    out_path = os.path.join(OUT_DIR, filename)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        size_kb = os.path.getsize(out_path) / 1024
        total_size += size_kb
        manifest.append({"file": filename, "riferimento": riferimento, "query": query})
        print(f"{riferimento}: gia presente ({size_kb:.0f} KB), skip")
        continue

    print(f"Scaricando {riferimento} (query: '{query}')... ", end="")
    try:
        search_url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape",
            "content_filter": "high",
        }
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_KEY}",
            "User-Agent": "Mozilla/5.0 (QuizzoneScript/1.0)",
        }
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("results"):
            print("NESSUN RISULTATO")
            continue

        img_url = data["results"][0]["urls"]["regular"]

        img_resp = requests.get(img_url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (QuizzoneScript/1.0)"})
        img_resp.raise_for_status()

        img = Image.open(BytesIO(img_resp.content))
        if img.width > 800:
            ratio = 800 / img.width
            new_h = int(img.height * ratio)
            img = img.resize((800, new_h), Image.LANCZOS)

        img.convert("RGB").save(out_path, format="WEBP", quality=55, method=4)
        size_kb = os.path.getsize(out_path) / 1024
        total_size += size_kb
        print(f"OK ({size_kb:.0f} KB)")

        manifest.append({"file": filename, "riferimento": riferimento, "query": query})
    except Exception as e:
        print(f"ERRORE: {e}")

manifest_path = os.path.join(OUT_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n--- Totale: {total_size:.0f} KB ({total_size/1024:.1f} MB) ---")
print(f"Manifest salvato in {manifest_path}")
print(f"{len(manifest)}/{len(ITEMS)} immagini scaricate")
print("Immagini da Unsplash (unsplash.com) - licenza Unsplash (uso libero)")
