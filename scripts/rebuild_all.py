"""Rebuild puntate 13-26 using the current template."""
import re, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE, "template", "quiz_template.html")
PUNTATE_DIR = os.path.join(BASE, "puntate")
BG_MUSIC_URL = "https://raw.githubusercontent.com/Kerb89/Skars-1-taking-the-finals/master/background_music/trivia_tension.mp3"

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = f.read()


def extract_questions(content):
    m = re.search(r"const questions\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    return None


def extract_catbackgrounds(content):
    m = re.search(r"const catBackgrounds\s*=\s*(\{.*?\});", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def build_bg_script():
    return (
        '<script>\n(function(){'
        'var a=new Audio("' + BG_MUSIC_URL + '");'
        'a.loop=true;a.volume=0.35;var s=false;'
        'var n=document.getElementById("nameOverlay");'
        'new MutationObserver(function(){if(n.classList.contains("hidden")&&!s){'
        'a.play().catch(function(){});s=true}}).observe(n,{attributes:true,attributeFilter:["class"]});'
        'new MutationObserver(function(){if(document.getElementById("summary").classList.contains("visible"))'
        'a.pause()}).observe(document.getElementById("summary"),{attributes:true,attributeFilter:["class"]});'
        '})();\n</script>\n'
    )


rebuilt = 0
for i in range(13, 27):
    path = os.path.join(PUNTATE_DIR, f"quiz_puntata{i}_misto.html")
    if not os.path.exists(path):
        print(f"p{i}: FILE MISSING")
        continue

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    qs = extract_questions(content)
    bg = extract_catbackgrounds(content)
    if not qs or not bg:
        print(f"p{i}: SKIP (extraction failed)")
        continue

    title = f"Puntata {i} \u2014 Misto"
    filename = f"quiz_puntata{i}_misto"

    html = template
    html = html.replace("{{PUNTATA_TITLE}}", title)
    html = html.replace("{{SUBTITLE}}", "Misto \u2014 45 domande \u2014 20s timer")
    html = html.replace("{{FILENAME}}", filename)
    html = html.replace("{{QUESTIONS_JSON}}", json.dumps(qs, ensure_ascii=False))
    html = html.replace("{{CATEGORY_BACKGROUNDS_JSON}}", json.dumps(bg, ensure_ascii=False))

    # Add bg music
    html = html.replace("</body>", build_bg_script() + "</body>")

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    rebuilt += 1
    print(f"p{i}: rebuilt ({size_mb:.1f} MB)")

print(f"\nTotal rebuilt: {rebuilt}")
