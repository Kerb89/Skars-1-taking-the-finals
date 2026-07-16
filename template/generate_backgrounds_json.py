"""
Genera il JSON catBackgrounds per l'HTML del quiz.
Ridimensiona le immagini a max 600px lato lungo, qualità 60 JPEG.
Output: stampa il JSON da incollare nel template.

Uso: python generate_backgrounds_json.py [puntata_number]
  - puntata_number determina quale immagine usare per ogni categoria (rotazione)
"""
import sys, os, json, base64, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_DIR = os.path.join(BASE, "category_backgrounds")

# Mappa categoria -> lista immagini disponibili
CATEGORIES = [
    "anagrammi", "arte", "attualita", "cibo", "cinema", "dituttounpo",
    "geografia", "inglese", "letteratura", "lingua_italiana", "lingue",
    "matematica", "musica", "scienze", "sport", "storia", "tecnologia"
]

def get_images_for_cat(cat):
    folder = os.path.join(BG_DIR, cat)
    if not os.path.isdir(folder):
        return []
    return sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

def image_to_base64(filepath, max_size=600, quality=55):
    img = Image.open(filepath)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/jpeg;base64,{b64}"

def main():
    puntata = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    result = {}
    
    for cat in CATEGORIES:
        images = get_images_for_cat(cat)
        if not images:
            continue
        # Rotazione: puntata N usa immagine (N-1) % len(images)
        idx = (puntata - 1) % len(images)
        filepath = os.path.join(BG_DIR, cat, images[idx])
        b64 = image_to_base64(filepath)
        result[cat] = b64
        size_kb = len(b64) * 3 // 4 // 1024
        print(f"  {cat}: {images[idx]} -> {size_kb} KB base64", file=sys.stderr)
    
    # Output JSON
    print(json.dumps(result, indent=None))

if __name__ == "__main__":
    main()
