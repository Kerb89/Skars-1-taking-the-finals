"""Build script for Quizzone Puntata 28 - Misto. 3 audio questions via external URL."""
import os, re, json, base64
from PIL import Image
import io

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "template", "quiz_template.html")
QUIZ_MD = os.path.join(BASE, "puntate", "quiz_puntata28_misto.md")
OUTPUT = os.path.join(BASE, "puntate", "quiz_puntata28_misto.html")

# Audio clips as raw GitHub URLs (external, not inline base64)
AUDIO_URLS = {
    1: "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/canzoni/somebody_clip.mp3",
    8: "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/canzoni/drugs_clip.mp3",
    22: "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/canzoni/hotstepper_clip.mp3",
}

IMG_FILES = {}

CAT_BG_DIR = os.path.join(BASE, "category_backgrounds")
CAT_BG_MAP = {
    "anagrammi": os.path.join(CAT_BG_DIR, "anagrammi_2.jpg"),
    "arte": os.path.join(CAT_BG_DIR, "arte_2.jpg"),
    "attualita": os.path.join(CAT_BG_DIR, "attualita_2.jpg"),
    "cibo": os.path.join(CAT_BG_DIR, "cibo_2.jpg"),
    "cinema": os.path.join(CAT_BG_DIR, "cinema_1.jpg"),
    "dituttounpo": os.path.join(CAT_BG_DIR, "dituttounpo_2.jpg"),
    "geografia": os.path.join(CAT_BG_DIR, "geografia_4.jpg"),
    "inglese": os.path.join(CAT_BG_DIR, "inglese_4.jpg"),
    "letteratura": os.path.join(CAT_BG_DIR, "letteratura_2.jpg"),
    "lingua_italiana": os.path.join(CAT_BG_DIR, "lingua_italiana_2.jpg"),
    "lingue": os.path.join(CAT_BG_DIR, "lingue_4.jpg"),
    "matematica": os.path.join(CAT_BG_DIR, "matematica_3.jpg"),
    "musica": os.path.join(CAT_BG_DIR, "musica_3.jpg"),
    "scienze": os.path.join(CAT_BG_DIR, "scienze_1.jpg"),
    "sport": os.path.join(CAT_BG_DIR, "sport_2.jpg"),
    "storia": os.path.join(CAT_BG_DIR, "storia_3.jpg"),
    "tecnologia": os.path.join(CAT_BG_DIR, "tecnologia_3.jpg"),
}

CATEGORIES = {
    1: "musica", 2: "geografia", 3: "sport", 4: "scienze",
    5: "storia", 6: "cibo", 7: "tecnologia", 8: "musica",
    9: "cinema", 10: "matematica", 11: "letteratura", 12: "arte",
    13: "lingua_italiana", 14: "lingue", 15: "inglese", 16: "geografia",
    17: "sport", 18: "scienze", 19: "storia", 20: "cibo",
    21: "tecnologia", 22: "musica", 23: "matematica", 24: "cinema",
    25: "letteratura", 26: "arte", 27: "attualita", 28: "lingua_italiana",
    29: "lingue", 30: "inglese", 31: "anagrammi", 32: "geografia",
    33: "sport", 34: "scienze", 35: "storia", 36: "cibo",
    37: "tecnologia", 38: "dituttounpo", 39: "cinema", 40: "musica",
    41: "letteratura", 42: "dituttounpo", 43: "attualita", 44: "lingue",
    45: "dituttounpo",
}

ANSWERS = {
    1: 1, 2: 0, 3: 2, 4: 3, 5: 1, 6: 0, 7: 2, 8: 3, 9: 1, 10: 0,
    11: 3, 12: 2, 13: 1, 14: 1, 15: 0, 16: 2, 17: 1, 18: 3, 19: 0, 20: 2,
    21: 1, 22: 3, 23: 0, 24: 2, 25: 1, 26: 3, 27: 0, 28: 2, 29: 1, 30: 3,
    31: 0, 32: 2, 33: 1, 34: 3, 35: 0, 36: 2, 37: 1, 38: 3, 39: 0, 40: 2,
    41: 1, 42: 3, 43: 0, 44: 2, 45: 1,
}


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
            q_text = re.sub(r'^🎵\s*', '', q_text)
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
    if sol_start == -1:
        return {}
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
    print("=== Building Quizzone Puntata 28 ===")
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

    cat_backgrounds = {}
    for cat, path in CAT_BG_MAP.items():
        if os.path.exists(path):
            cat_backgrounds[cat] = convert_image_to_b64(path)
        else:
            print(f"  WARNING: background not found: {path}")

    questions_json = []
    for q in questions:
        num = q["num"]
        entry = {"q": q["q"], "opts": q["opts"], "ans": ANSWERS[num], "cat": CATEGORIES[num]}
        if num in AUDIO_URLS:
            entry["audio"] = AUDIO_URLS[num]
        if num in explanations:
            entry["expl"] = explanations[num]
        questions_json.append(entry)

    html = template
    html = html.replace("{{PUNTATA_TITLE}}", "Puntata 28 \u2014 Misto")
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", "quiz_puntata28_misto")
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(questions_json, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(cat_backgrounds, ensure_ascii=False))

    # Patch: riddles get 30s timer
    html = html.replace(
        "const hasAudio=!!q.audio;\n    const timer=hasAudio?QUIZ_META.timerAudio:QUIZ_META.timerDefault;",
        "const hasAudio=!!q.audio;\n    const isRiddle=(q.cat==='indovinelli');\n    const timer=hasAudio?QUIZ_META.timerAudio:(isRiddle?30:QUIZ_META.timerDefault);"
    )
    html = html.replace(
        "const maxTime=hasAudio?QUIZ_META.timerAudio:QUIZ_META.timerDefault;",
        "const isRiddleQ=(q.cat==='indovinelli');const maxTime=hasAudio?QUIZ_META.timerAudio:(isRiddleQ?30:QUIZ_META.timerDefault);"
    )

    # Background music via external URL
    bg_music_url = "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/background_music/trivia_tension.mp3"
    bg_script = '<script>\n(function(){var a=new Audio("'+bg_music_url+'");a.loop=true;a.volume=0.35;var s=false;var n=document.getElementById("nameOverlay");new MutationObserver(function(){if(n.classList.contains("hidden")&&!s){a.play().catch(function(){});s=true}}).observe(n,{attributes:true,attributeFilter:["class"]});new MutationObserver(function(){if(document.getElementById("summary").classList.contains("visible"))a.pause()}).observe(document.getElementById("summary"),{attributes:true,attributeFilter:["class"]})})();\n</script>\n'
    html = html.replace("</body>", bg_script + "</body>")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(OUTPUT)
    print(f"\n=== BUILD COMPLETE ===")
    print(f"Output: {OUTPUT}")
    print(f"Size: {size/(1024*1024):.2f} MB")
    print(f"Questions: {len(questions_json)}, Audio: {len(AUDIO_URLS)}, Backgrounds: {len(cat_backgrounds)}")


if __name__ == "__main__":
    main()
