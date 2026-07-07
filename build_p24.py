"""
Build script for Quizzone Puntata 24 - Misto
No audio. Image questions: D2 (Hokusai), D32 (El Greco).
"""

import os, re, json, base64
from PIL import Image
import io

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata24_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata24_misto.html")

AUDIO_FILES = {}

IMG_FILES = {
    2: os.path.join(BASE, "art_questions_images", "da_usare", "hokusai_b64.txt"),
    32: os.path.join(BASE, "art_questions_images", "da_usare", "el_greco_vista_toledo_1600_b64.txt"),
}

BG_MUSIC = os.path.join(BASE, "background_music", "trivia_tension_b64.txt")

CAT_BG_DIR = os.path.join(BASE, "category_backgrounds")
CAT_BG_MAP = {
    "anagrammi": os.path.join(CAT_BG_DIR, "anagrammi_2.jpg"),
    "arte": os.path.join(CAT_BG_DIR, "arte_1.jpg"),
    "attualita": os.path.join(CAT_BG_DIR, "attualita_2.jpg"),
    "cibo": os.path.join(CAT_BG_DIR, "cibo_1.jpg"),
    "cinema": os.path.join(CAT_BG_DIR, "cinema_3.jpg"),
    "dituttounpo": os.path.join(CAT_BG_DIR, "dituttounpo_2.jpg"),
    "geografia": os.path.join(CAT_BG_DIR, "geografia_4.jpg"),
    "inglese": os.path.join(CAT_BG_DIR, "inglese_4.jpg"),
    "indovinelli": os.path.join(CAT_BG_DIR, "dituttounpo_1.jpg"),
    "letteratura": os.path.join(CAT_BG_DIR, "letteratura_3.jpg"),
    "lingua_italiana": os.path.join(CAT_BG_DIR, "lingua_italiana_3.jpg"),
    "lingue": os.path.join(CAT_BG_DIR, "lingue_4.jpg"),
    "matematica": os.path.join(CAT_BG_DIR, "matematica_4.jpg"),
    "musica": os.path.join(CAT_BG_DIR, "musica_2.jpg"),
    "scienze": os.path.join(CAT_BG_DIR, "scienze_3.jpg"),
    "sport": os.path.join(CAT_BG_DIR, "sport_1.jpg"),
    "storia": os.path.join(CAT_BG_DIR, "storia_3.jpg"),
    "tecnologia": os.path.join(CAT_BG_DIR, "tecnologia_3.jpg"),
}

CATEGORIES = {
    1:"geografia", 2:"arte", 3:"sport", 4:"scienze", 5:"storia",
    6:"lingue", 7:"tecnologia", 8:"musica", 9:"letteratura", 10:"matematica",
    11:"cinema", 12:"cibo", 13:"inglese", 14:"sport", 15:"geografia",
    16:"lingua_italiana", 17:"attualita", 18:"dituttounpo", 19:"storia",
    20:"indovinelli", 21:"scienze", 22:"anagrammi", 23:"lingue", 24:"tecnologia",
    25:"musica", 26:"cinema", 27:"cibo", 28:"letteratura", 29:"geografia",
    30:"matematica", 31:"sport", 32:"arte", 33:"dituttounpo", 34:"inglese",
    35:"attualita", 36:"lingua_italiana", 37:"tecnologia", 38:"storia",
    39:"lingue", 40:"dituttounpo", 41:"sport", 42:"geografia", 43:"letteratura",
    44:"cinema", 45:"anagrammi",
}

ANSWERS = {
    1:3, 2:1, 3:0, 4:2, 5:1, 6:3, 7:0, 8:2, 9:3, 10:0,
    11:1, 12:2, 13:2, 14:0, 15:1, 16:3, 17:0, 18:2, 19:1, 20:3,
    21:0, 22:2, 23:1, 24:3, 25:0, 26:2, 27:1, 28:3, 29:0, 30:2,
    31:1, 32:3, 33:0, 34:1, 35:2, 36:3, 37:0, 38:2, 39:1, 40:3,
    41:0, 42:2, 43:1, 44:3, 45:0,
}

EXPLANATIONS = {
    20: "Ogni giorno netto sale 1 metro. Dopo 27 giorni e' a 27 m. Il 28 giorno sale 3 m e raggiunge i 30 m, uscendo prima di scivolare.",
    22: "RAPIMENTO e PIROMANTE contengono le stesse 9 lettere: A, E, I, M, N, O, P, R, T.",
    31: "Djokovic vinse il Roland Garros 2016, primo dopo Rod Laver (1969) a detenere tutti e 4 i major contemporaneamente.",
    36: "Solere e' un verbo difettivo: manca del futuro semplice, del condizionale e di altri tempi.",
    45: "IMPORTANTE e PORTAMENTI contengono le stesse 10 lettere: A, E, I, M, N, O, P, R, T, T.",
}


def read_b64_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip().replace("\ufeff", "")

def ensure_audio_prefix(b64):
    return b64 if b64.startswith("data:") else "data:audio/mp3;base64," + b64

def ensure_image_prefix(b64):
    return b64 if b64.startswith("data:") else "data:image/jpeg;base64," + b64

def convert_image_to_b64(path, max_size=800, quality=40):
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


def main():
    print("=== Building Quizzone Puntata 24 ===")
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    questions = parse_quiz_md(QUIZ_MD)
    print(f"  Found {len(questions)} questions")
    if len(questions) != 45:
        found = [q["num"] for q in questions]
        missing = [n for n in range(1,46) if n not in found]
        print(f"  ERROR: missing {missing}")
        return

    img_data = {}
    for qn, path in IMG_FILES.items():
        if os.path.exists(path):
            img_data[qn] = ensure_image_prefix(read_b64_file(path))
            print(f"  IMG D{qn}: loaded")
        else:
            print(f"  IMG D{qn}: NOT FOUND {path}")

    cat_backgrounds = {}
    for cat, path in CAT_BG_MAP.items():
        if os.path.exists(path):
            cat_backgrounds[cat] = convert_image_to_b64(path)

    bg_music = ""
    if os.path.exists(BG_MUSIC):
        bg_music = ensure_audio_prefix(read_b64_file(BG_MUSIC))

    questions_json = []
    for q in questions:
        num = q["num"]
        entry = {"q": q["q"], "opts": q["opts"], "ans": ANSWERS[num], "cat": CATEGORIES[num]}
        if num in img_data:
            entry["img"] = img_data[num]
        if num in EXPLANATIONS:
            entry["expl"] = EXPLANATIONS[num]
        questions_json.append(entry)

    html = template
    html = html.replace("{{PUNTATA_TITLE}}", "Puntata 24 \u2014 Misto")
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", "quiz_puntata24_misto")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(questions_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_backgrounds, ensure_ascii=False))

    if bg_music:
        bg_script = '<script>\n(function(){var a=new Audio("'+bg_music+'");a.loop=true;a.volume=0.35;var s=false;var n=document.getElementById("nameOverlay");new MutationObserver(function(){if(n.classList.contains("hidden")&&!s){a.play().catch(function(){});s=true}}).observe(n,{attributes:true,attributeFilter:["class"]});new MutationObserver(function(){if(document.getElementById("summary").classList.contains("visible"))a.pause()}).observe(document.getElementById("summary"),{attributes:true,attributeFilter:["class"]})})();\n</script>\n'
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
