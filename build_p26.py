"""Build script for Quizzone Puntata 26 - Misto. No audio, no images."""
import os, re, json, base64
from PIL import Image
import io

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata26_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata26_misto.html")

# No question-specific images in this puntata
IMG_FILES = {}

BG_MUSIC = os.path.join(BASE, "background_music", "trivia_tension_b64.txt")

CAT_BG_DIR = os.path.join(BASE, "category_backgrounds")
# Rotated from p25 (p25 used: anagrammi, arte_2, attualita_1, cibo_2, cinema_1,
# dituttounpo, geografia_1, inglese_1, letteratura_1, lingua_italiana_1,
# lingue_1, matematica_1, musica_3, scienze_1, sport_2, storia_1, tecnologia_1)
CAT_BG_MAP = {
    "anagrammi": os.path.join(CAT_BG_DIR, "anagrammi_2.jpg"),
    "arte": os.path.join(CAT_BG_DIR, "arte_3.jpg"),
    "attualita": os.path.join(CAT_BG_DIR, "attualita_2.jpg"),
    "cibo": os.path.join(CAT_BG_DIR, "cibo_3.jpg"),
    "cinema": os.path.join(CAT_BG_DIR, "cinema_2.jpg"),
    "dituttounpo": os.path.join(CAT_BG_DIR, "dituttounpo_2.jpg"),
    "geografia": os.path.join(CAT_BG_DIR, "geografia_2.jpg"),
    "inglese": os.path.join(CAT_BG_DIR, "inglese_2.jpg"),
    "indovinelli": os.path.join(CAT_BG_DIR, "dituttounpo_1.jpg"),
    "letteratura": os.path.join(CAT_BG_DIR, "letteratura_2.jpg"),
    "lingua_italiana": os.path.join(CAT_BG_DIR, "lingua_italiana_2.jpg"),
    "lingue": os.path.join(CAT_BG_DIR, "lingue_2.jpg"),
    "matematica": os.path.join(CAT_BG_DIR, "matematica_3.jpg"),
    "musica": os.path.join(CAT_BG_DIR, "musica_1.jpg"),
    "scienze": os.path.join(CAT_BG_DIR, "scienze_2.jpg"),
    "sport": os.path.join(CAT_BG_DIR, "sport_3.jpg"),
    "storia": os.path.join(CAT_BG_DIR, "storia_2.jpg"),
    "tecnologia": os.path.join(CAT_BG_DIR, "tecnologia_2.jpg"),
}

CATEGORIES = {
    1:"geografia", 2:"arte", 3:"sport", 4:"scienze", 5:"storia",
    6:"cibo", 7:"tecnologia", 8:"musica", 9:"cinema", 10:"matematica",
    11:"letteratura", 12:"lingua_italiana", 13:"inglese", 14:"lingue",
    15:"anagrammi", 16:"geografia", 17:"sport", 18:"scienze",
    19:"storia", 20:"indovinelli", 21:"musica", 22:"cinema", 23:"cibo",
    24:"tecnologia", 25:"arte", 26:"letteratura", 27:"matematica",
    28:"lingua_italiana", 29:"inglese", 30:"lingue", 31:"dituttounpo",
    32:"geografia", 33:"sport", 34:"dituttounpo", 35:"scienze",
    36:"storia", 37:"cinema", 38:"musica", 39:"cibo", 40:"letteratura",
    41:"tecnologia", 42:"indovinelli", 43:"lingue", 44:"inglese",
    45:"dituttounpo",
}

ANSWERS = {
    1:2, 2:3, 3:3, 4:0, 5:2, 6:0, 7:3, 8:3, 9:2, 10:1,
    11:3, 12:0, 13:1, 14:1, 15:3, 16:0, 17:2, 18:1, 19:3, 20:0,
    21:2, 22:1, 23:3, 24:0, 25:2, 26:1, 27:2, 28:0, 29:2, 30:1,
    31:1, 32:0, 33:2, 34:1, 35:2, 36:3, 37:1, 38:2, 39:3, 40:0,
    41:2, 42:1, 43:3, 44:0, 45:2,
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
            # Strip category tag like [Geografia] from the beginning
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
    print("=== Building Quizzone Puntata 26 ===")
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    questions = parse_quiz_md(QUIZ_MD)
    print(f"  Found {len(questions)} questions")
    if len(questions) != 45:
        found = [q["num"] for q in questions]
        missing = [n for n in range(1,46) if n not in found]
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
    html = html.replace("{{PUNTATA_TITLE}}", "Puntata 26 \u2014 Misto")
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", "quiz_puntata26_misto")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(questions_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_backgrounds, ensure_ascii=False))

    # Patch: add 30s timer for indovinelli (template doesn't support it natively)
    html = html.replace(
        "const hasAudio=!!q.audio;\n    const timer=hasAudio?QUIZ_META.timerAudio:QUIZ_META.timerDefault;",
        "const hasAudio=!!q.audio;\n    const isRiddle=(q.cat==='indovinelli');\n    const timer=hasAudio?QUIZ_META.timerAudio:(isRiddle?30:QUIZ_META.timerDefault);"
    )
    # Also patch processAnswer to use correct maxTime for riddles
    html = html.replace(
        "const maxTime=hasAudio?QUIZ_META.timerAudio:QUIZ_META.timerDefault;",
        "const isRiddleQ=(q.cat==='indovinelli');const maxTime=hasAudio?QUIZ_META.timerAudio:(isRiddleQ?30:QUIZ_META.timerDefault);"
    )

    # Use external MP3 file instead of inline base64 to reduce HTML size
    bg_music_url = "../background_music/trivia_tension.mp3"
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
