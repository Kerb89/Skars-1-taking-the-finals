"""Build script for Quizzone Puntata 27 - Misto. No audio, no question images."""
import os, re, json, base64
from PIL import Image
import io

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata27_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata27_misto.html")

# No question-specific images in this puntata
IMG_FILES = {}

BG_MUSIC = os.path.join(BASE, "background_music", "trivia_tension_b64.txt")

CAT_BG_DIR = os.path.join(BASE, "category_backgrounds")
# Rotated from p26 (p26 used: _2 and _3 variants)
# p27 uses: _1 and base variants
CAT_BG_MAP = {
    "anagrammi": os.path.join(CAT_BG_DIR, "anagrammi_1.jpg"),
    "arte": os.path.join(CAT_BG_DIR, "arte_1.jpg"),
    "attualita": os.path.join(CAT_BG_DIR, "attualita_1.jpg"),
    "cibo": os.path.join(CAT_BG_DIR, "cibo_1.jpg"),
    "cinema": os.path.join(CAT_BG_DIR, "cinema_3.jpg"),
    "dituttounpo": os.path.join(CAT_BG_DIR, "dituttounpo_1.jpg"),
    "geografia": os.path.join(CAT_BG_DIR, "geografia_3.jpg"),
    "inglese": os.path.join(CAT_BG_DIR, "inglese_3.jpg"),
    "letteratura": os.path.join(CAT_BG_DIR, "letteratura_1.jpg"),
    "lingua_italiana": os.path.join(CAT_BG_DIR, "lingua_italiana_1.jpg"),
    "lingue": os.path.join(CAT_BG_DIR, "lingue_3.jpg"),
    "matematica": os.path.join(CAT_BG_DIR, "matematica_1.jpg"),
    "musica": os.path.join(CAT_BG_DIR, "musica_2.jpg"),
    "scienze": os.path.join(CAT_BG_DIR, "scienze_3.jpg"),
    "sport": os.path.join(CAT_BG_DIR, "sport_1.jpg"),
    "storia": os.path.join(CAT_BG_DIR, "storia_1.jpg"),
    "tecnologia": os.path.join(CAT_BG_DIR, "tecnologia_1.jpg"),
}

# Category assignment for each question (1-45)
CATEGORIES = {
    1: "geografia",      2: "scienze",        3: "scienze",
    4: "sport",          5: "storia",         6: "cibo",
    7: "attualita",      8: "matematica",     9: "musica",
    10: "cinema",        11: "letteratura",   12: "cinema",
    13: "lingua_italiana", 14: "lingue",      15: "inglese",
    16: "geografia",     17: "tecnologia",    18: "scienze",
    19: "sport",         20: "storia",        21: "cibo",
    22: "attualita",     23: "matematica",    24: "musica",
    25: "cinema",        26: "letteratura",   27: "arte",
    28: "lingua_italiana", 29: "lingue",      30: "inglese",
    31: "anagrammi",     32: "sport",         33: "geografia",
    34: "scienze",       35: "tecnologia",    36: "cibo",
    37: "letteratura",   38: "dituttounpo",   39: "dituttounpo",
    40: "musica",        41: "tecnologia",    42: "dituttounpo",
    43: "musica",        44: "lingue",        45: "inglese",
}

# Answer indices (0=A, 1=B, 2=C, 3=D)
ANSWERS = {
    1: 1,  2: 2,  3: 0,  4: 3,  5: 1,  6: 1,  7: 3,  8: 2,  9: 1,  10: 0,
    11: 3, 12: 2, 13: 0, 14: 1, 15: 1, 16: 3, 17: 0, 18: 1, 19: 3, 20: 2,
    21: 0, 22: 3, 23: 1, 24: 2, 25: 0, 26: 3, 27: 1, 28: 2, 29: 0, 30: 1,
    31: 1, 32: 2, 33: 0, 34: 3, 35: 1, 36: 2, 37: 0, 38: 2, 39: 1, 40: 2,
    41: 1, 42: 3, 43: 1, 44: 2, 45: 0,
}


def read_b64_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("\ufeff", "")

def ensure_audio_prefix(b64):
    return b64 if b64.startswith("data:") else "data:audio/mp3;base64," + b64

def convert_image_to_b64(path, max_size=1400, quality=70):
    img = Image.open(path)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def parse_quiz_md(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    questions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r'\*\*(\d+)\.\*\*\s*(.*)', line)
        if m:
            num = int(m.group(1))
            q_text = m.group(2).strip()
            q_text = re.sub(r'^\[.*?\]\s*', '', q_text)
            opts = ["", "", "", ""]
            j = i + 1
            while j < len(lines) and j < i + 10:
                ol = lines[j].strip()
                if ol.startswith("A) "): opts[0] = ol[3:]
                elif ol.startswith("B) "): opts[1] = ol[3:]
                elif ol.startswith("C) "): opts[2] = ol[3:]
                elif ol.startswith("D) "):
                    opts[3] = ol[3:]
                    break
                j += 1
            if all(opts) and num <= 45:
                questions.append({"num": num, "q": q_text, "opts": opts})
            i = j + 1
        else:
            i += 1
    return questions

def parse_explanations(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    sol_start = content.find("## Soluzioni")
    if sol_start == -1: return {}
    sol_text = content[sol_start:]
    expls = {}
    current_num = None
    for line in sol_text.split('\n'):
        m2 = re.match(r'^(\d+)\.\s+[A-D]', line)
        if m2:
            current_num = int(m2.group(1))
        elif line.strip().startswith('> Spiegazione:') and current_num:
            expls[current_num] = line.strip().replace('> Spiegazione: ', '').replace('> Spiegazione:', '').strip()
    return expls


def main():
    print("=== Building Quizzone Puntata 27 ===")
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    questions = parse_quiz_md(QUIZ_MD)
    print(f"  Found {len(questions)} questions")
    if len(questions) != 45:
        found = [q["num"] for q in questions]
        missing = [n for n in range(1, 46) if n not in found]
        print(f"  ERROR: missing {missing}")
        return

    explanations = parse_explanations(QUIZ_MD)
    print(f"  Found {len(explanations)} explanations")

    img_data = {}
    for qn, path in IMG_FILES.items():
        if os.path.exists(path):
            img_data[qn] = convert_image_to_b64(path, max_size=500, quality=60)
            print(f"  IMG D{qn}: converted")
        else:
            print(f"  IMG D{qn}: NOT FOUND {path}")

    cat_backgrounds = {}
    for cat, path in CAT_BG_MAP.items():
        if os.path.exists(path):
            cat_backgrounds[cat] = convert_image_to_b64(path)
        else:
            print(f"  WARNING: background not found: {path}")

    bg_music = ""
    if os.path.exists(BG_MUSIC):
        bg_music = ensure_audio_prefix(read_b64_file(BG_MUSIC))

    questions_json = []
    for q in questions:
        num = q["num"]
        entry = {"q": q["q"], "opts": q["opts"], "ans": ANSWERS[num], "cat": CATEGORIES[num]}
        if num in img_data:
            entry["img"] = img_data[num]
        if num in explanations:
            entry["expl"] = explanations[num]
        questions_json.append(entry)

    html = template
    html = html.replace("{{PUNTATA_TITLE}}", "Puntata 27 \u2014 Misto")
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", "quiz_puntata27_misto")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(questions_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_backgrounds, ensure_ascii=False))

    # Background music via external URL (avoid bloating HTML)
    bg_music_url = "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/background_music/trivia_tension.mp3"
    bg_script = '<script>\n(function(){var a=new Audio("'+bg_music_url+'");a.loop=true;a.volume=0.35;var s=false;var n=document.getElementById("nameOverlay");new MutationObserver(function(){if(n.classList.contains("hidden")&&!s){a.play().catch(function(){});s=true}}).observe(n,{attributes:true,attributeFilter:["class"]});new MutationObserver(function(){if(document.getElementById("summary").classList.contains("visible"))a.pause()}).observe(document.getElementById("summary"),{attributes:true,attributeFilter:["class"]})})();\n</script>\n'
    html = html.replace("</body>", bg_script + "</body>")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(OUTPUT)
    print(f"\n=== BUILD COMPLETE ===")
    print(f"Output: {OUTPUT}")
    print(f"Size: {size/(1024*1024):.2f} MB")
    print(f"Questions: {len(questions_json)}, Images: {len(img_data)}, Backgrounds: {len(cat_backgrounds)}")

if __name__ == "__main__":
    main()
