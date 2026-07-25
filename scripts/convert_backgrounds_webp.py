"""
Converte tutte le immagini di categoria in WebP compressi.

Sorgente: category_backgrounds/<categoria>/<file>.jpg
Destinazione: assets/backgrounds/<categoria>_<indice>.webp

Target: 20-40 KB per immagine, max 800px lato lungo.
"""
import os, sys, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE, 'category_backgrounds')
DST_DIR = os.path.join(BASE, 'assets', 'backgrounds')

MAX_SIDE = 800
TARGET_MAX_KB = 40
TARGET_MIN_KB = 15  # sotto questo e' troppo basso, alza quality

CATEGORIES = [
    "anagrammi", "arte", "attualita", "cibo", "cinema", "dituttounpo",
    "geografia", "inglese", "letteratura", "lingua_italiana", "lingue",
    "matematica", "musica", "scienze", "sport", "storia", "tecnologia"
]


def convert_image(src_path: str, dst_path: str) -> int:
    """Convert a single image to WebP, returns file size in bytes."""
    img = Image.open(src_path)
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    img = img.convert("RGB")

    # Binary search for quality that hits target range
    lo, hi = 20, 80
    best_buf = None
    best_quality = 50

    for _ in range(8):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=mid, method=4)
        size_kb = buf.tell() / 1024

        if size_kb > TARGET_MAX_KB:
            hi = mid - 1
        elif size_kb < TARGET_MIN_KB:
            lo = mid + 1
        else:
            best_buf = buf
            best_quality = mid
            break

        best_buf = buf
        best_quality = mid

    # Final save with best quality found
    if best_buf is None:
        best_buf = io.BytesIO()
        img.save(best_buf, format="WEBP", quality=best_quality, method=4)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, 'wb') as f:
        f.write(best_buf.getvalue())

    return best_buf.tell()


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    total_src = 0
    total_dst = 0
    count = 0

    for cat in CATEGORIES:
        cat_dir = os.path.join(SRC_DIR, cat)
        if not os.path.isdir(cat_dir):
            print(f"  SKIP {cat}: cartella non trovata")
            continue

        images = sorted([
            f for f in os.listdir(cat_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])

        for idx, fname in enumerate(images):
            src_path = os.path.join(cat_dir, fname)
            dst_name = f"{cat}_{idx}.webp"
            dst_path = os.path.join(DST_DIR, dst_name)

            src_size = os.path.getsize(src_path)
            dst_size = convert_image(src_path, dst_path)

            ratio = dst_size / src_size * 100 if src_size > 0 else 0
            print(f"  {dst_name:40s} {src_size//1024:>5d}KB -> {dst_size//1024:>3d}KB ({ratio:.0f}%)")

            total_src += src_size
            total_dst += dst_size
            count += 1

    print(f"\n{'='*60}")
    print(f"Convertite {count} immagini")
    print(f"Totale sorgente: {total_src//1024:,d} KB")
    print(f"Totale WebP:     {total_dst//1024:,d} KB")
    print(f"Risparmio:       {(total_src-total_dst)//1024:,d} KB ({(1-total_dst/total_src)*100:.0f}%)")


if __name__ == '__main__':
    main()
