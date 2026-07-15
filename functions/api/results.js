/**
 * POST /api/results — Salva una partita nel database D1.
 * Atomico (db.batch) e idempotente (ON CONFLICT DO NOTHING).
 *
 * Binding D1: env.DB (configurato in wrangler.toml / Pages settings)
 */

const PLAYER_MAP = {
  'mattia': 'mattia', 'matt': 'mattia',
  'jacopo': 'jacopo', 'manuel': 'manuel',
  'tato': 'tato', 'gunny': 'gunny', 'ronny': 'gunny',
  '1': 'test'
};

export async function onRequestPost(context) {
  const { env, request } = context;
  const db = env.DB;

  try {
    const body = await request.json();

    // === Validazione ===
    if (!body.uploadId || !body.uploadId.trim()) {
      return jsonResponse({ error: 'uploadId mancante' }, 400);
    }
    if (!body.quizId || !/^quiz_puntata\d+_/.test(body.quizId)) {
      return jsonResponse({ error: 'quizId non valido (atteso: quiz_puntata\\d+_...)' }, 400);
    }
    if (!body.playerName || !body.playerName.trim()) {
      return jsonResponse({ error: 'playerName mancante' }, 400);
    }
    if (!Array.isArray(body.results) || body.results.length > 50) {
      return jsonResponse({ error: 'results deve essere un array con max 50 elementi' }, 400);
    }
    const score = Number(body.score) || 0;
    const correct = Number(body.correct) || 0;
    const total = Number(body.total) || 0;
    if (correct > total) {
      return jsonResponse({ error: 'correct > total' }, 400);
    }

    // === Mapping giocatore ===
    const playerNameRaw = body.playerName.trim();
    const playerKey = PLAYER_MAP[playerNameRaw.toLowerCase()] || null;

    // === Costruisci batch atomico ===
    const uploadId = body.uploadId.trim();
    const stmts = [];

    // stmt 1: INSERT game
    stmts.push(
      db.prepare(`
        INSERT INTO games (upload_id, quiz_id, quiz_title, player_key, player_name_raw,
                           timestamp, score, correct, total, percentage, max_streak,
                           avg_time, multiplier_used, multiplier_remaining, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'upload')
        ON CONFLICT(upload_id) DO NOTHING
      `).bind(
        uploadId,
        body.quizId,
        body.quizTitle || body.quizId,
        playerKey,
        playerNameRaw,
        body.timestamp || new Date().toISOString(),
        score,
        correct,
        total,
        Number(body.percentage) || 0,
        Number(body.maxStreak) || 0,
        Number(body.avgTime) || 0,
        (body.multiplierStats && body.multiplierStats.used) || 0,
        (body.multiplierStats && body.multiplierStats.remaining) || 0
      )
    );

    // stmt 2..N: INSERT answers via subquery su upload_id
    for (let i = 0; i < body.results.length; i++) {
      const r = body.results[i];
      stmts.push(
        db.prepare(`
          INSERT INTO answers (game_id, question_num, question_text, category,
                               is_correct, is_timeout, points, streak_bonus,
                               multiplier_used, time_used, chosen_option,
                               correct_option, contest)
          SELECT g.id, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
          FROM games g WHERE g.upload_id = ?
          ON CONFLICT(game_id, question_num) DO NOTHING
        `).bind(
          i + 1,
          r.question || null,
          r.category || null,
          r.correct ? 1 : 0,
          r.timeout ? 1 : 0,
          Number(r.points) || 0,
          Number(r.streakBonus) || 0,
          r.multiplierUsed ? 1 : 0,
          Number(r.timeUsed) || 0,
          r.chosenOption || null,
          r.correctOption || null,
          (r.contest && r.contest.trim()) || null,
          uploadId
        )
      );
    }

    // === Esegui batch atomico ===
    const results = await db.batch(stmts);

    // meta.changes dello stmt 1: >0 = nuovo, 0 = dedup
    const inserted = results[0].meta.changes > 0;

    return jsonResponse({ success: true, inserted });
  } catch (err) {
    console.error('POST /api/results error:', err.message);
    return jsonResponse({ error: err.message }, 500);
  }
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

// Handle CORS preflight
export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
