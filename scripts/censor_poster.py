"""
Censura automaticamente il titolo (e tutto il testo) dalle locandine dei film.
Usa EasyOCR per rilevare dove si trova il testo, poi applica un blur forte su quelle zone.

Uso:
  python scripts/censor_poster.py <input.jpg> <output.jpg> [--title-only]

Senza --title-only: blurra TUTTO il testo trovato nella locandina.
Con --title-only: blurra solo il testo piu' grande (presumibilmente il titolo).

Esempi:
  python scripts/censor_poster.py cinema_posters/matrix_poster.jpg cinema_posters/matrix_notext.jpg
  python scripts/censor_poster.py cinema_posters/matrix_poster.jpg cinema_posters/matrix_notitle.jpg --title-only
"""
import sys
import os
import easyocr
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

# Inizializza reader (una sola volta, supporta EN + IT)
reader = None

def get_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en', 'it'], gpu=False, verbose=False)
    return reader

def detect_text_regions(image_path):
    """Rileva tutte le regioni di testo nell'immagine."""
    r = get_reader()
    results = r.readtext(image_path)
    # results = list of (bbox, text, confidence)
    # bbox = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] (4 angoli del rettangolo)
    regions = []
    for bbox, text, conf in results:
        if conf < 0.2:  # ignora detections con confidenza troppo bassa
            continue
        # Converti bbox a rettangolo (x_min, y_min, x_max, y_max)
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x_min, x_max = int(min(xs)), int(max(xs))
        y_min, y_max = int(min(ys)), int(max(ys))
        area = (x_max - x_min) * (y_max - y_min)
        regions.append({
            'box': (x_min, y_min, x_max, y_max),
            'text': text,
            'confidence': conf,
            'area': area,
            'height': y_max - y_min
        })
    return regions

def blur_regions(image_path, output_path, regions, padding=10):
    """Applica blur forte sulle regioni specificate."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    
    for region in regions:
        x1, y1, x2, y2 = region['box']
        # Aggiungi padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        # Estrai la regione
        box_region = img.crop((x1, y1, x2, y2))
        rw, rh = box_region.size
        
        # Pixelate: riduci a pochi pixel e ri-ingrandisci
        tiny_w = max(2, rw // 12)
        tiny_h = max(2, rh // 6)
        pixelated = box_region.resize((tiny_w, tiny_h), Image.BILINEAR)
        pixelated = pixelated.resize((rw, rh), Image.NEAREST)
        
        # Applica anche gaussian blur sopra per rendere piu' uniforme
        blurred = pixelated.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Incolla
        img.paste(blurred, (x1, y1))
    
    img.save(output_path, "JPEG", quality=70, optimize=True)
    return output_path

def censor_poster(input_path, output_path, title_only=False):
    """Pipeline completa: rileva testo e blurra."""
    print(f"Analizzando: {input_path}")
    regions = detect_text_regions(input_path)
    
    if not regions:
        print("  Nessun testo rilevato! Copio l'originale.")
        from shutil import copy2
        copy2(input_path, output_path)
        return
    
    print(f"  Trovate {len(regions)} regioni di testo:")
    for r in sorted(regions, key=lambda x: -x['area']):
        print(f"    '{r['text']}' (conf={r['confidence']:.2f}, area={r['area']}, h={r['height']}px)")
    
    if title_only:
        # Prendi solo le scritte piu' grandi (presumibilmente il titolo)
        # Ordina per altezza del testo (font piu' grande = titolo)
        regions.sort(key=lambda x: -x['height'])
        max_height = regions[0]['height']
        # Prendi tutte le scritte che hanno almeno il 60% dell'altezza della piu' grande
        threshold = max_height * 0.6
        regions = [r for r in regions if r['height'] >= threshold]
        print(f"  Title-only: blurrando {len(regions)} regioni (le piu' grandi)")
    
    blur_regions(input_path, output_path, regions, padding=12)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Salvato: {output_path} ({size_kb:.0f} KB)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    title_only = "--title-only" in sys.argv
    
    censor_poster(input_path, output_path, title_only=title_only)
