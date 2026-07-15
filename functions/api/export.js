/**
 * GET /api/export — Dump JSON completo di games + answers per backup.
 * Produce un JSON con tutti i dati per archiviazione nel repo.
 */

export async function onRequestGet(context) {
  const db = context.env.DB;

  try {
    const { results: games } = await db.prepare(`
      SELECT * FROM games ORDER BY timestamp ASC
    `).all();

    const { results: answers } = await db.prepare(`
      SELECT * FROM answers ORDER BY game_id ASC, question_num ASC
    `).all();

    return jsonResponse({
      exported_at: new Date().toISOString(),
      games_count: games.length,
      answers_count: answers.length,
      games,
      answers
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
