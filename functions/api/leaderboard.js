/**
 * GET /api/leaderboard — Classifica generale.
 * Esclude test e giocatori ignoti (player_key NULL).
 */

export async function onRequestGet(context) {
  const db = context.env.DB;

  try {
    const { results } = await db.prepare(`
      SELECT player_key, COUNT(*) as games, SUM(score) as total_score,
             SUM(correct) as total_correct, SUM(total) as total_questions,
             ROUND(100.0 * SUM(correct) / SUM(total)) as avg_pct,
             ROUND(SUM(avg_time * total) / SUM(total), 1) as avg_time
      FROM games
      WHERE player_key IS NOT NULL AND player_key != 'test'
      GROUP BY player_key ORDER BY total_score DESC
    `).all();

    return jsonResponse({ leaderboard: results });
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
