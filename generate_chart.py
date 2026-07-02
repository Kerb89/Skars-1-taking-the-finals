import json
import os

# Load player stats
players_dir = r'stats\players'
player_files = ['mattia.json', 'jacopo.json', 'tato.json']
player_data = {}

for pf in player_files:
    path = os.path.join(players_dir, pf)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            player_data[pf.replace('.json', '')] = json.load(f)

# Print summary
print("=== RIEPILOGO GIOCATORI ===\n")
for name, data in player_data.items():
    print(f"👤 {name.upper()}")
    print(f"   Partite: {data['totalGames']}")
    print(f"   Punteggio totale: {data['totalScore']}")
    print(f"   Risposte corrette: {data['totalCorrect']}/{data['totalQuestions']} ({data['avgPercentage']}%)")
    print(f"   Tempo medio: {data['avgTime']}s")
    print()

# Extract game-by-game data for chart
print("\n=== DATI PER GRAFICO (% corrette per partita) ===\n")
all_games = {}
for name, data in player_data.items():
    all_games[name] = [(g['quizId'], g['percentage'], g['score']) for g in data.get('games', [])]
    print(f"{name}: {len(all_games[name])} partite")
    for g in all_games[name]:
        print(f"  {g[0]}: {g[1]}% ({g[2]} pt)")
    print()

# Generate HTML chart
html = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Quizzone - Prestazioni Giocatori</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1923; color: #e0e6ed; padding: 30px; }
.container { max-width: 1000px; margin: 0 auto; }
h1 { text-align: center; color: #4fc3f7; margin-bottom: 30px; }
.chart-box { background: #1a2a3a; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 30px; }
.stat-card { background: #1a2a3a; border-radius: 12px; padding: 20px; text-align: center; }
.stat-card h3 { color: #4fc3f7; margin-bottom: 8px; font-size: 1.1rem; }
.stat-card .value { font-size: 2rem; font-weight: 700; color: #fff; }
.stat-card .sub { color: #8899aa; font-size: 0.85rem; margin-top: 4px; }
</style>
</head>
<body>
<div class="container">
<h1>Quizzone — Prestazioni Giocatori</h1>
<div class="stats-grid">
"""

# Add player summary cards
colors = {'mattia': '#4fc3f7', 'jacopo': '#66bb6a', 'tato': '#ffb74d'}
for name, data in player_data.items():
    html += f"""<div class="stat-card">
<h3 style="color:{colors.get(name,'#fff')}">{name.upper()}</h3>
<div class="value">{data['avgPercentage']}%</div>
<div class="sub">{data['totalGames']} partite &middot; {data['totalScore']} pt totali &middot; {data['avgTime']}s media</div>
</div>
"""

html += """</div>
<div class="chart-box">
<canvas id="percentChart"></canvas>
</div>
<div class="chart-box">
<canvas id="scoreChart"></canvas>
</div>
</div>
<script>
"""

# Build datasets
# Get all unique quiz IDs in order
all_quiz_ids = []
for name, games in all_games.items():
    for g in games:
        if g[0] not in all_quiz_ids:
            all_quiz_ids.append(g[0])

# Sort quiz IDs naturally
def quiz_sort_key(qid):
    import re
    m = re.search(r'(\d+)', qid)
    return int(m.group(1)) if m else 0

# Actually just use Python to produce the sorted list
sorted_ids = sorted(all_quiz_ids, key=lambda x: int(''.join(filter(str.isdigit, x)) or '0'))

# Create label-friendly names
labels = [qid.replace('quiz_puntata', 'P').replace('_misto', '') for qid in sorted_ids]

html += f"const labels = {json.dumps(labels)};\n"

# Percentage datasets
html += "const percentData = {\n  labels: labels,\n  datasets: [\n"
for name, games in all_games.items():
    game_map = {g[0]: g[1] for g in games}
    values = [game_map.get(qid, 'null') for qid in sorted_ids]
    values_str = str(values).replace("'null'", "null")
    html += f"    {{label:'{name.upper()}', data:{values_str}, borderColor:'{colors.get(name,'#fff')}', backgroundColor:'{colors.get(name,'#fff')}22', tension:0.3, spanGaps:true}},\n"
html += "  ]\n};\n"

# Score datasets
html += "const scoreData = {\n  labels: labels,\n  datasets: [\n"
for name, games in all_games.items():
    game_map = {g[0]: g[2] for g in games}
    values = [game_map.get(qid, 'null') for qid in sorted_ids]
    values_str = str(values).replace("'null'", "null")
    html += f"    {{label:'{name.upper()}', data:{values_str}, borderColor:'{colors.get(name,'#fff')}', backgroundColor:'{colors.get(name,'#fff')}22', tension:0.3, spanGaps:true}},\n"
html += "  ]\n};\n"

html += """
new Chart(document.getElementById('percentChart'), {
  type: 'line',
  data: percentData,
  options: {
    responsive: true,
    plugins: { title: { display: true, text: '% Risposte Corrette per Puntata', color: '#e0e6ed', font:{size:16} }, legend: { labels: { color: '#e0e6ed' } } },
    scales: { y: { min: 0, max: 100, ticks: { color: '#8899aa' }, grid: { color: '#2a3a4a' } }, x: { ticks: { color: '#8899aa' }, grid: { color: '#2a3a4a' } } }
  }
});

new Chart(document.getElementById('scoreChart'), {
  type: 'line',
  data: scoreData,
  options: {
    responsive: true,
    plugins: { title: { display: true, text: 'Punteggio per Puntata', color: '#e0e6ed', font:{size:16} }, legend: { labels: { color: '#e0e6ed' } } },
    scales: { y: { min: 0, ticks: { color: '#8899aa' }, grid: { color: '#2a3a4a' } }, x: { ticks: { color: '#8899aa' }, grid: { color: '#2a3a4a' } } }
  }
});
</script>
</body>
</html>
"""

output_path = 'stats_chart.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Grafico generato: {output_path}")
print("   Aprilo nel browser per vedere i grafici interattivi!")
