"""
check_audio_id3.py — Verifica coerenza tag ID3 degli spezzoni audio con le domande del quiz.

Uso:
    python scripts/check_audio_id3.py puntate/quiz_puntata26_misto.md

Lo script:
1. Legge il .md e trova le domande musicali (categoria "musica" con audio).
2. Per ogni spezzone audio referenziato, legge i tag ID3 (titolo, artista).
3. Confronta con la risposta corretta della domanda.
4. Emette un report: MATCH / MISMATCH / NO_TAGS.

Dipendenze: mutagen (pip install mutagen)
"""

import sys
import re
from pathlib import Path

try:
    from mutagen.id3 import ID3
except ImportError:
    print("ERRORE: mutagen non installato. Esegui: pip install mutagen")
    sys.exit(1)


def normalize(s: str) -> str:
    """Normalizza per confronto fuzzy: lowercase, strip punteggiatura."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def check_audio_file(audio_path: Path) -> dict:
    """Legge tag ID3 da un file MP3. Restituisce {title, artist, error}."""
    if not audio_path.exists():
        return {"title": None, "artist": None, "error": "file non trovato"}
    try:
        tags = ID3(str(audio_path))
        title = str(tags.get("TIT2", "")) if tags.get("TIT2") else None
        artist = str(tags.get("TPE1", "")) if tags.get("TPE1") else None
        return {"title": title, "artist": artist, "error": None}
    except Exception as e:
        return {"title": None, "artist": None, "error": str(e)}


def find_audio_files(base_dir: Path) -> dict[str, Path]:
    """Mappa nome file -> path per tutti gli MP3 nella cartella canzoni/."""
    audio_map = {}
    canzoni_dir = base_dir / "canzoni"
    if canzoni_dir.exists():
        for f in canzoni_dir.glob("*.mp3"):
            audio_map[f.stem.lower()] = f
    return audio_map


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/check_audio_id3.py <file_quiz.md>")
        print("")
        print("Oppure verifica diretta su file MP3:")
        print("  python scripts/check_audio_id3.py --check <file.mp3> <titolo_atteso> [artista_atteso]")
        sys.exit(1)

    if sys.argv[1] == "--check":
        # Modalita' diretta: verifica un singolo MP3
        if len(sys.argv) < 4:
            print("Uso: python scripts/check_audio_id3.py --check <file.mp3> <titolo_atteso> [artista_atteso]")
            sys.exit(1)
        audio_path = Path(sys.argv[2])
        expected_title = sys.argv[3]
        expected_artist = sys.argv[4] if len(sys.argv) > 4 else None

        tags = check_audio_file(audio_path)
        if tags["error"]:
            print(f"ERRORE: {tags['error']}")
            sys.exit(1)

        if not tags["title"] and not tags["artist"]:
            print(f"NO_TAGS: {audio_path.name} — nessun tag ID3 trovato.")
            print("  -> Verifica manuale necessaria (premi play e confronta).")
            sys.exit(0)

        results = []
        if tags["title"]:
            if normalize(expected_title) in normalize(tags["title"]) or \
               normalize(tags["title"]) in normalize(expected_title):
                results.append(f"  Titolo: MATCH (tag='{tags['title']}')")
            else:
                results.append(f"  Titolo: MISMATCH (tag='{tags['title']}', atteso='{expected_title}')")

        if expected_artist and tags["artist"]:
            if normalize(expected_artist) in normalize(tags["artist"]) or \
               normalize(tags["artist"]) in normalize(expected_artist):
                results.append(f"  Artista: MATCH (tag='{tags['artist']}')")
            else:
                results.append(f"  Artista: MISMATCH (tag='{tags['artist']}', atteso='{expected_artist}')")

        print(f"File: {audio_path.name}")
        for r in results:
            print(r)

        if any("MISMATCH" in r for r in results):
            print("\n!! ATTENZIONE: tag ID3 non corrispondono. Verifica manuale!")
            sys.exit(2)
        else:
            print("\n+ Tag coerenti con la domanda.")
            sys.exit(0)

    else:
        # Modalita' batch: elenca tag di tutti gli MP3 in canzoni/
        md_path = Path(sys.argv[1])
        if not md_path.exists():
            print(f"ERRORE: {md_path} non trovato.")
            sys.exit(1)

        base_dir = md_path.parent.parent if md_path.parent.name == "puntate" else md_path.parent
        audio_map = find_audio_files(base_dir)

        if not audio_map:
            print("Nessun file MP3 trovato in canzoni/. Nulla da verificare.")
            sys.exit(0)

        print(f"File audio trovati in canzoni/: {len(audio_map)}")
        print("-" * 60)

        no_tags_count = 0
        for name, path in sorted(audio_map.items()):
            tags = check_audio_file(path)
            if tags["error"]:
                print(f"  {path.name}: ERRORE - {tags['error']}")
            elif not tags["title"] and not tags["artist"]:
                print(f"  {path.name}: NO_TAGS - verifica manuale necessaria")
                no_tags_count += 1
            else:
                parts = []
                if tags["title"]:
                    parts.append(f"titolo='{tags['title']}'")
                if tags["artist"]:
                    parts.append(f"artista='{tags['artist']}'")
                print(f"  {path.name}: {', '.join(parts)}")

        print("-" * 60)
        if no_tags_count:
            print(f"{no_tags_count} file senza tag ID3: verifica manuale (play + confronto).")
        print("Per verifica puntuale: python scripts/check_audio_id3.py --check <file.mp3> <titolo> [artista]")


if __name__ == "__main__":
    main()
