"""Test: scarica locandina da TMDB e croppa il titolo"""
from PIL import Image
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
poster_dir = os.path.join(BASE, "cinema_posters")

img = Image.open(os.path.join(poster_dir, "matrix_1999_poster.jpg"))
print(f"Dimensioni originali: {img.size}")
w, h = img.size

# Crop: togliamo il 18% inferiore (dove di solito c'e' il titolo)
cropped = img.crop((0, 0, w, int(h * 0.82)))
out_path = os.path.join(poster_dir, "matrix_1999_notitle.jpg")
cropped.save(out_path, quality=60)
print(f"Dopo crop: {cropped.size}")
print(f"File croppato: {os.path.getsize(out_path) // 1024} KB")
print("OK! Locandina croppata salvata.")
