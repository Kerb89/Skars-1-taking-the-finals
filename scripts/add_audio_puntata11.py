import json, os, re

BASE = r"c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS"
html_path = os.path.join(BASE, "puntate", "quiz_puntata11_misto.html")

# Read audio b64
with open(os.path.join(BASE, "canzoni", "canzone_mengoni_clean.txt")) as f:
    b64_mengoni = f.read().strip()
with open(os.path.join(BASE, "canzoni", "canzone_verve_clean.txt")) as f:
    b64_verve = f.read().strip()
with open(os.path.join(BASE, "canzoni", "canzone_carpenter_clean.txt")) as f:
    b64_carpenter = f.read().strip()

# Read HTML
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Find the quizData JSON array
m = re.search(r'const questions = (\[.*?\]);\s', html, re.DOTALL)
if not m:
    print("ERROR: quizData not found")
    exit(1)

questions = json.loads(m.group(1))
print(f"Found {len(questions)} questions")

# Add audio to questions 2, 6, 12 (0-indexed: 1, 5, 11)
audio_map = {
    1: b64_mengoni,   # Question 2 - Mengoni
    5: b64_verve,     # Question 6 - The Verve
    11: b64_carpenter  # Question 12 - Sabrina Carpenter
}

for idx, b64 in audio_map.items():
    questions[idx]["audio"] = b64
    print(f"  Q{idx+1}: added audio ({len(b64)} chars)")

# Replace the JSON in HTML
new_json = json.dumps(questions, ensure_ascii=False)
html = html[:m.start(1)] + new_json + html[m.end(1):]

# Write
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(html_path) / (1024*1024)
print(f"\nDone! Size: {size_mb:.2f} MB")
