"""Verifica copertura bidirezionale + i 5 file mancanti dall'indice."""
import json
from pathlib import Path

results_dir = Path("stats/results")
players_dir = Path("stats/players")

PLAYER_MAP = {
    "mattia": "mattia", "matt": "mattia",
    "jacopo": "jacopo", "manuel": "manuel",
    "tato": "tato", "gunny": "gunny", "ronny": "gunny", "1": "test"
}

# === Indicizza tutti i grezzi ===
all_files = sorted(results_dir.glob("*.json"))
grezzo_index = {}  # (quizId, playerName_lower) -> filename
non_parsabili = []

for f in all_files:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        pname = (d.get("playerName") or "").strip().lower()
        qid = d.get("quizId", "")
        grezzo_index[(qid, pname)] = f.name
    except Exception as e:
        non_parsabili.append((f.name, str(e)[:80]))

print(f"File grezzi su disco: {len(all_files)}")
print(f"Indicizzati con successo: {len(grezzo_index)}")
print(f"Non parsabili: {len(non_parsabili)}")
if non_parsabili:
    for name, err in non_parsabili:
        print(f"  ❌ {name}: {err}")
print()

# === Check (a): grezzo → player file (esistono grezzi non in games[]?) ===
print("=== CHECK INVERSO: grezzi non presenti nei file player ===")
grezzi_orfani = []

for (qid, pname), fname in sorted(grezzo_index.items()):
    player_key = PLAYER_MAP.get(pname)
    if not player_key or player_key == "test":
        continue  # escludi test
    pf = players_dir / f"{player_key}.json"
    if not pf.exists():
        grezzi_orfani.append((fname, qid, pname, player_key, "file player non esiste"))
        continue
    pd = json.loads(pf.read_text(encoding="utf-8"))
    games = pd.get("games", [])
    found = any(g.get("quizId") == qid for g in games)
    if not found:
        grezzi_orfani.append((fname, qid, pname, player_key, "non in games[]"))

if grezzi_orfani:
    print(f"  Grezzi NON presenti nei player file: {len(grezzi_orfani)}")
    for fname, qid, pname, pk, reason in grezzi_orfani:
        print(f"    {fname} | {pk} | {qid} | {reason}")
else:
    print("  ✅ Tutti i grezzi (non-test) risultano nei file player")

# === Check overall: quali dei grezzi non sono in overall.history? ===
print()
print("=== GREZZI MANCANTI DA OVERALL.HISTORY ===")
overall_path = players_dir / "overall.json"
overall = json.loads(overall_path.read_text(encoding="utf-8")) if overall_path.exists() else {}
history = overall.get("history", [])

mancanti_overall = []
for (qid, pname), fname in sorted(grezzo_index.items()):
    player_key = PLAYER_MAP.get(pname)
    if not player_key or player_key == "test":
        continue
    found = any(h.get("quizId") == qid and h.get("player") == player_key for h in history)
    if not found:
        mancanti_overall.append((fname, qid, player_key))

if mancanti_overall:
    print(f"  Grezzi non in overall.history: {len(mancanti_overall)}")
    for fname, qid, pk in mancanti_overall:
        print(f"    {fname} | {pk} | {qid}")
else:
    print("  ✅ Tutti i grezzi presenti in overall.history")
