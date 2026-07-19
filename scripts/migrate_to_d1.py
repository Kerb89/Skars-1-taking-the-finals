#!/usr/bin/env python3
"""
migrate_to_d1.py — Migra i risultati grezzi da stats/results/ al database D1
via POST /api/results (endpoint idempotente).

Uso:
    python scripts/migrate_to_d1.py [--target URL] [--dry-run]

Default target: https://dashboard.skars-1.pages.dev/api/results
"""

import json
import sys
import re
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERRORE: installa requests (pip install requests)")
    sys.exit(1)

DEFAULT_TARGET = "https://dashboard.skars-1.pages.dev/api/results"
UA = {"User-Agent": "Mozilla/5.0 (QuizzoneScript/1.0)"}

# Pattern per estrarre upload_id dal nome file
NAME_PATTERN = re.compile(r"^(.+)\.json$")


def build_upload_id(filename):
    """Costruisce un uploadId deterministico dal nome del file."""
    m = NAME_PATTERN.match(filename)
    if m:
        return f"migration_raw_{m.group(1)}"
    return f"migration_raw_{filename}"


def load_result(path):
    """Carica un file risultato e lo converte nel formato POST /api/results."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    upload_id = build_upload_id(path.name)

    payload = {
        "uploadId": upload_id,
        "quizId": data.get("quizId", ""),
        "quizTitle": data.get("quizTitle", ""),
        "playerName": data.get("playerName", ""),
        "timestamp": data.get("timestamp", ""),
        "score": data.get("score", 0),
        "correct": data.get("correct", 0),
        "total": data.get("total", 0),
        "percentage": data.get("percentage", 0),
        "maxStreak": data.get("maxStreak", 0),
        "avgTime": data.get("avgTime", 0),
        "multiplierStats": data.get("multiplierStats", {"used": 0, "remaining": 0}),
        "results": data.get("results", [])
    }

    # Normalizza results — alcuni file hanno "num" ma non "question"
    for r in payload["results"]:
        r.setdefault("question", "")
        r.setdefault("category", "")
        r.setdefault("correct", False)
        r.setdefault("timeout", False)
        r.setdefault("points", 0)
        r.setdefault("streakBonus", 0)
        r.setdefault("multiplierUsed", False)
        r.setdefault("timeUsed", 0)
        r.setdefault("chosenOption", "")
        r.setdefault("correctOption", "")
        r.setdefault("contest", None)

    return payload


def main():
    parser = argparse.ArgumentParser(description="Migra risultati in D1")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="URL endpoint")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostra, non invia")
    args = parser.parse_args()

    results_dir = Path("stats/results")
    if not results_dir.is_dir():
        print(f"ERRORE: cartella {results_dir} non trovata")
        sys.exit(1)

    files = sorted([
        f for f in results_dir.glob("*.json")
        if not re.search(r"test|reprocessed", f.name, re.IGNORECASE)
    ])

    print(f"\n=== Migrazione D1 — {len(files)} file da importare ===")
    print(f"Target: {args.target}")
    if args.dry_run:
        print("*** DRY RUN — nessuna richiesta inviata ***")
    print()

    ok = 0
    dedup = 0
    errors = []

    for i, f in enumerate(files, 1):
        try:
            payload = load_result(f)
        except Exception as e:
            errors.append((f.name, f"errore parsing: {e}"))
            print(f"  [{i}/{len(files)}] ERRORE {f.name}: {e}")
            continue

        if args.dry_run:
            print(f"  [{i}/{len(files)}] {f.name} -> uploadId={payload['uploadId'][:50]}... "
                  f"({payload['playerName']}, {len(payload['results'])} answers)")
            ok += 1
            continue

        try:
            r = requests.post(
                args.target,
                json=payload,
                headers=UA,
                timeout=30
            )
            body = r.json()

            if r.status_code == 200 and body.get("success"):
                if body.get("inserted"):
                    ok += 1
                    status = "NUOVO"
                else:
                    dedup += 1
                    status = "DEDUP"
                print(f"  [{i}/{len(files)}] {status} -- {f.name} ({payload['playerName']})")
            else:
                errors.append((f.name, body.get("error", f"HTTP {r.status_code}")))
                print(f"  [{i}/{len(files)}] FAIL -- {f.name}: {body}")
        except Exception as e:
            errors.append((f.name, str(e)))
            print(f"  [{i}/{len(files)}] ERRORE -- {f.name}: {e}")

        # Rate limit gentile
        time.sleep(0.2)

    print(f"\n=== Risultato ===")
    print(f"  Inseriti: {ok}")
    print(f"  Dedup (gia presenti): {dedup}")
    print(f"  Errori: {len(errors)}")
    if errors:
        print("\n  Dettaglio errori:")
        for name, err in errors:
            print(f"    - {name}: {err}")
    print()


if __name__ == "__main__":
    main()
