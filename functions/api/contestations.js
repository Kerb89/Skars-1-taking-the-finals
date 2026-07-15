/**
 * GET /api/contestations — Tutte le contestazioni.
 */

export async function onRequestGet(context) {
  const db = context.env.DB;

  try {
    const { results } = await db.prepare(`
      SELECT g.player_key, g.quiz_id, g.timestamp, a.question_num,
             a.question_text, a.correct_option, a.chosen_option, a.contest
      FROM answers a JOIN games g ON a.game_id = g.id
      WHERE a.contest IS NOT NULL
      ORDER BY g.timestamp DESC
    `).all();

    return jsonResponse({ contestations: results });
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
