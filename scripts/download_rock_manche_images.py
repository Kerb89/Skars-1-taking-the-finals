"""
Scarica immagini tematiche da Unsplash per la manche monotematica Rock
(Puntata 36, domande 16-30) e le salva come .webp in una cartella separata
per revisione manuale.

Le immagini sono generiche/evocative (strumenti, palco, atmosfera), MAI
ritratti di persone specifiche, mascotte o luoghi che comparirebbero come
risposta corretta — per non suggerire la risposta alla domanda associata.

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
    "ROCK_IMG_OUT_DIR",
    r"C:\Users\Aldor\AppData\Local\Temp\claude\C--Progetti-PROGETTO-SKARS\2a7fbc9a-c54f-45cf-a394-40a6001c3b6e\scratchpad\rock_manche_images",
)
os.makedirs(OUT_DIR, exist_ok=True)

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# (nome_file, domanda di riferimento, query Unsplash — generica, non spoiler)
QUESTIONS = [
    ("d16_acdc.webp", "D16 - AC/DC", "electric guitar power chord stage red lights"),
    ("d17_led_zeppelin.webp", "D17 - Led Zeppelin", "vintage drum kit concert stage moody light"),
    ("d18_black_sabbath.webp", "D18 - Black Sabbath", "industrial factory smoke dark heavy metal"),
    ("d19_deep_purple.webp", "D19 - Deep Purple", "stage fog machine smoke concert lights"),
    ("d20_guns_n_roses.webp", "D20 - Guns N' Roses", "guitar strings closeup black and white"),
    ("d21_rolling_stones.webp", "D21 - Rolling Stones", "vintage guitar amplifier retro rock sixties"),
    ("d22_the_doors.webp", "D22 - The Doors", "psychedelic concert lights organ keyboard rock"),
    ("d23_iron_maiden.webp", "D23 - Iron Maiden", "leather jacket studs heavy metal fashion"),
    ("d24_metallica.webp", "D24 - Metallica", "electric bass guitar close up strings metal"),
    ("d25_pink_floyd.webp", "D25 - Pink Floyd", "prism light beam dark stage"),
    ("d26_queen.webp", "D26 - Queen", "microphone stage spotlight"),
    ("d27_red_hot_chili_peppers.webp", "D27 - Red Hot Chili Peppers", "bass guitar funk rock stage energetic"),
    ("d28_woodstock.webp", "D28 - Woodstock", "outdoor music festival crowd vintage"),
    ("d29_nirvana.webp", "D29 - Nirvana", "grunge rock flannel guitar distortion stage"),
    ("d30_the_who.webp", "D30 - The Who", "smashed guitar rock stage energy"),
]

manifest = []
total_size = 0

for filename, domanda, query in QUESTIONS:
    out_path = os.path.join(OUT_DIR, filename)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        size_kb = os.path.getsize(out_path) / 1024
        total_size += size_kb
        manifest.append({"file": filename, "domanda": domanda, "query": query})
        print(f"{domanda}: gia presente ({size_kb:.0f} KB), skip")
        continue

    print(f"Scaricando {domanda} (query: '{query}')... ", end="")
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

        manifest.append({"file": filename, "domanda": domanda, "query": query})
    except Exception as e:
        print(f"ERRORE: {e}")

manifest_path = os.path.join(OUT_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n--- Totale: {total_size:.0f} KB ({total_size/1024:.1f} MB) ---")
print(f"Manifest salvato in {manifest_path}")
print(f"{len(manifest)}/{len(QUESTIONS)} immagini scaricate")
print("Immagini da Unsplash (unsplash.com) - licenza Unsplash (uso libero)")
