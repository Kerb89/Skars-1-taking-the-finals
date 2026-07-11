"""Replace inline base64 background music with external MP3 reference in all quiz HTML files."""
import os, re

PUNTATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "puntate")
EXTERNAL_URL = "../background_music/trivia_tension.mp3"

count = 0
for f in sorted(os.listdir(PUNTATE_DIR)):
    if f.startswith("quiz_puntata") and f.endswith(".html"):
        path = os.path.join(PUNTATE_DIR, f)
        size_before = os.path.getsize(path) / (1024 * 1024)

        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()

        if "trivia_tension.mp3" in content:
            print(f"{f}: already updated ({size_before:.1f} MB)")
            continue

        if "data:audio/mp3;base64," not in content and "bgMusicData" not in content:
            print(f"{f}: no bg music ({size_before:.1f} MB)")
            continue

        content_new = content

        # Pattern 1: new Audio("data:audio/mp3;base64,...")
        p1 = r'new Audio\("data:audio/mp3;base64,[A-Za-z0-9+/=]+"\)'
        content_new = re.sub(p1, f'new Audio("{EXTERNAL_URL}")', content_new)

        # Pattern 2: new Audio('data:audio/mp3;base64,...')  (single quotes)
        p2 = r"new Audio\('data:audio/mp3;base64,[A-Za-z0-9+/=]+'\)"
        content_new = re.sub(p2, f"new Audio('{EXTERNAL_URL}')", content_new)

        # Pattern 3: bgMusicData variable containing base64
        # Remove the huge variable and replace usage
        p3_var = r"const bgMusicData\s*=\s*['\"][A-Za-z0-9+/=]+['\"];"
        if re.search(p3_var, content_new):
            content_new = re.sub(p3_var, "const bgMusicData=null;", content_new)
            # Replace: new Audio('data:audio/mp3;base64,'+bgMusicData)
            content_new = re.sub(
                r"new Audio\(['\"]data:audio/mp3;base64,['\"]?\+bgMusicData\)",
                f"new Audio('{EXTERNAL_URL}')",
                content_new
            )
            # Also handle: bgAudio=new Audio('data:audio/mp3;base64,'+bgMusicData)
            content_new = content_new.replace(
                "bgAudio=new Audio('data:audio/mp3;base64,'+bgMusicData)",
                f"bgAudio=new Audio('{EXTERNAL_URL}')"
            )

        # Pattern 4: Audio source set via src attribute
        p4 = r"\.src\s*=\s*['\"]data:audio/mp3;base64,[A-Za-z0-9+/=]+['\"]"
        content_new = re.sub(p4, f".src='{EXTERNAL_URL}'", content_new)

        if content_new != content:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content_new)
            size_after = os.path.getsize(path) / (1024 * 1024)
            print(f"{f}: {size_before:.1f} MB -> {size_after:.1f} MB (saved {size_before - size_after:.1f} MB)")
            count += 1
        else:
            print(f"{f}: no pattern matched ({size_before:.1f} MB)")

print(f"\nTotal updated: {count}")
