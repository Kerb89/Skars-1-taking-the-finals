"""
Download immagini da Unsplash per il quiz.

Uso:
    python scripts/download_unsplash.py "colosseum rome" --out category_backgrounds/geografia/colosseo.jpg
    python scripts/download_unsplash.py "northern lights" --out category_backgrounds/scienze/aurora.jpg --b64

Opzioni:
    --out FILE      Percorso di salvataggio (default: unsplash_download.jpg)
    --b64           Genera anche il file _b64.txt con la stringa base64 compressa
    --orientation   landscape | portrait | squarish (default: landscape)
    --size          small | regular | full (default: regular)
"""

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installa requests: pip install requests")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Installa Pillow: pip install Pillow")
    sys.exit(1)

# Carica API key da .env nella root del progetto
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

def load_api_key():
    """Carica UNSPLASH_ACCESS_KEY da .env"""
    if not ENV_PATH.exists():
        print(f"File .env non trovato in {ENV_PATH}")
        print("Crea il file con: UNSPLASH_ACCESS_KEY=la_tua_chiave")
        sys.exit(1)
    
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("UNSPLASH_ACCESS_KEY="):
                return line.split("=", 1)[1].strip()
    
    print("UNSPLASH_ACCESS_KEY non trovata nel file .env")
    sys.exit(1)


def search_photo(query, api_key, orientation="landscape"):
    """Cerca una foto su Unsplash e restituisce i dati della prima corrispondenza."""
    resp = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "orientation": orientation, "per_page": 1},
        headers={"Authorization": f"Client-ID {api_key}"},
        timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    
    if not data.get("results"):
        print(f"Nessun risultato per: '{query}'")
        sys.exit(1)
    
    return data["results"][0]


def trigger_download(photo_id, api_key):
    """Triggera l'endpoint download come richiesto dai TOS Unsplash."""
    resp = requests.get(
        f"https://api.unsplash.com/photos/{photo_id}/download",
        headers={"Authorization": f"Client-ID {api_key}"},
        timeout=10
    )
    if resp.status_code == 200:
        print("  ✓ Download triggerato (TOS Unsplash)")
    else:
        print(f"  ⚠ Trigger download fallito (HTTP {resp.status_code})")


def download_image(url, output_path):
    """Scarica l'immagine dall'URL e la salva."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    
    size_kb = len(resp.content) / 1024
    print(f"  ✓ Salvata: {output_path} ({size_kb:.0f} KB)")


def image_to_base64(filepath, max_size=500, quality=50):
    """Converte un'immagine in base64 compresso (thumbnail 500px, JPEG q50)."""
    img = Image.open(filepath)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return b64


def save_credit_json(photo_data, output_path):
    """Salva i dati di credit in un file JSON accanto all'immagine."""
    credit = {
        "photographer": photo_data["user"]["name"],
        "profile_url": photo_data["user"]["links"]["html"] + "?utm_source=quizzone&utm_medium=referral",
        "photo_url": photo_data["links"]["html"] + "?utm_source=quizzone&utm_medium=referral",
        "unsplash_id": photo_data["id"],
        "description": photo_data.get("alt_description", "")
    }
    
    credit_path = Path(output_path).with_suffix(".credit.json")
    with open(credit_path, "w", encoding="utf-8") as f:
        json.dump(credit, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Credit salvato: {credit_path}")
    return credit


def main():
    parser = argparse.ArgumentParser(description="Scarica immagini da Unsplash per il quiz")
    parser.add_argument("query", help="Termine di ricerca (es. 'colosseum rome')")
    parser.add_argument("--out", default="unsplash_download.jpg", help="Percorso file output")
    parser.add_argument("--b64", action="store_true", help="Genera anche file base64")
    parser.add_argument("--orientation", default="landscape", choices=["landscape", "portrait", "squarish"])
    parser.add_argument("--size", default="regular", choices=["small", "regular", "full"],
                       help="Dimensione immagine (small=400w, regular=1080w, full=originale)")
    args = parser.parse_args()

    api_key = load_api_key()
    
    print(f"🔍 Cerco: '{args.query}'...")
    photo = search_photo(args.query, api_key, args.orientation)
    
    print(f"  📷 {photo['user']['name']} — {photo.get('alt_description', 'Senza titolo')}")
    
    # Trigger download endpoint (TOS)
    trigger_download(photo["id"], api_key)
    
    # Scarica l'immagine
    img_url = photo["urls"][args.size]
    download_image(img_url, args.out)
    
    # Salva credit
    credit = save_credit_json(photo, args.out)
    
    # Genera base64 se richiesto
    if args.b64:
        b64 = image_to_base64(args.out)
        b64_path = Path(args.out).with_suffix(".b64.txt")
        with open(b64_path, "w") as f:
            f.write(b64)
        print(f"  ✓ Base64: {b64_path} ({len(b64) / 1024:.0f} KB)")
    
    # Stampa snippet per il JSON della domanda
    print("\n📋 Snippet per il campo 'credit' nel JSON domanda:")
    print(json.dumps({
        "name": credit["photographer"],
        "url": credit["photo_url"],
        "profile": credit["profile_url"]
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
