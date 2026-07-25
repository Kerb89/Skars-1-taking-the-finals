"""
Ricodifica clip audio MP3 a 64kbps mono per ridurre il peso inline.

Uso:
  python scripts/compress_audio_b64.py <input.mp3> [--output output.mp3]
  python scripts/compress_audio_b64.py --b64 <base64_string> [--output output_b64.txt]
  python scripts/compress_audio_b64.py --scan-html <file.html>

Modalita:
  1. File MP3 -> ricodifica e salva (o stampa base64)
  2. Stringa base64 -> decodifica, ricodifica, restituisce nuova base64
  3. Scan HTML -> trova tutti i campi audio base64 in un quiz HTML,
     li ricodifica in-place e salva il file (con backup .bak)

Target: 64kbps mono MP3 (sufficiente per snippet di riconoscimento).
"""
import sys, os, subprocess, tempfile, base64, re, shutil


BITRATE = "64k"
CHANNELS = 1
SAMPLE_RATE = 22050  # 22kHz e' sufficiente per snippet vocali/musicali


def compress_mp3(input_path: str, output_path: str) -> int:
    """Ricodifica un MP3 a basso bitrate. Ritorna la dimensione in bytes."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", str(CHANNELS),
        "-ar", str(SAMPLE_RATE),
        "-b:a", BITRATE,
        "-map_metadata", "-1",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERRORE ffmpeg: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return os.path.getsize(output_path)


def compress_b64(b64_input: str) -> str:
    """Prende base64 audio, ricodifica, restituisce nuova base64."""
    # Strip data URI prefix if present
    raw_b64 = b64_input
    if raw_b64.startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]

    audio_bytes = base64.b64decode(raw_b64)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path + "_out.mp3"

    try:
        compress_mp3(tmp_in_path, tmp_out_path)
        with open(tmp_out_path, "rb") as f:
            compressed = f.read()
        return base64.b64encode(compressed).decode("ascii")
    finally:
        os.unlink(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.unlink(tmp_out_path)


def scan_and_compress_html(html_path: str):
    """Trova tutti i campi audio base64 in un quiz HTML e li ricomprime."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern: "audio":"<base64 or data uri>"
    pattern = r'("audio"\s*:\s*")([A-Za-z0-9+/=]+|data:audio[^"]+)(")'
    
    matches = list(re.finditer(pattern, content))
    if not matches:
        print("Nessun campo audio trovato.")
        return

    print(f"Trovati {len(matches)} clip audio. Ricompressione...")

    # Backup
    backup_path = html_path + ".bak"
    shutil.copy2(html_path, backup_path)

    total_saved = 0
    for i, m in enumerate(reversed(matches)):  # reversed per non spostare gli offset
        original_b64 = m.group(2)
        
        # Skip null/empty
        if not original_b64 or original_b64 == "null":
            continue

        original_size = len(original_b64)
        compressed_b64 = compress_b64(original_b64)
        new_size = len(compressed_b64)
        saved = original_size - new_size

        # Add data URI prefix for consistency
        if not compressed_b64.startswith("data:"):
            compressed_b64_full = "data:audio/mp3;base64," + compressed_b64
        else:
            compressed_b64_full = compressed_b64

        # Replace in content
        start = m.start(2)
        end = m.end(2)
        content = content[:start] + compressed_b64_full + content[end:]

        total_saved += saved
        orig_kb = len(base64.b64decode(original_b64.split(",")[-1])) // 1024
        comp_kb = len(base64.b64decode(compressed_b64)) // 1024
        print(f"  Clip {len(matches)-i}: {orig_kb}KB -> {comp_kb}KB")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nSalvato. Backup in {backup_path}")
    print(f"Risparmio testo base64: ~{total_saved//1024}KB di caratteri")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--scan-html":
        if len(sys.argv) < 3:
            print("Uso: --scan-html <file.html>")
            sys.exit(1)
        scan_and_compress_html(sys.argv[2])

    elif sys.argv[1] == "--b64":
        if len(sys.argv) < 3:
            print("Uso: --b64 <base64_string_or_file>")
            sys.exit(1)
        inp = sys.argv[2]
        if os.path.isfile(inp):
            with open(inp, "r") as f:
                inp = f.read().strip()
        result = compress_b64(inp)
        if "--output" in sys.argv:
            out_path = sys.argv[sys.argv.index("--output") + 1]
            with open(out_path, "w") as f:
                f.write(result)
            print(f"Scritto in {out_path} ({len(result)//1024}KB b64)")
        else:
            print(result)

    else:
        input_path = sys.argv[1]
        if not os.path.isfile(input_path):
            print(f"File non trovato: {input_path}")
            sys.exit(1)
        
        if "--output" in sys.argv:
            output_path = sys.argv[sys.argv.index("--output") + 1]
        else:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_compressed{ext}"

        orig_size = os.path.getsize(input_path)
        new_size = compress_mp3(input_path, output_path)
        print(f"{orig_size//1024}KB -> {new_size//1024}KB ({new_size/orig_size*100:.0f}%)")
        print(f"Salvato: {output_path}")


if __name__ == "__main__":
    main()
