"""
Build script for Quizzone Puntata 22 - Misto
Reads template, quiz MD, audio/image base64 files, category backgrounds,
and assembles the final self-contained HTML file.
"""

import os
import re
import json
import base64
from PIL import Image
import io

# === PATHS ===
BASE = r"c:\Users\Aldor\OneDrive\Desktop\PROGETTO SKARS"
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata22_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata22_misto.html")

# Audio files
AUDIO_FILES = {
    1: os.path.join(BASE, "canzoni", "harry_styles_b64.txt"),
    8: os.path.join(BASE, "canzoni", "mgmt_b64.txt"),
    21: os.path.join(BASE, "canzoni", "rosalia_b64.txt"),
}

# Image files for questions
IMG_FILES = {
    5: os.path.join(BASE, "art_questions_images", "da_usare", "vermeer_maid_b64.txt"),
    12: os.path.join(BASE, "art_questions_images", "da_usare", "mozambique_flag_b64.txt"),
}

# Background music
BG_MUSIC = os.path.join(BASE, "background_music", "trivia_tension_b64.txt")

# Category backgrounds (image files to convert)
CAT_BG_MAP = {
    "anagrammi": os.path.join(BASE, "category_backgrounds", "anagrammi_1.jpg"),
    "arte": os.path.join(BASE, "category_backgrounds", "arte_3.jpg"),
    "attualita": os.path.join(BASE, "category_backgrounds", "attualita_1.jpg"),
    "cibo": os.path.join(BASE, "category_backgrounds", "cibo_3.jpg"),
    "cinema": os.path.join(BASE, "category_backgrounds", "cinema_2.jpg"),
    "dituttounpo": os.path.join(BASE, "category_backgrounds", "dituttounpo_1.jpg"),
    "geografia": os.path.join(BASE, "category_backgrounds", "geografia_3.jpg"),
    "inglese": os.path.join(BASE, "category_backgrounds", "inglese_3.jpg"),
    "indovinelli": os.path.join(BASE, "category_backgrounds", "dituttounpo_2.jpg"),
    "letteratura": os.path.join(BASE, "category_backgrounds", "letteratura_2.jpg"),
    "lingua_italiana": os.path.join(BASE, "category_backgrounds", "lingua_italiana_2.jpg"),
    "lingue": os.path.join(BASE, "category_backgrounds", "lingue_3.jpg"),
    "matematica": os.path.join(BASE, "category_backgrounds", "matematica_3.jpg"),
    "musica": os.path.join(BASE, "category_backgrounds", "musica_1.jpg"),
    "scienze": os.path.join(BASE, "category_backgrounds", "scienze_2.jpg"),
    "sport": os.path.join(BASE, "category_backgrounds", "sport_3.jpg"),
    "storia": os.path.join(BASE, "category_backgrounds", "storia_2.jpg"),
    "tecnologia": os.path.join(BASE, "category_backgrounds", "tecnologia_2.jpg"),
}

# Category assignment for each question (1-indexed)
CATEGORIES = {
    1: "musica", 2: "tecnologia", 3: "sport", 4: "scienze", 5: "arte",
    6: "storia", 7: "lingue", 8: "musica", 9: "sport", 10: "matematica",
    11: "letteratura", 12: "geografia", 13: "scienze", 14: "geografia",
    15: "musica", 16: "inglese", 17: "cibo", 18: "cinema", 19: "storia",
    20: "indovinelli", 21: "musica", 22: "dituttounpo", 23: "dituttounpo",
    24: "sport", 25: "geografia", 26: "cibo", 27: "lingue", 28: "matematica",
    29: "dituttounpo", 30: "cinema", 31: "anagrammi", 32: "lingue",
    33: "attualita", 34: "letteratura", 35: "geografia", 36: "tecnologia",
    37: "lingua_italiana", 38: "sport", 39: "storia", 40: "arte",
    41: "attualita", 42: "tecnologia", 43: "sport", 44: "dituttounpo",
    45: "tecnologia",
}

# Answers (0-indexed: A=0, B=1, C=2, D=3)
ANSWERS = {
    1: 0, 2: 2, 3: 0, 4: 3, 5: 1, 6: 3, 7: 0, 8: 1, 9: 3, 10: 0,
    11: 2, 12: 3, 13: 0, 14: 3, 15: 1, 16: 3, 17: 1, 18: 0, 19: 3,
    20: 2, 21: 0, 22: 2, 23: 1, 24: 0, 25: 2, 26: 1, 27: 3, 28: 0,
    29: 2, 30: 3, 31: 2, 32: 1, 33: 2, 34: 3, 35: 0, 36: 2, 37: 0,
    38: 2, 39: 1, 40: 3, 41: 0, 42: 2, 43: 1, 44: 3, 45: 2,
}


def read_b64_file(path):
    """Read a base64 file and return its content, stripped of whitespace."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    # Remove BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]
    return content


def ensure_audio_prefix(b64_content):
    """Ensure audio base64 has proper data URI prefix."""
    if b64_content.startswith("data:"):
        return b64_content
    return "data:audio/mp3;base64," + b64_content


def ensure_image_prefix(b64_content):
    """Ensure image base64 has proper data URI prefix."""
    if b64_content.startswith("data:"):
        return b64_content
    return "data:image/jpeg;base64," + b64_content


def convert_image_to_b64(path, max_size=800, quality=40):
    """Convert an image file to compressed base64 data URI."""
    img = Image.open(path)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/jpeg;base64," + b64


def parse_quiz_md(md_path):
    """Parse the quiz MD file and extract questions with options."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    questions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for **N.** pattern
        m = re.match(r'\*\*(\d+)\.\*\*\s*(?:[\U0001f3b5\U0001f5bc\ufe0f]*\s*)?(.*)', line)
        if m:
            num = int(m.group(1))
            q_text = m.group(2).strip()

            # Read options (look for A), B), C), D) on subsequent lines)
            opts = ["", "", "", ""]
            j = i + 1
            while j < len(lines) and j < i + 10:
                ol = lines[j].strip()
                if ol.startswith("A) "):
                    opts[0] = ol[3:].strip()
                elif ol.startswith("B) "):
                    opts[1] = ol[3:].strip()
                elif ol.startswith("C) "):
                    opts[2] = ol[3:].strip()
                elif ol.startswith("D) "):
                    opts[3] = ol[3:].strip()
                    break
                j += 1

            if all(opts) and num <= 45:
                questions.append({"num": num, "q": q_text, "opts": opts})
            i = j + 1
        else:
            i += 1

    return questions


def main():
    print("=== Building Quizzone Puntata 22 ===")

    # 1. Read template
    print("Reading template...")
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    # 2. Parse quiz MD
    print("Parsing quiz MD...")
    questions = parse_quiz_md(QUIZ_MD)
    print(f"  Found {len(questions)} questions")

    if len(questions) != 45:
        print(f"  ERROR: Expected 45 questions, got {len(questions)}")
        # Print which questions were found
        found_nums = [q["num"] for q in questions]
        missing = [n for n in range(1, 46) if n not in found_nums]
        if missing:
            print(f"  Missing questions: {missing}")
        return

    # 3. Read audio files
    print("Reading audio files...")
    audio_data = {}
    for q_num, path in AUDIO_FILES.items():
        print(f"  D{q_num}: {os.path.basename(path)}")
        audio_data[q_num] = ensure_audio_prefix(read_b64_file(path))

    # 4. Read image files
    print("Reading image files...")
    img_data = {}
    for q_num, path in IMG_FILES.items():
        print(f"  D{q_num}: {os.path.basename(path)}")
        img_data[q_num] = ensure_image_prefix(read_b64_file(path))

    # 5. Convert category backgrounds
    print("Converting category backgrounds...")
    cat_backgrounds = {}
    for cat, path in CAT_BG_MAP.items():
        print(f"  {cat}: {os.path.basename(path)}")
        cat_backgrounds[cat] = convert_image_to_b64(path)

    # 6. Read background music
    print("Reading background music...")
    bg_music = ensure_audio_prefix(read_b64_file(BG_MUSIC))

    # 7. Build questions JSON
    print("Building questions JSON...")
    questions_json = []
    for q in questions:
        num = q["num"]
        entry = {
            "q": q["q"],
            "opts": q["opts"],
            "ans": ANSWERS[num],
            "cat": CATEGORIES[num],
        }
        # Add audio if applicable
        if num in audio_data:
            entry["audio"] = audio_data[num]
        # Add image if applicable
        if num in img_data:
            entry["img"] = img_data[num]
        questions_json.append(entry)

    # 8. Assemble HTML
    print("Assembling HTML...")
    html = template
    html = html.replace("{{PUNTATA_TITLE}}", "Puntata 22 \u2014 Misto")
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", "quiz_puntata22_misto")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(questions_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_backgrounds, ensure_ascii=False))

    # 9. Inject background music into the HTML
    # Add a script block for background music right before </body>
    bg_music_html = f'''
<script>
// Background Music
(function() {{
    const bgMusic = new Audio('{bg_music}');
    bgMusic.loop = true;
    bgMusic.volume = 0.35;
    let bgMusicStarted = false;

    // Start music when quiz starts (name overlay hidden)
    const nameOv = document.getElementById('nameOverlay');
    const obs = new MutationObserver(function(muts) {{
        if(nameOv.classList.contains('hidden') && !bgMusicStarted) {{
            bgMusic.play().catch(function(){{}});
            bgMusicStarted = true;
        }}
    }});
    obs.observe(nameOv, {{ attributes: true, attributeFilter: ['class'] }});

    // Pause on audio questions
    document.getElementById('audioPlayBtn').addEventListener('click', function() {{
        bgMusic.pause();
    }});

    // Resume after audio question via next button
    document.getElementById('nextBtn').addEventListener('click', function() {{
        if(!bgMusicStarted) return;
        // Check if next question has audio
        const progText = document.getElementById('progressDisplay').textContent;
        const current = parseInt(progText.split('/')[0].trim());
        if(current < questions.length && !questions[current].audio) {{
            bgMusic.play().catch(function(){{}});
        }} else if(current >= questions.length) {{
            bgMusic.pause(); // Quiz ended
        }}
    }});

    // Pause when showing summary
    const summaryEl = document.getElementById('summary');
    const sumObs = new MutationObserver(function() {{
        if(summaryEl.classList.contains('visible')) {{
            bgMusic.pause();
        }}
    }});
    sumObs.observe(summaryEl, {{ attributes: true, attributeFilter: ['class'] }});
}})();
</script>
'''
    html = html.replace("</body>", bg_music_html + "</body>")

    # 10. Write output
    print(f"Writing output to {OUTPUT}...")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    # Print stats
    file_size = os.path.getsize(OUTPUT)
    print(f"\n=== BUILD COMPLETE ===")
    print(f"Output: {OUTPUT}")
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    print(f"Questions: {len(questions_json)}")
    print(f"Audio questions: {len(audio_data)}")
    print(f"Image questions: {len(img_data)}")
    print(f"Category backgrounds: {len(cat_backgrounds)}")


if __name__ == "__main__":
    main()
