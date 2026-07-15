/**
 * GET /api/player/:key — Profilo giocatore.
 * Stats aggregate + lista partite + categorie deboli.
 */

export async function onRequestGet(context) {
  const db = context.env.DB;
  const playerKey = context.params.key;

  if (!playerKey) return jsonResponse({ error: 'player key mancante' }, 400);

  try {
    // Stats aggregate
    const stats = await db.prepare(`
      SELECT player_key, COUNT(*) as games, SUM(score) as total_score,
             SUM(correct) as total_correct, SUM(total) as total_questions,
             ROUND(100.0 * SUM(correct) / SUM(total)) as avg_pct,
             ROUND(SUM(avg_time * total) / SUM(total), 1) as avg_time
      FROM games WHERE player_key = ?
    `).bind(playerKey).first();

    if (!stats || !stats.games) {
      return jsonResponse({ error: 'Giocatore non trovato' }, 404);
    }

    // Lista partite
    const { results: games } = await db.prepare(`
      SELECT quiz_id, quiz_title, timestamp, score, correct, total,
             percentage, max_streak, avg_time
      FROM games WHERE player_key = ?
      ORDER BY timestamp DESC
    `).bind(playerKey).all();

    // Categorie deboli
    const { results: categories } = await db.prepare(`
      SELECT a.category, COUNT(*) as total,
             SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) as wrong,
             ROUND(100.0 * SUM(a.is_correct) / COUNT(*)) as pct_correct
      FROM answers a JOIN games g ON a.game_id = g.id
      WHERE g.player_key = ?
      GROUP BY a.category ORDER BY pct_correct ASC
    `).bind(playerKey).all();

    return jsonResponse({
      player: playerKey,
      stats,
      games,
      weakCategories: categories
    });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    }
  });
}
