"""
Retrofit puntate esistenti: sostituisce catBackgrounds base64 con URL WebP esterni
e ricomprime l'audio inline a 64kbps mono.

Uso: python scripts/retrofit_puntate.py [--dry-run] [--only-bg] [--only-audio]

Prerequisito: aver eseguito scripts/convert_backgrounds_webp.py (genera i WebP)
"""
import os, sys, re, json, base64, subprocess, tempfile, shutil
from pathlib import Path

BASE = Path(__file__).parent.parent
PUNTATE_DIR = BASE / "puntate"
BG_DIR = BASE / "assets" / "backgrounds"

# Audio compression settings
BITRATE = "64k"
CHANNELS = 1
SAMPLE_RATE = 22050

CATEGORIES = [
    "anagrammi", "arte", "attualita", "cibo", "cinema", "dituttounpo",
    "geografia", "inglese", "letteratura", "lingua_italiana", "lingue",
    "matematica", "musica", "scienze", "sport", "storia", "tecnologia"
]


def get_puntata_number(filename):
    """Estrae il numero di puntata dal nome file."""
    m = re.search(r'quiz_puntata(\d+)', filename)
    return int(m.group(1)) if m else 0


def get_bg_url_for_category(cat, puntata):
    """Restituisce l'URL WebP per una categoria e puntata (rotazione)."""
    cat_files = sorted([
        f for f in os.listdir(BG_DIR)
        if f.startswith(cat + '_') and f.endswith('.webp')
    ])
    if not cat_files:
        return None
    idx = (puntata - 1) % len(cat_files)
    return f"/assets/backgrounds/{cat_files[idx]}"


def replace_cat_backgrounds(content, puntata):
    """Sostituisce il JSON di catBackgrounds con URL relativi."""
    # Match: const catBackgrounds = {...};
    # The base64 content contains semicolons, so we can't use [^;]+
    # Instead, find the opening { and match to the closing } before the ;
    m = re.search(r'(const\s+catBackgrounds\s*=\s*)', content)
    if not m:
        return content, False
    
    # Find the JSON object: starts at first { after "= "
    start_obj = content.index('{', m.end() - 1)
    # Find matching closing brace by counting nesting
    depth = 0
    end_obj = start_obj
    for i in range(start_obj, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end_obj = i
                break
    
    # Find the semicolon after the closing brace
    semi = content.index(';', end_obj)
    
    # Build new backgrounds object with URLs
    new_bg = {}
    for cat in CATEGORIES:
        url = get_bg_url_for_category(cat, puntata)
        if url:
            new_bg[cat] = url
    
    new_json = json.dumps(new_bg, ensure_ascii=True)
    new_content = content[:m.start()] + m.group(1) + new_json + ";" + content[semi + 1:]
    return new_content, True


def compress_mp3_bytes(audio_bytes):
    """Ricodifica bytes MP3 a basso bitrate, restituisce bytes compressi."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name
    
    tmp_out_path = tmp_in_path + "_out.mp3"
    
    try:
        cmd = [
            "ffmpeg", "-y", "-i", tmp_in_path,
            "-ac", str(CHANNELS),
            "-ar", str(SAMPLE_RATE),
            "-b:a", BITRATE,
            "-map_metadata", "-1",
            tmp_out_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None  # Skip on error
        
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_in_path):
            os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def compress_audio_in_content(content):
    """Trova e ricomprime tutti i clip audio base64 nel contenuto."""
    # Pattern for audio fields: "audio":"data:audio/mp3;base64,..." or "audio":"<raw_b64>"
    pattern = r'("audio"\s*:\s*")([^"]+)(")'
    
    matches = list(re.finditer(pattern, content))
    if not matches:
        return content, 0, 0
    
    total_saved = 0
    clips_processed = 0
    
    # Process in reverse to maintain offsets
    for m in reversed(matches):
        original_value = m.group(2)
        
        # Skip null/empty
        if not original_value or original_value == "null" or len(original_value) < 100:
            continue
        
        # Extract raw base64
        if original_value.startswith("data:"):
            raw_b64 = original_value.split(",", 1)[1]
        else:
            raw_b64 = original_value
        
        try:
            audio_bytes = base64.b64decode(raw_b64)
        except Exception:
            continue
        
        orig_size = len(audio_bytes)
        
        # Compress
        compressed = compress_mp3_bytes(audio_bytes)
        if compressed is None or len(compressed) >= orig_size:
            continue  # Skip if compression failed or didn't help
        
        new_b64 = base64.b64encode(compressed).decode("ascii")
        new_value = "data:audio/mp3;base64," + new_b64
        
        # Replace
        start = m.start(2)
        end = m.end(2)
        content = content[:start] + new_value + content[end:]
        
        saved = orig_size - len(compressed)
        total_saved += saved
        clips_processed += 1
    
    return content, clips_processed, total_saved


def process_puntata(html_path, dry_run=False, do_bg=True, do_audio=True):
    """Processa una singola puntata."""
    fname = html_path.name
    puntata = get_puntata_number(fname)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content.encode('utf-8'))
    bg_replaced = False
    audio_clips = 0
    audio_saved = 0
    
    if do_bg:
        content, bg_replaced = replace_cat_backgrounds(content, puntata)
    
    if do_audio:
        content, audio_clips, audio_saved = compress_audio_in_content(content)
    
    new_size = len(content.encode('utf-8'))
    saved_kb = (original_size - new_size) // 1024
    
    status = []
    if bg_replaced:
        status.append("BG->URL")
    if audio_clips > 0:
        status.append(f"audio:{audio_clips}clip/-{audio_saved//1024}KB")
    
    if not status:
        print(f"  {fname:45s} SKIP (niente da fare)")
        return 0
    
    print(f"  {fname:45s} {original_size//1024:>5d}KB -> {new_size//1024:>5d}KB  "
          f"(-{saved_kb}KB)  [{', '.join(status)}]")
    
    if not dry_run:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return original_size - new_size


def main():
    dry_run = "--dry-run" in sys.argv
    only_bg = "--only-bg" in sys.argv
    only_audio = "--only-audio" in sys.argv
    
    do_bg = not only_audio
    do_audio = not only_bg
    
    if dry_run:
        print("=== DRY RUN (nessun file modificato) ===\n")
    
    # Verify WebP files exist
    if do_bg and not BG_DIR.exists():
        print(f"ERRORE: {BG_DIR} non esiste. Esegui prima: python scripts/convert_backgrounds_webp.py")
        sys.exit(1)
    
    # Find all quiz HTML files
    files = sorted(PUNTATE_DIR.glob("quiz_puntata*.html"))
    if not files:
        print("Nessuna puntata trovata.")
        return
    
    print(f"Retrofit {len(files)} puntate (bg={'si' if do_bg else 'no'}, audio={'si' if do_audio else 'no'})\n")
    
    total_saved = 0
    for html_path in files:
        saved = process_puntata(html_path, dry_run=dry_run, do_bg=do_bg, do_audio=do_audio)
        total_saved += saved
    
    print(f"\n{'='*60}")
    print(f"Risparmio totale: {total_saved//1024} KB ({total_saved//1024//1024} MB)")
    if dry_run:
        print("(dry-run: nessun file modificato)")


if __name__ == "__main__":
    main()
