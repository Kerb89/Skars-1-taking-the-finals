/***
 * Cloudflare Worker — Proxy per salvare risultati quiz su GitHub
 * + Aggiornamento automatico stats per giocatori riconosciuti
 * 
 * Variabili d'ambiente (Secrets su Cloudflare):
 *   GITHUB_TOKEN = Personal Access Token GitHub
 *   GITHUB_REPO  = "Kerb89/Skars-1-taking-the-finals"
 *
 * Deploy: wrangler deploy
 * URL: https://quiz-results.kerberozzo89.workers.dev
 */

const PLAYER_MAP = {
  'mattia': 'mattia', 'matt': 'mattia',
  'jacopo': 'jacopo', 'manuel': 'manuel',
  'tato': 'tato', 'gunny': 'gunny', 'ronny': 'gunny',
  '1': 'test'
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return corsResponse(null, 204);
    if (request.method !== 'POST') return corsResponse(JSON.stringify({ error: 'Metodo non permesso' }), 405);

    try {
      const body = await request.json();
      if (!body.filePath || !body.payload) return corsResponse(JSON.stringify({ error: 'Mancano filePath o payload' }), 400);

      const content = btoa(unescape(encodeURIComponent(JSON.stringify(body.payload, null, 2))));
      const saveResp = await githubPut(env, body.filePath, content, body.commitMessage || 'Nuovo risultato quiz');

      if (saveResp.status !== 201 && saveResp.status !== 200) {
        const err = await saveResp.json();
        return corsResponse(JSON.stringify({ error: err.message || 'Errore salvataggio' }), saveResp.status);
      }

      const playerName = (body.payload.playerName || '').trim().toLowerCase();
      const playerKey = PLAYER_MAP[playerName];
      if (playerKey) {
        try {
          await updatePlayerStats(env, playerKey, body.payload);
          await updateOverallStats(env, playerKey, body.payload);
        } catch (e) { console.error('Stats error:', e.message); }
      }

      return corsResponse(JSON.stringify({ success: true, statsUpdated: !!playerKey }), 200);
    } catch (err) {
      return corsResponse(JSON.stringify({ error: err.message }), 500);
    }
  }
};

function corsResponse(body, status = 200) {
  return new Response(body, { status, headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  }});
}

async function githubGet(env, path) {
  return await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
    headers: { 'Accept': 'application/vnd.github.v3+json', 'Authorization': `token ${env.GITHUB_TOKEN}`, 'User-Agent': 'Quiz-Results-Worker' }
  });
}

async function githubPut(env, path, contentBase64, message, sha = null) {
  const body = { message, content: contentBase64 };
  if (sha) body.sha = sha;
  return await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
    method: 'PUT', headers: { 'Accept': 'application/vnd.github.v3+json', 'Authorization': `token ${env.GITHUB_TOKEN}`, 'Content-Type': 'application/json', 'User-Agent': 'Quiz-Results-Worker' },
    body: JSON.stringify(body)
  });
}

async function readJsonFromRepo(env, path) {
  const resp = await githubGet(env, path);
  if (resp.status === 404) return { data: null, sha: null };
  if (!resp.ok) throw new Error(`GitHub GET ${path}: ${resp.status}`);
  const file = await resp.json();
  const decoded = decodeURIComponent(escape(atob(file.content.replace(/\n/g, ''))));
  return { data: JSON.parse(decoded), sha: file.sha };
}

async function writeJsonToRepo(env, path, data, message, sha) {
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(data, null, 2))));
  return await githubPut(env, path, encoded, message, sha);
}

async function updatePlayerStats(env, playerKey, result) {
  const path = `stats/players/${playerKey}.json`;
  const { data: existing, sha } = await readJsonFromRepo(env, path);
  const s = existing || { player: playerKey, totalGames: 0, totalScore: 0, totalCorrect: 0, totalQuestions: 0, avgPercentage: 0, avgTime: 0, games: [], weakCategories: {}, wrongQuestions: [] };

  s.totalGames += 1; s.totalScore += result.score || 0; s.totalCorrect += result.correct || 0; s.totalQuestions += result.total || 0;
  s.avgPercentage = Math.round(s.totalCorrect / s.totalQuestions * 100);
  s.avgTime = parseFloat(((s.avgTime * (s.totalGames - 1) + (result.avgTime || 0)) / s.totalGames).toFixed(1));

  s.games.push({ quizId: result.quizId, quizTitle: result.quizTitle || result.quizId, date: (result.timestamp || new Date().toISOString()).split('T')[0], score: result.score || 0, correct: result.correct || 0, total: result.total || 0, percentage: result.percentage || 0, maxStreak: result.maxStreak || 0, avgTime: result.avgTime || 0 });

  if (result.results && Array.isArray(result.results)) {
    const catStats = {};
    for (const r of result.results) {
      const cat = r.category || 'altro';
      if (!catStats[cat]) catStats[cat] = { wrong: 0, total: 0 };
      catStats[cat].total += 1;
      if (!r.correct) {
        catStats[cat].wrong += 1;
        const ew = s.wrongQuestions.find(w => w.question === r.question && w.correctAnswer === r.correctOption);
        if (ew) { ew.timesWrong += 1; if (!ew.quizIds.includes(result.quizId)) ew.quizIds.push(result.quizId); }
        else { s.wrongQuestions.push({ question: r.question, category: cat, correctAnswer: r.correctOption || null, givenAnswer: r.chosenOption || '(timeout)', quizIds: [result.quizId], timesWrong: 1 }); }
      }
    }
    for (const [cat, st] of Object.entries(catStats)) {
      if (!s.weakCategories[cat]) s.weakCategories[cat] = { wrong: 0, total: 0, percentage: 0 };
      s.weakCategories[cat].wrong += st.wrong; s.weakCategories[cat].total += st.total;
      s.weakCategories[cat].percentage = Math.round((1 - s.weakCategories[cat].wrong / s.weakCategories[cat].total) * 100);
    }
  }
  s.wrongQuestions.sort((a, b) => b.timesWrong - a.timesWrong);
  await writeJsonToRepo(env, path, s, `Stats ${playerKey} aggiornate`, sha);
}

async function updateOverallStats(env, playerKey, result) {
  const path = 'stats/players/overall.json';
  const { data: existing, sha } = await readJsonFromRepo(env, path);
  const o = existing || { lastUpdated: null, totalGamesPlayed: 0, leaderboard: {}, history: [], mostWrongQuestions: [] };

  o.lastUpdated = new Date().toISOString(); o.totalGamesPlayed += 1;
  if (!o.leaderboard[playerKey]) o.leaderboard[playerKey] = { games: 0, totalScore: 0, totalCorrect: 0, totalQuestions: 0, avgPercentage: 0, avgTime: 0 };
  const lb = o.leaderboard[playerKey];
  lb.games += 1; lb.totalScore += result.score || 0; lb.totalCorrect += result.correct || 0; lb.totalQuestions += result.total || 0;
  lb.avgPercentage = Math.round(lb.totalCorrect / lb.totalQuestions * 100);
  lb.avgTime = parseFloat(((lb.avgTime * (lb.games - 1) + (result.avgTime || 0)) / lb.games).toFixed(1));

  o.history.push({ date: (result.timestamp || new Date().toISOString()).split('T')[0], quizId: result.quizId, quizTitle: result.quizTitle || result.quizId, player: playerKey, score: result.score || 0, correct: result.correct || 0, total: result.total || 0, percentage: result.percentage || 0 });

  if (result.results && Array.isArray(result.results)) {
    for (const r of result.results) {
      if (!r.correct) {
        const ew = o.mostWrongQuestions.find(w => w.question === r.question && w.correctAnswer === r.correctOption);
        if (ew) { ew.timesWrong += 1; if (!ew.wrongBy.includes(playerKey)) ew.wrongBy.push(playerKey); }
        else { o.mostWrongQuestions.push({ question: r.question, category: r.category || 'altro', correctAnswer: r.correctOption || null, wrongBy: [playerKey], timesWrong: 1 }); }
      }
    }
    o.mostWrongQuestions.sort((a, b) => b.timesWrong - a.timesWrong);
  }
  await writeJsonToRepo(env, path, o, `Overall stats aggiornate`, sha);
}
