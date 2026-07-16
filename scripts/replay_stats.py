#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
replay_stats.py — Replay chirurgico delle stats perse.

Operazioni:
1. Rigenera contestations[] in player file e overall (da tutti i 52 grezzi)
2. Replay partite mancanti in overall.history + leaderboard
3. Replay tato/P28 in tato.json.games[]
4. Genera report markdown delle contestazioni

Esclusioni: file _reprocessed, quizId non matching quiz_puntata*, player '1'/test.

USO:
    python scripts/replay_stats.py              # dry-run (default)
    python scripts/replay_stats.py --apply      # scrive i file

NOTA: NON modifica i totali dei player file (totalGames, totalScore, ecc.)
per le partite già presenti in games[]. Aggiunge solo ciò che manca.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

APPLY = "--apply" in sys.argv

PLAYER_MAP = {
    "mattia": "mattia", "matt": "mattia",
    "jacopo": "jacopo", "manuel": "manuel",
    "tato": "tato", "gunny": "gunny", "ronny": "gunny",
}

RESULTS_DIR = Path("stats/results")
PLAYERS_DIR = Path("stats/players")


def load_grezzi():
    """Carica tutti i file grezzi validi, escludendo test e reprocessed."""
    grezzi = []
    for f in sorted(RESULTS_DIR.glob("*.json")):
        if "_reprocessed" in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        qid = d.get("quizId", "")
        if not qid.startswith("quiz_puntata"):
            continue
        pname = (d.get("playerName") or "").strip().lower()
        pkey = PLAYER_MAP.get(pname)
        if not pkey:
            continue
        grezzi.append({"file": f.name, "data": d, "playerKey": pkey, "quizId": qid})
    return grezzi


def extract_contestazioni(grezzi):
    """Estrae tutte le contestazioni, dedup per (player, quizId, questionNum, text)."""
    per_player = {}
    overall_list = []
    seen = set()

    for g in grezzi:
        d = g["data"]
        pk = g["playerKey"]
        qid = g["quizId"]
        ts = d.get("timestamp", "")
        date = ts.split("T")[0] if "T" in ts else ""

        for i, r in enumerate(d.get("results", [])):
            contest = r.get("contest")
            if not contest or not str(contest).strip():
                continue
            text = str(contest).strip()
            dedup_key = (pk, qid, i + 1, text)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            entry_player = {
                "quizId": qid, "date": date, "questionNum": i + 1,
                "question": r.get("question", ""),
                "correctAnswer": r.get("correctOption"),
                "givenAnswer": r.get("chosenOption", "(timeout)"),
                "contestText": text,
            }
            entry_overall = {
                "player": pk, "quizId": qid, "date": date,
                "questionNum": i + 1, "question": r.get("question", ""),
                "contestText": text,
            }
            per_player.setdefault(pk, []).append(entry_player)
            overall_list.append(entry_overall)

    return per_player, overall_list


def find_missing_overall(grezzi, overall):
    """Trova grezzi non presenti in overall.history."""
    history = overall.get("history", [])
    missing = []
    for g in grezzi:
        pk = g["playerKey"]
        qid = g["quizId"]
        found = any(h.get("quizId") == qid and h.get("player") == pk for h in history)
        if not found:
            missing.append(g)
    return missing


def find_missing_player(grezzi, player_data, player_key):
    """Trova grezzi non presenti in player.games[]."""
    games = player_data.get("games", [])
    missing = []
    for g in grezzi:
        if g["playerKey"] != player_key:
            continue
        qid = g["quizId"]
        found = any(gm.get("quizId") == qid for gm in games)
        if not found:
            missing.append(g)
    return missing


def replay_overall_entry(overall, g):
    """Aggiunge una partita a overall (history + leaderboard + mostWrongQuestions)."""
    d = g["data"]
    pk = g["playerKey"]
    ts = d.get("timestamp", "")
    date = ts.split("T")[0] if "T" in ts else ""

    overall.setdefault("history", []).append({
        "date": date, "quizId": d.get("quizId"),
        "quizTitle": d.get("quizTitle", d.get("quizId")),
        "player": pk, "score": d.get("score", 0), "correct": d.get("correct", 0),
        "total": d.get("total", 0), "percentage": d.get("percentage", 0),
    })

    overall.setdefault("leaderboard", {})
    if pk not in overall["leaderboard"]:
        overall["leaderboard"][pk] = {"games": 0, "totalScore": 0, "totalCorrect": 0,
                                      "totalQuestions": 0, "avgPercentage": 0, "avgTime": 0}
    lb = overall["leaderboard"][pk]
    lb["games"] += 1
    lb["totalScore"] += d.get("score", 0)
    lb["totalCorrect"] += d.get("correct", 0)
    lb["totalQuestions"] += d.get("total", 0)
    if lb["totalQuestions"] > 0:
        lb["avgPercentage"] = round(lb["totalCorrect"] / lb["totalQuestions"] * 100)
    lb["avgTime"] = round(
        ((lb["avgTime"] * (lb["games"] - 1) + (d.get("avgTime") or 0)) / lb["games"]), 1)

    overall.setdefault("mostWrongQuestions", [])
    for r in d.get("results", []):
        if not r.get("correct"):
            ew = next((w for w in overall["mostWrongQuestions"]
                       if w.get("question") == r.get("question") and
                       w.get("correctAnswer") == r.get("correctOption")), None)
            if ew:
                ew["timesWrong"] += 1
                if pk not in ew.get("wrongBy", []):
                    ew.setdefault("wrongBy", []).append(pk)
            else:
                overall["mostWrongQuestions"].append({
                    "question": r.get("question", ""),
                    "category": r.get("category", "altro"),
                    "correctAnswer": r.get("correctOption"),
                    "wrongBy": [pk], "timesWrong": 1,
                })
    overall["mostWrongQuestions"].sort(key=lambda w: w["timesWrong"], reverse=True)


def replay_player_entry(player_data, g):
    """Aggiunge una partita a player.games[] + aggiorna totali."""
    d = g["data"]
    ts = d.get("timestamp", "")
    date = ts.split("T")[0] if "T" in ts else ""

    player_data.setdefault("games", []).append({
        "quizId": d.get("quizId"),
        "quizTitle": d.get("quizTitle", d.get("quizId")),
        "date": date, "score": d.get("score", 0), "correct": d.get("correct", 0),
        "total": d.get("total", 0), "percentage": d.get("percentage", 0),
        "maxStreak": d.get("maxStreak", 0), "avgTime": d.get("avgTime", 0),
    })

    player_data["totalGames"] = player_data.get("totalGames", 0) + 1
    player_data["totalScore"] = player_data.get("totalScore", 0) + (d.get("score") or 0)
    player_data["totalCorrect"] = player_data.get("totalCorrect", 0) + (d.get("correct") or 0)
    player_data["totalQuestions"] = player_data.get("totalQuestions", 0) + (d.get("total") or 0)
    if player_data["totalQuestions"] > 0:
        player_data["avgPercentage"] = round(
            player_data["totalCorrect"] / player_data["totalQuestions"] * 100)
    n = player_data["totalGames"]
    player_data["avgTime"] = round(
        ((player_data.get("avgTime", 0) * (n - 1) + (d.get("avgTime") or 0)) / n), 1)


def generate_report(contest_per_player):
    """Genera report markdown delle contestazioni."""
    lines = ["# Report Contestazioni Recuperate", "",
             f"Data generazione: {datetime.now().strftime('%d/%m/%Y %H:%M')}", "",
             f"Totale contestazioni: {sum(len(v) for v in contest_per_player.values())}", ""]

    all_contests = []
    for pk, contests in contest_per_player.items():
        for c in contests:
            all_contests.append({**c, "player": pk})
    all_contests.sort(key=lambda x: (x["quizId"], x["questionNum"]))

    current_quiz = None
    for c in all_contests:
        if c["quizId"] != current_quiz:
            current_quiz = c["quizId"]
            lines.append(f"## {current_quiz.replace('_', ' ').title()}")
            lines.append("")
        lines.append(f"**D{c['questionNum']}** — {c['player'].capitalize()}")
        lines.append(f"- Domanda: {c.get('question', '?')[:120]}")
        lines.append(f"- Risposta data: {c.get('givenAnswer', '?')}")
        lines.append(f"- Corretta: {c.get('correctAnswer', '?')}")
        lines.append(f"- Contestazione: *\"{c['contestText']}\"*")
        lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("REPLAY STATS" + (" [DRY RUN]" if not APPLY else " [APPLY]"))
    print("=" * 70)
    print()

    grezzi = load_grezzi()
    print(f"File grezzi validi caricati: {len(grezzi)}")

    # --- Contestazioni ---
    contest_per_player, contest_overall = extract_contestazioni(grezzi)
    print(f"Contestazioni estratte: {len(contest_overall)}")
    for pk, cl in sorted(contest_per_player.items()):
        print(f"  {pk}: {len(cl)}")
    print()

    # --- Overall ---
    overall_path = PLAYERS_DIR / "overall.json"
    overall = json.loads(overall_path.read_text(encoding="utf-8")) if overall_path.exists() else {}
    missing_overall = find_missing_overall(grezzi, overall)
    print(f"Partite mancanti da overall.history: {len(missing_overall)}")
    for m in missing_overall:
        d = m["data"]
        print(f"  {m['file']} | {m['playerKey']} | {m['quizId']} | score={d.get('score')}")
    print()

    # --- Player files ---
    player_replays = {}
    for pk in set(PLAYER_MAP.values()):
        pf = PLAYERS_DIR / f"{pk}.json"
        if not pf.exists():
            continue
        pd = json.loads(pf.read_text(encoding="utf-8"))
        missing = find_missing_player(grezzi, pd, pk)
        if missing:
            player_replays[pk] = missing
            print(f"Partite mancanti da {pk}.json.games[]: {len(missing)}")
            for m in missing:
                print(f"  {m['file']} | {m['quizId']}")
    print()

    # === DIFF ===
    print("=" * 70)
    print("DIFF")
    print("=" * 70)
    print()
    print(f"1. Contestazioni: +{len(contest_overall)} totali")
    for pk, cl in sorted(contest_per_player.items()):
        print(f"   {pk}.json.contestations[]: 0 → {len(cl)}")
    print(f"   overall.json.contestations[]: 0 → {len(contest_overall)}")
    print()
    print(f"2. overall.history[]: {len(overall.get('history',[]))} → "
          f"{len(overall.get('history',[])) + len(missing_overall)} "
          f"(+{len(missing_overall)})")
    for m in missing_overall:
        d = m["data"]
        print(f"   + {m['playerKey']} | {m['quizId']} | "
              f"score={d.get('score')} | {d.get('correct')}/{d.get('total')}")
    print()
    if player_replays:
        print(f"3. Player games[]:")
        for pk, ms in player_replays.items():
            for m in ms:
                d = m["data"]
                print(f"   + {pk}.json: {m['quizId']} | score={d.get('score')}")
    else:
        print("3. Player games[]: nessuna aggiunta")
    print()

    # Leaderboard delta
    print("4. Leaderboard delta:")
    for m in missing_overall:
        d = m["data"]
        pk = m["playerKey"]
        print(f"   {pk}: +{d.get('score',0)} score, "
              f"+{d.get('correct',0)} correct, +{d.get('total',0)} questions")
    print()

    if not APPLY:
        print("[DRY RUN] Nessun file stats modificato.")
        report = generate_report(contest_per_player)
        report_path = Path("stats/report_contestazioni.md")
        report_path.write_text(report, encoding="utf-8")
        print(f"Report contestazioni generato: {report_path}")
        return

    # === APPLY ===
    for pk, contests in contest_per_player.items():
        pf = PLAYERS_DIR / f"{pk}.json"
        if not pf.exists():
            continue
        pd = json.loads(pf.read_text(encoding="utf-8"))
        pd["contestations"] = contests
        pf.write_text(json.dumps(pd, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ {pk}.json: contestations[] = {len(contests)} entry")

    overall["contestations"] = contest_overall
    for m in missing_overall:
        replay_overall_entry(overall, m)
    overall["lastUpdated"] = datetime.now().isoformat()
    overall["totalGamesPlayed"] = len(overall.get("history", []))
    overall_path.write_text(json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ overall.json: +{len(missing_overall)} history, "
          f"+{len(contest_overall)} contestazioni")

    for pk, ms in player_replays.items():
        pf = PLAYERS_DIR / f"{pk}.json"
        pd = json.loads(pf.read_text(encoding="utf-8"))
        for m in ms:
            replay_player_entry(pd, m)
        pf.write_text(json.dumps(pd, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ {pk}.json: +{len(ms)} games[], totali aggiornati")

    report = generate_report(contest_per_player)
    report_path = Path("stats/report_contestazioni.md")
    report_path.write_text(report, encoding="utf-8")
    print(f"  ✅ Report: {report_path}")
    print("\nDone. Commit e push quando pronto.")


if __name__ == "__main__":
    main()
