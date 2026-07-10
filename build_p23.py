"""
Build script for Quizzone Puntata 23 - Misto
Reads template, quiz MD, image base64 files, category backgrounds,
and assembles the final self-contained HTML file.

No audio questions in this episode.
Image questions: D2 (arte - Monet Terrazza Sainte-Adresse)
"""

import os
import re
import json
import base64

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL not available, category backgrounds will be skipped")

# === PATHS ===
BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata23_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata23_misto.html")

# Audio files (none this episode)
AUDIO_FILES = {}

# Image files for questions (question number -> b64 file path)
# D2: Monet "Terrazza a Sainte-Adresse" - use the existing image file
IMG_FILES = {
    2: os.path.join(BASE, "art_questions_images", "da_usare", "monet_terrazza_sainte_adresse_1867.jpg"),
}

# Category backgrounds (rotate from previous puntata)
CAT_BG_DIR = os.path.join(BASE, "category_backgrounds")
CAT_BG_MAP = {
    "anagrammi": os.path.join(CAT_BG_DIR, "anagrammi_1.jpg"),
    "arte": os.path.join(CAT_BG_DIR, "arte_1.jpg"),
    "attualita": os.path.join(CAT_BG_DIR, "attualita_1.jpg"),
    "cibo": os.path.join(CAT_BG_DIR, "cibo_1.jpg"),
    "cinema": os.path.join(CAT_BG_DIR, "cinema_1.jpg"),
    "dituttounpo": os.path.join(CAT_BG_DIR, "dituttounpo_1.jpg"),
    "geografia": os.path.join(CAT_BG_DIR, "geografia_1.jpg"),
    "inglese": os.path.join(CAT_BG_DIR, "inglese_1.jpg"),
    "indovinelli": os.path.join(CAT_BG_DIR, "dituttounpo_2.jpg"),
    "letteratura": os.path.join(CAT_BG_DIR, "letteratura_1.jpg"),
    "lingua_italiana": os.path.join(CAT_BG_DIR, "lingua_italiana_1.jpg"),
    "lingue": os.path.join(CAT_BG_DIR, "lingue_1.jpg"),
    "matematica": os.path.join(CAT_BG_DIR, "matematica_1.jpg"),
    "musica": os.path.join(CAT_BG_DIR, "musica_1.jpg"),
    "scienze": os.path.join(CAT_BG_DIR, "scienze_1.jpg"),
    "sport": os.path.join(CAT_BG_DIR, "sport_1.jpg"),
    "storia": os.path.join(CAT_BG_DIR, "storia_1.jpg"),
    "tecnologia": os.path.join(CAT_BG_DIR, "tecnologia_1.jpg"),
}

# Category assignment for each question (1-indexed)
CATEGORIES = {
    1: "musica", 2: "arte", 3: "sport", 4: "scienze", 5: "storia",
    6: "geografia", 7: "cibo", 8: "matematica", 9: "cinema", 10: "letteratura",
    11: "tecnologia", 12: "lingua_italiana", 13: "inglese", 14: "lingue",
    15: "anagrammi", 16: "indovinelli", 17: "dituttounpo", 18: "attualita",
    19: "sport", 20: "geografia", 21: "scienze", 22: "storia",
    23: "musica", 24: "arte", 25: "cinema", 26: "letteratura",
    27: "tecnologia", 28: "matematica", 29: "cibo", 30: "lingua_italiana",
    31: "lingue", 32: "inglese", 33: "indovinelli", 34: "dituttounpo",
    35: "attualita", 36: "sport", 37: "geografia", 38: "scienze",
    39: "anagrammi", 40: "letteratura", 41: "cinema", 42: "storia",
    43: "tecnologia", 44: "musica", 45: "cibo",
}

# Answers (0-indexed: A=0, B=1, C=2, D=3)
ANSWERS = {
    1: 2, 2: 0, 3: 3, 4: 1, 5: 0, 6: 2, 7: 1, 8: 3, 9: 3, 10: 0,
    11: 1, 12: 2, 13: 0, 14: 3, 15: 1, 16: 2, 17: 2, 18: 0, 19: 3,
    20: 1, 21: 0, 22: 2, 23: 3, 24: 1, 25: 0, 26: 3, 27: 2, 28: 1,
    29: 0, 30: 2, 31: 3, 32: 1, 33: 3, 34: 0, 35: 2, 36: 1, 37: 0,
    38: 2, 39: 1, 40: 3, 41: 0, 42: 2, 43: 3, 44: 2, 45: 0,
}

# === QUIZ META ===
QUIZ_META = {
    "title": "Puntata 23 — Misto",
    "filename": "quiz_puntata23_misto",
    "timerDefault": 20,
    "timerAudio": 30,
}


def parse_questions_from_md(md_path):
    """Parse questions and options from the MD file."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    questions = []
    # Pattern: **N.** question text\nA) ...\nB) ...\nC) ...\nD) ...
    pattern = r"\*\*(\d+)\.\*\*\s*(.*?)\nA\)\s*(.*?)\nB\)\s*(.*?)\nC\)\s*(.*?)\nD\)\s*(.*?)(?:\n|$)"
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        num = int(match[0])
        q_text = match[1].strip()
        opts = [match[2].strip(), match[3].strip(), match[4].strip(), match[5].strip()]
        questions.append({
            "num": num,
            "q": q_text,
            "opts": opts,
        })

    return questions


def load_b64_file(path):
    """Load base64 content from file, stripping whitespace."""
    if not os.path.exists(path):
        print(f"  WARNING: file not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def img_to_b64(path, max_width=600, quality=50):
    """Convert image to base64 JPEG thumbnail."""
    if not HAS_PIL or not os.path.exists(path):
        return None
    img = Image.open(path)
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build():
    print("=== Building Puntata 23 ===")

    # 1. Parse questions
    questions = parse_questions_from_md(QUIZ_MD)
    print(f"  Parsed {len(questions)} questions from MD")
    assert len(questions) == 45, f"Expected 45 questions, got {len(questions)}"

    # 2. Build questions JSON
    q_json = []
    for q in questions:
        num = q["num"]
        item = {
            "q": q["q"],
            "opts": q["opts"],
            "ans": ANSWERS[num],
            "cat": CATEGORIES[num],
        }

        # Add audio if present
        if num in AUDIO_FILES:
            audio_b64 = load_b64_file(AUDIO_FILES[num])
            if audio_b64:
                item["audio"] = f"data:audio/mp3;base64,{audio_b64}"
                print(f"  D{num}: audio attached")

        # Add image if present
        if num in IMG_FILES:
            img_path = IMG_FILES[num]
            if img_path.endswith(".jpg") or img_path.endswith(".png"):
                img_b64 = img_to_b64(img_path, max_width=600, quality=60)
                if img_b64:
                    item["img"] = f"data:image/jpeg;base64,{img_b64}"
                    print(f"  D{num}: image attached (from jpg)")
            else:
                img_b64 = load_b64_file(img_path)
                if img_b64:
                    item["img"] = f"data:image/jpeg;base64,{img_b64}"
                    print(f"  D{num}: image attached (from b64 file)")

        q_json.append(item)

    # 3. Category backgrounds
    cat_bg_json = {}
    for cat, path in CAT_BG_MAP.items():
        if os.path.exists(path):
            b64 = img_to_b64(path, max_width=800, quality=40)
            if b64:
                cat_bg_json[cat] = f"data:image/jpeg;base64,{b64}"
    print(f"  Loaded {len(cat_bg_json)} category backgrounds")

    # 4. Load template
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    # 5. Replace placeholders
    html = template.replace("{{PUNTATA_TITLE}}", QUIZ_META["title"])
    html = html.replace("{{FILENAME}}", QUIZ_META["filename"])
    html = html.replace("{{SUBTITLE}}", "45 domande — 7 luglio 2026")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(q_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_bg_json, ensure_ascii=False))

    # 6. Write output
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✓ Output written to: {OUTPUT}")
    print(f"  File size: {os.path.getsize(OUTPUT) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
