/**
 * GET /api/player/:key — Profilo giocatore.
 * Stats aggregate + lista partite (con media del gruppo) + categorie deboli.
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
             ROUND(SUM(avg_time * total) / SUM(total), 1) as avg_time,
             MAX(score) as best_score, MAX(max_streak) as max_streak
      FROM games WHERE player_key = ?
    `).bind(playerKey).first();

    if (!stats || !stats.games) {
      return jsonResponse({ error: 'Giocatore non trovato' }, 404);
    }

    // Lista partite, con la media del gruppo sulla stessa puntata
    const { results: games } = await db.prepare(`
      SELECT g.quiz_id, g.quiz_title, g.timestamp, g.score, g.correct, g.total,
             g.percentage, g.max_streak, g.avg_time,
             (SELECT ROUND(AVG(g2.percentage)) FROM games g2
              WHERE g2.quiz_id = g.quiz_id AND g2.player_key IS NOT NULL
                AND g2.player_key != 'test') as group_pct,
             (SELECT COUNT(*) FROM games g2
              WHERE g2.quiz_id = g.quiz_id AND g2.player_key IS NOT NULL
                AND g2.player_key != 'test') as group_games
      FROM games g WHERE g.player_key = ?
      ORDER BY g.timestamp DESC
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
